// Tooltips: tell each tooltip how much room it has before the right edge of the screen, so the CSS can shift it
// left instead of letting it run off screen.
const margin = 8;

function place(tip) {
  const room = document.documentElement.clientWidth - margin - tip.getClientRects()[0].left;
  tip.style.setProperty("--tip-room", `${room}px`);
}

for (const type of ["pointerover", "focusin"]) {
  document.addEventListener(type, ({ target }) => {
    const tip = target.closest?.(".hover-tip");
    if (tip) place(tip);
  });
}

// A phone rotated while a tooltip is open needs the room measured again.
addEventListener("resize", () => {
  for (const tip of document.querySelectorAll(".hover-tip:hover, .hover-tip:focus")) place(tip);
});
