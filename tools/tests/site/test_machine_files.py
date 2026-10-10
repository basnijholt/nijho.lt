"""Files for machines: RSS feeds, robots.txt, the web manifest, Netlify headers and redirects, and the search index."""

import json
import struct
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
import yaml

from helpers import TOOLS
from parity.site import Build

ORIGIN = "https://www.nijho.lt"
CONTENT = TOOLS.parent / "content"
INDEX_KEYS = {
    "objectID", "date", "publishdate", "lastmod", "expirydate", "lang", "permalink", "relpermalink", "title",
    "summary", "content", "authors", "kind", "type", "section", "tags", "categories",
}


def channel(build: Build, path: str) -> ET.Element:
    return ET.parse(build.root / path.lstrip("/")).getroot().find("channel")


def page_url(file: Path) -> str:
    """The URL path of a content page: its bundle directory or file name, or the `slug:` in its front matter."""
    path = file.parent if file.name == "index.md" else file.with_suffix("")
    text = file.read_text(encoding="utf-8")
    front_matter = yaml.safe_load(text.split("---", 2)[1]) if text.startswith("---") else {}
    if slug := front_matter.get("slug"):
        path = path.with_name(slug)
    return f"/{path.relative_to(CONTENT).as_posix()}/"


def headers(build: Build) -> dict[str, dict[str, str]]:
    """The rules of _headers: path -> {header name: value}."""
    rules, current = {}, None
    for line in (build.root / "_headers").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0].isspace():
            name, value = line.strip().split(":", 1)
            rules[current][name] = value.strip()
        else:
            current = line.strip()
            rules[current] = {}
    return rules


def png_size(file: Path) -> tuple[int, int]:
    return struct.unpack(">II", file.read_bytes()[16:24])


def test_feed_parity_clean(failures):
    assert failures("feeds") == []


def test_guid_relative_with_ispermalink_false(site):
    for path in site.feeds:
        for item in channel(site, path).iterfind("item"):
            guid = item.find("guid")
            assert guid.get("isPermaLink") == "false", path
            assert guid.text.startswith("/") and item.findtext("link") == ORIGIN + guid.text, path


def test_home_feed_has_every_regular_page(site):
    pages = [
        file for file in CONTENT.rglob("*.md")
        if file.name != "_index.md" and not file.is_relative_to(CONTENT / "home") and "authors" not in file.parts
    ]
    links = [item.findtext("link") for item in channel(site, "/index.xml").iterfind("item")]
    assert sorted(links) == sorted(ORIGIN + page_url(file) for file in pages)


def test_feed_channel(site):
    feed = channel(site, "/post/index.xml")
    assert feed.findtext("title") == "Posts | Bas Nijholt"
    assert feed.findtext("link") == ORIGIN + "/post/"
    assert feed.find("{http://www.w3.org/2005/Atom}link").get("href") == ORIGIN + "/post/index.xml"
    assert feed.findtext("description") == "Posts"
    assert feed.findtext("language") == "en-us"
    assert feed.findtext("copyright").startswith("© 20")
    assert feed.findtext("lastBuildDate")
    assert feed.findtext("image/url").startswith(ORIGIN + "/media/icon_hu_")
    item = feed.find("item")
    assert "<p>" in item.findtext("description")


def test_robots_sitemap_absolute(site):
    robots = (site.root / "robots.txt").read_text(encoding="utf-8")
    assert robots.splitlines() == ["User-agent: *", "", f"Sitemap: {ORIGIN}/sitemap.xml"]
    assert site.sitemap_locs and all(not loc.startswith("http") for loc in site.sitemap_locs)
    sitemap = (site.root / "sitemap.xml").read_text(encoding="utf-8")
    assert "<loc>/" not in sitemap and f"<loc>{ORIGIN}/" in sitemap


def test_headers_manifest_rule(site, baseline):
    rules = headers(site)
    assert rules["/*"] == headers(baseline)["/*"]
    assert len(rules["/*"]) == 6
    assert rules["/index.xml"] == {"Content-Type": "application/rss+xml"}
    assert rules["/manifest.webmanifest"] == {"Content-Type": "application/manifest+json"}


def test_manifest_icons_and_start_url(site):
    manifest = json.loads((site.root / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["name"] == manifest["short_name"] == "Bas Nijholt"
    assert manifest["display"] == "standalone"
    assert manifest["start_url"] == "/?utm_source=web_app_manifest"
    assert manifest["background_color"] == manifest["theme_color"] == "#f5f5f4"
    sizes = {icon["sizes"]: png_size(site.root / icon["src"].lstrip("/")) for icon in manifest["icons"]}
    assert sizes == {"192x192": (192, 192), "512x512": (512, 512)}


def test_index_json_schema_and_count(site, baseline):
    index = json.loads((site.root / "index.json").read_text(encoding="utf-8"))
    assert all(entry.keys() == INDEX_KEYS for entry in index)
    assert len(index) == len(json.loads((baseline.root / "index.json").read_text(encoding="utf-8")))
    author = next(entry for entry in index if entry["relpermalink"] == "/authors/admin/")
    assert author["permalink"] == ORIGIN + "/authors/admin/" and author["kind"] == "term"
    # truncate skips anything that looks like markup when it counts, so a cut text can run a little over 5000
    cut = [entry["content"] for entry in index if entry["content"].endswith("…")]
    assert cut and max(len(content) for content in cut) < 5500


def test_redirects_parity_clean(failures):
    assert failures("redirects") == []


def test_redirects_cover_day_nn_and_llamaswap(site):
    days = sorted(path for path in (CONTENT / "post/advent-of-open-source").iterdir() if path.is_dir())
    assert len(days) == 24
    expected = {f"/post/advent-of-open-source/day_{day.name[:2]}/": page_url(day / "index.md") for day in days}
    expected["/post/llamaswap/"] = "/post/llama-nixos/"
    for old, new in expected.items():
        rule, target = site.redirect(old)
        assert (target, rule.status, rule.force) == (new, 301, False), old
        assert site.final_target(old) == (new, True), old


def test_every_redirect_target_resolves(site):
    targets = {rule.target for rule in site.redirects if rule.target.startswith("/") and ":" not in rule.target}
    assert targets
    assert sorted(target for target in targets if not site.resolves(target)) == []


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("/tags/python/", "/tag/python/"),
        ("/tags/python/index.xml", "/tag/python/index.xml"),
        ("/categories/ai/", "/category/ai/"),
        ("/tags/page/2/", "/tags/"),
        ("/tag/python/page/2/", "/tag/python/"),
        ("/post/page/2/", "/post/"),
        ("/project/page/2/", "/project/"),
        ("/publication_types/2/", "/publication/"),
        ("/publication-type/7/", "/publication/"),
    ],
)
def test_old_url_schemes_redirect(site, old, new):
    assert site.final_target(old) == (new, True)


def test_netlify_subdomain_redirects_to_the_site(site):
    rule = next(rule for rule in site.redirects if rule.source.startswith("https://nijholt.netlify.app/"))
    assert (rule.source, rule.target, rule.status, rule.force) == (
        "https://nijholt.netlify.app/*", "https://www.nijho.lt/:splat", 301, True
    )
