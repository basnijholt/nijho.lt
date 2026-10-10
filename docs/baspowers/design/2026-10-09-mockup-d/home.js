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



// Projects: tag filter, search, and sort (same controls as the current Isotope toolbar).
(() => {
  const grid = document.querySelector('[data-proj-grid]');
  const cards = [...grid.children];
  const search = document.querySelector('[data-proj-search]');
  const sort = document.querySelector('[data-proj-sort]');
  const count = document.querySelector('[data-proj-count]');
  const empty = document.querySelector('[data-proj-empty]');
  const buttons = [...document.querySelectorAll('.filter')];
  const labels = { 'original-order': 'GitHub stars', date: 'newest first', name: 'name' };
  let tag = 'all';
  function apply() {
    const q = search.value.trim().toLowerCase();
    let shown = 0;
    for (const c of cards) {
      const okTag = tag === 'all' || c.dataset.ids.split(' ').includes(tag);
      const okQ = !q || c.dataset.name.includes(q) || c.dataset.text.includes(q);
      c.hidden = !(okTag && okQ);
      if (!c.hidden) shown++;
    }
    const key = sort.value;
    const sorted = [...cards].sort((a, b) =>
      key === 'date' ? b.dataset.date - a.dataset.date :
      key === 'name' ? a.dataset.name.localeCompare(b.dataset.name) :
      a.dataset.order - b.dataset.order);
    grid.append(...sorted);
    empty.hidden = shown !== 0;
    const what = tag === 'all' ? '' : ` tagged ${tag}`;
    count.textContent = shown === cards.length
      ? `Showing all ${cards.length} projects, sorted by ${labels[key]}`
      : `Showing ${shown} of ${cards.length} projects${what}${q ? ` matching "${search.value.trim()}"` : ''}, sorted by ${labels[key]}`;
  }
  buttons.forEach((b) => b.addEventListener('click', () => {
    tag = b.dataset.filter;
    buttons.forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
    apply();
  }));
  search.addEventListener('input', apply);
  sort.addEventListener('change', apply);
  document.querySelector('[data-proj-reset]').addEventListener('click', () => {
    search.value = ''; tag = 'all';
    buttons.forEach((x) => x.setAttribute('aria-pressed', String(x.dataset.filter === 'all')));
    apply(); search.focus();
  });
})();



// Justified rows: the same minimum-cost row breaking the live site uses, with a taller target row height.
(() => {
  const grid = document.querySelector('[data-photo-grid]');
  const photos = [...grid.querySelectorAll('a')];
  const ratios = photos.map((p) => parseFloat(p.style.getPropertyValue('--ar')));
  let laidOut = 0;
  const layOut = () => {
    const width = grid.clientWidth;
    if (!width || width === laidOut) return;
    laidOut = width;
    const gap = parseFloat(getComputedStyle(grid).columnGap) || 10;
    const target = Math.min(Math.max(width / 4.2, 140), 290);
    const cost = [0], start = [0];
    for (let j = 1; j <= photos.length; j++) {
      cost[j] = Infinity;
      let sum = 0;
      for (let i = j - 1; i >= 0; i--) {
        sum += ratios[i];
        const h = (width - gap * (j - i - 1)) / sum;
        const c = cost[i] + Math.log(h / target) ** 2;
        if (c < cost[j]) { cost[j] = c; start[j] = i; }
      }
    }
    const rows = [];
    for (let j = photos.length; j > 0; j = start[j]) {
      const row = document.createElement('div');
      row.className = 'photo-row';
      row.append(...photos.slice(start[j], j));
      rows.unshift(row);
    }
    grid.replaceChildren(...rows);
  };
  new ResizeObserver(layOut).observe(grid);
})();



// Highlight the nav link of the section in view.
(() => {
  const links = [...document.querySelectorAll('.nav-links a')];
  const map = new Map(links.map((a) => [a.hash.slice(1), a]));
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return;
      links.forEach((a) => a.removeAttribute('aria-current'));
      map.get(e.target.id)?.setAttribute('aria-current', 'page');
    });
  }, { rootMargin: '-45% 0px -50% 0px' });
  map.forEach((_, id) => { const s = document.getElementById(id); if (s) io.observe(s); });
})();
