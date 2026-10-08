// Charts for this post, rendered by layouts/shortcodes/plot.html with Observable Plot.
// Numbers from the Artificial Analysis Intelligence Index model pages, read on 2026-10-08.
// Cost per task is the average API cost of one Intelligence Index task, including input,
// cache and output tokens; tokens are average output (reasoning plus answer) tokens per task.

const COLORS = { opus: "#4269d0", sonnet: "#ff725c" };

const STYLE = { fontSize: "13px", fontFamily: "system-ui, sans-serif", background: "transparent" };

// Centered axis labels below the tick labels, so they never collide with them.
const X_LABEL = { labelAnchor: "center", labelArrow: "none", labelOffset: 42 };

const MODELS = ["Claude Opus 5.5", "Claude Sonnet 5.5"];

// prettier-ignore
const DATA = [
  { model: MODELS[0], level: "low", score: 42.3, cost: 0.551, tokens: 10151 },
  { model: MODELS[0], level: "medium", score: 51.2, cost: 1.336, tokens: 25745 },
  { model: MODELS[0], level: "high", score: 53.6, cost: 1.823, tokens: 35584 },
  { model: MODELS[0], level: "xhigh", score: 56.0, cost: 3.459, tokens: 65667 },
  { model: MODELS[0], level: "max", score: 57.6, cost: 5.982, tokens: 119166 },
  { model: MODELS[1], level: "low", score: 35.9, cost: 0.345, tokens: 14253 },
  { model: MODELS[1], level: "medium", score: 40.8, cost: 0.483, tokens: 20938 },
  { model: MODELS[1], level: "high", score: 46.8, cost: 0.884, tokens: 37327 },
  { model: MODELS[1], level: "xhigh", score: 51.9, cost: 2.012, tokens: 74810 },
  { model: MODELS[1], level: "max", score: 56.0, cost: 5.461, tokens: 197430 },
];

export default {
  costPerTask: ({ Plot, width }) => {
    return Plot.plot({
      width,
      height: Math.min(420, Math.max(300, width * 0.55)),
      marginRight: width < 600 ? 24 : 40,
      marginBottom: 52,
      style: STYLE,
      x: {
        type: "log",
        domain: [0.3, 8],
        label: "Cost per task (USD, log scale)",
        tickFormat: (d) => `$${d}`,
        ticks: [0.3, 0.5, 1, 2, 3, 5],
        ...X_LABEL,
      },
      y: { domain: [34, 60], label: "Intelligence Index", labelArrow: "none", grid: true },
      color: { domain: MODELS, range: [COLORS.opus, COLORS.sonnet], legend: true },
      marks: [
        Plot.line(DATA, { x: "cost", y: "score", stroke: "model", strokeWidth: 2.5, z: "model" }),
        Plot.dot(DATA, { x: "cost", y: "score", fill: "model", r: 5 }),
        // Effort labels above the Opus line and below the Sonnet line.
        ...MODELS.map((m, i) =>
          Plot.text(
            DATA.filter((d) => d.model === m),
            { x: "cost", y: "score", text: "level", fill: "model", dy: i === 0 ? -12 : 14, fontSize: 11 }
          )
        ),
        Plot.tip(
          DATA,
          Plot.pointer({
            x: "cost",
            y: "score",
            title: (d) =>
              `${d.model}, ${d.level}\nScore ${d.score}\n$${d.cost.toFixed(2)} per task\n${Math.round(d.tokens / 1000)}k output tokens per task`,
          })
        ),
      ],
    });
  },
};
