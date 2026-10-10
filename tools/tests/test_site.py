"""Reading a build: URLs, listings, feeds, redirect rules and path resolution."""

import pytest

from helpers import item, rss, sitemap
from parity import ParityError
from parity.site import Feed, FeedItem, Redirect, norm_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        pytest.param("https://www.nijho.lt/post/a/", "/post/a/", id="https"),
        pytest.param("http://www.nijho.lt/a/", "/a/", id="http"),
        pytest.param("//www.nijho.lt/a/?q=1", "/a/?q=1", id="scheme-relative"),
        pytest.param("https://www.nijho.lt", "/", id="bare-root"),
        pytest.param("https://www.nijho.lt#about", "/#about", id="root-fragment"),
        pytest.param("/post/a/", "/post/a/", id="root-relative"),
        pytest.param("https://nijho.lt/a/", "https://nijho.lt/a/", id="apex-domain"),
        pytest.param("https://www.nijho.lt.example/x", "https://www.nijho.lt.example/x", id="look-alike-host"),
        pytest.param("https://github.com/x", "https://github.com/x", id="other-host"),
    ],
)
def test_norm_url_turns_only_www_urls_into_paths(url, expected):
    assert norm_url(url) == expected


def test_listings_sort_pages_and_feeds(make_build):
    files = ("/b.html", "/a/index.html", "/post/index.xml", "/sitemap.xml", "/a.css")
    build = make_build("b", dict.fromkeys(files, ""))
    assert build.pages == ("/a/index.html", "/b.html")
    assert build.feeds == ("/post/index.xml",)


def test_listings_are_read_once(make_build):
    build = make_build("b", {"/index.html": ""})
    assert build.files is build.files
    (build.root / "late.html").write_text("")
    assert build.pages == ("/index.html",)


def test_sitemap_locs_are_paths(make_build):
    build = make_build("b", {"/sitemap.xml": sitemap(["/", "/post/a/"])})
    assert build.sitemap_locs == {"/", "/post/a/"}
    assert make_build("empty", {}).sitemap_locs == frozenset()


def test_redirects_parse_status_and_force(make_build):
    """Netlify writes force as a ! glued to the status code; the status defaults to 301."""
    rules = "/a/ /b/ 301!\n/c/ /d/ 302\n/e/ /f/ 200!\n# /x/ /y/\n/lonely\n\n/g/ /h/\n/i/ /j/ 404 Country=nl\n"
    assert make_build("b", {"/_redirects": rules}).redirects == (
        Redirect("/a/", "/b/", 301, True),
        Redirect("/c/", "/d/", 302, False),
        Redirect("/e/", "/f/", 200, True),
        Redirect("/g/", "/h/", 301, False),
        Redirect("/i/", "/j/", 404, False),
    )
    assert make_build("empty", {}).redirects == ()


def test_feed_normalizes_urls_and_keeps_raw_guid(make_build):
    entry = item("a", guid="https://www.nijho.lt/post/a/", description="Some &lt;b&gt;bold&lt;/b&gt;\n  text")
    build = make_build("b", {"/post/index.xml": rss([entry])})
    assert build.feed("/post/index.xml") == Feed(
        title="Posts",
        link="/post/",
        items=(
            FeedItem(
                title="Post a",
                link="/post/a/",
                guid="/post/a/",
                text="Some bold text",
                raw_guid="https://www.nijho.lt/post/a/",
                pub_date="Mon, 01 Jan 2024 00:00:00 +0000",
            ),
        ),
    )


@pytest.mark.parametrize(
    ("file", "content", "read", "message"),
    [
        pytest.param(
            "index.xml", "<feed></feed>", lambda b: b.feed("/index.xml"), " has no <channel>; not an RSS 2.0 feed",
            id="feed-without-channel",
        ),
        pytest.param(
            "index.xml", "<rss><channel>", lambda b: b.feed("/index.xml"),
            ": invalid XML: no element found: line 1, column 14", id="feed-not-xml",
        ),
        pytest.param(
            "index.xml", b"<rss><channel><title>caf\xe9</title></channel></rss>", lambda b: b.feed("/index.xml"),
            ": invalid XML: not well-formed (invalid token): line 1, column 24", id="feed-not-utf8",
        ),
        pytest.param(
            "sitemap.xml", "<urlset>", lambda b: b.sitemap_locs, ": invalid XML: no element found: line 1, column 8",
            id="sitemap-not-xml",
        ),
        pytest.param(
            "sitemap.xml", b"<urlset>\xff</urlset>", lambda b: b.sitemap_locs,
            ": invalid UTF-8 at byte 8: invalid start byte", id="sitemap-not-utf8",
        ),
        pytest.param(
            "post/index.html", b"<p>caf\xe9</p>", lambda b: b.soup("/post/index.html"),
            ": invalid UTF-8 at byte 6: invalid continuation byte", id="page-not-utf8",
        ),
        pytest.param(
            "_redirects", b"/caf\xe9/ /x/ 301\n", lambda b: b.redirects,
            ": invalid UTF-8 at byte 4: invalid continuation byte", id="redirects-not-utf8",
        ),
    ],
)
def test_unreadable_file_is_an_error_naming_it(make_build, file, content, read, message):
    build = make_build("b", {file: content})
    with pytest.raises(ParityError) as error:
        read(build)
    assert str(error.value) == f"{build.root / file}{message}"


def chain(hops: int) -> str:
    """Redirect rules from /0/ to /1/, and on, to /<hops>/."""
    return "".join(f"/{i}/ /{i + 1}/ 301\n" for i in range(hops))


@pytest.mark.parametrize(
    ("files", "rules", "path", "expected"),
    [
        pytest.param(["/a.png"], "", "/a.png", True, id="file"),
        pytest.param(["/a/index.html"], "", "/a/", True, id="directory-index"),
        pytest.param(["/a/other.html"], "", "/a/", False, id="directory-without-index"),
        pytest.param(["/a/index.html"], "", "/a", True, id="directory-without-trailing-slash"),
        pytest.param(["/a/other.html"], "", "/a", False, id="no-index-without-trailing-slash"),
        pytest.param([], "", "/gone/", False, id="missing"),
        pytest.param(["/a b.png"], "", "/a%20b.png", True, id="percent-encoded-file"),
        pytest.param(["/padkær/index.html"], "", "/padk%C3%A6r/", True, id="percent-encoded-directory"),
        pytest.param(["/new/index.html"], "/old/ /new/ 301\n", "/old/", True, id="redirect"),
        pytest.param(["/new/index.html"], "/old/ /new/ 302\n", "/old/", True, id="temporary-redirect"),
        pytest.param(["/new/index.html"], "/old/ /new/ 200\n", "/old/", True, id="rewrite"),
        pytest.param([], "/old/ /gone/ 301\n", "/old/", False, id="redirect-to-missing-page"),
        pytest.param(["/new/index.html"], "/old/ /new/ 404\n", "/old/", False, id="not-found-rule"),
        pytest.param(["/ok/index.html"], "/old/ /gone/ 301\n/old/ /ok/ 301\n", "/old/", False, id="first-rule-wins"),
        pytest.param(["/c/index.html"], "/a/ /b/ 301\n/b/ /c/ 301\n", "/a/", True, id="chain"),
        pytest.param([], "/a/ /b/ 301\n/b/ /a/ 301\n", "/a/", False, id="loop"),
        pytest.param(["/10/index.html"], chain(10), "/0/", True, id="10-hops"),
        pytest.param(["/11/index.html"], chain(11), "/0/", False, id="11-hops"),
        pytest.param([], "/old/ https://github.com/x 301\n", "/old/", True, id="other-host"),
        pytest.param(["/new/index.html"], "/old/ https://www.nijho.lt/new/ 301\n", "/old/", True, id="own-host"),
        pytest.param([], "/old/ https://www.nijho.lt/gone/ 301\n", "/old/", False, id="own-host-missing"),
        pytest.param(["/new/index.html"], "/old/ /new/?a=1#b 301\n", "/old/", True, id="target-query-fragment"),
        pytest.param(["/new/index.html"], "/old/ /new/ 301\n", "/old/sub/", False, id="redirect-matches-whole-path"),
        pytest.param(["/tag/python/index.html"], "/tags/* /tag/:splat 301\n", "/tags/python/", True, id="splat"),
        pytest.param(["/tag/python/index.html"], "/tags/* /tag/:splat 301\n", "/tags/rust/", False, id="splat-missing"),
        pytest.param(["/tag/a/b/index.html"], "/tags/* /tag/:splat 301\n", "/tags/a/b/", True,
                     id="splat-spans-segments"),
        pytest.param(["/tag/a/index.html"], "/tags/:t/ /tag/:t/ 301\n", "/tags/a/", True, id="placeholder"),
        pytest.param(["/tag/b/index.html"], "/tags/:t/ /tag/:t/ 301\n", "/tags/a/", False, id="placeholder-missing"),
        pytest.param(["/tag/a/b/index.html"], "/tags/:t/ /tag/:t/ 301\n", "/tags/a/b/", False,
                     id="placeholder-is-one-segment"),
        pytest.param(["/b/docs/index.html"], "/a.py/* /b/:splat 301\n", "/a.py/docs/", True, id="dot-in-source"),
        pytest.param(["/b/docs/index.html"], "/a.py/* /b/:splat 301\n", "/aXpy/docs/", False, id="dot-is-literal"),
        pytest.param(["/a.html"], "/a.html /gone/ 301!\n", "/a.html", False, id="forced-rule-over-file"),
        pytest.param(["/a/index.html"], "/a/ /gone/ 200!\n", "/a/", False, id="forced-rewrite-over-directory"),
        pytest.param(["/a.html", "/b/index.html"], "/a.html /b/ 302!\n", "/a.html", True, id="forced-rule-to-page"),
        pytest.param(["/a.html"], "/a.html /gone/ 301\n", "/a.html", True, id="file-shadows-unforced-rule"),
        pytest.param(["/b/index.html"], "/a:8080/ /b/ 301\n", "/a:8080/", True, id="colon-digits-is-literal"),
        pytest.param(["/b/x/index.html"], "/:a/:a/ /b/:a/ 301\n", "/x/x/", True, id="repeated-placeholder"),
        pytest.param(["/b/x/index.html"], "/:a/:a/ /b/:a/ 301\n", "/x/y/", False, id="repeated-placeholder-differs"),
        pytest.param(["/c/index.html"], "/a*b/ /c/ 301\n", "/a*b/", True, id="inner-star-is-literal"),
        pytest.param(["/c/index.html"], "/a*b/ /c/ 301\n", "/axb/", False, id="inner-star-is-not-a-splat"),
        pytest.param(["/c/d/index.html"], "/a*b/* /c/:splat 301\n", "/a*b/d/", True, id="inner-and-trailing-star"),
        pytest.param(["/c/x/index.html"], "/a/*/b/* /c/:splat 301\n", "/a/*/b/x/", True, id="inner-star-segment"),
        pytest.param([], "https://h.example:8080/* https://www.nijho.lt/:splat 301!\n", "/gone/", False,
                     id="source-with-host-and-port"),
        pytest.param(["/z/index.html"], "/x%20y/ /z/ 301\n", "/x%20y/", True, id="redirect-on-raw-path"),
        pytest.param(["/z/index.html"], "/café/ /z/ 301\n", "/caf%C3%A9/", True, id="redirect-on-decoded-path"),
    ],
)
def test_resolves_files_directories_and_redirects(make_build, files, rules, path, expected):
    build = make_build("b", {file: "" for file in files} | {"/_redirects": rules})
    assert build.resolves(path) is expected


@pytest.mark.parametrize(
    ("files", "rules", "path", "expected"),
    [
        pytest.param(["/a.png"], "", "/a.png", ("/a.png", True), id="file"),
        pytest.param(["/a/index.html"], "", "/a/", ("/a/", True), id="directory-index"),
        pytest.param([], "", "/gone/", ("/gone/", False), id="missing"),
        pytest.param(["/c.png"], "/a/ /b/ 301\n/b/ /c.png 302\n", "/a/", ("/c.png", True), id="chain"),
        pytest.param(["/new/index.html"], "/old/ https://www.nijho.lt/new/?a=1 301\n", "/old/", ("/new/", True),
                     id="own-host-with-query"),
        pytest.param([], "/a/ /b/ 301\n/b/ /gone/ 301\n", "/a/", ("/gone/", False), id="chain-to-missing-page"),
        pytest.param(["/b.png"], "/a/ /b.png 301\n/b.png /gone/ 301!\n", "/a/", ("/gone/", False),
                     id="forced-rule-on-the-target"),
        pytest.param([], "/a/ /b/ 301\n/b/ https://nijho.lt/b/ 301\n", "/a/", ("https://nijho.lt/b/", False),
                     id="later-hop-to-another-host"),
        pytest.param(["/b/index.html"], "/a/ /b/ 404\n", "/a/", ("/a/", False), id="not-found-rule"),
    ],
)
def test_final_target_is_where_the_redirects_end_and_whether_a_file_is_served(make_build, files, rules, path, expected):
    build = make_build("b", {file: "" for file in files} | {"/_redirects": rules})
    assert build.final_target(path) == expected
