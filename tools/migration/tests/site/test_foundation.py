"""The CSS bundle, self-hosted fonts, theme script, header and footer that every page shares."""

import base64
import hashlib
import re
from datetime import date
from urllib.parse import quote

import yaml

from helpers import REPO

CONFIG = REPO / "config/_default"
MENU = [
    (item["name"], f"/{item['url']}")
    for item in sorted(yaml.safe_load((CONFIG / "menus.yaml").read_text(encoding="utf-8"))["main"], key=lambda i: i["weight"])
]
TITLE = yaml.safe_load((CONFIG / "hugo.yaml").read_text(encoding="utf-8"))["title"]
PARAMS = yaml.safe_load((CONFIG / "params.yaml").read_text(encoding="utf-8"))
LAYERS = "reset,tokens,base,layout,components,prose,syntax,home,pages,icons,shortcodes"


def sample_pages(site) -> list[str]:
    """The homepage, a post, a list page, a term page and the 404 page."""
    post = next(p for p in site.pages if re.fullmatch(r"/post/[^/]+/index\.html", p))
    return ["/index.html", post, "/post/index.html", "/tag/ai/index.html", "/404.html"]


def stylesheet(site):
    links = site.soup("/index.html").head.find_all("link", rel="stylesheet")
    assert len(links) == 1
    return links[0]


def rule_body(css: str, selector: str) -> str:
    """The text between the braces of the first `selector{` rule, nested rules included."""
    start = css.index(selector + "{") + len(selector) + 1
    depth = 1
    for i in range(start, len(css)):
        depth += {"{": 1, "}": -1}.get(css[i], 0)
        if depth == 0:
            return css[start:i]
    raise AssertionError(f"unbalanced braces after {selector}")


def test_css_bundle_fingerprinted_and_nested_rules_survive_minify(site):
    link = stylesheet(site)
    assert re.fullmatch(r"/css/main\.[0-9a-f]{64}\.css", link["href"])
    data = (site.root / link["href"].lstrip("/")).read_bytes()
    assert link["integrity"] == "sha256-" + base64.b64encode(hashlib.sha256(data).digest()).decode()
    assert link["crossorigin"] == "anonymous"
    css = data.decode()
    assert css.startswith(f"@layer {LAYERS};")
    assert "@layer layout{" in css
    header = rule_body(css, ".site-header")
    assert "{" in header and "&" in header, "no nested rule left inside .site-header"
    assert "ns-hugo" not in css and "/*" not in css


def test_no_google_fonts(site):
    offenders = [
        p for p in site.pages
        if re.search(r"fonts\.(googleapis|gstatic)\.com", (site.root / p.lstrip("/")).read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_fonts_preloaded(site):
    css = (site.root / stylesheet(site)["href"].lstrip("/")).read_text()
    fonts = set(re.findall(r"url\((/fonts/[^)]+\.woff2)\)", css))
    assert fonts == {
        "/fonts/bricolage-grotesque-latin.woff2",
        "/fonts/geist-latin.woff2",
        "/fonts/geist-italic-latin.woff2",
        "/fonts/geist-mono-latin.woff2",
    }
    assert fonts <= site.files
    for path in sample_pages(site):
        preloads = site.soup(path).head.select('link[rel="preload"][as="font"]')
        assert {p["href"] for p in preloads} == {"/fonts/geist-latin.woff2", "/fonts/bricolage-grotesque-latin.woff2"}
        assert all(p["type"] == "font/woff2" and p.has_attr("crossorigin") for p in preloads)


def test_theme_init_inline_script_before_css(site):
    for path in sample_pages(site):
        head = site.soup(path).head
        tags = [t for t in head.find_all(["script", "link"]) if t.name == "script" or "stylesheet" in t.get("rel", [])]
        first = tags[0]
        assert first.name == "script" and not first.has_attr("src"), f"{path}: CSS comes before the theme script"
        script = first.string
        assert len(script.encode()) <= 400
        assert re.search(r"localStorage\.getItem\([\"']theme[\"']\)", script) and "dataset.theme" in script


def test_unusual_paths_exist(site, baseline):
    paths = [
        "/project/rsync-time-machine.py/index.html",
        "/project/nijho.lt/index.html",
        "/publication/phd_thesis/index.html",
        "/authors/andrey-e.-antipov/index.html",
    ]
    encoded = [p for p in baseline.pages if re.fullmatch(r"/authors/[^/]+/index\.html", p) and "%" in quote(p)]
    assert encoded, "the baseline has no author whose URL needs percent-encoding"
    assert [p for p in paths + encoded if p not in site.files] == []


def test_header_has_six_menu_links_and_skip_link(site):
    for path in sample_pages(site):
        body = site.soup(path).body
        skip = body.find("a")
        assert skip["href"] == "#main" and "skip-link" in skip["class"]
        assert body.find("main", id="main")
        links = body.select("header.site-header nav .nav-links a")
        assert [(a.get_text(strip=True), a["href"]) for a in links] == MENU, path


def test_theme_and_mobile_menus_are_popovers(site):
    header = site.soup("/index.html").find("header", class_="site-header")
    menus = {b["popovertarget"]: header.find(id=b["popovertarget"]) for b in header.select("button[popovertarget]")}
    assert all(menu.has_attr("popover") for menu in menus.values())
    assert "nav-links" in menus["site-menu"]["class"]
    assert [b["data-theme-choice"] for b in menus["theme-menu"].find_all("button")] == ["light", "dark", "auto"]


def test_footer_copyright_rss_and_back_to_top(site):
    for path in sample_pages(site):
        footer = site.soup(path).find("footer", class_="site-footer")
        text = " ".join(footer.get_text().split())
        assert f"© {date.today().year} {TITLE}. Source code on GitHub and builds on Netlify." in text
        hrefs = {a.get_text(strip=True): a["href"] for a in footer.find_all("a")}
        assert hrefs["GitHub"] == PARAMS["features"]["repository"]["url"]
        assert hrefs["Netlify"] == PARAMS["features"]["deploys"]
        assert hrefs["RSS"] == "/index.xml"
        assert hrefs["Back to top"] == "#top"
