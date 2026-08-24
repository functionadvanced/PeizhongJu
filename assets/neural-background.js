/*
  Floating neural-network background effect

  Effect summary:
  - Adds a full-viewport, fixed-position canvas behind the page content.
  - Draws multiple soft blue/purple "mini neural nets" made of moving nodes
    and translucent connecting edges.
  - Each mini-net drifts across the viewport, wraps around screen edges, and
    gently rotates while its nodes wiggle locally.
  - Nearby nets can merge: bridge edges fade in, then both node sets are
    committed to one shared motion group so they continue moving together.
  - Large nets can split: cross-partition edges fade out, then the same nodes
    are committed into smaller child motion groups.
  - Node count stays constant during merge/split. The lifecycle changes graph
    membership and edge visibility rather than creating/deleting particles.

  Key implementation points:
  - Plain JavaScript and Canvas 2D only; no external dependencies.
  - The canvas is inserted as <canvas id="neural-background" aria-hidden="true">.
  - CSS should place #neural-background at fixed inset: 0, pointer-events: none,
    z-index below content, and set the page content above it.
  - The script exits early on Reveal.js slide pages by checking ".reveal".
    Remove that guard if the effect should appear everywhere.
  - Respects prefers-reduced-motion by slowing the animation instead of
    freezing it completely, and caps rendering at 20 FPS in that mode.
  - Caps normal rendering at 60 FPS so high-refresh displays do not perform
    unnecessary canvas redraws.
  - Caps devicePixelRatio at 2 to avoid excessive canvas work on high-DPI screens.
  - Normal edge drawing is optimized per cluster, so it does not compare every
    node against every other node globally.

  Tuning guide:
  - Initial density: spacingX / spacingY in createNodes().
  - Cluster sizes: scale, clusterRadius, and nodeCount in createNodes().
  - Motion speed: travelSpeed in createNodes(), plus node.speed and node.drift.
  - Edge reach/visibility: cluster.edgeLength and alpha multipliers in draw().
  - Lifecycle frequency: lifecycleTimer threshold in updateLifecycle().
  - Merge chance/distance: mergeDistance and Math.random() threshold.
  - Split threshold/chance: node-count check and Math.random() threshold.

  Integration requirements:
  - Load this script after document.body exists, e.g. near the end of <body> or
    via a framework hook that runs after mount.
  - Include print CSS that hides #neural-background if printed output should be
    plain white and ink-friendly.
  - Recommended CSS:
      #neural-background {
        inset: 0;
        opacity: 0.38;
        pointer-events: none;
        position: fixed;
        z-index: 0;
      }
      body > * {
        position: relative;
        z-index: 1;
      }
      @media print {
        #neural-background { display: none !important; }
      }
*/

(function () {
  if (document.querySelector(".reveal")) {
    return;
  }

  var prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var canvas = document.createElement("canvas");
  var ctx = canvas.getContext("2d");
  var bridges = [];
  var clusters = [];
  var nodes = [];
  var frameId = null;
  var width = 0;
  var height = 0;
  var pixelRatio = 1;
  var lastFrameTime = null;
  var lastDrawTime = null;
  var frameAccumulator = 0;
  var animationTime = 0;
  var lifecycleTimer = 0;
  var currentTimeSeconds = 0;
  var nextClusterId = 0;
  var nextNodeId = 0;

  canvas.id = "neural-background";
  canvas.setAttribute("aria-hidden", "true");
  document.body.prepend(canvas);

  function resetCanvas() {
    pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = Math.floor(width * pixelRatio);
    canvas.height = Math.floor(height * pixelRatio);
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    ctx.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  }

  function createCluster(x, y, scale, velocityAngle, velocitySpeed) {
    var resolvedScale = Math.max(0.48, Math.min(scale, 2.25));
    var radius = (width < 720 ? 52 : 66) * resolvedScale;
    var speed = velocitySpeed || (3 + Math.random() * 9);
    var angle = velocityAngle === undefined ? Math.random() * Math.PI * 2 : velocityAngle;
    var id = nextClusterId;

    nextClusterId += 1;

    return {
      id: id,
      x: x,
      y: y,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      edgeLength: (width < 720 ? 92 : 106) * (0.78 + resolvedScale * 0.28),
      phase: Math.random() * Math.PI * 2,
      phase2: Math.random() * Math.PI * 2,
      radius: radius,
      rotation: Math.random() * Math.PI * 2,
      rotationSpeed: (Math.random() - 0.5) * 0.035,
      scale: resolvedScale,
      merge: null,
      split: null,
      cooldown: 3 + Math.random() * 4
    };
  }

  function getClusterNodes(cluster) {
    return nodes.filter(function (node) {
      return node.cluster === cluster;
    });
  }

  function attachNodesToCluster(cluster, clusterNodes) {
    var cos = Math.cos(cluster.rotation);
    var sin = Math.sin(cluster.rotation);

    clusterNodes.forEach(function (node) {
      var wiggleX = Math.sin(currentTimeSeconds * node.speed + node.phase) * node.drift;
      var wiggleY = Math.cos(currentTimeSeconds * node.speed * 0.82 + node.phase2) * node.drift;
      var dx = node.renderX - cluster.x - wiggleX;
      var dy = node.renderY - cluster.y - wiggleY;

      node.cluster = cluster;
      node.clusterId = cluster.id;
      node.offsetX = dx * cos + dy * sin;
      node.offsetY = -dx * sin + dy * cos;
      node.drift = Math.max(5, Math.min(node.drift, 18 * (0.8 + cluster.scale * 0.18)));
    });
  }

  function createNodes() {
    clusters = [];
    bridges = [];
    nodes = [];
    nextClusterId = 0;
    nextNodeId = 0;
    lifecycleTimer = 0;

    var spacingX = width < 720 ? 230 : 320;
    var spacingY = width < 720 ? 210 : 250;
    var cols = Math.ceil(width / spacingX) + 2;
    var rows = Math.ceil(height / spacingY) + 2;

    for (var row = 0; row < rows; row += 1) {
      for (var col = 0; col < cols; col += 1) {
        if ((row + col) % 3 === 1 && Math.random() < 0.55) {
          continue;
        }

        var centerX = (col - 0.45) * spacingX + (Math.random() - 0.5) * 82;
        var centerY = (row - 0.45) * spacingY + (Math.random() - 0.5) * 70;
        var scale = 0.62 + Math.pow(Math.random(), 1.7) * 1.18;
        var clusterRadius = (width < 720 ? 52 : 66) * scale;
        var nodeCount = Math.round(4 + scale * 3 + Math.random() * 4);
        var cluster = createCluster(centerX, centerY, scale);

        clusters.push(cluster);

        for (var index = 0; index < nodeCount; index += 1) {
          var angle = (index / nodeCount) * Math.PI * 2 + Math.random() * 0.75;
          var distance = clusterRadius * (0.38 + Math.random() * 0.68);
          var offsetX = Math.cos(angle) * distance;
          var offsetY = Math.sin(angle) * distance * (0.72 + Math.random() * 0.28);
          var phase = Math.random() * Math.PI * 2;

          if (index === 0) {
            offsetX = 0;
            offsetY = 0;
          }

          nodes.push({
            id: nextNodeId,
            clusterId: cluster.id,
            cluster: cluster,
            offsetX: offsetX,
            offsetY: offsetY,
            x: centerX + offsetX,
            y: centerY + offsetY,
            renderX: centerX + offsetX,
            renderY: centerY + offsetY,
            phase: phase,
            phase2: Math.random() * Math.PI * 2,
            speed: 0.2 + Math.random() * 0.18,
            radius: (1.65 + Math.random() * 1.8) * (0.82 + scale * 0.12),
            drift: (6 + Math.random() * 10) * (0.72 + scale * 0.18)
          });

          nextNodeId += 1;
        }
      }
    }
  }

  function commitMerge(bridge) {
    var firstNodes = getClusterNodes(bridge.first);
    var secondNodes = getClusterNodes(bridge.second);
    var mergedNodes = firstNodes.concat(secondNodes);

    if (!mergedNodes.length) {
      return;
    }

    var x = mergedNodes.reduce(function (sum, node) { return sum + node.renderX; }, 0) / mergedNodes.length;
    var y = mergedNodes.reduce(function (sum, node) { return sum + node.renderY; }, 0) / mergedNodes.length;
    var speedX = (bridge.first.vx * firstNodes.length + bridge.second.vx * secondNodes.length) / mergedNodes.length;
    var speedY = (bridge.first.vy * firstNodes.length + bridge.second.vy * secondNodes.length) / mergedNodes.length;
    var velocityAngle = Math.atan2(speedY, speedX) + (Math.random() - 0.5) * 0.25;
    var velocitySpeed = Math.max(2.5, Math.min(10, Math.sqrt(speedX * speedX + speedY * speedY)));
    var scale = Math.sqrt(bridge.first.scale * bridge.first.scale + bridge.second.scale * bridge.second.scale) * 0.76;
    var merged = createCluster(x, y, scale, velocityAngle, velocitySpeed);
    var partitions = {};

    firstNodes.forEach(function (node) {
      partitions[node.id] = 0;
    });
    secondNodes.forEach(function (node) {
      partitions[node.id] = 1;
    });

    merged.radius = Math.max(bridge.first.radius, bridge.second.radius) * 1.18;
    merged.edgeLength = Math.max(bridge.first.edgeLength, bridge.second.edgeLength) * 1.18;
    merged.rotation = 0;
    merged.merge = {
      alpha: 0.25,
      partitions: partitions
    };
    merged.cooldown = 8 + Math.random() * 5;
    clusters = clusters.filter(function (cluster) {
      return cluster !== bridge.first && cluster !== bridge.second;
    });
    clusters.push(merged);
    attachNodesToCluster(merged, mergedNodes);
  }

  function commitSplit(cluster) {
    var clusterNodes = getClusterNodes(cluster);
    var split = cluster.split;
    var groups = {};

    if (!split) {
      return;
    }

    clusterNodes.forEach(function (node) {
      var groupIndex = split.partitions[node.id];
      groups[groupIndex] = groups[groupIndex] || [];
      groups[groupIndex].push(node);
    });

    clusters = clusters.filter(function (item) {
      return item !== cluster;
    });

    Object.keys(groups).forEach(function (key) {
      var group = groups[key];
      var x = group.reduce(function (sum, node) { return sum + node.renderX; }, 0) / group.length;
      var y = group.reduce(function (sum, node) { return sum + node.renderY; }, 0) / group.length;
      var angle = Math.atan2(cluster.vy, cluster.vx) + (Number(key) - (Object.keys(groups).length - 1) / 2) * 0.72 + (Math.random() - 0.5) * 0.35;
      var speed = Math.max(3.5, Math.min(12, Math.sqrt(cluster.vx * cluster.vx + cluster.vy * cluster.vy) + Math.random() * 2.5));
      var scale = Math.max(0.56, Math.min(1.35, 0.5 + group.length * 0.11 + Math.random() * 0.16));
      var piece = createCluster(x, y, scale, angle, speed);

      piece.rotation = cluster.rotation;
      piece.rotationSpeed = cluster.rotationSpeed + (Math.random() - 0.5) * 0.025;
      piece.cooldown = 8 + Math.random() * 5;
      clusters.push(piece);
      attachNodesToCluster(piece, group);
    });
  }

  function mergeClusters(first, second) {
    var existing = bridges.find(function (bridge) {
      return (bridge.first === first && bridge.second === second) || (bridge.first === second && bridge.second === first);
    });

    if (existing) {
      existing.target = 1;
      existing.cooldown = 8 + Math.random() * 5;
      return;
    }

    bridges.push({
      first: first,
      second: second,
      alpha: 0,
      target: 1,
      committed: false,
      cooldown: 8 + Math.random() * 5,
      edgeLength: Math.max(first.edgeLength, second.edgeLength) * 1.15
    });

    first.cooldown = 7 + Math.random() * 4;
    second.cooldown = 7 + Math.random() * 4;
  }

  function splitCluster(cluster) {
    var clusterNodes = getClusterNodes(cluster);
    var pieceCount = clusterNodes.length > 16 ? 3 : 2;
    var partitions = {};

    clusterNodes
      .slice()
      .sort(function (a, b) {
        return Math.atan2(a.renderY - cluster.y, a.renderX - cluster.x) - Math.atan2(b.renderY - cluster.y, b.renderX - cluster.x);
      })
      .forEach(function (node, index) {
        var groupIndex = Math.min(pieceCount - 1, Math.floor(index / Math.ceil(clusterNodes.length / pieceCount)));
        partitions[node.id] = groupIndex;
      });

    cluster.split = {
      alpha: 0,
      partitions: partitions
    };
    cluster.cooldown = 10 + Math.random() * 5;
  }

  function updateLifecycle(delta) {
    lifecycleTimer += delta;

    for (var i = 0; i < clusters.length; i += 1) {
      clusters[i].cooldown = Math.max(0, clusters[i].cooldown - delta);
    }

    if (lifecycleTimer < 1.25) {
      return;
    }

    lifecycleTimer = 0;

    for (var splitIndex = 0; splitIndex < clusters.length; splitIndex += 1) {
      var candidate = clusters[splitIndex];

      if (!candidate.split && candidate.cooldown <= 0 && getClusterNodes(candidate).length >= 13 && Math.random() < 0.18) {
        splitCluster(candidate);
        return;
      }
    }

    for (var a = 0; a < clusters.length; a += 1) {
      for (var b = a + 1; b < clusters.length; b += 1) {
        var first = clusters[a];
        var second = clusters[b];

        if (first.cooldown > 0 || second.cooldown > 0) {
          continue;
        }

        var dx = first.x - second.x;
        var dy = first.y - second.y;
        var distance = Math.sqrt(dx * dx + dy * dy);
        var mergeDistance = (first.radius + second.radius) * 0.64;

        if (distance < mergeDistance && Math.random() < 0.24) {
          mergeClusters(first, second);
          return;
        }
      }
    }
  }

  function updateEdgeTransitions(delta) {
    clusters.forEach(function (cluster) {
      if (cluster.merge) {
        cluster.merge.alpha = Math.min(1, cluster.merge.alpha + delta * 0.7);

        if (cluster.merge.alpha >= 0.99) {
          cluster.merge = null;
        }
      }

      if (cluster.split) {
        cluster.split.alpha = Math.min(1, cluster.split.alpha + delta * 0.55);

        if (cluster.split.alpha >= 0.98) {
          commitSplit(cluster);
        }
      }
    });

    bridges.forEach(function (bridge) {
      bridge.alpha += (bridge.target - bridge.alpha) * Math.min(1, delta * 1.35);

      if (!bridge.committed && bridge.alpha >= 0.94) {
        bridge.committed = true;
        commitMerge(bridge);
        bridge.target = 0;
      }
    });

    bridges = bridges.filter(function (bridge) {
      return bridge.alpha > 0.015 || bridge.target > 0;
    });
  }

  function getLifecycleEdgeFactor(first, second) {
    var merge = first.cluster.merge;
    var split = first.cluster.split;
    var factor = 1;

    if (merge && merge.partitions[first.id] !== merge.partitions[second.id]) {
      factor *= merge.alpha;
    }

    if (!split || split.partitions[first.id] === split.partitions[second.id]) {
      return factor;
    }

    return factor * (1 - split.alpha);
  }

  function getNodesByCluster() {
    var nodesByCluster = new Map();

    clusters.forEach(function (cluster) {
      nodesByCluster.set(cluster, []);
    });

    nodes.forEach(function (node) {
      if (nodesByCluster.has(node.cluster)) {
        nodesByCluster.get(node.cluster).push(node);
      }
    });

    return nodesByCluster;
  }

  function drawBridgeEdges(nodesByCluster) {
    bridges.forEach(function (bridge) {
      var firstNodes = nodesByCluster.get(bridge.first) || [];
      var secondNodes = nodesByCluster.get(bridge.second) || [];
      var candidates = [];

      firstNodes.forEach(function (first) {
        secondNodes.forEach(function (second) {
          var dx = first.renderX - second.renderX;
          var dy = first.renderY - second.renderY;
          var distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < bridge.edgeLength) {
            candidates.push({
              first: first,
              second: second,
              distance: distance
            });
          }
        });
      });

      candidates
        .sort(function (a, b) { return a.distance - b.distance; })
        .slice(0, 5)
        .forEach(function (candidate) {
          var alpha = (1 - candidate.distance / bridge.edgeLength) * 0.34 * bridge.alpha;

          if (alpha <= 0.01) {
            return;
          }

          ctx.beginPath();
          ctx.moveTo(candidate.first.renderX, candidate.first.renderY);
          ctx.lineTo(candidate.second.renderX, candidate.second.renderY);
          ctx.strokeStyle = "rgba(39, 128, 227, " + alpha.toFixed(3) + ")";
          ctx.lineWidth = 1;
          ctx.stroke();
        });
    });
  }

  function draw(time, delta) {
    var t = time * 0.001;
    currentTimeSeconds = t;
    ctx.clearRect(0, 0, width, height);

    for (var clusterIndex = 0; clusterIndex < clusters.length; clusterIndex += 1) {
      var cluster = clusters[clusterIndex];
      var margin = cluster.radius + 48;

      cluster.x += cluster.vx * delta;
      cluster.y += cluster.vy * delta;
      cluster.rotation += cluster.rotationSpeed * delta;

      if (cluster.x > width + margin) {
        cluster.x = -margin;
      } else if (cluster.x < -margin) {
        cluster.x = width + margin;
      }

      if (cluster.y > height + margin) {
        cluster.y = -margin;
      } else if (cluster.y < -margin) {
        cluster.y = height + margin;
      }
    }

    for (var i = 0; i < nodes.length; i += 1) {
      var node = nodes[i];
      var cos = Math.cos(node.cluster.rotation);
      var sin = Math.sin(node.cluster.rotation);
      var rotatedX = node.offsetX * cos - node.offsetY * sin;
      var rotatedY = node.offsetX * sin + node.offsetY * cos;

      node.x = node.cluster.x + rotatedX + Math.sin(t * node.speed + node.phase) * node.drift;
      node.y = node.cluster.y + rotatedY + Math.cos(t * node.speed * 0.82 + node.phase2) * node.drift;
      node.renderX = node.x;
      node.renderY = node.y;
    }

    updateLifecycle(delta);
    updateEdgeTransitions(delta);
    var nodesByCluster = getNodesByCluster();

    clusters.forEach(function (cluster) {
      var clusterNodes = nodesByCluster.get(cluster) || [];

      for (var a = 0; a < clusterNodes.length; a += 1) {
        for (var b = a + 1; b < clusterNodes.length; b += 1) {
          var first = clusterNodes[a];
          var second = clusterNodes[b];
          var dx = first.renderX - second.renderX;
          var dy = first.renderY - second.renderY;
          var distance = Math.sqrt(dx * dx + dy * dy);
          var edgeLength = cluster.edgeLength;
          var edgeFactor = getLifecycleEdgeFactor(first, second);

          if (distance < edgeLength && edgeFactor > 0.015) {
            var alpha = (1 - distance / edgeLength) * 0.38 * edgeFactor;
            ctx.beginPath();
            ctx.moveTo(first.renderX, first.renderY);
            ctx.lineTo(second.renderX, second.renderY);
            ctx.strokeStyle = "rgba(39, 128, 227, " + alpha.toFixed(3) + ")";
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }
    });

    drawBridgeEdges(nodesByCluster);

    for (var n = 0; n < nodes.length; n += 1) {
      var point = nodes[n];
      var pulse = 0.65 + Math.sin(t * 0.7 + point.phase) * 0.15;
      ctx.beginPath();
      ctx.arc(point.renderX, point.renderY, point.radius, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(39, 128, 227, " + pulse.toFixed(3) + ")";
      ctx.fill();

      if (n % 6 === 0) {
        ctx.beginPath();
        ctx.arc(point.renderX, point.renderY, point.radius + 2.5, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(153, 84, 187, 0.12)";
        ctx.fill();
      }
    }
  }

  function animate(time) {
    var targetFrameRate = prefersReducedMotion.matches ? 20 : 60;
    var frameInterval = 1000 / targetFrameRate;

    if (lastFrameTime === null) {
      lastFrameTime = time;
      lastDrawTime = time;
      draw(animationTime * 1000, 0);
    } else {
      frameAccumulator += Math.min(time - lastFrameTime, 60);
      lastFrameTime = time;

      if (frameAccumulator + 0.25 >= frameInterval) {
        var delta = Math.min((time - lastDrawTime) / 1000, 0.06);
        var motionScale = prefersReducedMotion.matches ? 0.45 : 1;

        frameAccumulator = frameAccumulator >= frameInterval ? frameAccumulator % frameInterval : 0;
        animationTime += delta * motionScale;
        draw(animationTime * 1000, delta * motionScale);
        lastDrawTime = time;
      }
    }

    frameId = window.requestAnimationFrame(animate);
  }

  function start() {
    if (frameId) {
      return;
    }

    frameId = window.requestAnimationFrame(animate);
  }

  function rebuild() {
    resetCanvas();
    createNodes();
    lastFrameTime = null;
    lastDrawTime = null;
    frameAccumulator = 0;
    start();
  }

  window.addEventListener("resize", rebuild);

  function handleMotionPreferenceChange() {
    lastFrameTime = null;
    lastDrawTime = null;
    frameAccumulator = 0;
    start();
  }

  if (typeof prefersReducedMotion.addEventListener === "function") {
    prefersReducedMotion.addEventListener("change", handleMotionPreferenceChange);
  } else {
    prefersReducedMotion.addListener(handleMotionPreferenceChange);
  }

  rebuild();
}());
