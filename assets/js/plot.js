// Draw every Observable Plot chart on the page (plot shortcode): each container names a chart in an ES module of the
// page bundle, which exports { chartName: ({ Plot, width }) => Plot.plot({...}) }. Charts redraw when their width changes.
import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6.17/+esm";

// The charts arrive after the browser has scrolled to a #fragment, and push it down; once all are drawn, scroll to it
// again, unless the reader has started scrolling on their own.
let readerScrolled = false;
for (const event of ["wheel", "touchstart", "keydown", "pointerdown"]) {
  addEventListener(event, () => (readerScrolled = true), { once: true, passive: true });
}
const firstDraws = [];

const modules = new Map();
for (const container of document.querySelectorAll(".plot-container[data-plot-module]")) {
  const { plotModule, plotName } = container.dataset;
  if (!modules.has(plotModule)) modules.set(plotModule, import(plotModule).then((module) => module.default));
  let lastWidth = 0;
  let drawn;
  firstDraws.push(new Promise((resolve) => (drawn = resolve)));
  new ResizeObserver(async () => {
    const width = Math.round(container.clientWidth);
    if (!width || width === lastWidth) return;
    lastWidth = width;
    const plots = await modules.get(plotModule);
    container.replaceChildren(plots[plotName]({ Plot, width }));
    // The theme sets `svg { fill: currentColor }`, which beats the fill attribute on legend swatches.
    for (const svg of container.querySelectorAll("svg[fill]")) svg.style.fill = svg.getAttribute("fill");
    // The container is one labelled image; Plot's labels on its inner groups are not allowed there.
    for (const element of container.querySelectorAll("svg [aria-label]")) element.removeAttribute("aria-label");
    drawn();
  }).observe(container);
}

Promise.all(firstDraws).then(() => {
  const target = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
  if (target && !readerScrolled) target.scrollIntoView({ behavior: "instant" });
});
