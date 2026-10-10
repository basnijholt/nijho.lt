"""The post page: breadcrumb, byline, featured image, contents rail, end matter, comments and scripts."""

import gzip
import re
from datetime import datetime
from urllib.parse import quote

from helpers import CONTENT, page_url
from parity.site import read_utf8

POST = "/post/self-hosting-ai-is-not-cheaper/index.html"
URL = "https://www.nijho.lt/post/self-hosting-ai-is-not-cheaper/"


def posts_with(pattern: str, *, featured: bool = False) -> list[str]:
    """Pages of the posts whose index.md matches pattern, and that have a featured.* image if featured is set."""
    return sorted(
        page_url(file) + "index.html"
        for file in (CONTENT / "post").rglob("index.md")
        if re.search(pattern, file.read_text(encoding="utf-8"), re.MULTILINE)
        and (not featured or any(file.parent.glob("featured.*")))
    )


def post_pages(site) -> list[str]:
    return [p for p in site.pages if p.startswith("/post/") and p != "/post/index.html" and "/page/" not in p]


def test_breadcrumb(site):
    crumbs = site.soup(POST).select('nav[aria-label="Breadcrumb"] li')
    assert [(li.get_text(strip=True), li.a["href"] if li.a else None) for li in crumbs] == [
        ("Home", "/"),
        ("Posts", "/post/"),
        ("Self-hosting AI does not save money, and I do it anyway", None),
    ]
    assert crumbs[-1].select_one('[aria-current="page"]')
    day = "/post/advent-of-open-source/01-calendar-of-life/index.html"
    hrefs = [a["href"] for a in site.soup(day).select('nav[aria-label="Breadcrumb"] a')]
    assert hrefs == ["/", "/post/", "/post/advent-of-open-source/"]


def test_byline(site):
    soup = site.soup(POST)
    assert soup.select_one("h1").get_text(strip=True) == "Self-hosting AI does not save money, and I do it anyway"
    assert soup.select_one(".subtitle").get_text(strip=True).startswith("I run open-weight models")
    byline = soup.select_one(".byline")
    assert byline.select_one('a.who[href="/authors/admin/"] img')
    assert byline.select_one('time.published[datetime="2026-10-02"]').get_text(strip=True) == "Oct 2, 2026"
    assert re.search(r"\b\d+ min read\b", byline.get_text(" ", strip=True))
    assert [a["href"] for a in byline.select("a.chip")] == [
        "/category/ai/",
        "/category/homelab/",
        "/category/levelintermediate/",
    ]


def test_last_updated_only_when_different(site):
    checked = 0
    for page in post_pages(site):
        soup = site.soup(page)
        published = soup.select_one('meta[property="article:published_time"]')
        if not published:
            continue
        modified = soup.select_one('meta[property="article:modified_time"]')["content"][:10]
        updated = soup.select_one(".byline time.updated")
        if modified == published["content"][:10]:
            assert updated is None, page
        else:
            assert updated["datetime"] == modified, page
            assert updated.get_text(strip=True) == datetime.fromisoformat(modified).strftime("%b %-d, %Y")
        checked += 1
    assert checked > 60


def test_featured_image(site):
    previews = posts_with(r"^\s+preview_only: true")
    assert previews and all(not site.soup(p).select("figure.featured") for p in previews)
    wide = [p for p in posts_with(r"^\s+placement: 2", featured=True) if p not in previews]
    assert wide and all(site.soup(p).select_one("figure.featured.featured-wide img") for p in wide)
    gif = site.soup("/post/dotbins/index.html").select_one("figure.featured img")
    assert gif["src"] == "/post/dotbins/featured.gif"
    assert [f for f in site.files if re.search(r"_hu.*\.gif$", f)] == []


def test_contents_rail_lists_the_headings(site):
    soup = site.soup(POST)
    headings = [h["id"] for h in soup.select(".prose h2[id], .prose h3[id]")]
    assert [a["href"] for a in soup.select(".rail nav a")] == [f"#{i}" for i in headings]


def test_end_matter(site):
    soup = site.soup(POST)
    assert [a["href"] for a in soup.select(".post-end .tags a.chip")] == [
        "/tag/ai/", "/tag/local-ai/", "/tag/self-hosting/", "/tag/hardware/", "/tag/model-reviews/",
    ]
    share = [a["href"] for a in soup.select(".share a")]
    encoded = quote(URL, safe="")
    assert len(share) == 4 and all(encoded in href for href in share)
    assert soup.select_one(".share button[data-copy]")["data-copy"] == URL
    assert soup.select_one("a.edit")["href"] == (
        "https://github.com/basnijholt/nijho.lt/edit/main/content/post/self-hosting-ai-is-not-cheaper/index.md"
    )
    card = soup.select_one(".author-card")
    assert card.select_one("h3").get_text(strip=True) == "Bas Nijholt"
    assert len(card.select(".social a")) >= 6
    related = soup.select(".related > li a")
    assert 1 <= len(related) <= 5 and all(site.resolves(a["href"]) for a in related)


def test_chip_links_resolve(site):
    hrefs = {a["href"] for page in post_pages(site) for a in site.soup(page).select("a.chip")}
    assert hrefs and [h for h in sorted(hrefs) if not site.resolves(h)] == []


def test_comments_only_where_commentable(site):
    comments = site.soup(POST).select_one("#comments[data-giscus-repo]")
    assert comments["data-giscus-repo"] == "basnijholt/nijho.lt"
    assert comments["data-giscus-mapping"] == "pathname"
    for page in ("/phd-defense/index.html", "/project/agent-cli/index.html"):
        assert not site.soup(page).select("#comments"), page


def test_post_scripts_stay_small(site):
    scripts = [s["src"] for s in site.soup(POST).select('script[src^="/js/"]')]
    assert len(scripts) >= 3
    size = sum(len(gzip.compress((site.root / src[1:]).read_bytes())) for src in scripts)
    assert size < 15_000, size
    assert not site.soup("/phd-defense/index.html").select('script[src*="/js/toc."]')
