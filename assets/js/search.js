// Site search in the #search dialog. The index (/index.json) is fetched the first time the dialog opens. Each
// result must match every search word somewhere; it scores 3 for a word in the title, 2 in the tags, 1.5 in the
// summary and 1 in the text, and the ten best show, newest first among equal scores.
const dialog = document.getElementById("search");
const input = dialog.querySelector("input");
const list = dialog.querySelector("#search-results");
const status = dialog.querySelector(".search-status");
const opener = document.querySelector('.site-header button[aria-controls="search"]');
const sections = { post: "Post", project: "Project", publication: "Publication", authors: "Author" };
const fields = [
  ["title", 3],
  ["tags", 2],
  ["summary", 1.5],
  ["content", 1],
];
let index;
let active = -1;

const load = () => {
  index ??= fetch("/index.json")
    .then((response) => {
      if (!response.ok) throw new Error(`index.json: ${response.status}`);
      return response.json();
    })
    .then((pages) =>
      pages.map((page) => ({
        page,
        text: Object.fromEntries(
          fields.map(([key]) => [key, [page[key] ?? ""].flat().join(" ").toLowerCase()]),
        ),
      })),
    )
    .catch((error) => {
      // Forget the failure, so the next search fetches the index again.
      index = undefined;
      throw error;
    });
  return index;
};

const search = async () => {
  const words = input.value.toLowerCase().split(/\s+/).filter(Boolean);
  if (!words.length) return show([], "");
  status.textContent = "Searching…";
  let pages;
  try {
    pages = await load();
  } catch {
    return show([], "Search is unavailable right now. Try again in a moment.");
  }
  const results = [];
  for (const { page, text } of pages) {
    let score = 0;
    const all = words.every((word) => {
      const found = fields.filter(([key]) => text[key].includes(word));
      for (const [, weight] of found) score += weight;
      return found.length > 0;
    });
    if (all) results.push({ page, score });
  }
  results.sort((a, b) => b.score - a.score || b.page.date - a.page.date);
  show(results.slice(0, 10), `${results.length} ${results.length === 1 ? "result" : "results"}`);
};

const show = (results, message) => {
  active = -1;
  list.replaceChildren(
    ...results.map(({ page }, i) => {
      const item = document.createElement("li");
      item.id = `search-result-${i}`;
      item.setAttribute("role", "option");
      const link = document.createElement("a");
      link.href = page.relpermalink;
      link.tabIndex = -1;
      const label = document.createElement("span");
      label.className = "mono";
      label.textContent = sections[page.section] ?? page.section;
      const title = document.createElement("strong");
      title.textContent = page.title;
      const summary = document.createElement("span");
      summary.className = "snippet";
      summary.textContent = page.summary;
      link.append(label, title, summary);
      item.append(link);
      return item;
    }),
  );
  input.setAttribute("aria-expanded", String(results.length > 0));
  input.removeAttribute("aria-activedescendant");
  status.textContent = message;
};

const highlight = (i) => {
  const items = list.children;
  if (!items.length) return;
  active = (i + items.length) % items.length;
  for (const [n, item] of [...items].entries()) item.setAttribute("aria-selected", String(n === active));
  input.setAttribute("aria-activedescendant", items[active].id);
  items[active].scrollIntoView({ block: "nearest" });
};

const open = (query) => {
  if (query !== undefined) input.value = query;
  if (!dialog.open) dialog.showModal();
  input.focus();
  input.select();
  // Fetch the index while the reader types; a failure shows when the first search needs it.
  load().catch(() => {});
  search();
};

let timer;
input.addEventListener("input", () => {
  clearTimeout(timer);
  timer = setTimeout(search, 80);
});
input.addEventListener("keydown", (event) => {
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    highlight(active + (event.key === "ArrowDown" ? 1 : -1));
  } else if (event.key === "Enter") {
    event.preventDefault();
    list.children[Math.max(active, 0)]?.querySelector("a").click();
  } else if (event.key === "Escape") {
    // A search field spends the first Escape on clearing itself; here it closes the dialog straight away.
    event.preventDefault();
    dialog.close();
  }
});
dialog.querySelector("[data-search-close]").addEventListener("click", () => dialog.close());
// A click on the backdrop lands on the dialog itself.
dialog.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});
opener?.addEventListener("click", () => open());
document.addEventListener("keydown", (event) => {
  const typing = event.target.closest("input, textarea, select, [contenteditable]");
  if (event.key === "/" && !typing && !event.ctrlKey && !event.metaKey && !event.altKey) {
    event.preventDefault();
    open();
  }
});

const query = new URLSearchParams(location.search).get("q");
if (query) open(query);
