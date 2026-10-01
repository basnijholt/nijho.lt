"""Generate the MindRoom x IonQ animation and its preview images.

Run from this directory: `python make_images.py`
Writes entangled-cores.html (the animation inlined by the bleed-svg shortcode),
featured.png (wide, for social previews), and thumbnail.png (vertical, for post lists).
The PNGs are frozen frames of the animation, rendered with headless Chromium.
"""

import math
import re
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).parent

# Both marks are isometric hexagons: this is the MindRoom cube's core in mindroom-mark.svg coordinates.
HEX_M = "512,265 666,361 666,546 512,643 358,546 358,361"
DEFS = f"""<defs>
<mask id="outside"><rect x="0" y="0" width="2000" height="2000" fill="white"/><polygon points="{HEX_M}" fill="black"/></mask>
<clipPath id="hex"><polygon points="{HEX_M}"/></clipPath>
<radialGradient id="gold"><stop offset="0" stop-color="#fff6c8" stop-opacity="1"/><stop offset=".45" stop-color="#ffd86b" stop-opacity=".55"/><stop offset="1" stop-color="#ffb000" stop-opacity="0"/></radialGradient>
<radialGradient id="orange"><stop offset="0" stop-color="#fff1e0" stop-opacity="1"/><stop offset=".45" stop-color="#F58220" stop-opacity=".55"/><stop offset="1" stop-color="#F05323" stop-opacity="0"/></radialGradient>
<filter id="blur6"><feGaussianBlur stdDeviation="6"/></filter>
</defs>"""
FRAME = '<image href="mindroom-mark.svg" x="152" y="112" width="720" height="720" mask="url(#outside)"/>'
CORE = '<image href="mindroom-mark.svg" x="152" y="112" width="720" height="720" clip-path="url(#hex)"/>'
# The wordmark gets a class so the page CSS can switch its color between light and dark mode.
IONQ = re.search(r"<svg[^>]*>(.*)</svg>", (HERE / "ionq-logo.svg").read_text(), re.S).group(1)
IONQ = IONQ.replace('fill="#0d1b2a"', 'class="bleed-ink"')
TITLE = "Entanglement: a shared wave function collapses and both cores light up at once"

# The wave: N points from the M core edge to the Q edge, one keyframe per entry in `keys` (fractions of a 5 s loop).
X0, X1, Y = 830, 1195, 454
N = 120
DUR = 5.0


def path(ys):
    pts = [(X0 + (X1 - X0) * i / (N - 1), Y - y) for i, y in enumerate(ys)]
    return "M " + " L ".join(f"{x:.0f},{y:.0f}" for x, y in pts)


def area(ys):  # |psi|^2 cloud, symmetric around the axis
    top = [(X0 + (X1 - X0) * i / (N - 1), Y - y) for i, y in enumerate(ys)]
    bot = [(x, 2 * Y - y) for x, y in reversed(top)]
    return "M " + " L ".join(f"{x:.0f},{y:.0f}" for x, y in top + bot) + " Z"


frames_psi, frames_prob, keys, glow, flash = [], [], [], [], []


def add(t, env, phase, amp, g=0.15, fl=0.0):
    xs = [i / (N - 1) for i in range(N)]
    frames_psi.append([amp * env(u) * math.sin(2 * math.pi * (5 * u) - phase) for u in xs])
    frames_prob.append([amp * 0.9 * env(u) ** 2 for u in xs])
    keys.append(t)
    glow.append(g)
    flash.append(fl)


spread = lambda u: math.sin(math.pi * u) ** 0.8
# Superposition, 0..0.62: phase advancing, slight breathing, glow flickering with the wave.
steps = 48
for s in range(steps + 1):
    t = 0.62 * s / steps
    ph = 2 * math.pi * 3 * t / 0.62
    add(t, spread, ph, 60 * (0.9 + 0.1 * math.sin(2 * math.pi * 2 * t / 0.62)), g=0.22 + 0.28 * (0.5 + 0.5 * math.sin(ph)))
# Collapse, 0.62..0.68: the envelope narrows into both ends and spikes.
for s in range(1, 7):
    t = 0.62 + 0.06 * s / 6
    f = s / 6
    w = 0.5 * (1 - f) + 0.02 * f
    env = lambda u, w=w: math.exp(-((u) / w) ** 2) + math.exp(-((1 - u) / w) ** 2)
    add(t, env, 2 * math.pi * 3 + f * 3, 1.5 * (60 * (1 - f) + 90 * f * (1 - f) * 4 * 0.25), g=0.3 + 0.7 * f, fl=0.35 * f)
# Gone: both cores flash.
add(0.70, lambda u: 0, 0, 0, g=1.0, fl=1.0)
# Regrow from both ends, 0.72..1.0.
for s in range(1, 9):
    t = 0.72 + 0.28 * s / 8
    f = s / 8
    env = lambda u, f=f: spread(u) * min(1, (min(u, 1 - u)) / (0.5 * f + 1e-6))
    add(t, env, 2 * math.pi * 3 * f, 60 * f, g=max(0.15, 1 - 1.6 * f), fl=max(0, 1 - 2.2 * f))
frames_psi[-1], frames_prob[-1], glow[-1], flash[-1] = frames_psi[0], frames_prob[0], glow[0], flash[0]

# Alternate direction: rotate the loop to start at the collapse (amplitude 0), then play the same
# forward-time loop mirrored in space (Q to M). The switch happens while the wave is gone.
gi = keys.index(0.70)
n = len(keys) - 1  # the last frame duplicates frame 0
idx = list(range(gi, n)) + list(range(0, gi + 1))
rk = [(keys[i] - keys[gi]) % 1.0 for i in idx]
rk[-1] = 1.0
rot = lambda a: [a[i] for i in idx]
P, Pr, G, F = rot(frames_psi), rot(frames_prob), rot(glow), rot(flash)
keys2 = [k / 2 for k in rk] + [0.5 + k / 2 for k in rk[1:]]
frames_psi = [path(f) for f in P + [list(reversed(f)) for f in P[1:]]]
frames_prob = [area(f) for f in Pr + [list(reversed(f)) for f in Pr[1:]]]
glow, flash = G + G[1:], F + F[1:]
DUR *= 2
kt = ";".join(f"{k:.4f}" for k in keys2[:-1]) + ";1"


def anim(attr, vals):
    return f'<animate attributeName="{attr}" dur="{DUR}s" repeatCount="indefinite" calcMode="linear" keyTimes="{kt}" values="{";".join(vals)}"/>'


QC_X, QC_Y = 1200 + 104.5 * 1.3, 300 + 120.7 * 1.3  # center of the Q


def wave(wave_at=""):
    """The wave's gradient and its two animated paths: the |psi|^2 cloud and the wave itself."""
    return f"""
<linearGradient id="wg" x1="{X0}" x2="{X1}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#ffd86b"/><stop offset="1" stop-color="#F58220"/></linearGradient>
<path d="{frames_prob[0]}" fill="url(#wg)" opacity=".18"{wave_at}>{anim("d", frames_prob)}</path>
<path d="{frames_psi[0]}" fill="none" stroke="url(#wg)" stroke-width="3.5" stroke-linecap="round"{wave_at}>{anim("d", frames_psi)}</path>"""


def build(tall=False, logos_only=False):
    """The wide layout puts the Q right of the M; the tall one stacks M, wave, Q, and wordmark.

    With logos_only, the SVG has only the logos, for pages that draw the wave and glow with wave_overlay() and glow_overlay().
    """
    ionq, ionq_at, wave_at, q_at = IONQ, "", "", ""
    if tall:
        # Move the Q under the M, wave vertical from the cube's bottom tip to the Q's top tip, wordmark under the Q.
        q_at = "translate(-863.9,750)"
        ionq_at = q_at + " "
        wave_at = ' transform="translate(-540.5,392.5) rotate(90,1012.5,454) translate(1012.5,454) scale(1.115,1) translate(-1012.5,-454)"'
        letters = "".join(re.findall(r'<path d="[^"]*" class="bleed-ink"/>\n', ionq))
        ionq = ionq.replace(letters, f'<g transform="translate(-374.5,224)">{letters}</g>\n').replace(' clip-path="url(#clip0_13003_138)"', "")
    q_glow = f' transform="{q_at}"' if q_at else ""
    gold = 'cx="472" cy="454" rx="210" ry="250" fill="url(#gold)"'
    orange = f'cx="{QC_X:.1f}" cy="{QC_Y:.1f}" rx="170" ry="190" fill="url(#orange)"'
    logos = f"""{DEFS}
<g transform="translate(-40,0)">{FRAME}{CORE}</g>
<g transform="{ionq_at}translate(1200,300) scale(1.3)">{ionq}</g>"""
    if logos_only:
        return logos
    return logos + wave(wave_at) + f"""
<g style="mix-blend-mode:screen">
<ellipse {gold}>{anim("opacity", [f"{g:.3f}" for g in glow])}</ellipse>
<ellipse{q_glow} {orange}>{anim("opacity", [f"{g:.3f}" for g in glow])}</ellipse>
<ellipse {gold}>{anim("opacity", [f"{v:.3f}" for v in flash])}{anim("rx", [f"{210 + 390 * v:.0f}" for v in flash])}{anim("ry", [f"{250 + 410 * v:.0f}" for v in flash])}</ellipse>
<ellipse{q_glow} {orange}>{anim("opacity", [f"{v:.3f}" for v in flash])}{anim("rx", [f"{170 + 330 * v:.0f}" for v in flash])}{anim("ry", [f"{190 + 350 * v:.0f}" for v in flash])}</ellipse>
</g>"""


def svg(body, attrs):
    return f'<svg {attrs}xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"{body[0]}><title>{TITLE}</title>{body[1]}</svg>'


def place(viewbox, x, y, w, h):
    """CSS that positions an overlay over the region (x, y, w, h) of an SVG with this viewBox."""
    x0, y0, vw, vh = viewbox
    return f"left:{(x - x0) / vw * 100:.3f}%;top:{(y - y0) / vh * 100:.3f}%;width:{w / vw * 100:.3f}%;height:{h / vh * 100:.3f}%"


def wave_overlay(viewbox):
    """The wave in its own small SVG, positioned over the logos.

    In the same SVG as the masked logos, every frame of the wave made Chromium on macOS repaint the logos too,
    which made the animation stutter. In its own layer, only the wave repaints.
    """
    region = (790, 290, 450, 330)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{" ".join(map(str, region))}" aria-hidden="true" '
            f'style="position:absolute;{place(viewbox, *region)};overflow:visible;will-change:transform">{wave()}</svg>')


def glow_overlay(viewbox):
    """The same four glows as HTML elements with CSS animations, positioned over an SVG with this viewBox.

    Animating the glows inside the SVG made the browser repaint these large blended gradients on every frame,
    which made the wave stutter and scrolling slow. Opacity and transform animations on HTML elements run on the GPU.
    """

    def box(cx, cy, rx, ry):
        return place(viewbox, cx - rx, cy - ry, 2 * rx, 2 * ry)

    def keyframes(name, values):
        return f"@keyframes {name}{{" + "".join(f"{k * 100:.2f}%{{{v}}}" for k, v in zip(keys2, values)) + "}"

    # The flash glows are sized at their largest and scaled down, matching the rx/ry animation in build().
    css = "".join([
        f".ec-glow{{position:absolute;border-radius:50%;mix-blend-mode:screen;will-change:transform,opacity;animation:{DUR}s linear infinite}}",
        ".ec-gold{background:radial-gradient(closest-side,#fff6c8,rgba(255,216,107,.55) 45%,rgba(255,176,0,0))}",
        ".ec-orange{background:radial-gradient(closest-side,#fff1e0,rgba(245,130,32,.55) 45%,rgba(240,83,35,0))}",
        keyframes("ec-glow", [f"opacity:{g:.3f}" for g in glow]),
        keyframes("ec-flash-m", [f"opacity:{v:.3f};transform:scale({(210 + 390 * v) / 600:.4f},{(250 + 410 * v) / 660:.4f})" for v in flash]),
        keyframes("ec-flash-q", [f"opacity:{v:.3f};transform:scale({(170 + 330 * v) / 500:.4f},{(190 + 350 * v) / 540:.4f})" for v in flash]),
    ])
    divs = "".join(
        f'<div class="ec-glow {cls}" style="{box(cx, cy, rx, ry)};animation-name:{name}"></div>'
        for cls, cx, cy, rx, ry, name in [
            ("ec-gold", 472, 454, 210, 250, "ec-glow"),
            ("ec-orange", QC_X, QC_Y, 170, 190, "ec-glow"),
            ("ec-gold", 472, 454, 600, 660, "ec-flash-m"),
            ("ec-orange", QC_X, QC_Y, 500, 540, "ec-flash-q"),
        ]
    )
    return f"<style>{css}</style>{divs}"


def render(body, viewbox, size, t, out):
    """Freeze the animation at t seconds and screenshot it at 2x on the dark background."""
    w, h = size
    page = f"""<html><body style="margin:0;background:#0b1622"><style>.bleed-ink{{fill:#e8eef4}}</style>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" width="{w}" height="{h}">{body}</svg>
<script>onload=()=>{{const s=document.querySelector("svg");s.pauseAnimations();s.setCurrentTime({t})}}</script></body></html>"""
    with tempfile.NamedTemporaryFile("w", suffix=".html", dir=HERE, delete=False) as f:
        f.write(page)
    try:
        subprocess.run(
            ["chromium", "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
             "--force-device-scale-factor=2", f"--window-size={w},{h}", "--virtual-time-budget=3000",
             f"--screenshot={(HERE / out).resolve()}", Path(f.name).resolve().as_uri()],
            check=True, capture_output=True, timeout=60,
        )
    finally:
        Path(f.name).unlink()


# The page bleeds the glow past the text column, so the viewBox is padded to match the negative margins
# in assets/scss/custom.scss (.svg-bleed-stage).
PAGE_VIEWBOX = (-338, -338, 2900, 1620)
page_svg = svg((f' viewBox="{" ".join(map(str, PAGE_VIEWBOX))}"', build(logos_only=True)), "")
(HERE / "entangled-cores.html").write_text(page_svg + wave_overlay(PAGE_VIEWBOX) + glow_overlay(PAGE_VIEWBOX) + "\n")
render(build(), "70 -70 2084 1091", (1200, 628), 4.8, "featured.png")
render(build(tall=True), "42 90 860 1530", (430, 765), 4.5, "thumbnail.png")
print("wrote entangled-cores.html, featured.png, thumbnail.png")
