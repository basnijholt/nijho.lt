"""Per-page checks: ids, SEO fields and article content."""

import html
import json

import pytest
from bs4 import BeautifulSoup

from helpers import page
from parity.allow import AllowRule, partition
from parity.checks import Finding, check_content, check_ids, check_seo, seo_fields

POST = "/post/x/index.html"
HOME_SECTIONS = ("about", "blog-posts", "projects", "photography", "publications", "contact")


def old_article(body: str) -> str:
    return page(f'<div class="article-style">{body}</div>')


def new_article(body: str) -> str:
    return page(f'<div class="prose">{body}</div>')


def jsonld(data: dict) -> str:
    return f'<script type="application/ld+json">{json.dumps(data)}</script>'


@pytest.mark.parametrize(
    ("path", "base_html", "cand_html", "missing"),
    [
        pytest.param(
            POST,
            old_article('<h2 id="a"></h2><p id="fnref:1"></p><ol><li id="fn:1"></li></ol><figure id="figure-x">'),
            new_article('<h2 id="a"></h2><p></p><ol><li></li></ol><figure></figure>'),
            ["figure-x", "fn:1", "fnref:1"],
            id="ids-on-any-element",
        ),
        pytest.param(
            POST,
            page('<nav id="menu"></nav><div class="article-style"><p id="a"></p></div>'),
            new_article('<p id="a"></p>'),
            [],
            id="ids-outside-the-article-not-required",
        ),
        pytest.param(
            POST, old_article('<p id="a"></p>'), page('<p id="a"></p><div class="prose"></div>'), [],
            id="id-anywhere-in-candidate-counts",
        ),
        pytest.param(POST, old_article('<p id="a"></p>'), None, ["a"], id="candidate-page-missing"),
        pytest.param(
            "/index.html",
            page("".join(f'<section id="{id_}"></section>' for id_ in HOME_SECTIONS)),
            page(),
            sorted(HOME_SECTIONS),
            id="home-lost-all-sections",
        ),
        pytest.param(
            "/index.html",
            page('<section id="about"></section>'),
            page('<section id="about"></section><section id="contact"></section>'),
            ["blog-posts", "photography", "projects", "publications"],
            id="home-sections-required-without-baseline",
        ),
    ],
)
def test_ids_reports_each_lost_id(make_build, path, base_html, cand_html, missing):
    base = make_build("base", {path: base_html})
    cand = make_build("cand", {} if cand_html is None else {path: cand_html})
    assert check_ids(base, cand) == [Finding("ids", path, f"missing ID: {id_}") for id_ in missing]


@pytest.mark.parametrize(
    ("key", "base_head", "cand_head", "value"),
    [
        pytest.param("title", "<title>Post</title>", "", "Post", id="title"),
        pytest.param("description", '<meta name="description" content="About x">', "", "About x", id="description"),
        pytest.param("robots", '<meta name="robots" content="index, follow">', "", "index, follow", id="robots"),
        pytest.param("og:title", '<meta property="og:title" content="Post">', "", "Post", id="og-title"),
        pytest.param("og:description", '<meta property="og:description" content="X">', "", "X", id="og-description"),
        pytest.param("og:type", '<meta property="og:type" content="article">', "", "article", id="og-type"),
        pytest.param(
            "og:url", '<meta property="og:url" content="https://www.nijho.lt/post/x/">', "", "/post/x/", id="og-url"
        ),
        pytest.param(
            "og:image", '<meta property="og:image" content="https://www.nijho.lt/a.png">', "", "/a.png", id="og-image"
        ),
        pytest.param("twitter:card", '<meta name="twitter:card" content="summary">', "", "summary", id="twitter-card"),
        pytest.param("twitter:site", '<meta name="twitter:site" content="@bas">', "", "@bas", id="twitter-site"),
        pytest.param(
            "article:published_time", '<meta property="article:published_time" content="2024-01-01">', "",
            "2024-01-01", id="published-time",
        ),
        pytest.param(
            "article:modified_time", '<meta property="article:modified_time" content="2024-01-02">', "",
            "2024-01-02", id="modified-time",
        ),
        pytest.param(
            "canonical", '<link rel="canonical" href="https://www.nijho.lt/post/x/">', "", "/post/x/", id="canonical"
        ),
        pytest.param(
            "feeds",
            '<link rel="alternate" type="application/rss+xml" href="https://www.nijho.lt/post/index.xml">'
            '<link rel="alternate" type="application/rss+xml" href="/index.xml">',
            "",
            "/index.xml,/post/index.xml",
            id="feeds",
        ),
        pytest.param(
            "jsonld:@type", jsonld({"@type": "BlogPosting", "headline": "H"}), jsonld({"headline": "H"}),
            "BlogPosting", id="jsonld-type",
        ),
        pytest.param(
            "jsonld:headline", jsonld({"@type": "BlogPosting", "headline": "H"}), jsonld({"@type": "BlogPosting"}),
            "H", id="jsonld-headline",
        ),
        pytest.param(
            "jsonld:datePublished", jsonld({"headline": "H", "datePublished": "2024-01-01"}), jsonld({"headline": "H"}),
            "2024-01-01", id="jsonld-date-published",
        ),
        pytest.param(
            "jsonld:dateModified", jsonld({"headline": "H", "dateModified": "2024-01-02"}), jsonld({"headline": "H"}),
            "2024-01-02", id="jsonld-date-modified",
        ),
        pytest.param(
            "jsonld:author", jsonld({"headline": "H", "author": {"@type": "Person", "name": "Bas"}}),
            jsonld({"headline": "H"}), "Bas", id="jsonld-author",
        ),
    ],
)
def test_seo_reports_dropped_field(make_build, key, base_head, cand_head, value):
    base = make_build("base", {POST: page(head=base_head)})
    cand = make_build("cand", {POST: page(head=cand_head)})
    assert check_seo(base, cand) == [Finding("seo", POST, f"{key}: {value!r} -> ''")]


@pytest.mark.parametrize(
    ("base_head", "cand_head", "detail"),
    [
        pytest.param("<title>Old</title>", "<title>New</title>", "title: 'Old' -> 'New'", id="changed"),
        pytest.param("", '<meta name="robots" content="noindex">', "robots: '' -> 'noindex'", id="added"),
    ],
)
def test_seo_reports_changed_or_added_field(make_build, base_head, cand_head, detail):
    base = make_build("base", {POST: page(head=base_head)})
    cand = make_build("cand", {POST: page(head=cand_head)})
    assert check_seo(base, cand) == [Finding("seo", POST, detail)]


@pytest.mark.parametrize(
    ("base_head", "cand_head"),
    [
        pytest.param(
            '<link rel="canonical" href="/post/x/">', '<link rel="canonical" href="https://www.nijho.lt/post/x/">',
            id="canonical-compared-as-path",
        ),
        pytest.param(
            '<meta property="og:image" content="https://www.nijho.lt/a.png">',
            '<meta property="og:image" content="/a.png">',
            id="og-image-compared-as-path",
        ),
        pytest.param(
            '<meta name="twitter:card" content="summary">', '<meta property="twitter:card" content="summary">',
            id="name-or-property",
        ),
        pytest.param(
            '<meta name="generator" content="Hugo 0.123.3"><meta name="viewport" content="width=device-width">',
            '<meta name="generator" content="Hugo 0.167.0"><meta name="viewport" content="initial-scale=1">',
            id="unlisted-meta",
        ),
    ],
)
def test_seo_ignores_url_forms_attribute_kind_and_unlisted_meta(make_build, base_head, cand_head):
    base = make_build("base", {POST: page(head=base_head)})
    cand = make_build("cand", {POST: page(head=cand_head)})
    assert check_seo(base, cand) == []


def descriptions(text: str) -> str:
    value = html.escape(text)
    return f'<meta name="description" content="{value}"><meta property="og:description" content="{value}">'


@pytest.mark.parametrize(
    ("base", "cand"),
    [
        pytest.param(
            "📤 [`fileup`](https://github.com/basnijholt/fileup): upload with `fu x`", "📤 fileup: upload with fu x",
            id="markdown-link-and-code",
        ),
        pytest.param(
            "_**Tying Quantum Knots.**_ An *online* course, **very useful**",
            "Tying Quantum Knots. An online course, very useful",
            id="emphasis",
        ),
        pytest.param(
            "`ipynb_git_filters` keeps `__all__` and `_helper()`", "ipynb_git_filters keeps __all__ and _helper()",
            id="underscores-in-code",
        ),
        pytest.param("who doesn't need 'vibe' \"linking\"", "who doesn’t need ‘vibe’ “linking”", id="curly-quotes"),
        pytest.param("Day 01/24 -- one --- two...", "Day 01/24 – one — two…", id="dashes-and-ellipsis"),
        pytest.param("Q&amp;A, a\xa0b,\n  then c \n", "Q&A, a b, then c", id="entities-nbsp-and-whitespace"),
        pytest.param("**Bold**. Then _this_, (*that*)", "Bold. Then this, (that)", id="emphasis-before-punctuation"),
        pytest.param("ship `__init__.py` files", "ship __init__.py files", id="dunder-in-code"),
    ],
)
def test_seo_compares_descriptions_as_plain_text(make_build, base, cand):
    base_build = make_build("base", {POST: page(head=descriptions(base))})
    cand_build = make_build("cand", {POST: page(head=descriptions(cand))})
    assert check_seo(base_build, cand_build) == []


@pytest.mark.parametrize(
    ("base", "cand", "detail"),
    [
        pytest.param(
            "[`x`](https://x.org): a *fast* tool", "x: a slow tool", "description: 'x: a fast tool' -> 'x: a slow tool'",
            id="changed-word",
        ),
        pytest.param(
            "First sentence. Second sentence.", "First sentence.",
            "description: 'First sentence. Second sentence.' -> 'First sentence.'", id="truncated",
        ),
        pytest.param("use fu x", "use `fu x`", "description: 'use fu x' -> 'use `fu x`'", id="code-in-candidate"),
        pytest.param(
            "a **fast** tool", "a **fast** tool", "description: 'a fast tool' -> 'a **fast** tool'",
            id="emphasis-in-candidate",
        ),
        pytest.param(
            "[x](https://x.org) tool", "[x](https://x.org) tool", "description: 'x tool' -> '[x](https://x.org) tool'",
            id="link-in-candidate",
        ),
        pytest.param(
            "edit __init__.py", "edit init.py", "description: 'edit __init__.py' -> 'edit init.py'", id="dunder"
        ),
        pytest.param(
            "edit init.py", "edit __init__.py", "description: 'edit init.py' -> 'edit __init__.py'",
            id="dunder-in-candidate",
        ),
        pytest.param("a * b * c", "a b c", "description: 'a * b * c' -> 'a b c'", id="lone-asterisks"),
        pytest.param(
            "snake_case_name", "snakecasename", "description: 'snake_case_name' -> 'snakecasename'", id="snake-case"
        ),
    ],
)
def test_seo_reports_wording_changes_in_descriptions(make_build, base, cand, detail):
    base_build = make_build("base", {POST: page(head=descriptions(base))})
    cand_build = make_build("cand", {POST: page(head=descriptions(cand))})
    assert check_seo(base_build, cand_build) == [Finding("seo", POST, detail), Finding("seo", POST, "og:" + detail)]


def test_seo_skips_pages_the_candidate_lacks(make_build):
    assert check_seo(make_build("base", {POST: page()}), make_build("cand", {})) == []


def test_seo_title_comes_from_head():
    """An inline SVG <title> in the body is not the page title."""
    assert seo_fields(BeautifulSoup(page("<svg><title>Icon</title></svg>", head=""), "lxml")) == {}


def test_seo_jsonld_uses_first_object_with_headline_else_first_object():
    scripts = (
        '<script type="application/ld+json">[1]</script>'
        '<script type="application/ld+json">{not json</script>'
        + jsonld({"@type": "WebSite"})
        + jsonld({"@type": "BlogPosting", "headline": "H"})
    )
    assert seo_fields(BeautifulSoup(page(head=scripts), "lxml")) == {
        "jsonld:@type": "BlogPosting",
        "jsonld:headline": "H",
    }
    without_headline = scripts.rsplit("<script", 1)[0]
    assert seo_fields(BeautifulSoup(page(head=without_headline), "lxml")) == {"jsonld:@type": "WebSite"}


@pytest.mark.parametrize("path", ["/post/x/index.html", "/project/x/index.html", "/publication/x/index.html"])
def test_content_reports_text_change_on_articles(make_build, path):
    base = make_build("base", {path: old_article("<p>Old text</p>")})
    cand = make_build("cand", {path: new_article("<p>New text</p>")})
    assert check_content(base, cand) == [
        Finding("content", path, "text: 'Old text' -> 'New text'")
    ]


@pytest.mark.parametrize("path", ["/index.html", "/talk/x/index.html", "/tag/x/index.html"])
def test_content_skips_other_pages(make_build, path):
    base = make_build("base", {path: old_article("<p>Old text</p>")})
    cand = make_build("cand", {path: new_article("<p>New text</p>")})
    assert check_content(base, cand) == []


@pytest.mark.parametrize(
    ("base_body", "cand_body", "expected"),
    [
        pytest.param(
            '<p>See <a href="/x/">the docs</a>.</p>', "<p>See .</p>",
            ["text: 'See the docs .' -> 'See .'"], id="link-text-dropped",
        ),
        pytest.param(
            "<p>Python</p>", "<p>python</p>", ["text: 'Python' -> 'python'"], id="case"
        ),
        pytest.param(
            '<p>Claim<sup><a href="#fn:1">1</a></sup>.</p>', "<p>Claim.</p>",
            ["text: 'Claim 1 .' -> 'Claim.'"], id="footnote-reference-dropped",
        ),
        pytest.param("<p>a\n   b</p>", "<p>a b</p>", [], id="whitespace"),
        pytest.param("<p>One</p><p>Two</p>", "<p>One</p>\n\n<p>Two</p>", [], id="whitespace-between-blocks"),
        pytest.param(
            "<ul><li>One</li><li>Two</li></ul>", "<ul>\n<li>One</li>\n<li>Two</li>\n</ul>", [], id="list-items"
        ),
        pytest.param(
            "<p>One</p><p>Two</p>", "<p>One</p>\n<p></p>", ["text: 'One Two' -> 'One'"],
            id="word-dropped-between-blocks",
        ),
        pytest.param(
            '<pre class="chroma"><span class="nt">"key"</span><span class="p">:</span> 1</pre>',
            '<pre class="chroma">"key": 1</pre>', [], id="code-highlighted-differently",
        ),
        pytest.param(
            '<pre class="chroma"><span>"key"</span>: 1</pre>', '<pre class="chroma"><span>"key"</span>: 2</pre>',
            ["""text: '"key": 1' -> '"key": 2'"""], id="code-changed",
        ),
        pytest.param(
            '<div class="mermaid">A<br/>B</div>', '<pre class="mermaid">A<br/>B</pre>', ["pre count: 0 -> 1"],
            id="line-break-outside-code",
        ),
        pytest.param('<h2>H<a class="anchor" href="#h">#</a></h2>', "<h2>H</h2>", [], id="heading-anchor"),
        pytest.param(
            '<details class="toc"><summary>Contents</summary><a href="#a">A</a></details><p>Body</p>', "<p>Body</p>",
            [], id="toc",
        ),
        pytest.param(
            "<p>Body</p>", '<details class="toc-inpage"><summary>On this page</summary></details><p>Body</p>', [],
            id="toc-inpage",
        ),
        pytest.param('<nav id="TableOfContents"><a href="#a">A</a></nav><p>Body</p>', "<p>Body</p>", [], id="toc-nav"),
        pytest.param('<p>A</p><img src="a.png" alt="">', "<p>A</p>", ["img count: 1 -> 0"], id="img"),
        pytest.param("<pre>x = 1</pre>", "<p>x = 1</p>", ["pre count: 1 -> 0"], id="pre"),
        pytest.param("<table><tr><td>cell</td></tr></table>", "<p>cell</p>", ["table count: 1 -> 0"], id="table"),
        pytest.param('<p>A</p><video src="a.mp4"></video>', "<p>A</p>", ["video count: 1 -> 0"], id="video"),
        pytest.param(
            "<details><summary>More</summary>Hidden</details>", "<p>More</p>Hidden", ["details count: 1 -> 0"],
            id="details",
        ),
        pytest.param("<p>A</p>", '<p>A</p><img src="a.png" alt="">', ["img count: 0 -> 1"], id="img-added"),
        pytest.param('<img src="a.png"><img src="b.png">', '<img src="a.png">', ["img count: 2 -> 1"], id="img-2-to-1"),
        pytest.param(
            "<pre>a</pre><pre>b</pre><pre>c</pre>", "<pre>a</pre><pre>b</pre><p>c</p>", ["pre count: 3 -> 2"],
            id="pre-3-to-2",
        ),
    ],
)
def test_content_reports_text_and_element_count_changes(make_build, base_body, cand_body, expected):
    base = make_build("base", {POST: old_article(base_body)})
    cand = make_build("cand", {POST: new_article(cand_body)})
    assert check_content(base, cand) == [Finding("content", POST, detail) for detail in expected]


def test_content_reports_each_differing_region_so_allowing_one_keeps_the_other(make_build):
    """A changed first paragraph is allowed; a paragraph deleted further down still fails."""
    paragraphs = [f"<p>Paragraph {i} has some words in it.</p>" for i in range(6)]
    changed = ["<p>Paragraph 0 has other words in it.</p>", *paragraphs[1:4], paragraphs[5]]
    base = make_build("base", {POST: old_article(" ".join(paragraphs))})
    cand = make_build("cand", {POST: new_article(" ".join(changed))})
    first = "text: 'Paragraph 0 has some words in it.' -> 'Paragraph 0 has other words in it.'"
    deleted = "text: 'in it. Paragraph 4 has some words in it. Paragraph 5 has some' -> 'in it. Paragraph 5 has some'"
    findings = check_content(base, cand)
    assert findings == [Finding("content", POST, first), Finding("content", POST, deleted)]
    rule = AllowRule("content", POST, first, "new wording")
    assert partition(findings, [rule]) == ([Finding("content", POST, deleted)], [findings[0]], [])


def test_content_reports_lost_article_root(make_build):
    base = make_build("base", {POST: old_article("<p>Body</p>")})
    cand = make_build("cand", {POST: page("<article><p>Body</p></article>")})
    assert check_content(base, cand) == [Finding("content", POST, "article root missing in candidate")]


def test_content_skips_baseline_pages_without_article_and_pages_the_candidate_lacks(make_build):
    base = make_build("base", {POST: page("<p>Old</p>"), "/post/y/index.html": old_article("<p>Body</p>")})
    cand = make_build("cand", {POST: new_article("<p>New</p>")})
    assert check_content(base, cand) == []


def test_content_leaves_cached_pages_intact(make_build):
    """The other checks read the same cached soups, so stripping the uncompared parts must happen on a copy."""
    heading = '<h2>H<a class="anchor">#</a></h2>'
    base = make_build("base", {POST: old_article(f'<details class="toc"></details>{heading}')})
    cand = make_build("cand", {POST: new_article(f'<details class="toc-inpage"></details>{heading}')})
    check_content(base, cand)
    assert len(base.soup(POST).select("details.toc, a.anchor")) == 2
    assert len(cand.soup(POST).select("details.toc-inpage, a.anchor")) == 2
