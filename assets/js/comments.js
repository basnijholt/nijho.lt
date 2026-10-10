// Load the giscus thread with the page's data-giscus-* settings, in the theme the page shows.
const box = document.getElementById("comments");
const script = document.createElement("script");
script.src = "https://giscus.app/client.js";
for (const [key, value] of Object.entries(box.dataset)) {
  const name = key.replace(/^giscus./, (match) => match.at(-1).toLowerCase());
  script.dataset[name] = value;
}
Object.assign(script.dataset, {
  theme: document.documentElement.dataset.theme ?? "preferred_color_scheme",
  reactionsEnabled: "1",
  emitMetadata: "0",
  inputPosition: "top",
  loading: "lazy",
  strict: "0",
});
script.crossOrigin = "anonymous";
script.async = true;
box.append(script);
