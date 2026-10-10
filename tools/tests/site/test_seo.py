"""The <head> that search engines and social cards read: title, description, canonical, OpenGraph and Twitter tags,
JSON-LD, icons and analytics."""

import json
import re
import struct
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from helpers import TOOLS, require_hugo
from parity.build import build_site, resolve_hugo
from parity.site import Build

ORIGIN = "https://www.nijho.lt"
CONTENT = TOOLS.parent / "content"
GA = "https://www.googletagmanager.com/gtag/js?id=G-B50P3BHJ6C"
PLAUSIBLE = "https://plausible.nijho.lt/js/pa-ylHri3AS4w8PLULPjHH4G.js"
THEME_COLORS = {("(prefers-color-scheme: light)", "#f5f5f4"), ("(prefers-color-scheme: dark)", "#141413")}


def front_matter(index: Path) -> dict:
    return yaml.safe_load(index.read_text(encoding="utf-8").split("---", 2)[1])


def bundle_url(index: Path) -> str:
    """The URL path of content/.../<dir>/index.md, honouring a `slug:` in its front matter."""
    path = index.parent.relative_to(CONTENT)
    if slug := front_matter(index).get("slug"):
        path = path.with_name(slug)
    return f"/{path.as_posix()}/"


def bundles(pattern: str) -> list[Path]:
    return sorted(CONTENT.glob(f"{pattern}/index.md"))


def meta(head, key: str) -> str | None:
    tag = head.find("meta", attrs={"name": key}) or head.find("meta", property=key)
    return tag["content"] if tag else None


def jsonld(head) -> list[dict]:
    return [json.loads(script.string) for script in head.find_all("script", type="application/ld+json")]


def local_file(site: Build, url: str) -> Path:
    return site.root / url.removeprefix(ORIGIN).lstrip("/")


def image_size(file: Path) -> tuple[int, int]:
    """Width and height of a PNG or baseline/progressive JPEG."""
    data = file.read_bytes()
    if data.startswith(b"\x89PNG"):
        return struct.unpack(">II", data[16:24])
    i = 2
    while data[i] == 0xFF:
        marker, length = data[i + 1], struct.unpack(">H", data[i + 2 : i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height, width = struct.unpack(">HH", data[i + 5 : i + 9])
            return width, height
        i += 2 + length
    raise ValueError(f"{file}: no PNG header or JPEG frame")


PAGES = {
    "home": "/index.html",
    "post": bundle_url(bundles("post/*")[0]) + "index.html",
    "advent day": bundle_url(bundles("post/*/*")[0]) + "index.html",
    "project": bundle_url(bundles("project/*")[0]) + "index.html",
    "publication": bundle_url(bundles("publication/*")[0]) + "index.html",
    "section": "/post/index.html",
    "taxonomy": "/tags/index.html",
    "term": "/tag/ai/index.html",
    "author": "/authors/admin/index.html",
    "page": "/phd-defense/index.html",
    "404": "/404.html",
}


@pytest.fixture(scope="module")
def dev_site(repo_root, tmp_path_factory) -> Build:
    """The working tree built for the development environment."""
    hugo = require_hugo(resolve_hugo(), "0.167.0", "HUGO_BIN")
    return Build(build_site(repo_root, tmp_path_factory.mktemp("dev") / "public", production=False, hugo=hugo))


def test_seo_parity_clean(failures):
    assert failures("seo") == []


def test_canonical_absolute(site):
    for path in site.pages:
        head = site.soup(path).head
        canonical = [link["href"] for link in head.find_all("link", rel="canonical")]
        assert len(canonical) == 1 and canonical[0].startswith(ORIGIN + "/"), path
        assert meta(head, "og:url") in (None, canonical[0]), path


def test_description_has_no_markdown_link_syntax(site):
    offenders = []
    for path in site.pages:
        head = site.soup(path).head
        description = meta(head, "description")
        assert meta(head, "og:description") == description, path
        if description and "](" in description:
            offenders.append(path)
    assert offenders == []


def test_head_extras_on_every_kind(site):
    for kind, path in PAGES.items():
        head = site.soup(path).head
        canonical = head.find("link", rel="canonical")["href"]
        assert meta(head, "author") == "Bas Nijholt", kind
        assert meta(head, "og:locale") == "en_US", kind
        assert meta(head, "og:site_name") == "Bas Nijholt", kind
        assert not head.find("meta", property=re.compile("^twitter:")), kind
        twitter = {m["name"]: m["content"] for m in head.find_all("meta", attrs={"name": re.compile("^twitter:")})}
        assert twitter.keys() == {"twitter:card", "twitter:site", "twitter:creator", "twitter:image"}, kind
        assert twitter["twitter:site"] == twitter["twitter:creator"] == "@basnijholt", kind
        assert twitter["twitter:image"] == meta(head, "og:image"), kind
        colors = {(m["media"], m["content"]) for m in head.find_all("meta", attrs={"name": "theme-color"})}
        assert colors == THEME_COLORS, kind
        hreflang = head.find_all("link", hreflang=True)
        assert [(link["hreflang"], link["href"]) for link in hreflang] == [("en-us", canonical)], kind
        assert [link["href"] for link in head.find_all("link", rel="me")] == ["https://fosstodon.org/@basnijholt"], kind
        assert head.find("link", rel="manifest")["href"] == "/manifest.webmanifest", kind


def test_icons(site):
    head = site.soup("/index.html").head
    icons = {(" ".join(link["rel"]), link["sizes"]): link["href"] for link in head.find_all("link", sizes=True)}
    assert icons.pop(("icon", "32x32 48x48")) == "/favicon.ico"
    assert {key: image_size(local_file(site, href)) for key, href in icons.items()} == {
        ("icon", "32x32"): (32, 32),
        ("icon", "192x192"): (192, 192),
        ("apple-touch-icon", "180x180"): (180, 180),
    }
    ico = (site.root / "favicon.ico").read_bytes()
    reserved, kind, count = struct.unpack("<HHH", ico[:6])
    assert (reserved, kind) == (0, 1)
    assert sorted(ico[6 + 16 * i] for i in range(count)) == [32, 48]


def test_og_image_gif_featured_is_original(site):
    index = next(CONTENT.glob("post/*/featured.gif")).with_name("index.md")
    head = site.soup(bundle_url(index) + "index.html").head
    assert meta(head, "og:image") == ORIGIN + bundle_url(index) + "featured.gif"
    assert meta(head, "twitter:card") == "summary_large_image"


def test_og_image_fallback_icon_512_summary(site):
    index = next(i for i in bundles("post/*") if not list(i.parent.glob("*featured*")))
    head = site.soup(bundle_url(index) + "index.html").head
    image = meta(head, "og:image")
    assert re.fullmatch(rf"{ORIGIN}/media/icon_hu_[0-9a-f]+\.png", image)
    assert image_size(local_file(site, image)) == (512, 512)
    assert meta(head, "twitter:card") == "summary"


def test_preview_only_still_in_og_image(site):
    index = next(i for i in bundles("post/*") if (front_matter(i).get("image") or {}).get("preview_only"))
    featured = next(index.parent.glob("featured.*"))
    head = site.soup(bundle_url(index) + "index.html").head
    assert meta(head, "og:image") == ORIGIN + bundle_url(index) + featured.name
    assert meta(head, "twitter:card") == "summary_large_image"


def test_author_page_og_image_is_avatar_270(site):
    head = site.soup("/authors/admin/index.html").head
    image = meta(head, "og:image")
    assert re.fullmatch(rf"{ORIGIN}/authors/admin/avatar_hu_[0-9a-f]+\.jpg", image)
    assert image_size(local_file(site, image)) == (270, 270)
    assert meta(head, "twitter:card") == "summary"


def test_section_updated_time_is_newest_post(site):
    published = [
        meta(site.soup(path).head, "article:published_time")
        for path in site.pages
        if re.fullmatch(r"/post/.+/index\.html", path)
    ]
    newest = max(datetime.fromisoformat(time) for time in published if time)
    updated = meta(site.soup("/post/index.html").head, "og:updated_time")
    assert datetime.fromisoformat(updated) == newest


def test_jsonld_types_per_kind(site):
    types = {kind: [obj["@type"] for obj in jsonld(site.soup(path).head)] for kind, path in PAGES.items()}
    assert types == {
        "home": ["WebSite", "Person"],
        "post": ["BlogPosting", "BreadcrumbList"],
        "advent day": ["BlogPosting", "BreadcrumbList"],
        "project": ["Article"],
        "publication": ["ScholarlyArticle"],
        "section": [],
        "taxonomy": [],
        "term": [],
        "author": [],
        "page": [],
        "404": [],
    }

    website, person = jsonld(site.soup("/index.html").head)
    assert website["url"] == ORIGIN + "/"
    assert website["potentialAction"] == {
        "@type": "SearchAction",
        "target": ORIGIN + "/?q={search_term_string}",
        "query-input": "required name=search_term_string",
    }
    assert person["name"] == "Bas Nijholt" and person["url"] == ORIGIN + "/"
    assert person["jobTitle"] == "Senior Staff Engineer"
    assert person["image"] == meta(site.soup("/authors/admin/index.html").head, "og:image")
    assert "https://github.com/basnijholt" in person["sameAs"]
    assert all(url.startswith("https://") for url in person["sameAs"])

    for kind in ("post", "project", "publication"):
        head = site.soup(PAGES[kind]).head
        article = jsonld(head)[0]
        assert article["mainEntityOfPage"] == {"@type": "WebPage", "@id": head.find("link", rel="canonical")["href"]}
        assert article["headline"] + " | Bas Nijholt" == head.title.string
        assert article["description"] == meta(head, "description")
        assert datetime.fromisoformat(article["datePublished"]) == datetime.fromisoformat(
            meta(head, "article:published_time")
        )
        assert datetime.fromisoformat(article["dateModified"]) == datetime.fromisoformat(
            meta(head, "article:modified_time")
        )
        assert article["author"]["@type"] == "Person" and article["author"]["name"]
        logo = article["publisher"].pop("logo")
        assert article["publisher"] == {"@type": "Organization", "name": "Bas Nijholt"}
        assert logo["@type"] == "ImageObject" and image_size(local_file(site, logo["url"])) == (192, 192)

    day = PAGES["advent day"]
    crumbs = jsonld(site.soup(day).head)[1]["itemListElement"]
    assert [(c["position"], c["item"]) for c in crumbs] == [
        (1, ORIGIN + "/"),
        (2, ORIGIN + "/post/"),
        (3, ORIGIN + "/post/advent-of-open-source/"),
        (4, ORIGIN + day.removesuffix("index.html")),
    ]
    assert all(c["@type"] == "ListItem" and c["name"] for c in crumbs)


def test_analytics_only_in_production(site, dev_site):
    for path in PAGES.values():
        html = (site.root / path.lstrip("/")).read_text(encoding="utf-8")
        assert GA in html and PLAUSIBLE in html, path
        assert meta(site.soup(path).head, "robots") is None, path
    for path in dev_site.pages:
        html = (dev_site.root / path.lstrip("/")).read_text(encoding="utf-8")
        assert "googletagmanager.com" not in html and "plausible.nijho.lt" not in html, path
        assert meta(dev_site.soup(path).head, "robots") == "noindex", path
