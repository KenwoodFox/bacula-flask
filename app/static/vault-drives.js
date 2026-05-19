(function () {
  const nodes = document.querySelectorAll(".drive-stats[data-drive]");
  if (!nodes.length) return;

  function render(el, data) {
    if (!data.mounted) {
      el.textContent = "no tape";
      return;
    }
    el.textContent = data.lines.join(" · ");
  }

  function poll(el) {
    const drive = el.dataset.drive;
    fetch("/vault/api/drive/" + encodeURIComponent(drive) + "/stats")
      .then((r) => r.json())
      .then((data) => render(el, data))
      .catch(() => {
        el.textContent = "stats unavailable";
      });
  }

  function tick() {
    nodes.forEach(poll);
  }

  tick();
  setInterval(tick, 20000);
})();
