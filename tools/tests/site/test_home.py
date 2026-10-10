"""The homepage: every section of content/home in weight order, with its real content."""

import re
from datetime import datetime

import pytest
import yaml

from helpers import CONTENT, require_hugo
from parity.build import build_site, resolve_hugo
from parity.site import Build

HOME = "/index.html"


def front_matter(file) -> dict:
    text = file.read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---")[1]) if text.startswith("---") else {}


def published(section: str) -> list[dict]:
    pages = [front_matter(f) for f in (CONTENT / section).glob("*/index.md")]
    return [fm for fm in pages if not fm.get("draft")]


def cards(soup) -> list:
    return soup.select("#projects article.proj")


def test_home_section_ids_in_order(site):
    widgets = [(front_matter(f)["weight"], f.stem) for f in (CONTENT / "home").glob("*.md") if f.stem != "index"]
    ids = [s["id"] for s in site.soup(HOME).select("main > section[id]")]
    assert ids == [stem for _, stem in sorted(widgets)]
    assert ids == ["about", "blog-posts", "projects", "photography", "publications", "contact"]


def test_home_counts(site):
    soup = site.soup(HOME)
    assert len(soup.select("#blog-posts ul.w1 > li")) == 10
    assert len(cards(soup)) == len(published("project")) == 51
    assert len(soup.select("#publications ol.pubs > li")) == len(published("publication")) == 15
    assert len(soup.select("#photography .photo-grid a img")) == 9


def test_home_blog_rows_are_the_newest_posts(site):
    soup = site.soup(HOME)
    newest = sorted(
        ((datetime.fromisoformat(a["datetime"]), a) for a in soup.select("#blog-posts .post-meta time")),
        key=lambda pair: pair[0],
        reverse=True,
    )
    assert [a for _, a in newest] == soup.select("#blog-posts .post-meta time")
    assert soup.select_one('#blog-posts a.more[href="/post/"]').get_text(strip=True) == "See all blog posts"
    assert soup.select_one("#blog-posts .sub").get_text(strip=True) == "Sparse scribblings on a variety of topics"


def test_home_intro(site):
    author = front_matter(CONTENT / "authors/admin/_index.md")
    organization = author["organizations"][0]
    intro = site.soup(HOME).select_one("section#about")
    assert intro.select_one("h1").get_text(strip=True) == "Bas Nijholt"
    assert intro.select_one(".role").get_text(" ", strip=True) == f"{author['role']} at {organization['name']}"
    assert intro.select_one(f'.role a[href="{organization["url"]}"]')
    avatar = intro.select_one("img.avatar")
    assert avatar["src"].endswith(".webp") and avatar.get("loading") != "lazy"
    assert intro.select_one(".bio").get_text(" ", strip=True).startswith("Hi, my name is Bas.")
    assert len(intro.select(".social a")) == 7
    assert intro.select_one('.social a[href="/#contact"]')


def test_home_interests_and_education(site):
    intro = site.soup(HOME).select_one("section#about")
    interests = intro.select(".interests li")
    assert [li.get_text(strip=True) for li in interests] == [
        "Quantum Mechanics",
        "Landscape photography",
        "Open-source software",
        "Hiking in the mountains",
        "Blockchain technology",
        "Home automation",
        "Artificial Intelligence",
    ]
    assert all(li.select_one("em.fa-fw") for li in interests)
    assert [li.get_text(" ", strip=True) for li in intro.select(".edu li")] == [
        "2020 PhD in computational Quantum Mechanics TU Delft",
        "2015 MSc in Applied Physics TU Delft",
        "2012 BSc in Applied Physics TU Delft",
    ]


def test_author_admin_shows_the_intro(site):
    soup = site.soup("/authors/admin/index.html")
    assert soup.select_one("section#about .facts .edu")
    assert len(soup.select("ul.w1 > li")) > 20


def test_projects_sorted_by_stars(site):
    order = [(int(c["data-stars"]), int(c["data-date"])) for c in cards(site.soup(HOME))]
    assert order and order == sorted(order, reverse=True)


def test_project_card(site):
    soup = site.soup(HOME)
    by_link = {c.select_one("h3 a.stretch")["href"]: c for c in cards(soup)}
    agent = by_link["https://github.com/basnijholt/agent-cli"]
    assert agent.select_one("h3").get_text(strip=True) == "Agent CLI"
    assert agent["data-tags"] == "python,ai,llm,speech-to-text"
    assert agent.select_one(".proj-body p code").get_text() == "agent-cli"
    assert agent.select_one(".plate img")["src"].endswith(".webp")
    for card in cards(soup):
        if star := card.select_one(".stars"):
            count = int(card["data-stars"])
            text = f"{count / 1000:.1f}k".replace(".0k", "k") if count >= 1000 else str(count)
            assert star.get_text(strip=True) == text
    animated = by_link["https://github.com/basnijholt/compose-farm"]
    assert animated.select_one(".plate img")["src"] == "/project/compose-farm/animated.svg"
    gif = next(c for c in cards(soup) if c.select_one('.plate img[src$=".gif"]'))
    assert gif.select_one(".plate img")["src"] == "/project/adaptive/featured.gif"
    plain = by_link["https://github.com/basnijholt/clip-files"]
    assert plain.select_one(".plate.empty .emo").get_text(strip=True)
    assert all(c.select_one(".plate img")["loading"] == "lazy" for c in cards(soup) if c.select_one(".plate img"))


def test_project_toolbar(site):
    soup = site.soup(HOME)
    toolbar = soup.select_one("#projects [data-filter-toolbar]")
    assert toolbar.has_attr("hidden")
    buttons = {b["data-filter"]: int(b.select_one(".n").get_text()) for b in toolbar.select("button[data-filter]")}
    assert list(buttons) == ["*", "python", "ai", "homelab", "home automation", "education", "parallel computing"]
    assert buttons["*"] == 51
    tagged = [c for c in cards(soup) if "home automation" in c["data-tags"].split(",")]
    assert buttons["home automation"] == len(tagged) > 0
    assert toolbar.select_one("input[type=search][data-filter-search]")
    assert [o["value"] for o in toolbar.select("select[data-filter-sort] option")] == ["order", "date", "name"]
    assert soup.select_one("#projects [data-filter-empty][hidden]")


def test_no_resized_gifs_anywhere(site):
    assert [f for f in site.files if re.search(r"_hu.*\.gif$", f)] == []


def test_publications(site):
    soup = site.soup(HOME)
    items = soup.select("#publications ol.pubs > li")
    years = [li.select_one(".pub-year").get_text(strip=True) for li in items]
    assert years == sorted(years, reverse=True)
    assert [li.has_attr("class") and "cont" in li["class"] for li in items] == [
        i > 0 and years[i] == years[i - 1] for i in range(len(items))
    ]
    insb = next(li for li in items if "InSb nanowires" in li.select_one(".pub-title").get_text())
    assert insb.select_one(".pub-title")["href"] == "/publication/conductance_quantization/"
    assert insb.select_one(".pub-authors").get_text(" ", strip=True) == (
        "Jakob Kammhuber, Maja C. Cassidy, Hao Zhang, Önder Gül, Fei Pei, Michiel W. A. de Moor, "
        "and 7 more, including Bas Nijholt"
    )
    assert insb.select_one(".pub-authors strong").get_text() == "Bas Nijholt"
    assert insb.select_one(".pub-venue").get_text(" ", strip=True) == "Nano letters (Nano Lett.), April 2016"
    assert [a.get_text(strip=True) for a in insb.select(".pub-links a")] == [
        "PDF", "arXiv:1603.03751", "10.1021/acs.nanolett.6b00051",
    ]
    assert soup.select_one('#publications .callout a[href$="/publication/"]')


def test_contact(site):
    contact = site.soup(HOME).select_one("section#contact")
    assert contact.select_one('a.email[href="mailto:bas@nijho.lt"]').get_text(strip=True) == "bas@nijho.lt"
    channels = {li.select_one(".k").get_text(strip=True): li.select_one(".v") for li in contact.select(".channels li")}
    assert list(channels) == ["Location", "Directions", "PGP key", "Matrix", "Telegram", "Twitter", "GitHub"]
    assert channels["Location"].get_text(strip=True) == "Kirkland, Washington"
    assert channels["PGP key"]["href"] == "/bas.asc"
    assert channels["PGP key"].get_text(strip=True) == "A40D B603 2FCB 6B54 B570 8D53 82C7 7BBB A474 3E31"
    assert channels["GitHub"]["href"] == "https://github.com/basnijholt"
    card = contact.select_one("a.map-card")
    assert card["href"] == "https://www.openstreetmap.org/?mlat=47.6769&mlon=-122.2060#map=12/47.6769/-122.2060"
    assert card.select_one("img")["src"].endswith(".webp")


def test_home_weight_under_2mb(site):
    soup = site.soup(HOME)
    eager = [img["src"] for img in soup.select("img[src]") if img.get("loading") != "lazy"]
    lazy = [img["src"] for img in soup.select("img[src]") if img.get("loading") == "lazy"]
    assets = (
        [s["src"] for s in soup.select("script[src]")]
        + [link["href"] for link in soup.select('link[rel=stylesheet], link[rel=preload][as=font]')]
        + eager
    )
    sizes = {src: (site.root / src.lstrip("/")).stat().st_size for src in assets if src.startswith("/")}
    total = (site.root / "index.html").stat().st_size + sum(sizes.values())
    lazy_total = sum((site.root / src.lstrip("/")).stat().st_size for src in lazy if src.startswith("/"))
    print(f"home: {total:,} bytes up front; {len(lazy)} lazy images, {lazy_total:,} bytes")
    assert total < 2_000_000, sizes


@pytest.mark.slow
def test_build_survives_github_api_failure(repo_root, tmp_path):
    """With every remote request refused and no cached responses, the build still succeeds; projects lose their star
    counts and fall back to newest first. Hugo's HTTP client ignores HTTPS_PROXY, so its security policy refuses."""
    hugo = require_hugo(resolve_hugo(), "0.167.0", "HUGO_BIN")
    env = {"HUGO_SECURITY_HTTP_URLS": "^none$", "HUGO_CACHEDIR": str(tmp_path / "cache")}
    build = Build(build_site(repo_root, tmp_path / "public", hugo=hugo, env=env))
    home = cards(build.soup(HOME))
    assert len(home) == 51
    assert not [c for c in home if c.select_one(".stars")]
    dates = [int(c["data-date"]) for c in home]
    assert dates == sorted(dates, reverse=True)
