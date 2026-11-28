// Interactive Observable Plot charts for "Designing functions for AI isn't the same as designing them for humans"
// Data measured on 2026-11-27 (PST) from mindroom-ai/mindroom git snapshots:
//   before: df7f97a04 (2026-11-24 13:16 PST, before #4332 prompt tightening and Waves 1-9)
//   after:  295a31a16 (2026-11-27 17:34 PST, origin/main after Agno deletion + tool schema pass)
// Tokenized as compact JSON with tiktoken o200k_base.

const STYLE = {
  background: "transparent",
  fontSize: "12.5px",
  fontFamily: "system-ui, -apple-system, sans-serif",
};

const X_LABEL = { labelAnchor: "center", labelOffset: 42 };

const k = (n) => (n >= 1000 ? `${(n / 1000).toFixed(1)}k` : `${n}`);

// 1. Representative agent request (tests/fixtures/agno_parity/prompts/agent_anthropic.json)
const AGENT_REQUEST = [
  { stage: "Before (Nov 24)", part: "System prompt", x1: 0, x2: 2968, total: 6877, fns: 23 },
  { stage: "Before (Nov 24)", part: "Tool schemas", x1: 2968, x2: 6877, total: 6877, fns: 23 },
  { stage: "After (Nov 27)", part: "System prompt", x1: 0, x2: 1215, total: 2955, fns: 9 },
  { stage: "After (Nov 27)", part: "Tool schemas", x1: 1215, x2: 2955, total: 2955, fns: 9 },
];

const AGENT_TOTALS = [
  { stage: "Before (Nov 24)", total: 6877, label: "6,877 tok (23 tools)" },
  { stage: "After (Nov 27)", total: 2955, label: "2,955 tok (9 tools, -57%)" },
];

// 2. Top toolkits in tests/fixtures/agno_parity/tools/schemas.json (df7f97a04 -> 295a31a16)
const TOOLKIT_ROWS = [
  ["github", 39, 5, 6670, 1658],
  ["gmail", 26, 5, 4180, 1266],
  ["workflow", 6, 2, 3454, 2033],
  ["outlook_mail", 10, 4, 3243, 1540],
  ["outlook_calendar", 8, 2, 3203, 1183],
  ["docker", 24, 3, 3129, 819],
  ["spotify", 18, 4, 3123, 820],
  ["microsoft_teams", 11, 2, 2808, 923],
  ["google_calendar", 14, 2, 2564, 788],
  ["e2b", 19, 4, 2397, 726],
  ["atlassian", 13, 4, 2384, 1490],
  ["slack", 9, 3, 2224, 1163],
  ["homeassistant", 11, 2, 1449, 488],
];

export default {
  agentRequest({ Plot, width }) {
    const narrow = width < 520;
    return Plot.plot({
      width,
      height: 185,
      marginLeft: narrow ? 108 : 128,
      marginRight: narrow ? 132 : 172,
      marginBottom: 48,
      style: STYLE,
      x: {
        domain: [0, 7400],
        label: "Fixed tokens sent on every request (o200k_base)",
        grid: true,
        tickFormat: (d) => `${d / 1000}k`,
        ...X_LABEL,
      },
      y: {
        domain: ["Before (Nov 24)", "After (Nov 27)"],
        label: null,
        padding: 0.32,
      },
      color: {
        domain: ["System prompt", "Tool schemas"],
        range: ["#97bbf5", "#4269d0"],
        legend: true,
      },
      marks: [
        Plot.barX(AGENT_REQUEST, { y: "stage", x1: "x1", x2: "x2", fill: "part", rx: 3 }),
        Plot.text(AGENT_TOTALS, {
          y: "stage",
          x: "total",
          text: "label",
          textAnchor: "start",
          dx: 8,
          fontWeight: 600,
        }),
        Plot.tip(
          AGENT_REQUEST,
          Plot.pointer({
            y: "stage",
            x: (d) => (d.x1 + d.x2) / 2,
            title: (d) =>
              `${d.stage}\n${d.part}: ${(d.x2 - d.x1).toLocaleString()} tokens\nTotal fixed prefix: ${d.total.toLocaleString()} tokens (${d.fns} functions)`,
          })
        ),
      ],
    });
  },

  catalogReduction({ Plot, width }) {
    const narrow = width < 520;
    const data = TOOLKIT_ROWS.flatMap(([toolkit, bf, af, bt, at]) => {
      const pct = Math.round(((at - bt) / bt) * 100);
      return [
        { toolkit, state: "Before (Nov 24)", tokens: bt, fns: bf, bf, af, bt, at, pct },
        { toolkit, state: "After (Nov 27)", tokens: at, fns: af, bf, af, bt, at, pct },
      ];
    });
    const labels = TOOLKIT_ROWS.map(([toolkit, bf, af, bt, at]) => ({
      toolkit,
      x: bt,
      label: `${bf} -> ${af} fns (${Math.round(((at - bt) / bt) * 100)}%)`,
    }));

    return Plot.plot({
      width,
      height: 36 * TOOLKIT_ROWS.length + 100,
      marginLeft: narrow ? 118 : 138,
      marginRight: narrow ? 105 : 135,
      marginBottom: 52,
      style: STYLE,
      x: {
        domain: [0, 7200],
        label: "Schema tokens per toolkit (o200k_base)",
        grid: true,
        tickFormat: (d) => `${d / 1000}k`,
        ...X_LABEL,
      },
      y: { axis: null, domain: ["Before (Nov 24)", "After (Nov 27)"] },
      fy: { domain: TOOLKIT_ROWS.map((r) => r[0]), label: null, padding: 0.28 },
      color: {
        domain: ["Before (Nov 24)", "After (Nov 27)"],
        range: ["#cbd5e1", "#4269d0"],
        legend: true,
      },
      marks: [
        Plot.barX(data, { fy: "toolkit", y: "state", x: "tokens", fill: "state", insetTop: 1, insetBottom: 1, rx: 2 }),
        Plot.text(labels, {
          fy: "toolkit",
          y: () => "Before (Nov 24)",
          x: "x",
          text: "label",
          textAnchor: "start",
          dx: 6,
          fontSize: 11.5,
        }),
        Plot.tip(
          data,
          Plot.pointer({
            fy: "toolkit",
            y: "state",
            x: "tokens",
            title: (d) =>
              `${d.toolkit} (${d.state})\nSchema: ${d.tokens.toLocaleString()} tokens (${d.fns} functions)\nChange: ${d.bf} -> ${d.af} functions, ${k(d.bt)} -> ${k(d.at)} tokens (${d.pct}%)`,
          })
        ),
      ],
    });
  },

  githubShapes({ Plot, width }) {
    const narrow = width < 520;
    // Controlled 400-trial GitHub tool-calling eval (20 tasks x 4 arms x 5 models, temp=0)
    // Avg prompt tokens and pass rate (%) per arm
    const ARMS = [
      { arm: "1 fn", fns: 1, avgTok: 1649, schemaTok: 1258, maxParams: 42, pass: 79, leaked: 7, missing: 9, label: "1 fn (79%)", dx: 10, dy: 12 },
      { arm: "2 fns", fns: 2, avgTok: 1751, schemaTok: 1338, maxParams: 28, pass: 83, leaked: 1, missing: 8, label: "2 fns (83%)", dx: 14, dy: 2 },
      { arm: "5 fns", fns: 5, avgTok: 1971, schemaTok: 1488, maxParams: 15, pass: 93, leaked: 0, missing: 3, label: "5 fns (93%, sweet spot)", dx: 12, dy: 4 },
      { arm: "39 fns", fns: 39, avgTok: 5710, schemaTok: 4480, maxParams: 10, pass: 93, leaked: 0, missing: 3, label: "39 fns (93%, 3x tokens)", dx: -10, dy: -14, anchor: "end" },
    ];
    const MODEL_POINTS = [
      // inkling-2:mini (local)
      { model: "inkling-2:mini", arm: "1 fn", avgTok: 2080, pass: 65, n: "13/20" },
      { model: "inkling-2:mini", arm: "2 fns", avgTok: 2236, pass: 65, n: "13/20" },
      { model: "inkling-2:mini", arm: "5 fns", avgTok: 2618, pass: 85, n: "17/20" },
      { model: "inkling-2:mini", arm: "39 fns", avgTok: 7921, pass: 80, n: "16/20" },
      // qwen/qwen3.5-9b
      { model: "qwen3.5-9b", arm: "1 fn", avgTok: 1682, pass: 70, n: "14/20" },
      { model: "qwen3.5-9b", arm: "2 fns", avgTok: 1798, pass: 80, n: "16/20" },
      { model: "qwen3.5-9b", arm: "5 fns", avgTok: 2058, pass: 90, n: "18/20" },
      { model: "qwen3.5-9b", arm: "39 fns", avgTok: 6188, pass: 100, n: "20/20" },
      // google/gemma-4-26b-a4b-it
      { model: "gemma-4-26b", arm: "1 fn", avgTok: 1626, pass: 70, n: "14/20" },
      { model: "gemma-4-26b", arm: "2 fns", avgTok: 1719, pass: 75, n: "15/20" },
      { model: "gemma-4-26b", arm: "5 fns", avgTok: 1922, pass: 90, n: "18/20" },
      { model: "gemma-4-26b", arm: "39 fns", avgTok: 5578, pass: 95, n: "19/20" },
      // google/gemma-4-31b-it
      { model: "gemma-4-31b", arm: "1 fn", avgTok: 1624, pass: 90, n: "18/20" },
      { model: "gemma-4-31b", arm: "2 fns", avgTok: 1718, pass: 100, n: "20/20" },
      { model: "gemma-4-31b", arm: "5 fns", avgTok: 1921, pass: 100, n: "20/20" },
      { model: "gemma-4-31b", arm: "39 fns", avgTok: 5572, pass: 90, n: "18/20" },
      // openai/gpt-5-mini
      { model: "gpt-5-mini", arm: "1 fn", avgTok: 1235, pass: 100, n: "20/20" },
      { model: "gpt-5-mini", arm: "2 fns", avgTok: 1283, pass: 95, n: "19/20" },
      { model: "gpt-5-mini", arm: "5 fns", avgTok: 1337, pass: 100, n: "20/20" },
      { model: "gpt-5-mini", arm: "39 fns", avgTok: 3290, pass: 100, n: "20/20" },
    ];
    // Plot on categorical arm x-axis? No, plot exact average prompt tokens (model-average x for clarity,
    // plus per-model points at arm's average token x so every arm lines up cleanly vertically!).
    const armX = Object.fromEntries(ARMS.map((a) => [a.arm, a.avgTok]));
    const alignedModels = MODEL_POINTS.map((p) => ({ ...p, xTok: armX[p.arm] }));

    return Plot.plot({
      width,
      height: narrow ? 310 : 340,
      marginLeft: 54,
      marginRight: narrow ? 18 : 28,
      marginTop: 28,
      marginBottom: 52,
      style: STYLE,
      x: {
        domain: [1200, 6200],
        label: "Average prompt tokens per call (5-model mean)",
        grid: true,
        tickFormat: (d) => `${(d / 1000).toFixed(1)}k`,
        ...X_LABEL,
      },
      y: {
        domain: [58, 105],
        ticks: [60, 70, 80, 90, 100],
        label: "First-try exact pass rate (%)",
        grid: true,
        tickFormat: (d) => `${d}%`,
      },
      color: {
        domain: ["gpt-5-mini", "gemma-4-31b", "gemma-4-26b", "qwen3.5-9b", "inkling-2:mini"],
        range: ["#64748b", "#0ea5e9", "#8b5cf6", "#f59e0b", "#ec4899"],
        legend: true,
      },
      marks: [
        Plot.line(alignedModels, {
          x: "xTok",
          y: "pass",
          stroke: "model",
          strokeOpacity: 0.42,
          strokeWidth: 1.5,
        }),
        Plot.dot(alignedModels, {
          x: "xTok",
          y: "pass",
          fill: "model",
          fillOpacity: 0.72,
          r: 4,
        }),
        Plot.line(ARMS, {
          x: "avgTok",
          y: "pass",
          stroke: "#16a34a",
          strokeWidth: 3.2,
        }),
        Plot.dot(ARMS, {
          x: "avgTok",
          y: "pass",
          fill: (d) => (d.arm === "5 fns" ? "#16a34a" : "currentColor"),
          stroke: "#ffffff",
          strokeWidth: 1.5,
          r: (d) => (d.arm === "5 fns" ? 7 : 5.5),
        }),
        Plot.text(ARMS.filter((d) => !d.anchor), {
          x: "avgTok",
          y: "pass",
          text: "label",
          textAnchor: "start",
          dx: (d) => d.dx,
          dy: (d) => d.dy,
          fontWeight: (d) => (d.arm === "5 fns" ? 700 : 600),
          fontSize: narrow ? 10.5 : 12,
          fill: (d) => (d.arm === "5 fns" ? "#16a34a" : "currentColor"),
        }),
        Plot.text(ARMS.filter((d) => d.anchor === "end"), {
          x: "avgTok",
          y: "pass",
          text: "label",
          textAnchor: "end",
          dx: -10,
          dy: -14,
          fontWeight: 600,
          fontSize: narrow ? 10.5 : 12,
        }),
        Plot.tip(
          ARMS,
          Plot.pointer({
            x: "avgTok",
            y: "pass",
            title: (d) =>
              `${d.arm} (5-model average: ${d.pass}/100)\nSchema: ${d.schemaTok.toLocaleString()} tok (max ${d.maxParams} params/fn)\nAvg prompt: ${d.avgTok.toLocaleString()} tok/call\nLeaked args: ${d.leaked} | Missing args: ${d.missing}`,
          })
        ),
        Plot.tip(
          alignedModels,
          Plot.pointer({
            x: "xTok",
            y: "pass",
            title: (d) =>
              `${d.model} · ${d.arm}\nPassed: ${d.n} (${d.pass}%)\nModel avg prompt: ${d.avgTok.toLocaleString()} tok`,
          })
        ),
      ],
    });
  },

  spendBreakdown({ Plot, width }) {
    const narrow = width < 520;
    // 7-day real MindRoom usage (345,924 OpenRouter-priced requests, Nov 20-27 2026)
    // OpenRouter list-price spend share (%) by billing bucket
    const ROWS = [
      ["All models", 29.7, 21.6, 30.0, 18.7, 345924, 91.8],
      ["GPT-6.2 Sol", 40.1, 41.2, 0.1, 18.6, 19026, 95.6],
      ["Claude Opus 5.5", 38.7, 35.7, 2.7, 22.9, 85883, 95.6],
      ["GPT-6.2 Astra", 33.4, 54.0, 0.2, 12.5, 61155, 93.6],
      ["Claude Fable 5.2", 28.3, 24.6, 7.4, 39.6, 14897, 97.0],
      ["Gemini 4 Neon", 24.8, 0.0, 58.1, 17.1, 161925, 89.0],
    ];
    const segs = ROWS.flatMap(([model, cr, cw, unc, out, reqs, crTok]) => {
      let x = 0;
      const parts = [
        ["Cache read", cr],
        ["Cache write", cw],
        ["Uncached input", unc],
        ["Output", out],
      ];
      return parts
        .filter(([, v]) => v > 0)
        .map(([bucket, v]) => {
          const item = { model, bucket, x1: x, x2: x + v, pct: v, reqs, crTok };
          x += v;
          return item;
        });
    });

    return Plot.plot({
      width,
      height: 265,
      marginLeft: narrow ? 108 : 124,
      marginRight: narrow ? 14 : 24,
      marginBottom: 48,
      style: STYLE,
      x: {
        domain: [0, 100],
        label: "Share of estimated spend (%)",
        grid: true,
        tickFormat: (d) => `${d}%`,
        ...X_LABEL,
      },
      y: {
        domain: ROWS.map((r) => r[0]),
        label: null,
        padding: 0.28,
      },
      color: {
        domain: ["Cache read", "Cache write", "Uncached input", "Output"],
        range: ["#2563eb", "#60a5fa", "#f59e0b", "#16a34a"],
        legend: true,
      },
      marks: [
        Plot.barX(segs, { y: "model", x1: "x1", x2: "x2", fill: "bucket", rx: 2 }),
        Plot.text(
          segs.filter((d) => d.pct >= 12),
          {
            y: "model",
            x: (d) => (d.x1 + d.x2) / 2,
            text: (d) => `${Math.round(d.pct)}%`,
            fill: "#ffffff",
            fontWeight: 600,
            fontSize: 11,
          }
        ),
        Plot.tip(
          segs,
          Plot.pointer({
            y: "model",
            x: (d) => (d.x1 + d.x2) / 2,
            title: (d) =>
              `${d.model} (${d.reqs.toLocaleString()} requests)\n${d.bucket}: ${d.pct.toFixed(1)}% of spend\nCache-read token share: ${d.crTok}%`,
          })
        ),
      ],
    });
  },
};
