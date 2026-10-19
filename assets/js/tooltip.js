// Tooltips: tell each tooltip how much room it has before the right edge of the screen, so the CSS can shift it
// left instead of letting it run off screen. Hidden tooltips are laid out too, so all of them are placed up front,
// which also keeps a tooltip from sliding sideways the first time it fades in.
const margin = 8;

function place(tip) {
  const room = document.documentElement.clientWidth - margin - tip.getClientRects()[0].left;
  tip.style.setProperty("--tip-room", `${room}px`);
}

function placeAll() {
  for (const tip of document.querySelectorAll(".hover-tip")) place(tip);
}

placeAll();
addEventListener("load", placeAll); // web fonts can reflow the text after the first pass
addEventListener("resize", placeAll);
