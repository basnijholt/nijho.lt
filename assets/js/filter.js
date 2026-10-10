// Tag buttons, search and sort for the items of every [data-filter-root]. An item matches the pressed tag
// (data-filter="*" matches all) and every search word, anywhere in its text or tags.
for (const root of document.querySelectorAll("[data-filter-root]")) {
  const items = root.querySelector("[data-filter-items]");
  const cards = [...items.children];
  const buttons = [...root.querySelectorAll("button[data-filter]")];
  const search = root.querySelector("[data-filter-search]");
  const sort = root.querySelector("[data-filter-sort]");
  const count = root.querySelector("[data-filter-count]");
  const empty = root.querySelector("[data-filter-empty]");
  const noun = root.dataset.filterNoun;
  const pressed = () => buttons.find((b) => b.getAttribute("aria-pressed") === "true");

  const apply = () => {
    const tag = pressed()?.dataset.filter ?? "*";
    const query = search.value.trim();
    const words = query.toLowerCase().split(/\s+/).filter(Boolean);
    let shown = 0;
    for (const card of cards) {
      const text = `${card.textContent} ${card.dataset.tags}`.toLowerCase();
      card.hidden = !(
        (tag === "*" || card.dataset.tags.split(",").includes(tag)) && words.every((w) => text.includes(w))
      );
      if (!card.hidden) shown++;
    }
    const key = sort?.value ?? "order";
    const by = {
      order: (a, b) => a.dataset.order - b.dataset.order,
      date: (a, b) => b.dataset.date - a.dataset.date,
      name: (a, b) => a.dataset.name.localeCompare(b.dataset.name),
    }[key];
    items.append(...cards.toSorted(by));
    empty.hidden = shown > 0;
    const label = sort?.selectedOptions[0].dataset.label;
    const sorted = label ? `, sorted by ${label}` : "";
    if (shown === cards.length) {
      count.textContent = `Showing all ${cards.length} ${noun}${sorted}`;
    } else {
      const tagged = tag === "*" ? "" : ` tagged ${pressed().firstChild.textContent}`;
      const matching = query ? ` matching "${query}"` : "";
      count.textContent = `Showing ${shown} of ${cards.length} ${noun}${tagged}${matching}${sorted}`;
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
  search.addEventListener("input", apply);
  sort?.addEventListener("change", apply);
  root.querySelector("[data-filter-reset]").addEventListener("click", () => {
    search.value = "";
    press(buttons.find((b) => b.dataset.filter === "*"));
    apply();
    search.focus();
  });

  root.querySelector("[data-filter-toolbar]").hidden = false;
  apply();
}
