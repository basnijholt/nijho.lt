// Tag buttons, menus, search and sort for the items of every [data-filter-root]. An item matches the pressed tag
// (data-filter="*" matches all), every menu (select[data-filter-key="year"] keeps items whose data-year is the
// chosen value), and every search word, anywhere in its text or tags. A URL hash naming a tag or a menu value,
// such as /publication/#article-journal, preselects it.
for (const root of document.querySelectorAll("[data-filter-root]")) {
  const items = root.querySelector("[data-filter-items]");
  const cards = [...items.children];
  const buttons = [...root.querySelectorAll("button[data-filter]")];
  const menus = [...root.querySelectorAll("select[data-filter-key]")];
  const search = root.querySelector("[data-filter-search]");
  const sort = root.querySelector("[data-filter-sort]");
  const count = root.querySelector("[data-filter-count]");
  const empty = root.querySelector("[data-filter-empty]");
  const noun = root.dataset.filterNoun;
  // Items grouped by this data attribute show it only on the first visible item of each group.
  const group = items.dataset.filterGroup;
  const pressed = () => buttons.find((b) => b.getAttribute("aria-pressed") === "true");

  const apply = () => {
    const tag = pressed()?.dataset.filter ?? "*";
    const chosen = menus.filter((m) => m.value);
    const query = search.value.trim();
    const words = query.toLowerCase().split(/\s+/).filter(Boolean);
    let shown = 0;
    for (const card of cards) {
      const tags = card.dataset.tags ?? "";
      const text = `${card.textContent} ${tags}`.toLowerCase();
      card.hidden = !(
        (tag === "*" || tags.split(",").includes(tag)) &&
        chosen.every((m) => card.dataset[m.dataset.filterKey].split(",").includes(m.value)) &&
        words.every((w) => text.includes(w))
      );
      if (!card.hidden) shown++;
    }
    const by = {
      order: (a, b) => a.dataset.order - b.dataset.order,
      date: (a, b) => b.dataset.date - a.dataset.date,
      name: (a, b) => a.dataset.name.localeCompare(b.dataset.name),
    }[sort?.value];
    if (by) items.append(...cards.toSorted(by));
    if (group) {
      let previous;
      for (const card of cards.filter((c) => !c.hidden)) {
        card.classList.toggle("cont", card.dataset[group] === previous);
        previous = card.dataset[group];
      }
    }
    empty.hidden = shown > 0;

    const label = sort?.selectedOptions[0].dataset.label;
    const sorted = label ? `, sorted by ${label}` : "";
    if (shown === cards.length) {
      count.textContent = `Showing all ${cards.length} ${noun}${sorted}`;
    } else {
      const tagged = tag === "*" ? "" : ` tagged ${pressed().firstChild.textContent}`;
      const picked = chosen.length ? ` (${chosen.map((m) => m.selectedOptions[0].text).join(", ")})` : "";
      const matching = query ? ` matching "${query}"` : "";
      count.textContent = `Showing ${shown} of ${cards.length} ${noun}${tagged}${picked}${matching}${sorted}`;
    }
  };

  const press = (button) => {
    for (const b of buttons) b.setAttribute("aria-pressed", String(b === button));
  };
  for (const button of buttons) {
    button.addEventListener("click", () => {
      press(button);
      apply();
    });
  }
  for (const menu of menus) menu.addEventListener("change", apply);
  search.addEventListener("input", apply);
  sort?.addEventListener("change", apply);
  root.querySelector("[data-filter-reset]").addEventListener("click", () => {
    search.value = "";
    for (const menu of menus) menu.value = "";
    press(buttons.find((b) => b.dataset.filter === "*"));
    apply();
    search.focus();
  });

  const hash = decodeURIComponent(location.hash.slice(1));
  if (hash) {
    const button = buttons.find((b) => b.dataset.filter === hash);
    if (button) press(button);
    for (const menu of menus) {
      if ([...menu.options].some((o) => o.value === hash)) menu.value = hash;
    }
  }

  root.querySelector("[data-filter-toolbar]").hidden = false;
  apply();
}
