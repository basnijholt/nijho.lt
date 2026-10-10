// Charts for this post, rendered by layouts/_shortcodes/plot.html with Observable Plot.
// All numbers come from my runs of 12 held-out terminal tasks, three runs per task (36 per configuration),
// on MindRoom pull request #2766 (commit d73aafb51) and on MindRoom's main branch (v2026.10.228).

const COLORS = {
  whole: "#4269d0",
  capped: "#97bbf5",
  shell: "#a463f2",
  shellOnly: "#6cc5b0",
  standardFixed: "#ffb3a6",
  standardWork: "#ff725c",
  minimalFixed: "#9fd8a9",
  minimalWork: "#3ca951",
  mindroomFixed: "#97bbf5",
  mindroomWork: "#4269d0",
  nativeFixed: "#f7d58b",
  nativeWork: "#efb118",
  systemPrompt: "#9c9c9c",
  toolDefinitions: "#a463f2",
  claude: "#ff725c",
  gpt: "#4269d0",
};

const k = (d) => `${(d / 1000).toFixed(1)}k`;

// Two bars per model, each split into the fixed part (first-request input times requests) and the work on top of it.
// rows: [model, [fixed, work, requests], [fixed, work, requests]]; each segment carries its own start and end.
function splitChart({ Plot, width, rows, arms, colors, xMax }) {
  const narrow = width < 600;
  const parts = ["Fixed part", "Work"];
  const data = rows.flatMap(([model, ...bars]) =>
    bars.flatMap(([fixed, work, requests], i) => [
      { model, arm: arms[i], part: parts[0], key: `${arms[i]}, fixed`, tokens: fixed, x1: 0, x2: fixed, total: fixed + work, requests },
      { model, arm: arms[i], part: parts[1], key: `${arms[i]}, work`, tokens: work, x1: fixed, x2: fixed + work, total: fixed + work, requests },
    ])
  );
  const totals = rows.flatMap(([model, [af, aw], [bf, bw]]) => [
    { model, arm: arms[0], total: af + aw, label: k(af + aw) },
    { model, arm: arms[1], total: bf + bw, label: `${k(bf + bw)} (${pct(Math.round(((bf + bw) / (af + aw) - 1) * 100))})` },
  ]);
  const keys = arms.flatMap((arm) => [`${arm}, fixed`, `${arm}, work`]);
  return Plot.plot({
    width,
    height: 64 * rows.length + 110,
    marginLeft: 136,
    marginRight: narrow ? 92 : 104,
    marginBottom: 52,
    style: STYLE,
    x: { domain: [0, xMax], label: "Tokens per task", grid: true, tickFormat: (d) => `${d / 1000}k`, ...X_LABEL },
    y: { axis: null, domain: arms },
    fy: { domain: rows.map((r) => r[0]), label: null, padding: 0.25 },
    color: { domain: keys, range: colors, legend: true },
    marks: [
      Plot.barX(data, { fy: "model", y: "arm", x1: "x1", x2: "x2", fill: "key", insetTop: 2, insetBottom: 2 }),
      Plot.text(totals, { fy: "model", y: "arm", x: "total", text: "label", textAnchor: "start", dx: 6 }),
      Plot.tip(
        data,
        Plot.pointer({
          fy: "model",
          y: "arm",
          x: (d) => (d.x1 + d.x2) / 2,
          title: (d) => `${d.model}, ${d.arm}\n${d.part}: ${k(d.tokens)} tokens per task\nTotal: ${k(d.total)}, ${d.requests.toFixed(2)} requests per task`,
        })
      ),
    ],
  });
}

// Two dots per model, each a change in tokens per task with its 95% confidence interval.
// rows: [model, [change, lo, hi], [change, lo, hi]], in the order of series.
function deltaChart({ Plot, width, rows, series, colors, domain, label, shortLabel = label }) {
  const narrow = width < 600;
  const models = rows.map((r) => r[0]);
  const data = rows.flatMap(([model, ...values]) =>
    values.map(([change, lo, hi], i) => ({ model, series: series[i], change, lo, hi }))
  );
  return Plot.plot({
    width,
    height: 64 * rows.length + 110,
    marginLeft: 136,
    marginRight: 24,
    marginBottom: 52,
    style: STYLE,
    x: { domain, label: narrow ? shortLabel : label, grid: true, tickFormat: pct, ...X_LABEL },
    y: { axis: null, domain: series },
    fy: { domain: models, label: null, padding: 0.25 },
    color: { domain: series, range: colors, legend: true },
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
}

const STYLE = { fontSize: "13px", fontFamily: "system-ui, sans-serif", background: "transparent" };

// Centered axis labels below the tick labels, so they never collide with them.
const X_LABEL = { labelAnchor: "center", labelArrow: "none", labelOffset: 42 };

const MODELS = ["Claude Opus 5.5", "Claude Sonnet 5.5", "GPT-6 Astra", "GPT-6.1 Sol", "GPT-6 Luna"];

const pct = (d) => `${d > 0 ? "+" : d < 0 ? "−" : ""}${Math.abs(d)}%`;

export default {
  nativeDelta: ({ Plot, width }) =>
    // Change in tokens per task with native tools instead of MindRoom's, and its 95% confidence interval:
    // shell and file tools with whole output, and the same with the shell output capped at 100 lines.
    deltaChart({
      Plot,
      width,
      series: ["Whole output", "Last 100 lines"],
      colors: [COLORS.whole, COLORS.capped],
      domain: [-30, 45],
      label: "Change in tokens per task with native tools",
      shortLabel: "Change with native tools",
      rows: [
        [MODELS[0], [-9, -13, -4], [-8, -13, -3]],
        [MODELS[1], [-9, -15, -1], [-8, -13, -2]],
        [MODELS[2], [31, 24, 38], [26, 18, 34]],
        [MODELS[3], [19, 9, 29], [15, 6, 25]],
        [MODELS[4], [-4, -18, 14], [-10, -19, 1]],
      ],
    }),

  shellOnly: ({ Plot, width }) =>
    // Change in tokens per task with 95% confidence intervals, on the pull request through MindRoom's API:
    // MindRoom's shell tool alone against all of MindRoom's tools, and the native shell tools against MindRoom's shell tool.
    deltaChart({
      Plot,
      width,
      series: ["Without the file tools", "Native shell tools"],
      colors: [COLORS.shellOnly, COLORS.shell],
      domain: [-50, 15],
      label: "Change in tokens per task",
      rows: [
        [MODELS[0], [-32, -35, -29], [-6, -12, 0]],
        [MODELS[1], [-30, -34, -25], [-18, -24, -13]],
        [MODELS[2], [-27, -30, -24], [0, -3, 4]],
        [MODELS[3], [-30, -35, -25], [0, -5, 4]],
        [MODELS[4], [-41, -46, -34], [-1, -11, 9]],
      ],
    }),

  generations: ({ Plot, width }) => {
    const narrow = width < 600;
    // Change in tokens per task with native tools (shell and file tools) instead of MindRoom's, with 95% CIs.
    // Each model ran at its provider's default reasoning setting.
    const data = [
      { family: "Claude", model: "Opus 4.7", reasoning: "no thinking", change: -22, lo: -27, hi: -16 },
      { family: "Claude", model: "Opus 4.8", reasoning: "no thinking", change: -26, lo: -34, hi: -17 },
      { family: "Claude", model: "Sonnet 5", reasoning: "adaptive thinking", change: -36, lo: -46, hi: -22 },
      { family: "Claude", model: "Opus 5.5", reasoning: "adaptive thinking", change: -9, lo: -13, hi: -4 },
      { family: "Claude", model: "Sonnet 5.5", reasoning: "adaptive thinking", change: -9, lo: -15, hi: -1 },
      { family: "GPT", model: "GPT-5.5", reasoning: "default", change: -4, lo: -13, hi: 7 },
      { family: "GPT", model: "GPT-5.6 Sol", reasoning: "default", change: -15, lo: -23, hi: -5 },
      { family: "GPT", model: "GPT-6 Astra", reasoning: "default", change: 31, lo: 24, hi: 38 },
      { family: "GPT", model: "GPT-6 Luna", reasoning: "default", change: -4, lo: -18, hi: 14 },
      { family: "GPT", model: "GPT-6.1 Sol", reasoning: "default", change: 19, lo: 9, hi: 29 },
    ].map((d) => ({ ...d, label: narrow ? d.model : `${d.model} (${d.reasoning})` }));
    return Plot.plot({
      width,
      height: 30 * data.length + 110,
      marginLeft: narrow ? 92 : 210,
      marginRight: 24,
      marginBottom: 52,
      style: STYLE,
      x: { domain: [-50, 45], label: "Change in tokens per task with native tools", grid: true, tickFormat: pct, ...X_LABEL },
      y: { label: null, domain: data.map((d) => d.label) },
      color: { domain: ["Claude", "GPT"], range: [COLORS.standardWork, COLORS.whole], legend: true },
      marks: [
        Plot.ruleX([0], { stroke: "currentColor", strokeOpacity: 0.6 }),
        Plot.ruleY(data, { y: "label", x1: "lo", x2: "hi", stroke: "family", strokeWidth: 3 }),
        Plot.dot(data, { y: "label", x: "change", fill: "family", r: 5 }),
        Plot.tip(
          data,
          Plot.pointer({
            y: "label",
            x: "change",
            title: (d) => `${d.model}, ${d.reasoning}\n${pct(d.change)} tokens per task\n95% CI ${pct(d.lo)} to ${pct(d.hi)}`,
          })
        ),
      ],
    });
  },

  tokenSplit: ({ Plot, width }) =>
    // Through MindRoom's API on the pull request, default reasoning: MindRoom's shell and file tools against the native ones.
    splitChart({
      Plot,
      width,
      arms: ["MindRoom's tools", "Native tools"],
      colors: [COLORS.mindroomFixed, COLORS.mindroomWork, COLORS.nativeFixed, COLORS.nativeWork],
      xMax: 22000,
      rows: [
        [MODELS[0], [14617, 4326, 3.94], [12713, 4531, 3.94]],
        [MODELS[1], [13994, 3771, 3.78], [12610, 3627, 3.92]],
        [MODELS[2], [5767, 2483, 3.53], [7065, 3741, 4.0]],
        [MODELS[3], [6086, 2787, 3.72], [7072, 3462, 4.0]],
        [MODELS[4], [7924, 4079, 4.86], [6822, 4710, 3.86]],
      ],
    }),

  effortChange: ({ Plot, width }) => {
    const narrow = width < 600;
    const levels = ["low", "default", "high"];
    // Change in tokens per task with native tools instead of MindRoom's, with 95% CIs, at each reasoning effort.
    const data = [
      { model: "Claude Sonnet 5.5", level: "low", change: -19, lo: -23, hi: -15, mindroom: 15154, native: 12330 },
      { model: "Claude Sonnet 5.5", level: "default", change: -9, lo: -15, hi: -1, mindroom: 17765, native: 16237 },
      { model: "Claude Sonnet 5.5", level: "high", change: -15, lo: -19, hi: -10, mindroom: 18286, native: 15630 },
      { model: "GPT-6 Astra", level: "low", change: 27, lo: 20, hi: 34, mindroom: 8361, native: 10627 },
      { model: "GPT-6 Astra", level: "default", change: 31, lo: 24, hi: 38, mindroom: 8250, native: 10807 },
      { model: "GPT-6 Astra", level: "high", change: 45, lo: 37, hi: 52, mindroom: 8934, native: 12918 },
    ];
    const models = ["Claude Sonnet 5.5", "GPT-6 Astra"];
    const last = models.map((m) => data.filter((d) => d.model === m).at(-1));
    return Plot.plot({
      width,
      height: Math.min(360, Math.max(280, width * 0.5)),
      marginLeft: 52,
      marginRight: narrow ? 96 : 130,
      marginBottom: 52,
      style: STYLE,
      x: { domain: levels, label: "Reasoning effort", padding: 0.4, ...X_LABEL },
      y: { domain: [-30, 55], label: "Change in tokens per task with native tools", labelArrow: "none", grid: true, tickFormat: pct },
      color: { domain: models, range: [COLORS.claude, COLORS.gpt] },
      marks: [
        Plot.ruleY([0], { stroke: "currentColor", strokeOpacity: 0.6 }),
        Plot.ruleX(data, { x: "level", y1: "lo", y2: "hi", stroke: "model", strokeWidth: 3 }),
        Plot.line(data, { x: "level", y: "change", stroke: "model", strokeWidth: 1.5, strokeOpacity: 0.5 }),
        Plot.dot(data, { x: "level", y: "change", fill: "model", r: 5 }),
        Plot.text(last, { x: "level", y: "change", text: (d) => (narrow ? d.model.replace("Claude ", "") : d.model), fill: "model", textAnchor: "start", dx: 12, fontWeight: "bold" }),
        Plot.tip(
          data,
          Plot.pointer({
            x: "level",
            y: "change",
            title: (d) => `${d.model}, ${d.level} effort\n${pct(d.change)} tokens per task (95% CI ${pct(d.lo)} to ${pct(d.hi)})\nMindRoom's tools ${k(d.mindroom)}, native ${k(d.native)}`,
          })
        ),
      ],
    });
  },

  promptParts: ({ Plot, width }) => {
    const parts = ["System prompt", "Tool definitions"];
    // Tokens each part costs on every request, measured by sending it on its own and reading the reported input tokens.
    const bars = [
      { model: "Claude Sonnet 5.5", mode: "standard mode", system: 2295, tools: 1292 },
      { model: "Claude Sonnet 5.5", mode: "minimal mode", system: 152, tools: 363 },
      { model: "GPT-6 Astra", mode: "standard mode", system: 1463, tools: 867 },
      { model: "GPT-6 Astra", mode: "minimal mode", system: 97, tools: 72 },
    ].map((d) => ({ ...d, label: `${d.model}\n${d.mode}` }));
    const data = bars.flatMap((d) => [
      { ...d, part: parts[0], tokens: d.system, x1: 0, x2: d.system },
      { ...d, part: parts[1], tokens: d.tools, x1: d.system, x2: d.system + d.tools },
    ]);
    return Plot.plot({
      width,
      height: 54 * bars.length + 110,
      marginLeft: 136,
      marginRight: 64,
      marginBottom: 52,
      style: STYLE,
      x: { domain: [0, 4000], label: "Tokens on every request", grid: true, tickFormat: (d) => `${d / 1000}k`, ...X_LABEL },
      y: { domain: bars.map((d) => d.label), label: null, tickSize: 0, padding: 0.25 },
      color: { domain: parts, range: [COLORS.systemPrompt, COLORS.toolDefinitions], legend: true },
      marks: [
        Plot.barX(data, { y: "label", x1: "x1", x2: "x2", fill: "part" }),
        Plot.text(bars, { y: "label", x: (d) => d.system + d.tools, text: (d) => (d.system + d.tools).toLocaleString("en-US"), textAnchor: "start", dx: 6 }),
        Plot.tip(
          data,
          Plot.pointer({
            y: "label",
            x: (d) => (d.x1 + d.x2) / 2,
            title: (d) => `${d.model}, ${d.mode}\n${d.part}: ${d.tokens.toLocaleString("en-US")} tokens`,
          })
        ),
      ],
    });
  },

  minimalSplit: ({ Plot, width }) =>
    // Matrix conversations on main, default reasoning, the same agent with only the shell tool.
    splitChart({
      Plot,
      width,
      arms: ["Standard mode", "Minimal mode"],
      colors: [COLORS.standardFixed, COLORS.standardWork, COLORS.minimalFixed, COLORS.minimalWork],
      xMax: 24000,
      rows: [
        [MODELS[0], [18030, 4161, 3.89], [3919, 4111, 3.89]],
        [MODELS[1], [18300, 4148, 3.94], [3817, 4011, 3.81]],
        [MODELS[2], [8950, 2479, 3.44], [1265, 1533, 3.03]],
        [MODELS[3], [8666, 2404, 3.33], [1278, 2092, 3.06]],
        [MODELS[4], [10035, 2532, 3.86], [1678, 3541, 4.03]],
      ],
    }),
};
