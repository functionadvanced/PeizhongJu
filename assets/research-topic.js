// All citations are present in the static HTML; only the BibTeX disclosure needs JS.
document.querySelectorAll('.toggle-bibtex').forEach(function (button) {
  button.addEventListener('click', function () {
    var entry = document.getElementById(button.getAttribute('aria-controls'));
    var expanded = button.getAttribute('aria-expanded') === 'true';
    entry.style.display = expanded ? 'none' : 'block';
    button.setAttribute('aria-expanded', String(!expanded));
  });
});
