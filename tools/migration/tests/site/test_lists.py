"""Post lists, taxonomy and term pages, and author pages."""

import re

import yaml

from helpers import CONTENT
from parity.checks import broken_internal_links


def front_matter(file) -> dict:
    text = file.read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---")[1]) if text.startswith("---") else {}


def rows(site, page: str) -> list[str]:
    return [a["href"] for a in site.soup(page).select("ul.w1 > li .blog-title a")]


def test_post_list_has_every_top_level_post_and_the_advent_section(site):
    posts = [d for d in (CONTENT / "post").iterdir() if (d / "index.md").exists()]
    published = [d for d in posts if not front_matter(d / "index.md").get("draft")]
    hrefs = rows(site, "/post/index.html")
    assert len(hrefs) == len(published) + 1
    assert "/post/advent-of-open-source/" in hrefs


def test_post_row_shows_date_reading_time_categories_and_summary(site):
    row = site.soup("/post/index.html").select_one('ul.w1 > li:has(a[href="/post/self-hosting-ai-is-not-cheaper/"])')
    assert re.fullmatch(r"Oct 2, 2026 · \d+ min read", row.select_one(".post-meta").get_text(" ", strip=True))
    assert [a["href"] for a in row.select("a.chip")] == ["/category/ai/", "/category/homelab/", "/category/levelintermediate/"]
    assert row.select_one(".summary").get_text(strip=True).startswith("Whenever I say that self-hosting AI")


def test_post_row_thumbnail(site):
    with_thumb = [li for li in site.soup("/post/index.html").select("ul.w1 > li") if li.select_one("img.thumb")]
    assert with_thumb
    for li in with_thumb:
        img = li.select_one("img.thumb")
        assert img["src"] and img["loading"] == "lazy" and img["alt"] == ""


def test_advent_page_has_body_and_all_days(site):
    soup = site.soup("/post/advent-of-open-source/index.html")
    assert soup.select_one(".prose").get_text(strip=True)
    days = list((CONTENT / "post/advent-of-open-source").glob("*/index.md"))
    assert len(rows(site, "/post/advent-of-open-source/index.html")) == len(days) + 1  # plus the retrospective


def test_tag_page_lists_every_tagged_post(site):
    tagged = [f for f in CONTENT.rglob("*.md") if "ai" in [t.lower() for t in front_matter(f).get("tags") or []]]
    soup = site.soup("/tag/ai/index.html")
    assert soup.select_one("h1").get_text(strip=True) == "AI"
    assert len(rows(site, "/tag/ai/index.html")) == len(tagged)
    assert soup.select_one('a[href="/tag/ai/index.xml"]')


def test_taxonomy_lists_its_terms_with_counts(site):
    soup = site.soup("/tags/index.html")
    terms = {a["href"]: a for a in soup.select("ul.terms a")}
    assert "/tag/ai/" in terms
    assert re.search(r"\d+", terms["/tag/ai/"].get_text())


def test_author_pages(site):
    admin = site.soup("/authors/admin/index.html")
    assert admin.select_one("h1").get_text(strip=True) == "Bas Nijholt"
    assert len(admin.select("ul.w1 > li")) > 20
    coauthor = site.soup("/authors/anton-r.-akhmerov/index.html")
    assert coauthor.select("ul.w1 > li a[href^='/publication/']")
    for page in ("/authors/index.html", "/authors/page/2/index.html", "/authors/page/3/index.html"):
        assert site.soup(page).select("ul.terms a"), page


def test_retrospective_keeps_the_baseline_title(site, baseline):
    page = "/post/advent-of-open-source/retrospective/index.html"
    assert site.soup(page).title.string == baseline.soup(page).title.string


def test_no_broken_internal_links(site):
    assert broken_internal_links(site) == []


def test_publication_type_titles(site):
    taxonomy = site.soup("/publication_types/index.html")
    assert taxonomy.select_one("h1").get_text(strip=True) == "Publication types"
    assert taxonomy.title.string.startswith("Publication types |")
    term = site.soup("/publication-type/article-journal/index.html")
    assert term.select_one("h1").get_text(strip=True) == "Journal article"
    assert term.title.string.startswith("Journal article |")
    assert "Journal article" in [a.get_text(" ", strip=True).rsplit(" ", 1)[0] for a in taxonomy.select("ul.terms a")]


def test_untitled_page_row_uses_its_first_heading(site):
    row = site.soup("/post/advent-of-open-source/index.html").select_one(
        'ul.w1 > li:has(a[href="/post/advent-of-open-source/retrospective/"])'
    )
    assert row.select_one(".blog-title").get_text(strip=True) == "A Retrospective on Advent of Open Source"
    assert not row.select(".summary h1, .summary h2")
