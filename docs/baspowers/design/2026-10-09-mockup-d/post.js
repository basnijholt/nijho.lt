// Theme: Light / Dark / Automatic, like the current site's selector. Automatic follows prefers-color-scheme.
(() => {
  const root = document.documentElement;
  const btn = document.querySelector('[data-theme-btn]');
  const menu = document.querySelector('[data-theme-menu]');
  const mbtn = document.querySelector('[data-menu-btn]');
  const mmenu = document.querySelector('[data-menu]');
  const sync = () => menu.querySelectorAll('[data-set-theme]').forEach((b) =>
    b.setAttribute('aria-checked', String((root.dataset.theme || 'auto') === b.dataset.setTheme)));
  const toggle = (b, m, open) => { m.hidden = !open; b.setAttribute('aria-expanded', String(open)); };
  btn.addEventListener('click', (e) => { e.stopPropagation(); toggle(mbtn, mmenu, false); toggle(btn, menu, menu.hidden); });
  mbtn.addEventListener('click', (e) => { e.stopPropagation(); toggle(btn, menu, false); toggle(mbtn, mmenu, mmenu.hidden); });
  menu.addEventListener('click', (e) => {
    const t = e.target.closest('[data-set-theme]'); if (!t) return;
    if (t.dataset.setTheme === 'auto') delete root.dataset.theme; else root.dataset.theme = t.dataset.setTheme;
    sync(); toggle(btn, menu, false);
  });
  document.addEventListener('click', () => { toggle(btn, menu, false); toggle(mbtn, mmenu, false); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { toggle(btn, menu, false); toggle(mbtn, mmenu, false); } });
  sync();
})();



// Contents rail: mark the section currently in view.
(() => {
  const links = [...document.querySelectorAll('.rail a')];
  const heads = links.map((a) => document.getElementById(a.hash.slice(1))).filter(Boolean);
  const io = new IntersectionObserver((es) => es.forEach((e) => {
    if (!e.isIntersecting) return;
    links.forEach((a) => a.setAttribute('aria-current', String(a.hash.slice(1) === e.target.id)));
  }), { rootMargin: '0px 0px -70% 0px' });
  heads.forEach((h) => io.observe(h));
})();



  // Same chart as the live post (plots.js runCost), recolored to the site tokens.
  import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6.17/+esm";
  const LUNA_COST = 66.81, QWEN_KWH = 461, PRO6000_KWH = 760;
  const usd = (d) => (d >= 100 ? `$${Math.round(d).toLocaleString("en-US")}` : `$${Math.round(d)}`);
  const el = document.getElementById("runcost");
  let lastWidth = 0;
  function render() {
    const cs = getComputedStyle(document.documentElement);
    const v = (n) => cs.getPropertyValue(n).trim();
    const width = Math.round(el.clientWidth - 44);
    const narrow = width < 560;
    const groups = ["Closed model via API", "Open model at home (electricity only)", "Open model via API"];
    const data = [
      { label: "GPT-6 Luna via API", cost: LUNA_COST, group: groups[0] },
      { label: narrow ? "Qwen3.8 27B, quantized, on my 3090s" : "Qwen3.8 27B, quantized, on my two 3090s: electricity at 18 cents/kWh", cost: QWEN_KWH * 0.18, group: groups[1] },
      { label: narrow ? "Qwen3.8 27B, full precision, RTX PRO 6000" : "Qwen3.8 27B, full precision, on an RTX PRO 6000: electricity at 18 cents/kWh", cost: PRO6000_KWH * 0.18, group: groups[1] },
      { label: narrow ? "Qwen3.8 27B, full precision, ZDR API" : "Qwen3.8 27B, full precision, via the cheapest ZDR API", cost: 619, group: groups[2] },
    ];
    const svg = Plot.plot({
      width, height: 56 * data.length + 72, marginLeft: 14, marginRight: 56, marginTop: 10, marginBottom: 52,
      style: { fontSize: "13px", fontFamily: "Geist, system-ui, sans-serif", background: "transparent", color: v("--text") },
      x: { domain: [0, 700], label: "Cost of one benchmark run (USD)", grid: true, tickFormat: (d) => `$${d}`, labelAnchor: "center", labelArrow: "none", labelOffset: 42 },
      y: { axis: null, domain: data.map((d) => d.label), inset: 24 },
      color: { domain: groups, range: [v("--text-2"), v("--accent"), v("--muted")] },
      marks: [
        Plot.ruleY(data, { y: "label", x1: 0, x2: "cost", stroke: "group", strokeWidth: 14 }),
        Plot.text(data, { y: "label", x: 0, text: "label", textAnchor: "start", dy: -17, fill: v("--text-2") }),
        Plot.text(data, { y: "label", x: "cost", text: (d) => usd(d.cost), textAnchor: "start", dx: 6, fontWeight: "bold" }),
      ],
    });
    el.replaceChildren(svg);
  }
  new ResizeObserver(() => { const w = Math.round(el.clientWidth); if (w && w !== lastWidth) { lastWidth = w; render(); } }).observe(el);
  new MutationObserver(render).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", render);
