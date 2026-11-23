// Monthly lines-touched chart for "How I develop right now", rendered by layouts/_shortcodes/plot.html with Observable Plot.
// Data from trueloc run on 2026-11-20 (merged PRs plus direct commits, per-commit mode).

const STYLE = { fontSize: "13px", fontFamily: "system-ui, sans-serif", background: "transparent" };

const MONTHS = [
  { month: "2024-11", added: 21497, deleted: 11283, prs: 56 },
  { month: "2024-12", added: 70418, deleted: 12091, prs: 119 },
  { month: "2025-01", added: 44918, deleted: 16227, prs: 169 },
  { month: "2025-02", added: 19010, deleted: 5804, prs: 56 },
  { month: "2025-03", added: 56669, deleted: 23146, prs: 127 },
  { month: "2025-04", added: 29604, deleted: 9353, prs: 67 },
  { month: "2025-05", added: 17189, deleted: 5375, prs: 52 },
  { month: "2025-06", added: 52283, deleted: 18831, prs: 93 },
  { month: "2025-07", added: 130903, deleted: 79168, prs: 53 },
  { month: "2025-08", added: 220780, deleted: 105164, prs: 17 },
  { month: "2025-09", added: 138738, deleted: 72385, prs: 11 },
  { month: "2025-10", added: 150731, deleted: 68607, prs: 28 },
  { month: "2025-11", added: 586230, deleted: 202455, prs: 104 },
  { month: "2025-12", added: 141706, deleted: 55315, prs: 262 },
  { month: "2026-01", added: 155097, deleted: 107530, prs: 341 },
  { month: "2026-02", added: 220063, deleted: 80020, prs: 348 },
  { month: "2026-03", added: 198562, deleted: 94237, prs: 180 },
  { month: "2026-04", added: 465428, deleted: 221209, prs: 358 },
  { month: "2026-05", added: 258376, deleted: 139996, prs: 412 },
  { month: "2026-06", added: 206076, deleted: 75910, prs: 346 },
  { month: "2026-07", added: 516761, deleted: 269908, prs: 577 },
  { month: "2026-08", added: 412945, deleted: 261129, prs: 175 },
  { month: "2026-09", added: 1670024, deleted: 789009, prs: 728 },
  { month: "2026-10", added: 1780362, deleted: 1049347, prs: 1317 },
  { month: "2026-11", added: 3322160, deleted: 644475, prs: 1634, partial: true },
].map((d) => ({ ...d, total: d.added + d.deleted }));

const STACKED = MONTHS.flatMap((d) => [
  { month: d.month, kind: "Added", y1: 0, y2: d.added, partial: Boolean(d.partial) },
  { month: d.month, kind: "Deleted", y1: d.added, y2: d.total, partial: Boolean(d.partial) },
]);

const fmt = (n) => n.toLocaleString("en-US");
const TICKS = ["2024-11", "2025-01", "2025-07", "2026-01", "2026-07", "2026-11"];

export default {
  linesPerMonth: ({ Plot, width }) => {
    const narrow = width < 560;
    return Plot.plot({
      width,
      height: Math.min(400, Math.max(290, Math.round(width * 0.48))),
      marginLeft: 52,
      marginRight: narrow ? 16 : 24,
      marginTop: 28,
      marginBottom: 46,
      style: STYLE,
      x: {
        domain: MONTHS.map((d) => d.month),
        ticks: narrow ? ["2024-11", "2025-07", "2026-01", "2026-11"] : TICKS,
        label: null,
        padding: 0.18,
      },
      y: {
        domain: [0, 4_250_000],
        grid: true,
        label: "Lines touched per month",
        labelArrow: "none",
        tickFormat: (d) => (d === 0 ? "0" : `${d / 1_000_000}M`),
      },
      color: {
        domain: ["Added", "Deleted"],
        range: ["#3ca951", "#ff725c"],
        legend: true,
      },
      marks: [
        Plot.barY(STACKED, {
          x: "month",
          y1: "y1",
          y2: "y2",
          fill: "kind",
          fillOpacity: (d) => (d.partial ? 0.62 : 0.95),
          rx: 2,
        }),
        Plot.text(
          MONTHS.filter((d) => d.partial),
          {
            x: "month",
            y: "total",
            text: () => "Nov 1 to 20",
            dy: -9,
            textAnchor: "end",
            dx: 6,
            fontSize: 11,
            fill: "currentColor",
            fillOpacity: 0.78,
          }
        ),
        Plot.ruleY([0]),
        Plot.tip(
          MONTHS,
          Plot.pointerX({
            x: "month",
            y: "total",
            title: (d) =>
              `${d.month}${d.partial ? " (Nov 1 to 20)" : ""}\n${fmt(d.total)} lines touched\n+${fmt(d.added)} added / -${fmt(d.deleted)} deleted\n${fmt(d.prs)} merged PRs`,
          })
        ),
      ],
    });
  },
};
