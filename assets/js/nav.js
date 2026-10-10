const menu = document.getElementById("site-menu");
const links = new Map([...menu.querySelectorAll('a[href^="/#"]')].map((a) => [a.hash.slice(1), a]));

// A section is current while it crosses a thin band just above the middle of the viewport.
const observer = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      for (const link of links.values()) link.removeAttribute("aria-current");
      links.get(entry.target.id).setAttribute("aria-current", "true");
    }
  },
  { rootMargin: "-45% 0px -50% 0px" },
);
for (const id of links.keys()) {
  const section = document.getElementById(id);
  if (section) observer.observe(section);
}

// A link to a section of this page loads no new page, so the open menu is closed here.
menu.addEventListener("click", (event) => {
  if (event.target.closest("a") && menu.matches(":popover-open")) menu.hidePopover();
});
