const menu = document.getElementById("site-menu");
const links = new Map([...menu.querySelectorAll('a[href^="/#"]')].map((a) => [a.hash.slice(1), a]));
const lastId = [...links.keys()].at(-1);

// A section is current while it crosses a thin band just above the middle of the viewport. The last section can be
// too short to reach that band on a tall screen, so it is current whenever the page is scrolled to the bottom.
let inBand;
let shown;
const update = () => {
  const atBottom = innerHeight + scrollY >= document.documentElement.scrollHeight - 2;
  const current = atBottom ? lastId : inBand;
  if (current === shown) return;
  shown = current;
  for (const [id, link] of links) {
    if (id === current) link.setAttribute("aria-current", "true");
    else link.removeAttribute("aria-current");
  }
};
const observer = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) if (entry.isIntersecting) inBand = entry.target.id;
    update();
  },
  { rootMargin: "-45% 0px -50% 0px" },
);
for (const id of links.keys()) {
  const section = document.getElementById(id);
  if (section) observer.observe(section);
}
addEventListener("scroll", update, { passive: true });

// A link to a section of this page loads no new page, so the open menu is closed here.
menu.addEventListener("click", (event) => {
  if (event.target.closest("a") && menu.matches(":popover-open")) menu.hidePopover();
});
