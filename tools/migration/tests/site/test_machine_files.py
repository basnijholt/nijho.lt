"""Files for machines: RSS feeds, robots.txt, the web manifest, Netlify headers and redirects, and the search index."""

import json
import struct
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
import yaml

from helpers import CONTENT, page_url, require_hugo
from parity.build import build_site, resolve_hugo
from parity.site import Build

ORIGIN = "https://www.nijho.lt"
INDEX_KEYS = {
    "objectID", "date", "publishdate", "lastmod", "expirydate", "lang", "permalink", "relpermalink", "title",
    "summary", "content", "authors", "kind", "type", "section", "tags", "categories",
}


def channel(build: Build, path: str) -> ET.Element:
    return ET.parse(build.root / path.lstrip("/")).getroot().find("channel")


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


def test_old_images_parity_clean(failures):
    assert failures("old-images") == []


ALIASES = {
    "/post/old/": "/post/old/",
    "/post/no-slash": "/post/no-slash/",
    "/project/rsync-time-machine.py": "/project/rsync-time-machine.py/",
    "/project/nijho.lt/": "/project/nijho.lt/",
    "/page.html": "/page.html",
}


@pytest.fixture(scope="module")
def alias_redirects(repo_root, tmp_path_factory) -> dict[str, str]:
    """The _redirects rules (source -> target) of a small site with layouts/home.redirects and ALIASES on one page."""
    hugo = require_hugo(resolve_hugo(), "0.167.0", "HUGO_BIN")
    root = tmp_path_factory.mktemp("aliases")
    config = yaml.safe_load((repo_root / "config/_default/hugo.yaml").read_text(encoding="utf-8"))
    site_config = {key: config[key] for key in ("outputFormats", "mediaTypes", "disableAliases")}
    site_config |= {"baseURL": ORIGIN + "/", "outputs": {"home": ["html", "redirects"]}}
    (root / "hugo.yaml").write_text(yaml.safe_dump(site_config), encoding="utf-8")
    (root / "layouts").mkdir()
    (root / "layouts/home.redirects").write_text((repo_root / "layouts/home.redirects").read_text(encoding="utf-8"))
    for name in ("home.html", "page.html"):
        (root / "layouts" / name).write_text("{{ .Title }}", encoding="utf-8")
    (root / "content/post/p").mkdir(parents=True)
    (root / "content/post/p/index.md").write_text(f"---\ntitle: P\naliases: {list(ALIASES)}\n---\n")
    rules = Build(build_site(root, root / "public", production=False, hugo=hugo)).redirects
    return {rule.source: rule.target for rule in rules}


@pytest.mark.parametrize(("alias", "source"), ALIASES.items())
def test_alias_redirect_sources(alias_redirects, alias, source):
    """An alias is a folder with a trailing slash unless it names an .html file, as Hugo writes alias pages."""
    assert alias_redirects[source] == "/post/p/"


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
