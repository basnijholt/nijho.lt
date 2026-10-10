// Charts for this post, rendered by layouts/_shortcodes/plot.html with Observable Plot.
// All numbers come from my runs of 12 held-out terminal tasks, three runs per task (36 per configuration),
// on MindRoom pull request #2766 (commit d73aafb51) and on MindRoom's main branch (v2026.10.228).

const COLORS = {
  whole: "#4269d0",
  capped: "#97bbf5",
  shell: "#a463f2",
  standardFixed: "#ffb3a6",
  standardWork: "#ff725c",
  minimalFixed: "#9fd8a9",
  minimalWork: "#3ca951",
};

const STYLE = { fontSize: "13px", fontFamily: "system-ui, sans-serif", background: "transparent" };

// Centered axis labels below the tick labels, so they never collide with them.
const X_LABEL = { labelAnchor: "center", labelArrow: "none", labelOffset: 42 };

const MODELS = ["Claude Opus 5.5", "Claude Sonnet 5.5", "GPT-6 Astra", "GPT-6.1 Sol", "GPT-6 Luna"];

const pct = (d) => `${d > 0 ? "+" : d < 0 ? "−" : ""}${Math.abs(d)}%`;

export default {
  nativeDelta: ({ Plot, width }) => {
    const narrow = width < 600;
    const series = ["Whole output", "Last 100 lines", "Shell tool only"];
    // Change in tokens per task with native tools instead of MindRoom's, and its 95% confidence interval:
    // shell and file tools with whole output, the same capped at 100 lines, and only the shell tool.
    const rows = [
      [MODELS[0], [-9, -13, -4], [-8, -13, -3], [-6, -12, 0]],
      [MODELS[1], [-9, -15, -1], [-8, -13, -2], [-18, -24, -13]],
      [MODELS[2], [31, 24, 38], [26, 18, 34], [0, -3, 4]],
      [MODELS[3], [19, 9, 29], [15, 6, 25], [0, -5, 4]],
      [MODELS[4], [-4, -18, 14], [-10, -19, 1], [-1, -11, 9]],
    ];
    const data = rows.flatMap(([model, ...values]) =>
      values.map(([change, lo, hi], i) => ({ model, series: series[i], change, lo, hi }))
    );
    return Plot.plot({
      width,
      height: 84 * MODELS.length + 90,
      marginLeft: narrow ? 120 : 136,
      marginRight: 24,
      marginBottom: 52,
      style: STYLE,
      x: { domain: [-30, 45], label: "Change in tokens per task with native tools", grid: true, tickFormat: pct, ...X_LABEL },
      y: { axis: null, domain: series },
      fy: { domain: MODELS, label: null, padding: 0.25 },
      color: { domain: series, range: [COLORS.whole, COLORS.capped, COLORS.shell], legend: true },
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

  minimalSplit: ({ Plot, width }) => {
    const narrow = width < 600;
    const arms = ["Standard mode", "Minimal mode"];
    // Tokens per task in Matrix conversations, same agent with only the shell tool. The fixed part is the first
    // request's input (system prompt, tool definitions, and task) times the number of requests; work is the rest.
    const rows = [
      [MODELS[0], [18030, 4161], [3919, 4111]],
      [MODELS[1], [18300, 4148], [3817, 4011]],
      [MODELS[2], [8950, 2479], [1265, 1533]],
      [MODELS[3], [8666, 2404], [1278, 2092]],
      [MODELS[4], [10035, 2532], [1678, 3541]],
    ];
    const parts = ["Fixed part", "Work"];
    // Each segment carries its own start and end, so the bars need no stacking transform.
    const data = rows.flatMap(([model, ...arms_]) =>
      arms_.flatMap(([fixed, work], i) => [
        { model, arm: arms[i], part: parts[0], key: `${arms[i]}, fixed`, tokens: fixed, x1: 0, x2: fixed, total: fixed + work },
        { model, arm: arms[i], part: parts[1], key: `${arms[i]}, work`, tokens: work, x1: fixed, x2: fixed + work, total: fixed + work },
      ])
    );
    const totals = rows.flatMap(([model, [sf, sw], [mf, mw]]) => [
      { model, arm: arms[0], total: sf + sw, label: `${((sf + sw) / 1000).toFixed(1)}k` },
      { model, arm: arms[1], total: mf + mw, label: `${((mf + mw) / 1000).toFixed(1)}k (${pct(Math.round(((mf + mw) / (sf + sw) - 1) * 100))})` },
    ]);
    const keys = [`${arms[0]}, fixed`, `${arms[0]}, work`, `${arms[1]}, fixed`, `${arms[1]}, work`];
    return Plot.plot({
      width,
      height: 64 * MODELS.length + 110,
      marginLeft: narrow ? 120 : 136,
      marginRight: narrow ? 92 : 104,
      marginBottom: 52,
      style: STYLE,
      x: { domain: [0, 24000], label: "Tokens per task", grid: true, tickFormat: (d) => `${d / 1000}k`, ...X_LABEL },
      y: { axis: null, domain: arms },
      fy: { domain: MODELS, label: null, padding: 0.25 },
      color: { domain: keys, range: [COLORS.standardFixed, COLORS.standardWork, COLORS.minimalFixed, COLORS.minimalWork], legend: true },
      marks: [
        Plot.barX(data, { fy: "model", y: "arm", x1: "x1", x2: "x2", fill: "key", insetTop: 2, insetBottom: 2 }),
        Plot.text(totals, { fy: "model", y: "arm", x: "total", text: "label", textAnchor: "start", dx: 6 }),
        Plot.tip(
          data,
          Plot.pointer({
            fy: "model",
            y: "arm",
            x: (d) => (d.x1 + d.x2) / 2,
            title: (d) => `${d.model}, ${d.arm.toLowerCase()}\n${d.part}: ${(d.tokens / 1000).toFixed(1)}k tokens per task\nTotal: ${(d.total / 1000).toFixed(1)}k`,
          })
        ),
      ],
    });
  },
};
