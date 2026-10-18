// Tooltips: tell each tooltip how much room it has before the right edge of the screen, so the CSS can shift it
// left instead of letting it run off screen.
const margin = 8;

for (const type of ["pointerover", "focusin"]) {
  document.addEventListener(type, ({ target }) => {
    const tip = target.closest?.(".hover-tip");
    if (!tip) return;
    const room = document.documentElement.clientWidth - margin - tip.getClientRects()[0].left;
    tip.style.setProperty("--tip-room", `${room}px`);
  });
}
