// Pause each .svg-bleed animation while it is off screen. Whenever it plays, line every SVG and CSS animation up with
// the first SVG's clock.
for (const stage of document.querySelectorAll(".svg-bleed-stage")) {
  const [clock, ...others] = stage.querySelectorAll(":scope > svg");
  const css = () => stage.getAnimations({ subtree: true });
  const play = () => {
    const time = clock.getCurrentTime();
    clock.unpauseAnimations();
    for (const svg of others) {
      svg.setCurrentTime(time);
      svg.unpauseAnimations();
    }
    for (const animation of css()) {
      animation.currentTime = time * 1000;
      animation.play();
    }
  };
  let visible = false;
  new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    if (visible) {
      play();
    } else {
      for (const svg of [clock, ...others]) svg.pauseAnimations();
      for (const animation of css()) animation.pause();
    }
  }).observe(stage);
  // The SVG clock only starts at the load event, while the CSS animations start right away.
  addEventListener("load", () => visible && play());
}
