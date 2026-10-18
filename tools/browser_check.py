# /// script
# requires-python = ">=3.12"
# dependencies = ["axe-playwright-python==0.1.8", "playwright==1.63.0"]
# ///
"""Check a build of the site in Chromium: behaviour, accessibility, page weight and rendering without JavaScript.

    uv run tools/browser_check.py [BUILD_DIR] [--screenshots OUT_DIR [--no-checks]]

Without BUILD_DIR it builds the working tree with $HUGO_BIN first. $CHROMIUM overrides the Chromium binary; empty
means Playwright's own (.github/workflows/check.yml installs it). Analytics requests are blocked, so checks count no
visits. Every check runs, and the script exits non-zero when any of them fails. --screenshots also writes the review
screenshot set (key pages, light and dark, 1440 and 390 px wide) to OUT_DIR; with --no-checks it only does that.
The checks run in parallel, each in its own Chromium.
"""

import argparse
import functools
import gzip
import http.server
import os
import re
import subprocess
import sys
import tempfile
import threading
from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Browser, Page, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
CHROMIUM = os.environ.get("CHROMIUM", "/run/current-system/sw/bin/chromium") or None
POST = "/post/self-hosting-ai-is-not-cheaper/"
# A long post without charts, diagrams, GIFs or videos, for the page-weight budget.
PLAIN_POST = "/post/agentic-coding/"
# Site configuration and the comments, not the theme; the budget leaves them out.
ANALYTICS = re.compile(r"googletagmanager\.com|google-analytics\.com|plausible\.nijho\.lt")
UNBUDGETED = ("giscus.app",)
KEY_PAGES = [
    "/",
    POST,
    "/post/",
    "/project/",
    "/publication/",
    "/publication/quasi_majoranas/",
    "/tag/ai/",
    "/authors/admin/",
    "/404.html",
]
SCREENSHOTS = {
    "home": "/",
    "blog": "/post/",
    "post": POST,
    "project": "/project/agent-cli/",
    "publication": "/publication/majorana-fusion/",
    "author": "/authors/admin/",
    "tag": "/tag/nixos/",
    "404": "/404.html",
    "search": "/?q=zfs",
}
DARK_BACKGROUND = "rgb(20, 20, 19)"
VISIBLE_CARDS = "[...document.querySelectorAll('#projects article.proj')].filter(c => c.getClientRects().length)"

CHECKS: list[tuple[Callable[..., None], tuple]] = []


def check(function: Callable[..., None] | None = None, *, cases: Iterable[tuple] = ((),)) -> Callable[..., None]:
    """Register a check once per case, a tuple of arguments after (browser, base). Each case runs on its own, so a
    slow check split into cases finishes sooner."""

    def register(function: Callable[..., None]) -> Callable[..., None]:
        CHECKS.extend((function, case) for case in cases)
        return function

    return register(function) if function else register


def build(out: Path) -> Path:
    """Build the working tree for production into out; a fresh resource cache keeps image names as Netlify has them."""
    with tempfile.TemporaryDirectory(prefix="hugo-resources-") as resources:
        env = os.environ | {"HUGO_ENV": "production", "HUGO_RESOURCEDIR": resources}
        hugo = os.environ.get("HUGO_BIN", "hugo")
        subprocess.run([hugo, "--gc", "--minify", "-s", str(ROOT), "-d", str(out)], env=env, check=True)
    return out


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(root: Path) -> str:
    """Serve root on a free local port in a background thread and return its base URL."""
    handler = functools.partial(QuietHandler, directory=str(root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_port}"


@contextmanager
def page(browser: Browser, base: str, path: str = "/", on: dict | None = None, **options) -> Iterator[Page]:
    """Open path in a fresh browser context (1440 px wide unless options say otherwise) and close it afterwards.
    on maps page events to handlers, attached before the page loads."""
    options.setdefault("viewport", {"width": 1440, "height": 900})
    context = browser.new_context(base_url=base, **options)
    context.route(ANALYTICS, lambda route: route.abort())
    try:
        new = context.new_page()
        for event, handler in (on or {}).items():
            new.on(event, handler)
        new.goto(path, wait_until="networkidle")
        yield new
    finally:
        context.close()


def settle(p: Page) -> None:
    """Wait until a smooth scroll has stopped: the scroll position is the same in three readings 150 ms apart."""
    readings = []
    while len(readings) < 3 or len(set(readings[-3:])) > 1:
        p.wait_for_timeout(150)
        readings.append(p.evaluate("scrollY"))
        if len(readings) > 60:
            raise AssertionError("the page kept scrolling for 9 s")


def contrast(a: str, b: str) -> float:
    """The WCAG contrast ratio of two rgb(...) colors."""

    def luminance(color: str) -> float:
        channels = [int(x) / 255 for x in re.findall(r"\d+", color)[:3]]
        r, g, b = (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


@check
def theme_choice_survives_navigation(browser, base):
    with page(browser, base, color_scheme="light") as p:
        p.click('button[popovertarget="theme-menu"]')
        p.click('[data-theme-choice="dark"]')
        p.goto("/post/", wait_until="networkidle")
        assert p.evaluate("document.documentElement.dataset.theme") == "dark"
        assert p.evaluate("getComputedStyle(document.body).backgroundColor") == DARK_BACKGROUND


@check
def slash_opens_search_and_finds_a_post(browser, base):
    with page(browser, base, "/project/") as p:
        p.keyboard.press("/")
        p.keyboard.type("zfs")
        p.wait_for_selector("#search-results a")
        hrefs = p.eval_on_selector_all("#search-results a", "links => links.map(a => a.getAttribute('href'))")
        assert any(h.startswith("/post/") for h in hrefs), hrefs


@check
def project_filter_and_search(browser, base):
    with page(browser, base) as p:
        total = p.evaluate("document.querySelectorAll('#projects article.proj').length")
        button = p.locator('#projects button[data-filter="homelab"]')
        expected = int(button.locator(".n").text_content())
        button.click()
        assert p.evaluate(f"{VISIBLE_CARDS}.length") == expected
        p.click('#projects button[data-filter="*"]')
        p.fill("#projects [data-filter-search]", "adaptive")
        titles = p.evaluate(f"{VISIBLE_CARDS}.map(c => c.querySelector('h3').textContent)")
        assert "Adaptive Lighting" in titles and len(titles) < total, titles


@check
def no_errors_in_the_console(browser, base):
    errors = []
    for path in KEY_PAGES:

        def own_error(message, path=path):
            if message.type == "error" and message.location.get("url", "").startswith(base):
                errors.append(f"{path}: {message.text}")

        handlers = {"pageerror": lambda error, path=path: errors.append(f"{path}: {error}"), "console": own_error}
        with page(browser, base, path, on=handlers):
            pass
    assert errors == [], errors


@check(cases=[("light",), ("dark",)])
def axe_finds_nothing_serious(browser, base, scheme):
    axe = Axe()
    found = []
    for path in KEY_PAGES:
        with page(browser, base, path, color_scheme=scheme) as p:
            for violation in axe.run(p).response["violations"]:
                if violation["impact"] in ("serious", "critical"):
                    targets = [node["target"] for node in violation["nodes"]][:3]
                    found.append(f"{scheme} {path}: {violation['id']} ({violation['impact']}) {targets}")
    assert found == [], "\n".join(found)


@check
def chart_tips_are_readable_in_both_schemes(browser, base):
    """A chart's hover tip fills its box with --plot-background behind text in the chart's color, so the two must
    contrast in either scheme. A probe rect stands in for the tip, which Plot draws only under the pointer."""
    for scheme in ("light", "dark"):
        with page(browser, base, POST, color_scheme=scheme) as p:
            chart = p.locator(".plot-container svg[class^=plot-]").first
            chart.wait_for()
            box, text = chart.evaluate("""svg => {
                const probe = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                probe.setAttribute("fill", "var(--plot-background)");
                svg.append(probe);
                const colors = [getComputedStyle(probe).fill, getComputedStyle(svg).color];
                probe.remove();
                return colors;
            }""")
            assert contrast(box, text) >= 4.5, f"{scheme}: tip text {text} on {box}"


@check
def plain_post_stays_light(browser, base):
    """A plain post loads under 300 KB in under 20 requests, not counting the comments (analytics are blocked).
    The local server sends files uncompressed, so each response counts at its gzip size, as Netlify serves text."""
    responses = []
    with page(browser, base, PLAIN_POST, on={"response": lambda response: responses.append(response)}):
        sizes = {}
        for response in responses:
            if not any(host in response.url for host in UNBUDGETED):
                body = response.body()
                sizes[response.url] = min(len(body), len(gzip.compress(body)))
    print(f"    {PLAIN_POST}: {len(sizes)} requests, {sum(sizes.values()):,} bytes compressed")
    assert len(sizes) < 20 and sum(sizes.values()) < 300_000, sizes


@check
def works_without_javascript(browser, base):
    with page(browser, base, java_script_enabled=False, color_scheme="dark") as p:
        visible, total = p.evaluate(
            f"[{VISIBLE_CARDS}.length, document.querySelectorAll('#projects article.proj').length]"
        )
        assert total and visible == total, (visible, total)
        assert not p.evaluate("document.querySelector('[data-filter-toolbar]').getClientRects().length")
        assert not p.evaluate("[...document.querySelectorAll('.needs-js')].some(e => e.getClientRects().length)")
        assert p.evaluate("getComputedStyle(document.body).backgroundColor") == DARK_BACKGROUND
        p.click('#site-menu a[href="/#publications"]')
        assert p.url.endswith("/#publications")
        p.goto("/post/")
        p.click("ul.w1 > li .blog-title a >> nth=0")
        assert "/post/" in p.url and p.url != f"{base}/post/"


@check(cases=[(width, start) for width in (1440, 390) for start in ("/", POST)])
def menu_links_land_on_their_sections(browser, base, width, start):
    """Each menu link, followed from the homepage and from a post, shows its section's heading near the top, below
    the sticky header."""
    off = []
    with page(browser, base, start, viewport={"width": width, "height": 900}) as p:
        for href in p.eval_on_selector_all("#site-menu a", "links => links.map(a => a.getAttribute('href'))"):
            p.goto(start, wait_until="networkidle")
            if width < 920:
                p.click(".menu-btn")
            p.click(f'#site-menu a[href="{href}"]')
            p.wait_for_url(f"**{href}")
            settle(p)
            top = p.eval_on_selector(f"{href[1:]} :is(h1, h2)", "h => h.getBoundingClientRect().top")
            bottom = p.eval_on_selector(".site-header", "h => h.getBoundingClientRect().bottom")
            # The last section cannot rise further once the page is scrolled to its end, and the first one starts at
            # the header with the avatar above its heading on small screens.
            at_end = p.evaluate("innerHeight + scrollY >= document.documentElement.scrollHeight - 2")
            at_start = p.evaluate("scrollY") == 0
            if not (top >= bottom and (top - bottom <= 160 or at_end or at_start)):
                off.append(f"{width}px from {start}: {href} heading top {top:.0f}, header bottom {bottom:.0f}")
    assert off == [], off


@check
def keyboard_reaches_the_header(browser, base):
    """Tab from the top reaches the skip link, the brand, every menu link, search and the theme menu, in that order,
    each with a visible focus ring."""
    with page(browser, base) as p:
        menu = p.eval_on_selector_all("#site-menu a", "links => links.map(a => a.textContent.trim())")
        expected = ["Skip to content", p.text_content(".site-header .brand").strip(), *menu, "Search", "Color theme"]
        reached = []
        for _ in expected:
            p.keyboard.press("Tab")
            reached.append(
                p.evaluate(
                    """() => {
                      const el = document.activeElement, style = getComputedStyle(el);
                      const ring = style.outlineStyle !== "none" && parseFloat(style.outlineWidth) > 0;
                      return [el.getAttribute("aria-label") || el.textContent.trim(), ring];
                    }"""
                )
            )
        assert [name for name, _ in reached] == expected, reached
        assert all(ring for _, ring in reached), reached


def screenshots(browser: Browser, base: str, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for scheme in ("light", "dark"):
        for width in (1440, 390):
            for name, path in SCREENSHOTS.items():
                options = {"color_scheme": scheme, "viewport": {"width": width, "height": 900}}
                with page(browser, base, path, **options) as p:
                    p.wait_for_timeout(500)
                    p.screenshot(path=out / f"{name}-{width}-{scheme}.png", full_page=name not in ("home", "search"))
    print(f"screenshots in {out}")


def run(function: Callable[..., None], case: tuple, base: str) -> str | None:
    """Run one case of a check in its own Chromium, as Playwright's sync API takes one instance per thread, and return
    the error it raised, if any."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=CHROMIUM)
        try:
            function(browser, base, *case)
        except Exception as error:  # noqa: BLE001 - one broken check must not hide the others
            return f"{type(error).__name__}: {error}"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("build", nargs="?", type=Path, help="a built site (default: build the working tree)")
    parser.add_argument("--screenshots", type=Path, metavar="OUT_DIR", help="also write the screenshot set here")
    parser.add_argument("--no-checks", action="store_true", help="only write the screenshots")
    args = parser.parse_args()
    checks = [] if args.no_checks else CHECKS
    failed = 0
    with tempfile.TemporaryDirectory(prefix="browser-check-") as tmp:
        base = serve(args.build or build(Path(tmp) / "public"))
        with ThreadPoolExecutor() as pool:
            errors = pool.map(lambda check: run(*check, base), checks)
            for (function, case), error in zip(checks, errors):
                name = function.__name__ + (f"[{', '.join(map(str, case))}]" if case else "")
                failed += error is not None
                print(f"FAIL {name}: {error}" if error else f"ok   {name}")
        if args.screenshots:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path=CHROMIUM)
                screenshots(browser, base, args.screenshots)
                browser.close()
    if checks:
        print(f"{len(checks) - failed} of {len(checks)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
