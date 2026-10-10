// Copy buttons: one on every code block, plus the post's copy-link button.
async function copy(text, button) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    return; // No clipboard access (an insecure context or a denied permission); leave the button as it was.
  }
  button.dataset.copied = "";
  setTimeout(() => delete button.dataset.copied, 1500);
}

for (const pre of document.querySelectorAll(".prose .highlight > pre")) {
  const bar = document.createElement("div");
  bar.className = "code-bar";
  const lang = document.createElement("span");
  lang.className = "mono";
  lang.textContent = pre.querySelector("code[data-lang]")?.dataset.lang ?? "";
  const button = document.createElement("button");
  button.type = "button";
  button.className = "copy";
  button.textContent = "Copy";
  button.addEventListener("click", () => copy(pre.innerText, button));
  bar.append(lang, button);
  pre.before(bar);
}

for (const button of document.querySelectorAll("button[data-copy]")) {
  button.hidden = false;
  button.addEventListener("click", () => copy(button.dataset.copy, button));
}
