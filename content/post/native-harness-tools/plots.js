// Charts for this post, rendered by layouts/_shortcodes/plot.html with Observable Plot.
// All numbers come from my runs of 12 held-out terminal tasks, three runs per task (36 per configuration),
// on MindRoom pull request #2766 (commit d73aafb51) and on MindRoom's main branch (v2026.10.228).

const COLORS = {
  whole: "#4269d0",
  capped: "#97bbf5",
  standard: "#ff725c",
  minimal: "#3ca951",
};

const STYLE = { fontSize: "13px", fontFamily: "system-ui, sans-serif", background: "transparent" };

// Centered axis labels below the tick labels, so they never collide with them.
const X_LABEL = { labelAnchor: "center", labelArrow: "none", labelOffset: 42 };

const MODELS = ["Claude Opus 5.5", "Claude Sonnet 5.5", "GPT-6 Astra", "GPT-6.1 Sol", "GPT-6 Luna"];

const pct = (d) => `${d > 0 ? "+" : d < 0 ? "−" : ""}${Math.abs(d)}%`;

export default {
  nativeDelta: ({ Plot, width }) => {
    const narrow = width < 600;
    const series = ["Whole output", "Last 100 lines"];
    // Change in tokens per task with native tools instead of MindRoom's, and its 95% confidence interval.
    const rows = [
      [MODELS[0], -9, -13, -4, -8, -13, -3],
      [MODELS[1], -9, -15, -1, -8, -13, -2],
      [MODELS[2], 31, 24, 38, 26, 18, 34],
      [MODELS[3], 19, 9, 29, 15, 6, 25],
      [MODELS[4], -4, -18, 14, -10, -19, 1],
    ];
    const data = rows.flatMap(([model, w, wlo, whi, c, clo, chi]) => [
      { model, series: series[0], change: w, lo: wlo, hi: whi },
      { model, series: series[1], change: c, lo: clo, hi: chi },
    ]);
    return Plot.plot({
      width,
      height: 64 * MODELS.length + 90,
      marginLeft: narrow ? 120 : 136,
      marginRight: 24,
      marginBottom: 52,
      style: STYLE,
      x: { domain: [-25, 45], label: "Change in tokens per task with native tools", grid: true, tickFormat: pct, ...X_LABEL },
      y: { axis: null, domain: series },
      fy: { domain: MODELS, label: null, padding: 0.25 },
      color: { domain: series, range: [COLORS.whole, COLORS.capped], legend: true },
      marks: [
        Plot.ruleX([0], { stroke: "currentColor", strokeOpacity: 0.6 }),
        Plot.ruleY(data, { fy: "model", y: "series", x1: "lo", x2: "hi", stroke: "series", strokeWidth: 3 }),
        Plot.dot(data, { fy: "model", y: "series", x: "change", fill: "series", r: 5 }),
        Plot.tip(
          data,
          Plot.pointer({
            fy: "model",
            y: "series",
            x: "change",
            title: (d) => `${d.model}, ${d.series.toLowerCase()}\n${pct(d.change)} tokens per task\n95% CI ${pct(d.lo)} to ${pct(d.hi)}`,
          })
        ),
      ],
    });
  },

  minimalTokens: ({ Plot, width }) => {
    const narrow = width < 600;
    const arms = ["Standard mode", "Minimal mode, one Bash tool"];
    // Tokens per task in Matrix conversations, same agent with only the shell tool.
    const rows = [
      [MODELS[0], 22192, 8030],
      [MODELS[1], 22448, 7828],
      [MODELS[2], 11429, 2798],
      [MODELS[3], 11070, 3370],
      [MODELS[4], 12568, 5219],
    ];
    const data = rows.flatMap(([model, standard, minimal]) => [
      { model, arm: arms[0], tokens: standard },
      { model, arm: arms[1], tokens: minimal, change: Math.round((minimal / standard - 1) * 100) },
    ]);
    const label = (d) => `${(d.tokens / 1000).toFixed(1)}k${d.change === undefined ? "" : ` (${pct(d.change)})`}`;
    return Plot.plot({
      width,
      height: 64 * MODELS.length + 90,
      marginLeft: narrow ? 120 : 136,
      marginRight: narrow ? 92 : 104,
      marginBottom: 52,
      style: STYLE,
      x: { domain: [0, 24000], label: "Tokens per task", grid: true, tickFormat: (d) => `${d / 1000}k`, ...X_LABEL },
      y: { axis: null, domain: arms },
      fy: { domain: MODELS, label: null, padding: 0.25 },
      color: { domain: arms, range: [COLORS.standard, COLORS.minimal], legend: true },
      marks: [
        Plot.ruleY(data, { fy: "model", y: "arm", x1: 0, x2: "tokens", stroke: "arm", strokeWidth: 12 }),
        Plot.text(data, { fy: "model", y: "arm", x: "tokens", text: label, textAnchor: "start", dx: 6 }),
        Plot.tip(data, Plot.pointer({ fy: "model", y: "arm", x: "tokens", title: (d) => `${d.model}, ${d.arm.toLowerCase()}\n${label(d)} tokens per task` })),
      ],
    });
  },
};
