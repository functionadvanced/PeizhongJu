#!/usr/bin/env python3
"""Regenerate static research pages using the homepage's canonical citations.

Run from any directory: python3 scripts/build-topic-pages.py
Edit introductions and topic memberships in assets/research-topic-content.json.
"""

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TOPICS = json.loads((ROOT / "assets/research-topic-content.json").read_text())
INDEX = (ROOT / "index.html").read_text()

FIGURES = {
    "reinforcement-learning": (
        "An agent chooses actions using a policy, observes the environment, and uses rewards and new observations to improve its decisions.",
        "Reinforcement learning feedback loop connecting an agent, its policy, actions, the environment, observations, and rewards.",
    ),
    "federated-learning": (
        "Clients train on their own data and exchange model updates with a coordinator. Repeated aggregation and redistribution improve a shared model while raw data remain at each client.",
        "Federated learning system with local client data, local training, model update aggregation, and redistribution of a shared model.",
    ),
    "continual-transfer-learning": (
        "A learner adapts as tasks arrive, using retained knowledge and rehearsal to balance new learning with earlier skills. Transfer learning reuses knowledge from a source task to support a target task.",
        "Sequential tasks, a shared learner, retained knowledge, and source-to-target adaptation illustrate continual and transfer learning.",
    ),
    "diffusion-flow-matching": (
        "Diffusion models generate samples through successive denoising steps. Flow matching learns a velocity field that transports a simple starting distribution toward the data distribution.",
        "Two generative modeling paths from noise to data: iterative denoising in diffusion models and learned velocity-driven transport in flow matching.",
    ),
    "interpretability-generalization": (
        "Interpretability connects model predictions to internal features and neuron behavior. Generalization examines performance on unseen data and the effects of model capacity and training choices.",
        "A trained model connects internal features and explanations with evaluation on held-out data to study interpretability and generalization.",
    ),
}


def publication_catalog():
    section = re.search(r'<section id="publications">(.*?)</section>', INDEX, re.S).group(1)
    catalog = {}
    for group in re.finditer(
        r'<h3 class="timeline-title">(.*?)</h3>.*?<ol>(.*?)</ol>', section, re.S
    ):
        category, entries = group.groups()
        for entry in re.findall(r"<li\b[^>]*>.*?</li>", entries, re.S):
            key_match = re.search(r"@\w+\{\s*([^,\s]+)", entry)
            if key_match:
                key = key_match.group(1)
            else:
                doi = re.search(r"https?://(?:dx\.)?doi\.org/([^\"<>]+)", entry)
                if not doi:
                    continue
                key = doi.group(1)
            if key in catalog:
                raise ValueError(f"Duplicate publication key: {key}")
            catalog[key] = (html.unescape(category), entry)
    return catalog


def render_publications(topic, catalog):
    groups = []
    seen = set()
    for group in topic["publication_groups"]:
        entries = []
        for key in group["keys"]:
            if key in seen:
                raise ValueError(f"Duplicate topic membership: {key}")
            seen.add(key)
            category, entry = catalog[key]
            if category != group["category"]:
                raise ValueError(f"Publication category changed for {key}; update topic mapping.")
            if 'class="bibtex-entry"' in entry:
                control_id = "bibtex-" + re.sub(r"[^a-zA-Z0-9_-]", "-", key)
                entry = entry.replace(
                    '<button class="badge rounded-pill bg-secondary border-0 toggle-bibtex">',
                    f'<button type="button" class="badge rounded-pill bg-secondary border-0 toggle-bibtex" '
                    f'aria-expanded="false" aria-controls="{control_id}">',
                )
                entry = entry.replace('<pre class="bibtex-entry">', f'<pre class="bibtex-entry" id="{control_id}">')
            entries.append(entry)
        groups.append(
            '      <div class="timeline-item">\n'
            f'        <h3 class="timeline-title">{html.escape(group["category"])}</h3>\n'
            '        <ol class="publication-list">\n'
            + "\n".join(entries)
            + '\n        </ol>\n      </div>'
        )
    return "\n".join(groups)


def render_sidebar():
    sidebar = re.search(r'<nav class="nav flex-column">.*?</nav>', INDEX, re.S).group(0)
    sidebar = sidebar.replace('<nav class="nav flex-column">', '<nav class="nav flex-column" aria-label="Main navigation">')
    sidebar = re.sub(r'href="#([a-z]+)"', r'href="../index.html#\1"', sidebar)
    sidebar = re.sub(r' data-bs-target="#[a-z]+"', '', sidebar)
    sidebar = sidebar.replace('class="nav-link" href="../index.html#research"', 'class="nav-link active" href="../index.html#research"')
    return sidebar


def render_page(slug, topic, catalog):
    title = html.escape(topic["title"])
    caption, alt = map(html.escape, FIGURES[slug])
    links = []
    for other_slug, other in TOPICS.items():
        label = html.escape(other["title"])
        if other_slug == slug:
            links.append(f'<li><span aria-current="page">{label}</span></li>')
        else:
            links.append(
                f'<li><a href="{other_slug}.html">{label}</a></li>'
            )
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(topic['intro'], quote=True)}">
  <title>{title} | Peizhong Ju</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/css/bootstrap.min.css" rel="stylesheet"
    integrity="sha384-eOJMYsd53ii+scO/bJGFsiCZc+5NDVN2yr8+0RDqr0Ql0h+rP48ckxlpbzKgwra6" crossorigin="anonymous">
  <link rel="icon" href="../favicon.ico" type="image/x-icon">
  <link rel="stylesheet" href="../assets/site.css">
  <link rel="stylesheet" href="../assets/research-topic.css">
</head>
<body class="topic-page">
  {render_sidebar()}
  <main class="container">
    <section id="overview" class="topic-overview" aria-labelledby="topic-title">
      <div class="topic-breadcrumb"><a href="../index.html">Home</a> / <a href="../index.html#research">Machine Learning</a></div>
      <h1 id="topic-title" class="section-title">{title}</h1>
      <hr>
      <p class="topic-intro">{html.escape(topic['intro'])}</p>
    </section>
    <section id="system" aria-labelledby="system-title">
      <h2 id="system-title" class="research-subsection-title">System Diagram</h2>
      <figure class="topic-diagram">
        <img src="../assets/research-diagrams/{slug}.svg" alt="{alt}">
        <figcaption>{caption}</figcaption>
      </figure>
    </section>
    <section id="publications" aria-labelledby="publications-title">
      <h2 id="publications-title" class="research-subsection-title">My publications on this area</h2>
{render_publications(topic, catalog)}
      <div class="topic-explore">
        <h3>Explore Machine Learning</h3>
        <ul class="topic-links">
          {''.join(links)}
        </ul>
        <a href="../index.html#research">← Back to all research topics</a>
      </div>
    </section>
  </main>
  <script src="../assets/research-topic.js"></script>
  <script src="../assets/neural-background.js"></script>
</body>
</html>
'''


def main():
    catalog = publication_catalog()
    destination = ROOT / "research"
    destination.mkdir(exist_ok=True)
    for slug, topic in TOPICS.items():
        (destination / f"{slug}.html").write_text(render_page(slug, topic, catalog))
        count = sum(len(group["keys"]) for group in topic["publication_groups"])
        print(f"{slug}.html: {count} publications")


if __name__ == "__main__":
    main()
