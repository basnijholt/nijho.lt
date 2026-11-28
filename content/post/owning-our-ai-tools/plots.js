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
};
