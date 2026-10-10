// Play each demo recording while at least half of it is on screen, and pause it once it scrolls away or a theme switch
// hides it. Inline, each video plays a small preview; in fullscreen it switches to the full-resolution file at the same
// moment, and back on exit.
const onScreen = new IntersectionObserver(
  (entries) => {
    for (const { target, isIntersecting } of entries) {
      // play() rejects when a quick scroll pauses the video before it starts; there is nothing to recover.
      if (isIntersecting) target.play().catch(() => {});
      else target.pause();
    }
  },
  { threshold: 0.5 },
);

const swap = (video, src) => {
  if (!src || video.currentSrc.split("#")[0] === src) return;
  const time = video.currentTime;
  const playing = !video.paused;
  video.src = src;
  video.addEventListener(
    "loadedmetadata",
    () => {
      video.currentTime = time;
      if (playing) video.play().catch(() => {});
    },
    { once: true },
  );
};

const videos = [...document.querySelectorAll(".demo-clips video")];
for (const video of videos) {
  video.dataset.preview = video.getAttribute("src").split("#")[0];
  onScreen.observe(video);
  // iOS plays fullscreen video in its own player and only fires these events on the element.
  video.addEventListener("webkitbeginfullscreen", () => swap(video, video.dataset.full));
  video.addEventListener("webkitendfullscreen", () => swap(video, video.dataset.preview));
}
for (const event of ["fullscreenchange", "webkitfullscreenchange"]) {
  document.addEventListener(event, () => {
    const fullscreen = document.fullscreenElement || document.webkitFullscreenElement;
    for (const video of videos) swap(video, video === fullscreen ? video.dataset.full : video.dataset.preview);
  });
}
