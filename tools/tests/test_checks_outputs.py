"""Checks on output files: paths, sitemap, feeds and redirects."""

import pytest

from helpers import item, rss, sitemap
from parity.checks import Finding, check_feeds, check_paths, check_redirects, check_sitemap, text_diff

FEED = "/post/index.xml"
HU_IMAGE = "/media/photo_hu0123456789abcdef0123456789abcdef_5000_300x200_fit_q90_lanczos.jpg"


@pytest.mark.parametrize(
    "path",
    [
        "/post/a/index.html", "/index.xml", "/sitemap.xml", "/index.json", "/manifest.webmanifest", "/robots.txt",
        "/bas.asc", "/a.png", "/a.jpg", "/a.jpeg", "/a.gif", "/a.svg", "/a.webp", "/v.mp4", "/v.mov", "/code/x.py",
        "/x.js", "/_headers", "/_redirects",
        # Names that only contain a theme folder or "_hu"
        "/post/css-grid/index.html", "/post/nodejs/index.html", "/media/github_hub.png",
    ],
)
def test_paths_reports_missing_public_file(make_build, path):
    base = make_build("base", {path: "", "/kept.html": ""})
    cand = make_build("cand", {"/kept.html": ""})
    assert check_paths(base, cand) == [Finding("paths", path, "missing from candidate")]


@pytest.mark.parametrize(
    "path",
    [
        # Public extensions skipped only for their theme folder
        pytest.param("/css/icon.svg", id="css-folder"),
        pytest.param("/js/app.abc123.js", id="js-folder"),
        pytest.param("/en/js/search.js", id="en-js-folder"),
        pytest.param("/webfonts/fa.svg", id="webfonts-folder"),
        # Not public: stylesheets and fonts change with the theme
        pytest.param("/css/main.abc123.css", id="stylesheet"),
        pytest.param("/fonts/geist.woff2", id="font"),
        # The old-images check covers these
        pytest.param(HU_IMAGE, id="resized-image"),
        pytest.param("/media/x_hu0123456789abcdef0123456789abcdef.png", id="resized-image-without-size"),
    ],
)
def test_paths_skips_theme_assets_and_resized_images(make_build, path):
    assert check_paths(make_build("base", {path: ""}), make_build("cand", {})) == []


PAGES = {"/index.html": "", "/post/a/index.html": ""}


@pytest.mark.parametrize(
    ("base_locs", "cand_locs", "cand_files", "expected"),
    [
        pytest.param(["/", "/post/a/"], ["/", "/post/a/"], PAGES, [], id="unchanged"),
        pytest.param(
            ["/", "/post/a/"], ["/"], PAGES, [("/post/a/", "missing from candidate sitemap")], id="loc-dropped"
        ),
        pytest.param(["/"], ["/", "/post/b/"], PAGES | {"/post/b/index.html": ""}, [], id="new-loc-with-page"),
        pytest.param(
            ["/"], ["/", "/tags/a/"], PAGES, [("/tags/a/", "sitemap entry lacks /tags/a/index.html")],
            id="new-loc-without-page",
        ),
        pytest.param(
            ["/post/a/"], ["/post/a/"], {}, [("/post/a/", "sitemap entry lacks /post/a/index.html")], id="page-dropped"
        ),
        pytest.param(["/tags/a/"], ["/tags/a/"], PAGES, [], id="baseline-lacked-the-page-too"),
        pytest.param([], ["/caf%C3%A9/"], {"/café/index.html": ""}, [], id="percent-encoded-loc"),
        pytest.param(
            [], ["/caf%C3%A9/"], {}, [("/caf%C3%A9/", "sitemap entry lacks /café/index.html")],
            id="percent-encoded-loc-without-page",
        ),
        pytest.param([], ["/cv.pdf"], {}, [], id="file-loc"),
        pytest.param(
            [], ["/tags/a/"], {"/_redirects": "/tags/* /tag/:splat 301\n"},
            [("/tags/a/", "sitemap entry lacks /tags/a/index.html")], id="redirect-is-not-a-page",
        ),
    ],
)
def test_sitemap_keeps_locs_and_their_pages(make_build, base_locs, cand_locs, cand_files, expected):
    base = make_build("base", PAGES | {"/sitemap.xml": sitemap(base_locs)})
    cand = make_build("cand", cand_files | {"/sitemap.xml": sitemap(cand_locs)})
    assert check_sitemap(base, cand) == [Finding("sitemap", loc, detail) for loc, detail in expected]


DATE = "Mon, 01 Jan 2024 00:00:00 +0000"


@pytest.mark.parametrize(
    ("base_items", "cand_items", "channel", "expected"),
    [
        pytest.param([item("a")], [item("a")], {}, [], id="unchanged"),
        pytest.param(
            [item("a"), item("b"), item("c")],
            [item("a")],
            {},
            [
                "missing guid '/post/b/'",
                "missing guid '/post/c/'",
                "missing link '/post/b/'",
                "missing link '/post/c/'",
            ],
            id="items-dropped",
        ),
        pytest.param(
            [item("a")], [item("a"), item("b")], {}, ["extra guid '/post/b/'", "extra link '/post/b/'"], id="item-added"
        ),
        pytest.param(
            [item("a")], [item("a"), item("a")], {}, ["duplicate guid: '/post/a/' (2 items)"], id="duplicate-guid"
        ),
        pytest.param([item("a"), item("a")], [item("a"), item("a")], {}, [], id="duplicate-guid-in-baseline-too"),
        pytest.param(
            [item("a")], [item("a")], {"title": "Blog"}, ["channel title: 'Posts' -> 'Blog'"], id="channel-title"
        ),
        pytest.param(
            [item("a")],
            [item("a")],
            {"link": "https://www.nijho.lt/blog/"},
            ["channel link: '/post/' -> '/blog/'"],
            id="channel-link",
        ),
        pytest.param([item("a")], [item("a", link="/post/a/")], {"link": "/post/"}, [], id="links-compared-as-paths"),
        pytest.param(
            [item("a")],
            [item("a", link="/post/moved/")],
            {},
            ["extra link '/post/moved/'", "missing link '/post/a/'"],
            id="item-link",
        ),
        pytest.param(
            [item("a")],
            [item("a", title="Renamed")],
            {},
            ["item '/post/a/' title: 'Post a' -> 'Renamed'"],
            id="item-title",
        ),
        pytest.param(
            [item("a")],
            [item("a", guid="https://www.nijho.lt/post/a/", title="Renamed")],
            {},
            [
                "extra guid 'https://www.nijho.lt/post/a/'",
                "item '/post/a/' title: 'Post a' -> 'Renamed'",
                "missing guid '/post/a/'",
            ],
            id="guid-made-absolute-and-title",
        ),
        pytest.param(
            [item("a")],
            [item("a", guid=" /post/a/ ")],
            {},
            ["extra guid ' /post/a/ '", "missing guid '/post/a/'"],
            id="guid-whitespace",
        ),
        pytest.param(
            [item("a")], [item("a", date="Mon, 01 Jan 2024 01:00:00 +0100")], {}, [], id="pubdate-same-instant"
        ),
        pytest.param(
            [item("a")],
            [item("a", date="Mon, 01 Jan 2024 05:00:00 +0000")],
            {},
            [f"item '/post/a/' pubDate: {DATE!r} -> 'Mon, 01 Jan 2024 05:00:00 +0000'"],
            id="pubdate-same-day",
        ),
        pytest.param(
            [item("a")],
            [item("a", date="Tue, 02 Jan 2024 00:00:00 +0000")],
            {},
            [f"item '/post/a/' pubDate: {DATE!r} -> 'Tue, 02 Jan 2024 00:00:00 +0000'"],
            id="pubdate",
        ),
        pytest.param(
            [item("a")], [item("a", date="")], {}, [f"item '/post/a/' pubDate: {DATE!r} -> ''"], id="pubdate-unparsable"
        ),
        pytest.param(
            [item("a")],
            [item("a", description="")],
            {},
            ["item '/post/a/' text: 'Text of a' -> ''"],
            id="item-text",
        ),
        pytest.param(
            [item("a", description="One a b c d e f g two")],
            [item("a", description="1 a b c d e f g 2")],
            {},
            ["item '/post/a/' text: 'One a b c' -> '1 a b c'", "item '/post/a/' text: 'e f g two' -> 'e f g 2'"],
            id="item-text-in-two-places",
        ),
        pytest.param(
            [item("a")], [item("a", description="Text &lt;em&gt;of&lt;/em&gt;\n a")], {}, [], id="item-text-markup-only"
        ),
    ],
)
def test_feeds_report_each_difference(make_build, base_items, cand_items, channel, expected):
    base = make_build("base", {FEED: rss(base_items)})
    cand = make_build("cand", {FEED: rss(cand_items, **channel)})
    assert check_feeds(base, cand) == [Finding("feeds", FEED, detail) for detail in expected]


def test_feeds_reports_missing_feed(make_build):
    base = make_build("base", {FEED: rss([item("a")])})
    assert check_feeds(base, make_build("cand", {})) == [Finding("feeds", FEED, "missing from candidate")]


def words(start: int, stop: int) -> str:
    return " ".join(f"w{i}" for i in range(start, stop))


@pytest.mark.parametrize(
    ("base", "cand", "expected"),
    [
        pytest.param(words(0, 9), words(0, 9), [], id="equal"),
        pytest.param("a b c d e f g", "a b c X e f g", ["text: 'a b c d e f g' -> 'a b c X e f g'"], id="replacement"),
        pytest.param("a b c d e f g", "a b c e f g", ["text: 'a b c d e f g' -> 'a b c e f g'"], id="deletion"),
        pytest.param("a b c e f g", "a b c d e f g", ["text: 'a b c e f g' -> 'a b c d e f g'"], id="insertion"),
        pytest.param("a\nb", "a   c", ["text: 'a b' -> 'a c'"], id="whitespace-is-a-word-break"),
        pytest.param("", "a b", ["text: '' -> 'a b'"], id="from-empty"),
        pytest.param(
            f"x {words(0, 20)} y", f"x {words(0, 10)} middle {words(10, 20)} z",
            [
                "text: 'w7 w8 w9 w10 w11 w12' -> 'w7 w8 w9 middle w10 w11 w12'",
                "text: 'w17 w18 w19 y' -> 'w17 w18 w19 z'",
            ],
            id="two-differences",
        ),
        pytest.param(
            "one two three four five", "one 2 three 4 five",
            ["text: 'one two three' -> 'one 2 three'", "text: 'three four five' -> 'three 4 five'"],
            id="context-stops-at-the-next-difference",
        ),
        pytest.param(
            f"a b c {words(0, 20)} d e f", "a b c d e f",
            [f"text: 'a b c {words(0, 6)} [8 words] {words(14, 20)} d e f' -> 'a b c d e f'"],
            id="long-deletion-is-shortened",
        ),
        pytest.param(
            " ".join(f"keep{i} old{i}" for i in range(25)),
            " ".join(f"keep{i} new{i}" for i in range(25)),
            [f"text: 'keep{i} old{i} keep{i + 1}' -> 'keep{i} new{i} keep{i + 1}'" for i in range(20)]
            + ["text: 5 more differences"],
            id="capped-at-20",
        ),
    ],
)
def test_text_diff_gives_one_line_per_differing_region(base, cand, expected):
    assert text_diff(base, cand) == expected


BASE_RULES = "/old/ /new/ 301!\n/a/ /b/ 302\n"


@pytest.mark.parametrize(
    ("cand_rules", "expected"),
    [
        pytest.param(BASE_RULES, [], id="unchanged"),
        pytest.param(BASE_RULES + "/c/ /d/ 301\n", [], id="rule-added"),
        pytest.param("/old/ /new/ 301!\n", [("/a/", "missing redirect to /b/ 302")], id="rule-dropped"),
        pytest.param("/old/ /new/ 302!\n/a/ /b/ 302\n", [("/old/", "missing redirect to /new/ 301!")], id="status"),
        pytest.param("/old/ /new/ 301\n/a/ /b/ 302\n", [("/old/", "missing redirect to /new/ 301!")], id="force"),
        pytest.param("/old/ /newer/ 301!\n/a/ /b/ 302\n", [("/old/", "missing redirect to /new/ 301!")], id="target"),
        pytest.param(
            "/old/* /elsewhere/ 301\n" + BASE_RULES,
            [("/old/", "redirect to /new/ 301! is shadowed by /old/* /elsewhere/ 301")],
            id="shadowed-by-a-broader-rule",
        ),
        pytest.param(
            "/a/ /c/ 302\n" + BASE_RULES, [("/a/", "redirect to /b/ 302 is shadowed by /a/ /c/ 302")],
            id="shadowed-by-the-same-source",
        ),
        pytest.param(BASE_RULES + "/old/* /elsewhere/ 301\n", [], id="broader-rule-below"),
    ],
)
def test_redirects_report_each_lost_rule(make_build, cand_rules, expected):
    base = make_build("base", {"/_redirects": BASE_RULES})
    cand = make_build("cand", {"/_redirects": cand_rules})
    assert check_redirects(base, cand) == [Finding("redirects", source, detail) for source, detail in expected]
