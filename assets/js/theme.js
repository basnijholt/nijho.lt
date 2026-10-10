const root = document.documentElement;
const menu = document.getElementById("theme-menu");
const choices = menu.querySelectorAll("[data-theme-choice]");

function apply(theme) {
  if (theme === "auto") delete root.dataset.theme;
  else root.dataset.theme = theme;
  for (const choice of choices) choice.setAttribute("aria-pressed", String(choice.dataset.themeChoice === theme));
}

apply(root.dataset.theme ?? "auto");

menu.addEventListener("click", (event) => {
  const choice = event.target.closest("[data-theme-choice]");
  if (!choice) return;
  const theme = choice.dataset.themeChoice;
  try {
    localStorage.setItem("theme", theme);
  } catch {
    // Storage is blocked; the choice then lasts until the next page load.
  }
  apply(theme);
  menu.hidePopover();
});
