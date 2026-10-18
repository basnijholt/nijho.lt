// Charts for this post, rendered by layouts/_shortcodes/plot.html with Observable Plot.
// Lines of code counted with tokei, comments and blank lines included: Linux 7.3-rc7 (fs, net, mm and kernel for the
// host kernel; arch/x86/kvm and virt/kvm for KVM) and gVisor at commit 9e94959 (pkg/sentry and pkg/tcpip, without
// _test.go files).

const STYLE = { fontSize: "13px", fontFamily: "system-ui, sans-serif", background: "transparent" };

// Centered axis labels below the tick labels, so they never collide with them.
const X_LABEL = { labelAnchor: "center", labelArrow: "none", labelOffset: 42 };

const LANGUAGES = ["Written in C", "Written in Go"];

const SURFACE = [
  { setup: "Plain Docker: the host kernel", language: LANGUAGES[0], lines: 3_766_187, label: "3.8 million lines" },
  { setup: "gVisor: its own kernel", language: LANGUAGES[1], lines: 218_066 + 92_032, label: "310,000 lines" },
  { setup: "Kata Containers: KVM", language: LANGUAGES[0], lines: 113_720, label: "114,000 lines" },
];

export default {
  attackSurface: ({ Plot, width }) => {
    // Each row: its name above the bar, and the count inside a long bar or after a short one.
    const inside = (d) => d.lines > 2_000_000;
    return Plot.plot({
      width,
      height: 72 * SURFACE.length + 90,
      marginLeft: 8,
      marginRight: 16,
      marginBottom: 52,
      style: STYLE,
      x: {
        domain: [0, 4_000_000],
        label: "Lines of code",
        grid: true,
        ticks: 4,
        tickFormat: (d) => (d ? `${d / 1_000_000}M` : "0"),
        ...X_LABEL,
      },
      y: { axis: null, domain: SURFACE.map((d) => d.setup), paddingInner: 0.1 },
      color: { domain: LANGUAGES, range: ["#ff725c", "#4269d0"], legend: true },
      marks: [
        Plot.barX(SURFACE, { y: "setup", x: "lines", fill: "language", insetTop: 30, insetBottom: 6 }),
        Plot.text(SURFACE, { y: "setup", x: 0, text: "setup", textAnchor: "start", fontWeight: "bold", dy: -14 }),
        Plot.text(SURFACE.filter(inside), { y: "setup", x: "lines", text: "label", textAnchor: "end", dx: -8, dy: 12, fill: "white" }),
        Plot.text(SURFACE.filter((d) => !inside(d)), { y: "setup", x: "lines", text: "label", textAnchor: "start", dx: 6, dy: 12 }),
        Plot.tip(
          SURFACE,
          Plot.pointer({ y: "setup", x: (d) => d.lines / 2, title: (d) => `${d.setup}\n${d.lines.toLocaleString("en-US")} lines` })
        ),
      ],
    });
  },
};
