// Open a zoomable image at its largest size in a dialog; a click or Escape closes it.
const dialog = document.createElement("dialog");
dialog.className = "zoom";
const image = document.createElement("img");
dialog.append(image);
document.body.append(dialog);
dialog.addEventListener("click", () => dialog.close());

function largest(img) {
  // A gallery thumbnail links to its original.
  const link = img.closest("a[href]");
  if (link) return link.href;
  const candidates = (img.getAttribute("srcset") ?? "")
    .split(",")
    .map((entry) => entry.trim().split(/\s+/))
    .filter(([url]) => url);
  candidates.sort((a, b) => parseInt(b[1], 10) - parseInt(a[1], 10));
  return candidates[0]?.[0] ?? img.currentSrc;
}

document.addEventListener("click", (event) => {
  const img = event.target.closest("img[data-zoomable]");
  if (!img) return;
  event.preventDefault();
  image.src = largest(img);
  image.alt = img.alt;
  dialog.showModal();
});
