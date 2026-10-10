# /// script
# requires-python = ">=3.12"
# dependencies = ["axe-playwright-python", "playwright"]
# ///
"""Check a build of the site in Chromium: behaviour, accessibility, page weight, no-JS rendering and the header.

    uv run tools/browser_check.py [BUILD_DIR] [--screenshots OUT_DIR [--no-checks]]

Without BUILD_DIR it builds the working tree with $HUGO_BIN first. $CHROMIUM overrides the Chromium binary. Every
check runs, and the script exits non-zero when any of them fails. --screenshots also writes the review screenshot
set (key pages, light and dark, 1440 and 390 px wide) to OUT_DIR; with --no-checks it only does that, for example
for a baseline build.
"""

import argparse
import os
import functools
import gzip
import http.server
import subprocess
import sys
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path

from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Browser, Page, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
CHROMIUM = os.environ.get("CHROMIUM", "/run/current-system/sw/bin/chromium")
POST = "/post/self-hosting-ai-is-not-cheaper/"
# A long post without charts, diagrams, GIFs or videos, for the page-weight budget.
PLAIN_POST = "/post/agentic-coding/"
# Site configuration and the comments, not the theme; the budget leaves them out.
UNBUDGETED = ("googletagmanager.com", "google-analytics.com", "plausible.nijho.lt", "giscus.app")
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

CHECKS: list[Callable[[Browser, str], None]] = []


def check(function: Callable[[Browser, str], None]) -> Callable[[Browser, str], None]:
    CHECKS.append(function)
    return function


def build(out: Path) -> Path:
    """Build the working tree for production into out. A fresh resource cache keeps image names as Netlify makes them."""
    with tempfile.TemporaryDirectory(prefix="hugo-resources-") as resources:
        env = os.environ | {"HUGO_ENV": "production", "HUGO_RESOURCEDIR": resources}
        hugo = os.environ.get("HUGO_BIN", "hugo")
        subprocess.run([hugo, "--gc", "--minify", "-s", str(ROOT), "-d", str(out)], env=env, check=True)
    return out


def serve(root: Path) -> str:
    """Serve root on a free local port in a background thread and return its base URL."""
    handler = functools.partial(QuietHandler, directory=str(root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_port}"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def page(browser: Browser, base: str, path: str = "/", **options) -> Page:
    options.setdefault("viewport", {"width": 1440, "height": 900})
    context = browser.new_context(base_url=base, **options)
    new = context.new_page()
    new.goto(path, wait_until="networkidle")
    return new


def settle(p: Page) -> None:
    """Wait until a smooth scroll has stopped: the scroll position is the same in three readings 150 ms apart."""
    readings = []
    while len(readings) < 3 or len(set(readings[-3:])) > 1:
        p.wait_for_timeout(150)
        readings.append(p.evaluate("scrollY"))
        if len(readings) > 60:
            raise AssertionError("the page kept scrolling for 9 s")


@check
def theme_toggle_persists_across_navigation(browser, base):
    p = page(browser, base, color_scheme="light")
    p.click('button[popovertarget="theme-menu"]')
    p.click('[data-theme-choice="dark"]')
    p.goto("/post/", wait_until="networkidle")
    assert p.evaluate("document.documentElement.dataset.theme") == "dark"
    assert p.evaluate("getComputedStyle(document.body).backgroundColor") == "rgb(20, 20, 19)"


@check
def search_slash_opens_and_finds_post(browser, base):
    p = page(browser, base, "/project/")
    p.keyboard.press("/")
    p.keyboard.type("zfs")
    p.wait_for_selector("#search-results a")
    assert p.evaluate("document.getElementById('search').open")
    hrefs = p.eval_on_selector_all("#search-results a", "links => links.map(a => a.getAttribute('href'))")
    assert any(h.startswith("/post/") for h in hrefs), hrefs


@check
def project_filter_and_search(browser, base):
    p = page(browser, base)
    shown = "[...document.querySelectorAll('#projects article.proj')].filter(c => c.getClientRects().length)"
    button = p.locator('#projects button[data-filter="homelab"]')
    expected = int(button.locator(".n").text_content())
    button.click()
    assert p.evaluate(f"{shown}.length") == expected
    p.click('#projects button[data-filter="*"]')
    p.fill("#projects [data-filter-search]", "adaptive")
    titles = p.evaluate(f"{shown}.map(c => c.querySelector('h3').textContent)")
    assert "Adaptive Lighting" in titles and len(titles) < 51, titles


@check
def no_console_errors_on_key_pages(browser, base):
    errors = []
    for path in KEY_PAGES:
        context = browser.new_context(base_url=base)
        p = context.new_page()
        p.on("pageerror", lambda error, path=path: errors.append(f"{path}: {error}"))
        p.on(
            "console",
            lambda message, path=path: errors.append(f"{path}: {message.text}")
            if message.type == "error" and message.location.get("url", "").startswith(base)
            else None,
        )
        p.goto(path, wait_until="networkidle")
        context.close()
    assert errors == [], errors


@check
def axe_no_serious_or_critical(browser, base):
    axe = Axe()
    found = []
    for scheme in ("light", "dark"):
        for path in KEY_PAGES:
            p = page(browser, base, path, color_scheme=scheme)
            for violation in axe.run(p).response["violations"]:
                if violation["impact"] in ("serious", "critical"):
                    targets = [node["target"] for node in violation["nodes"]][:3]
                    found.append(f"{scheme} {path}: {violation['id']} ({violation['impact']}) {targets}")
            p.context.close()
    assert found == [], "\n".join(found)


@check
def post_page_budget(browser, base):
    """A plain post loads under 300 KB in under 20 requests, not counting analytics and the comments. The local
    server sends files uncompressed, so each response counts at its gzip size, as Netlify serves text."""
    context = browser.new_context(viewport={"width": 1440, "height": 900}, base_url=base)
    p = context.new_page()
    responses = []
    p.on("response", lambda response: responses.append(response))
    p.goto(PLAIN_POST, wait_until="networkidle")
    sizes = {}
    for response in responses:
        if not any(host in response.url for host in UNBUDGETED):
            body = response.body()
            sizes[response.url] = min(len(body), len(gzip.compress(body)))
    print(f"    {PLAIN_POST}: {len(sizes)} requests, {sum(sizes.values()):,} bytes compressed")
    assert len(sizes) < 20 and sum(sizes.values()) < 300_000, sizes


@check
def no_js(browser, base):
    p = page(browser, base, java_script_enabled=False, color_scheme="dark")
    visible, total = p.evaluate(
        """() => {
          const cards = [...document.querySelectorAll('#projects article.proj')];
          return [cards.filter(c => c.getClientRects().length).length, cards.length];
        }"""
    )
    assert total and visible == total, (visible, total)
    assert not p.evaluate("document.querySelector('[data-filter-toolbar]').getClientRects().length")
    assert p.evaluate("getComputedStyle(document.body).backgroundColor") == "rgb(20, 20, 19)"
    p.click('#site-menu a[href="/#publications"]')
    assert p.url.endswith("/#publications")
    p.goto("/post/")
    p.click("ul.w1 > li .blog-title a >> nth=0")
    assert "/post/" in p.url and p.url != f"{base}/post/"


@check
def anchor_not_hidden_under_header(browser, base):
    p = page(browser, base, POST)
    heading = p.eval_on_selector(".prose h2[id]", "h => h.id")
    p.goto(f"{POST}#{heading}", wait_until="networkidle")
    p.wait_for_timeout(300)
    top = p.eval_on_selector(f"[id='{heading}']", "h => h.getBoundingClientRect().top")
    bottom = p.eval_on_selector(".site-header", "h => h.getBoundingClientRect().bottom")
    assert top >= bottom, (top, bottom)


@check
def menu_links_land_on_their_sections(browser, base):
    """Each menu link, followed from the homepage and from a post, shows its section's heading near the top, below
    the sticky header."""
    off = []
    for width in (1440, 390):
        for start in ("/", POST):
            p = page(browser, base, start, viewport={"width": width, "height": 900})
            for href in p.eval_on_selector_all("#site-menu a", "links => links.map(a => a.getAttribute('href'))"):
                p.goto(start, wait_until="networkidle")
                if width < 920:
                    p.click(".menu-btn")
                p.click(f'#site-menu a[href="{href}"]')
                p.wait_for_url(f"**{href}")
                settle(p)
                section = href.split("#")[1]
                top = p.eval_on_selector(f"#{section} :is(h1, h2)", "h => h.getBoundingClientRect().top")
                bottom = p.eval_on_selector(".site-header", "h => h.getBoundingClientRect().bottom")
                # The last section cannot rise further once the page is scrolled to its end, and the first one starts
                # at the header with the avatar above its heading on small screens.
                at_end = p.evaluate("innerHeight + scrollY >= document.documentElement.scrollHeight - 2")
                at_start = p.evaluate("scrollY") == 0
                if not (top >= bottom and (top - bottom <= 160 or at_end or at_start)):
                    off.append(f"{width}px from {start}: {href} heading top {top:.0f}, header bottom {bottom:.0f}")
            p.context.close()
    assert off == [], off


@check
def list_text_keeps_a_readable_measure(browser, base):
    p = page(browser, base, "/post/advent-of-open-source/")
    width = p.eval_on_selector(".list > .prose", "e => e.getBoundingClientRect().width")
    p.context.close()
    assert width <= 760, width


@check
def header_height_and_single_line_nav(browser, base):
    for width in (1024, 1440):
        p = page(browser, base, viewport={"width": width, "height": 900})
        assert p.eval_on_selector(".site-header", "h => h.offsetHeight") <= 72
        tops = p.eval_on_selector_all("#site-menu a", "links => links.map(a => a.offsetTop)")
        assert tops and len(set(tops)) == 1, (width, tops)
        p.context.close()


@check
def keyboard_reaches_nav_search_and_theme(browser, base):
    p = page(browser, base)
    menu = p.eval_on_selector_all("#site-menu a", "links => links.map(a => a.textContent.trim())")
    header = ["Skip to content", p.text_content(".site-header .brand").strip(), *menu]
    reached = []
    for _ in range(len(header) + 2):
        p.keyboard.press("Tab")
        reached.append(
            p.evaluate(
                """() => {
                  const el = document.activeElement, style = getComputedStyle(el);
                  const visible = style.outlineStyle !== "none" && parseFloat(style.outlineWidth) > 0;
                  return [el.className || el.tagName, el.getAttribute("aria-label") || el.textContent.trim(), visible];
                }"""
            )
        )
    names = [name for _, name, _ in reached]
    assert names[: len(header) + 2] == [*header, "Search", "Color theme"], names
    assert all(visible for _, _, visible in reached[: len(header) + 2]), reached


def screenshots(browser: Browser, base: str, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for scheme in ("light", "dark"):
        for width in (1440, 390):
            for name, path in SCREENSHOTS.items():
                p = page(browser, base, path, color_scheme=scheme, viewport={"width": width, "height": 900})
                p.wait_for_timeout(500)
                p.screenshot(path=out / f"{name}-{width}-{scheme}.png", full_page=name not in ("home", "search"))
                p.context.close()
    print(f"screenshots in {out}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("build", nargs="?", type=Path, help="a built site (default: build the working tree)")
    parser.add_argument("--screenshots", type=Path, metavar="OUT_DIR", help="also write the screenshot set here")
    parser.add_argument("--no-checks", action="store_true", help="only write the screenshots")
    args = parser.parse_args()
    checks = [] if args.no_checks else CHECKS
    with tempfile.TemporaryDirectory(prefix="browser-check-") as tmp:
        root = args.build or build(Path(tmp) / "public")
        base = serve(root)
        failed = 0
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=CHROMIUM)
            for function in checks:
                try:
                    function(browser, base)
                except Exception as error:  # noqa: BLE001 - one broken check must not hide the others
                    failed += 1
                    print(f"FAIL {function.__name__}: {type(error).__name__}: {error}")
                else:
                    print(f"ok   {function.__name__}")
            if args.screenshots:
                screenshots(browser, base, args.screenshots)
            browser.close()
    if checks:
        print(f"{len(checks) - failed} of {len(checks)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
