"""Project and publication pages: the singles, the new /project/ index and the filterable /publication/ list."""

import yaml

from helpers import CONTENT


def front_matter(file) -> dict:
    text = file.read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---")[1]) if text.startswith("---") else {}


def published(section: str) -> dict[str, dict]:
    pages = {f.parent.name: front_matter(f) for f in (CONTENT / section).glob("*/index.md")}
    return {slug: fm for slug, fm in pages.items() if not fm.get("draft")}


def test_project_single_has_external_button(site):
    soup = site.soup("/project/agent-cli/index.html")
    assert soup.select_one("h1").get_text(strip=True) == "Agent CLI"
    assert soup.select_one('a.btn[href="https://github.com/basnijholt/agent-cli"]').get_text(strip=True) == (
        "Go to project site"
    )
    assert soup.select_one('.byline time[datetime="2025-06-25"]').get_text(strip=True) == "Jun 25, 2025"
    assert [a["href"] for a in soup.select(".post-end .tags a.chip")] == [
        "/tag/python/", "/tag/ai/", "/tag/llm/", "/tag/speech-to-text/",
    ]
    assert soup.select_one("figure.featured img")["src"].endswith(".webp")
    crumbs = [a["href"] for a in soup.select('nav[aria-label="Breadcrumb"] a')]
    assert crumbs == ["/", "/project/"]


def test_project_index_lists_all(site):
    soup = site.soup("/project/index.html")
    assert soup.select_one("h1").get_text(strip=True) == "Projects"
    cards = soup.select("article.proj")
    assert len(cards) == len(published("project"))
    order = [(int(c["data-stars"]), int(c["data-date"])) for c in cards]
    assert order == sorted(order, reverse=True)
    assert soup.select_one("[data-filter-root] [data-filter-toolbar] button[data-filter='python']")
    assert soup.select('script[src^="/js/filter."]')


def test_publication_authors_truncated_and_linked(site):
    soup = site.soup("/publication/majorana-fusion/index.html")
    authors = soup.select(".pub-authors a")
    assert len(authors) == 20
    assert authors[0]["href"] == "/authors/morteza-aghaee/"
    assert authors[5]["href"] == "/authors/andrey-e.-antipov/"
    assert all(site.resolves(a["href"]) for a in authors)
    assert soup.select_one(".pub-authors").get_text(" ", strip=True).endswith("and 142 more")
    assert soup.select_one(".byline").get_text(" ", strip=True).startswith("February 2025")
    assert soup.select_one(".abstract p").get_text().startswith("The fusion of non-Abelian anyons")
    facts = {dt.get_text(strip=True): dd for dt, dd in zip(soup.select(".pub-facts dt"), soup.select(".pub-facts dd"))}
    assert facts["Publication type"].a["href"] == "/publication-type/article-journal/"
    assert facts["Publication type"].get_text(strip=True) == "Journal article"
    assert facts["Publication"].get_text(" ", strip=True) == "In Nature ."
    assert [a.get_text(strip=True) for a in soup.select(".post-head .pub-links a")][:2] == ["PDF", "Code"]
    small = site.soup("/publication/zigzag/index.html")
    assert not small.select_one(".pub-authors").get_text().strip().endswith("more")
    assert small.select_one('.pub-authors a[href="/authors/bas-nijholt/"] strong')


def test_mathjax_only_on_math_pages(site):
    math = {slug for slug, fm in published("publication").items() if fm.get("math")}
    assert math == {"quasi_majoranas", "shortjunction"}
    for slug in published("publication"):
        soup = site.soup(f"/publication/{slug}/index.html")
        scripts = [s for s in soup.select("script[src]") if "mathjax" in s["src"]]
        assert bool(scripts) == (slug in math), slug
    soup = site.soup("/publication/quasi_majoranas/index.html")
    assert "$4\\pi$" in soup.select_one(".abstract").get_text()
    assert "inlineMath" in soup.select_one("script:not([src])#mathjax-config").get_text()


def test_publication_filters_present(site):
    soup = site.soup("/publication/index.html")
    items = soup.select("[data-filter-root] ol.pubs > li")
    assert len(items) == len(published("publication"))
    toolbar = soup.select_one("[data-filter-root] [data-filter-toolbar][hidden]")
    assert toolbar.select_one("input[type=search][data-filter-search]")
    types = toolbar.select_one('select[data-filter-key="type"]')
    assert [o["value"] for o in types.select("option")] == ["", "article-journal", "paper", "patent", "thesis"]
    years = [o["value"] for o in toolbar.select_one('select[data-filter-key="year"]').select("option")]
    assert years[0] == "" and years[1:] == sorted({li["data-year"] for li in items}, reverse=True)
    assert {li["data-type"] for li in items} == {"article-journal", "paper", "patent", "thesis"}
    assert soup.select('script[src^="/js/filter."]')


def test_old_images_parity_clean(failures):
    assert failures("old-images") == []


def test_publication_links_accented_coauthors(site):
    hrefs = {a["href"] for a in site.soup("/publication/spin_orbit/index.html").select(".pub-authors a")}
    assert "/authors/onder-gul/" in hrefs
    names = [a.get_text(strip=True) for a in site.soup("/publication/conductance_quantization/index.html").select(".pub-authors a")]
    assert "Önder Gül" in names and "Sébastien R. Plissard" in names
