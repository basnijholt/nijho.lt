// Videos that play by themselves (video shortcode with autoplay) stay still for readers who ask for less motion.
if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
  for (const video of document.querySelectorAll("video[autoplay]")) {
    video.removeAttribute("autoplay");
    video.pause();
  }
}
