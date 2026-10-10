// Mark the contents entry of the heading at the top of the viewport.
const links = new Map(
  [...document.querySelectorAll(".rail nav a")].map((a) => [decodeURIComponent(a.hash.slice(1)), a]),
);
let current;
const observer = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      current?.removeAttribute("aria-current");
      current = links.get(entry.target.id);
      current?.setAttribute("aria-current", "true");
    }
  },
  { rootMargin: "0px 0px -70% 0px" },
);
for (const id of links.keys()) {
  const heading = document.getElementById(id);
  if (heading) observer.observe(heading);
}
