// Charts for this post, rendered by layouts/shortcodes/plot.html with Observable Plot.
// All numbers come from Artificial Analysis and OpenRouter as of 2026-09-30,
// or from the assumptions spelled out in the post (two RTX 3090s, ~150 tok/s, 700 W).

const COLORS = {
  closed: "#4269d0",
  open: "#ff725c",
  local: "#3ca951",
  paid: "#efb118",
};

const STYLE = { fontSize: "13px", fontFamily: "system-ui, sans-serif", background: "transparent" };

// Centered axis labels below the tick labels, so they never collide with them.
const X_LABEL = { labelAnchor: "center", labelArrow: "none", labelOffset: 42 };

const LUNA_COST = 66.81; // GPT-6 Luna (xhigh), one Intelligence Index run, via API
const QWEN_KWH = 357; // Qwen3.8 27B, one Intelligence Index run, on two 3090s at 700 W
const PRO6000_KWH = 760; // Same run at full precision on one RTX PRO 6000 (~48 tok/s) at 600 W

const usd = (d) => (d >= 100 ? `$${Math.round(d).toLocaleString("en-US")}` : `$${Math.round(d)}`);

export default {
  effortTokens: ({ Plot, width }) => {
    const levels = ["low", "medium", "high", "xhigh", "max"];
    const models = ["GPT-6 Luna", "Qwen3.8 27B"];
    // Output tokens per Intelligence Index task and score, per reasoning setting.
    const data = [
      { model: models[0], level: "low", tokens: 2086, score: 21.5 },
      { model: models[0], level: "medium", tokens: 11456, score: 29.9 },
      { model: models[0], level: "high", tokens: 19693, score: 32.9 },
      { model: models[0], level: "xhigh", tokens: 27487, score: 34.6 },
      { model: models[0], level: "max", tokens: 49956, score: 38.1 },
      { model: models[1], level: "low", tokens: 45426, score: 26.2 },
      { model: models[1], level: "medium", tokens: 51943, score: 27.6 },
      { model: models[1], level: "xhigh", tokens: 66797, score: 33.7 },
    ];
    const last = models.map((m) => data.filter((d) => d.model === m).at(-1));
    return Plot.plot({
      width,
      height: Math.min(340, Math.max(260, width * 0.45)),
      marginRight: width < 600 ? 90 : 110,
      marginBottom: 52,
      style: STYLE,
      x: { domain: levels, label: "Reasoning setting", padding: 0.3, ...X_LABEL },
      y: { domain: [0, 70000], label: "Output tokens per task", labelArrow: "none", grid: true, tickFormat: (d) => `${d / 1000}k` },
      color: { domain: models, range: [COLORS.closed, COLORS.open] },
      marks: [
        Plot.line(data, { x: "level", y: "tokens", stroke: "model", strokeWidth: 2.5 }),
        Plot.dot(data, { x: "level", y: "tokens", fill: "model", r: 5 }),
        Plot.text(last, { x: "level", y: "tokens", text: "model", fill: "model", textAnchor: "start", dx: 10, fontWeight: "bold" }),
        Plot.tip(
          data,
          Plot.pointer({
            x: "level",
            y: "tokens",
            title: (d) => `${d.model}, ${d.level}\n${(d.tokens / 1000).toFixed(1)}k tokens per task\nScore ${d.score}`,
          })
        ),
      ],
    });
  },

  runCost: ({ Plot, width }) => {
    const narrow = width < 600;
    const groups = ["Closed model via API", "Open model at home (electricity only)", "Open model via API"];
    const data = [
      { label: "GPT-6 Luna via API", cost: LUNA_COST, group: groups[0] },
      { label: narrow ? "Qwen3.8 27B, quantized, on my 3090s" : "Qwen3.8 27B, quantized, on my two 3090s: electricity at 18 cents/kWh", cost: QWEN_KWH * 0.18, group: groups[1] },
      { label: narrow ? "Qwen3.8 27B, full precision, RTX PRO 6000" : "Qwen3.8 27B, full precision, on an RTX PRO 6000: electricity at 18 cents/kWh", cost: PRO6000_KWH * 0.18, group: groups[1] },
      { label: narrow ? "Qwen3.8 27B, full precision, ZDR API" : "Qwen3.8 27B, full precision, via the cheapest ZDR API", cost: 619, group: groups[2] },
    ];
    // Horizontal bars drawn as thick rules, with the label above each bar so it fits on phones.
    return Plot.plot({
      width,
      height: 56 * data.length + 72,
      marginLeft: 16,
      marginRight: 56,
      marginTop: 10,
      marginBottom: 52,
      style: STYLE,
      x: { domain: [0, 700], label: "Cost of one benchmark run (USD)", grid: true, tickFormat: (d) => `$${d}`, ...X_LABEL },
      y: { axis: null, domain: data.map((d) => d.label), inset: 24 },
      color: { domain: groups, range: [COLORS.closed, COLORS.local, COLORS.open] },
      marks: [
        Plot.ruleY(data, { y: "label", x1: 0, x2: "cost", stroke: "group", strokeWidth: 14 }),
        Plot.text(data, { y: "label", x: 0, text: "label", textAnchor: "start", dy: -17 }),
        Plot.text(data, { y: "label", x: "cost", text: (d) => usd(d.cost), textAnchor: "start", dx: 6, fontWeight: "bold" }),
      ],
    });
  },

  electricityCost: ({ Plot, width }) => {
    const rates = Array.from({ length: 41 }, (_, i) => i / 100);
    const data = rates.map((rate) => ({ rate, cost: QWEN_KWH * rate }));
    const breakEven = LUNA_COST / QWEN_KWH;
    return Plot.plot({
      width,
      height: Math.min(380, Math.max(280, width * 0.55)),
      marginLeft: 48,
      marginRight: 28,
      marginBottom: 52,
      style: STYLE,
      x: { domain: [0, 0.4], label: "Electricity price (USD per kWh)", tickFormat: (d) => `$${d.toFixed(2)}`, ...X_LABEL },
      y: { domain: [0, 150], label: "Cost of one benchmark run (USD)", labelArrow: "none", grid: true, tickFormat: (d) => `$${d}` },
      marks: [
        Plot.ruleY([LUNA_COST], { stroke: COLORS.closed, strokeDasharray: "5 4" }),
        Plot.text([width < 600 ? `Luna: ${usd(LUNA_COST)}` : `GPT-6 Luna via API: ${usd(LUNA_COST)}`], { x: 0.4, y: LUNA_COST, textAnchor: "end", dy: 12, fill: COLORS.closed }),
        Plot.lineY(data, { x: "rate", y: "cost", stroke: COLORS.local, strokeWidth: 3 }),
        Plot.text([width < 600 ? "My 3090s" : "Electricity for Qwen3.8 27B on my 3090s"], {
          x: 0.4,
          y: QWEN_KWH * 0.4,
          textAnchor: "end",
          dy: -12,
          fill: COLORS.local,
        }),
        Plot.dot([{ rate: breakEven, cost: LUNA_COST }], { x: "rate", y: "cost", fill: COLORS.local, r: 5 }),
        Plot.text([`${Math.round(breakEven * 100)} cents/kWh`], { x: breakEven, y: LUNA_COST, textAnchor: "end", dx: -8, dy: -12, fontWeight: "bold" }),
        Plot.tip(
          data,
          Plot.pointer({ x: "rate", y: "cost", title: (d) => `At $${d.rate.toFixed(2)}/kWh: ${usd(d.cost)} of electricity per run` })
        ),
      ],
    });
  },

  agentsPerKw: ({ Plot, width }) => {
    const narrow = width < 600;
    const data = [
      { label: "8× H200 server", agents: 1.8, color: COLORS.closed },
      { label: narrow ? "My two 3090s (estimate)" : "My two RTX 3090s (estimate, much smaller model)", agents: 2.9, color: COLORS.local },
      { label: "8× B300 server", agents: 6.9, color: COLORS.closed },
      { label: narrow ? "36× GB300 rack" : "Rack of 36 GB300s, prefill and decode on separate GPUs", agents: 35.8, color: COLORS.closed },
    ];
    // Horizontal bars drawn as thick rules, with the label above each bar so it fits on phones.
    return Plot.plot({
      width,
      height: 56 * data.length + 72,
      marginLeft: 16,
      marginRight: 48,
      marginTop: 10,
      marginBottom: 52,
      style: STYLE,
      x: { domain: [0, 40], label: "Agents per kW, each at 60+ tokens/s", grid: true, ...X_LABEL },
      y: { axis: null, domain: data.map((d) => d.label), inset: 24 },
      marks: [
        Plot.ruleY(data, { y: "label", x1: 0, x2: "agents", stroke: "color", strokeWidth: 14 }),
        Plot.text(data, { y: "label", x: 0, text: "label", textAnchor: "start", dy: -17 }),
        Plot.text(data, { y: "label", x: "agents", text: (d) => `${d.agents}`, textAnchor: "start", dx: 6, fontWeight: "bold" }),
      ],
    });
  },

  breakEven: ({ Plot, width }) => {
    const narrow = width < 600;
    const scenarios = [
      "Same model: Qwen3.8 27B via a ZDR API",
      narrow ? "Open model as efficient as Luna" : "Open model as efficient as Luna, at Luna's price",
      narrow ? "Same, after a 50% price cut" : "Same, after Luna's next 50% price cut",
    ];
    const rates = ["Free (solar)", "18 cents/kWh"];
    const hours = [
      [1.1, 1.6],
      [3.0, 5.2],
      [6.0, 15.1],
    ];
    const data = scenarios.flatMap((scenario, i) => rates.map((rate, j) => ({ scenario, rate, hours: hours[i][j] })));
    return Plot.plot({
      width,
      height: 330,
      marginLeft: 108,
      marginRight: 48,
      marginTop: 34,
      marginBottom: 52,
      style: STYLE,
      fy: { domain: scenarios, axis: null, padding: 0.45 },
      y: { domain: rates, label: null, tickSize: 0 },
      x: { domain: [0, 24], label: "Hours per day the GPUs are busy", ticks: [0, 4, 8, 12, 16, 20, 24], grid: true, ...X_LABEL },
      color: { domain: rates, range: [COLORS.local, COLORS.paid] },
      marks: [
        Plot.text(scenarios, { fy: (d) => d, text: (d) => d, frameAnchor: "top-left", lineAnchor: "bottom", dy: -8, dx: -100, fontWeight: "bold" }),
        Plot.barX(data, { fy: "scenario", y: "rate", x: "hours", fill: "rate" }),
        Plot.text(data, { fy: "scenario", y: "rate", x: "hours", text: (d) => `${d.hours.toFixed(1)} h`, textAnchor: "start", dx: 5 }),
      ],
    });
  },

  frontierGap: ({ Plot, width }) => {
    const narrow = width < 600;
    const day = (s) => new Date(s);
    const today = day("2026-10-01");
    const series = ["Best model available", "My go-to coding model", "Qwen 27B, fits on a 3090"];
    // Each new best model on the AA Intelligence Index (xhigh where available), by release date.
    const frontier = [
      { model: "GPT-5.2", date: day("2025-12-11"), score: 30.4 },
      { model: "Claude Opus 4.6", date: day("2026-02-05"), score: 31.9 },
      { model: "GPT-5.4", date: day("2026-03-05"), score: 39.0 },
      { model: "Claude Opus 4.7", date: day("2026-04-16"), score: 40.7 },
      { model: "Claude Opus 4.8", date: day("2026-05-28"), score: 41.8 },
      { model: "Claude Fable 5", date: day("2026-06-09"), score: 49.6 },
      { model: "Claude Opus 5", date: day("2026-07-24"), score: 49.7 },
      { model: "Claude Fable 5.1", date: day("2026-09-01"), score: 53.2 },
      { model: "Claude Opus 5.5", date: day("2026-09-22"), score: 56.0 },
    ];
    const qwen = [
      { model: "Qwen3.5 27B", date: day("2026-02-24"), score: 22.9 },
      { model: "Qwen3.6 27B", date: day("2026-04-22"), score: 21.4 },
      { model: "Qwen3.8 27B", date: day("2026-08-14"), score: 33.7 },
    ];
    const goTo = [
      { model: "Opus 4.6", date: day("2026-02-05"), score: 31.9 },
      { model: "GPT-5.6 Sol", date: day("2026-07-09"), score: 44.0 },
      { model: "GPT-6 Astra", date: day("2026-09-03"), score: 52.4 },
      { model: "Opus 5.5", date: day("2026-09-22"), score: 56.0 },
    ];
    // Extend both step lines to today.
    const toToday = (points) => [...points, { ...points.at(-1), date: today }];
    return Plot.plot({
      width,
      height: Math.min(420, Math.max(320, width * 0.6)),
      marginRight: 16,
      style: STYLE,
      x: { type: "utc", domain: [day("2025-12-01"), day("2026-10-08")], label: null },
      y: { domain: [0, 60], label: "Intelligence Index", labelArrow: "none", grid: true },
      color: { legend: true, domain: series, range: [COLORS.closed, COLORS.paid, COLORS.local] },
      marks: [
        Plot.line(toToday(frontier), { x: "date", y: "score", curve: "step-after", stroke: () => series[0], strokeWidth: 2.5 }),
        Plot.line(toToday(qwen), { x: "date", y: "score", curve: "step-after", stroke: () => series[2], strokeWidth: 2.5 }),
        Plot.dot(qwen, { x: "date", y: "score", fill: () => series[2], r: 4 }),
        Plot.arrow([{ from: goTo[0], to: qwen[2] }], {
          x1: (d) => d.from.date,
          y1: (d) => d.from.score,
          x2: (d) => d.to.date,
          y2: (d) => d.to.score,
          bend: 10,
          inset: 8,
          stroke: "currentColor",
          strokeOpacity: 0.6,
        }),
        Plot.text([narrow ? "6 months later" : "Six months later, on my 3090s"], {
          x: narrow ? day("2026-06-10") : day("2026-05-10"),
          y: 31,
          lineAnchor: "top",
          dy: 4,
          fontStyle: "italic",
        }),
        Plot.dot(goTo, { x: "date", y: "score", fill: () => series[1], r: 6, stroke: "var(--plot-background)" }),
        Plot.text(goTo.slice(0, 1), { x: "date", y: "score", text: "model", textAnchor: "start", lineAnchor: "top", dx: 4, dy: 8 }),
        Plot.text(goTo.slice(1, 2), { x: "date", y: "score", text: "model", textAnchor: "start", dx: 10 }),
        Plot.text(goTo.slice(2, 3), { x: "date", y: "score", text: "model", textAnchor: "end", dx: -10 }),
        Plot.text(goTo.slice(3), { x: "date", y: "score", text: "model", textAnchor: "end", lineAnchor: "bottom", dx: -4, dy: -8 }),
        Plot.tip(
          [...frontier.map((d) => ({ ...d, series: series[0] })), ...qwen.map((d) => ({ ...d, series: series[2] }))],
          Plot.pointer({ x: "date", y: "score", title: (d) => `${d.model}\n${d.series}\nScore ${d.score}` })
        ),
      ],
    });
  },

  peakLoad: ({ Plot, width }) => {
    // Illustrative: share of the busiest hour of the year, per hour of a typical workday.
    const workday = { 8: 0.2, 9: 0.5, 10: 0.9, 11: 1.0, 12: 0.5, 13: 0.7, 14: 0.9, 15: 1.0, 16: 0.8, 17: 0.5, 18: 0.2 };
    const peak = 30;
    const typical = 0.75;
    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const data = Array.from({ length: 7 * 24 }, (_, i) => {
      const day = Math.floor(i / 24);
      const share = day < 5 ? (workday[i % 24] ?? 0) * typical : 0.03;
      return { hour: i, agents: share * peak };
    });
    const used = data.reduce((sum, d) => sum + d.agents, 0) / (peak * data.length);
    return Plot.plot({
      width,
      height: Math.min(360, Math.max(260, width * 0.45)),
      style: STYLE,
      x: { domain: [0, 168], ticks: days.map((_, i) => i * 24 + 12), tickFormat: (h) => days[Math.floor(h / 24)], tickSize: 0, label: null },
      y: { domain: [0, 36], label: "Concurrent coding agents", labelArrow: "none", grid: true },
      marks: [
        Plot.ruleY([peak], { stroke: COLORS.open, strokeWidth: 2, strokeDasharray: "6 4" }),
        Plot.text([width < 600 ? `Hardware you have to buy: ${peak} agents` : `Hardware you have to buy: ${peak} agents at the busiest hour of the year`], {
          x: 0,
          y: peak,
          textAnchor: "start",
          dy: -9,
          fill: COLORS.open,
        }),
        Plot.areaY(data, { x: "hour", y: "agents", curve: "step-after", fill: COLORS.closed, fillOpacity: 0.3 }),
        Plot.lineY(data, { x: "hour", y: "agents", curve: "step-after", stroke: COLORS.closed }),
        Plot.text([`${width < 600 ? "Used" : "Used on a typical week"}: ${Math.round(used * 100)}%`], {
          x: 168,
          y: 5,
          textAnchor: "end",
          fontWeight: "bold",
        }),
      ],
    });
  },

  priceDrop: ({ Plot, width }) => {
    const groups = ["Closed model", "Open model"];
    // `place` puts each label where it does not collide with the others, also on narrow screens.
    const data = [
      { model: "Claude Opus 4.6", date: new Date("2026-02-05"), price: 25, group: groups[0], place: "right" },
      { model: "DeepSeek V4 Pro", date: new Date("2026-04-24"), price: 0.87, group: groups[1], place: "below" },
      { model: "GPT-5.6 Luna", date: new Date("2026-07-09"), price: 1.2, group: groups[0], place: "above" },
      { model: "GPT-6 Luna", date: new Date("2026-09-22"), price: 0.5, group: groups[0], place: "below-left" },
    ];
    const label = (d) => `${d.model}\n$${d.price.toFixed(2)}`;
    const placements = {
      right: { textAnchor: "start", dx: 10 },
      above: { lineAnchor: "bottom", dy: -10 },
      below: { lineAnchor: "top", dy: 10 },
      "below-left": { textAnchor: "end", lineAnchor: "top", dy: 8 },
    };
    return Plot.plot({
      width,
      height: Math.min(400, Math.max(300, width * 0.55)),
      marginRight: 20,
      style: STYLE,
      x: { type: "utc", domain: [new Date("2026-01-01"), new Date("2026-10-15")], label: null },
      y: { type: "log", domain: [0.25, 40], ticks: [0.5, 1, 2, 5, 10, 20], tickFormat: (d) => `$${d}`, label: "Output price (USD per million tokens, log scale)", labelArrow: "none", grid: true },
      color: { legend: true, domain: groups, range: [COLORS.closed, COLORS.open] },
      marks: [
        Plot.line(
          data.filter((d) => d.group === groups[0]),
          { x: "date", y: "price", stroke: COLORS.closed, strokeDasharray: "4 3", strokeOpacity: 0.6 }
        ),
        Plot.dot(data, { x: "date", y: "price", fill: "group", r: 6 }),
        ...Object.entries(placements).map(([place, options]) =>
          Plot.text(data.filter((d) => d.place === place), { x: "date", y: "price", text: label, ...options })
        ),
      ],
    });
  },
};
