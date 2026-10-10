"""Checks that URLs keep working: internal links and old resized images."""

import pytest

from helpers import bmp, page
from parity.checks import Finding, broken_internal_links, check_internal_links, check_old_images

PAGE = "/post/x/index.html"
# bmp(16, 16) and the source md5 and size that Hugo 0.123.3 puts in the names of its resizes (see test_old_images.py)
ORIGINAL, DIGEST, SIZE = bmp(16, 16), "3e42b460547f9240314cce9a8a6e4c9d", 822
OLD = f"/media/photo_hu{DIGEST}_{SIZE}_300x200_fit_q90_lanczos.webp"
OLD_NAME = OLD.removeprefix("/media/")
OLD_WITHOUT_SIZE = "/css/x_hu0123456789abcdef0123456789abcdef.png"


@pytest.mark.parametrize(
    ("html", "target"),
    [
        pytest.param(page('<a href="/gone/">x</a>'), "/gone/", id="a-href"),
        pytest.param(page('<a href="/gone/#part">x</a>'), "/gone/", id="a-href-with-fragment"),
        pytest.param(page(head='<link rel="stylesheet" href="/gone.css">'), "/gone.css", id="stylesheet-in-head"),
        pytest.param(page(head='<script src="/gone.js"></script>'), "/gone.js", id="script-in-head"),
        pytest.param(page('<iframe src="/gone.html"></iframe>'), "/gone.html", id="iframe-src"),
        pytest.param(page('<img src="/gone.png">'), "/gone.png", id="img-src"),
        pytest.param(page('<img src="/a.png" srcset="/a.png 1x, /gone.png 2x">'), "/gone.png", id="img-srcset"),
        pytest.param(page('<picture><source srcset="/gone.webp"></picture>'), "/gone.webp", id="source-srcset"),
        pytest.param(page('<video src="/a.mp4" poster="/gone.jpg"></video>'), "/gone.jpg", id="video-poster"),
        pytest.param(page('<a href="https://www.nijho.lt/gone/">x</a>'), "/gone/", id="own-host"),
        pytest.param(page('<img src="gone.png">'), "/post/x/gone.png", id="relative"),
        pytest.param(page('<a href="../gone/">x</a>'), "/post/gone/", id="parent-relative"),
    ],
)
def test_internal_links_reports_link_to_a_lost_path(make_build, html, target):
    files = {PAGE: html, "/a.png": "", "/a.mp4": ""}
    base = make_build("base", files | {target + ("index.html" if target.endswith("/") else ""): ""})
    cand = make_build("cand", files)
    assert check_internal_links(base, cand) == [Finding("internal-links", PAGE, f"{target} does not resolve")]


@pytest.mark.parametrize(
    "html",
    [
        pytest.param(
            '<a href="mailto:a@b.c">m</a><a href="tel:+31">t</a><a href="javascript:void(0)">j</a>'
            '<img src="data:image/png;base64,AAAA">',
            id="other-schemes",
        ),
        pytest.param(
            '<a href="https://example.com/x/">e</a><img src="//cdn.example.com/x.png">'
            '<img srcset="https://cdn.example.com/a.png 1x, //cdn.example.com/b.png 2x">',
            id="other-hosts",
        ),
        pytest.param('<a href="#top">top</a><a href="">empty</a>', id="fragment-and-empty"),
        pytest.param('<img src="/a.png?v=1"><a href="/post/x/#top">top</a>', id="query-and-fragment"),
        pytest.param('<a href="/old-post/x/">moved</a>', id="splat-redirect"),
    ],
)
def test_internal_links_skips_links_that_resolve_or_leave_the_site(make_build, html):
    build = make_build("site", {PAGE: page(html), "/a.png": "", "/_redirects": "/old-post/* /post/:splat 301\n"})
    assert broken_internal_links(build) == []


def test_internal_links_reports_known_broken_link_on_a_new_page(make_build):
    """A link broken in the baseline is only excused on the page that had it."""
    link = page('<a href="/gone/">x</a>')
    base = make_build("base", {"/a/index.html": link})
    cand = make_build("cand", {"/a/index.html": link, "/b/index.html": link})
    assert check_internal_links(base, cand) == [Finding("internal-links", "/b/index.html", "/gone/ does not resolve")]


NOT_ORIGINAL = f"which is not the original ({SIZE} bytes, Hugo fast md5 {DIGEST})"


@pytest.mark.parametrize(
    ("rules", "detail"),
    [
        pytest.param("", "no redirect", id="no-rule"),
        pytest.param(f"{OLD} /media/photo.bmp 301\n", None, id="redirect"),
        pytest.param(f"{OLD} /media/photo.bmp 302\n", None, id="temporary-redirect"),
        pytest.param(f"{OLD} /media/copy.bmp 301\n", None, id="original-under-another-name"),
        pytest.param(f"{OLD} https://www.nijho.lt/media/photo.bmp 301\n", None, id="absolute-target-on-site"),
        pytest.param(f"{OLD} /x/ 301\n/x/ /media/photo.bmp 301\n", None, id="chain-to-the-original"),
        pytest.param("/media/* /media/photo.bmp 301\n", None, id="splat-rule"),
        pytest.param("/media/:name /media/photo.bmp 301\n", None, id="placeholder-rule"),
        pytest.param(f"{OLD} / 301\n", f"redirects to /, {NOT_ORIGINAL}", id="home-page"),
        pytest.param(f"{OLD} /post/x/ 301\n", f"redirects to /post/x/, {NOT_ORIGINAL}", id="page"),
        pytest.param(
            f"{OLD} /media/photo.png/ 301\n", f"redirects to /media/photo.png/, {NOT_ORIGINAL}", id="directory"
        ),
        pytest.param(
            f"{OLD} /media/photo.webp 301\n", f"redirects to /media/photo.webp, {NOT_ORIGINAL}",
            id="same-stem-other-image",
        ),
        pytest.param(
            f"{OLD} /media/longer.bmp 301\n", f"redirects to /media/longer.bmp, {NOT_ORIGINAL}",
            id="same-fast-md5-other-size",
        ),
        pytest.param(
            "/media/* /img/:splat 301\n", f"redirects to /img/{OLD_NAME}, {NOT_ORIGINAL}", id="splat-target-is-a-copy"
        ),
        pytest.param(
            f"{OLD} /media/gone.webp 301\n", "redirects to /media/gone.webp, which does not resolve",
            id="target-missing",
        ),
        pytest.param(
            f"{OLD} /media/gone.webp 301\n{OLD} /media/photo.bmp 301\n",
            "redirects to /media/gone.webp, which does not resolve",
            id="first-rule-wins",
        ),
        pytest.param(
            f"/media/* /media/gone.webp 301\n{OLD} /media/photo.bmp 301\n",
            "redirects to /media/gone.webp, which does not resolve",
            id="earlier-splat-rule-wins",
        ),
        pytest.param(
            "/media/* /new/:splat 301\n", f"redirects to /new/{OLD_NAME}, which does not resolve",
            id="splat-target-missing",
        ),
        pytest.param(
            f"{OLD} /media/photo.bmp 301\n/media/photo.bmp /gone/ 301!\n",
            "redirects to /gone/, which does not resolve",
            id="forced-rule-on-the-target",
        ),
        pytest.param(f"{OLD} /media/photo.bmp 200\n", "rule for the old URL is a 200, not a redirect", id="rewrite"),
        pytest.param(f"{OLD} /media/photo.bmp 404\n", "rule for the old URL is a 404, not a redirect", id="not-found"),
        pytest.param(
            f"{OLD} https://elsewhere.example/p.webp 301\n",
            "redirects to https://elsewhere.example/p.webp, which leaves the site",
            id="target-on-another-host",
        ),
        pytest.param(
            f"{OLD} /x/ 301\n/x/ https://nijho.lt/media/photo.bmp 301\n",
            "redirects to https://nijho.lt/media/photo.bmp, which leaves the site",
            id="later-hop-to-the-apex-domain",
        ),
    ],
)
def test_old_images_need_a_redirect_to_their_original(make_build, rules, detail):
    """The original is a file of this site with the source size and Hugo fast md5 written in the old name."""
    base = make_build("base", {OLD: b"old"})
    files = {
        "/media/photo.bmp": ORIGINAL,
        "/media/copy.bmp": ORIGINAL,
        "/media/photo.webp": bmp(8, 8),
        # Files of 64 to 2048 bytes hash only their first 64 bytes, so this one shares the original's fast md5
        "/media/longer.bmp": ORIGINAL + b"x",
        f"/img/{OLD_NAME}": b"copy",
    }
    pages = dict.fromkeys(("/index.html", "/post/x/index.html", "/media/photo.png/index.html"), b"page")
    cand = make_build("cand", files | pages | {"/_redirects": rules})
    assert check_old_images(base, cand) == ([] if detail is None else [Finding("old-images", OLD, detail)])


def test_old_images_accept_names_without_the_source_stem(make_build):
    """Hugo 0.123.3 leaves the stem out of images resized from a long file name; the hash and size still match."""
    album = "/media/albums/cover"
    olds = [f"{album}/_hu{DIGEST}_{SIZE}_{suffix * 32}.webp" for suffix in "abc"]
    original = f"{album}/data__sweep__data_learner_0457.pickle.jpg"
    rules = "".join(f"{old} {original} 301\n" for old in olds)
    base = make_build("base", dict.fromkeys(olds, b"old"))
    cand = make_build("cand", {original: ORIGINAL, "/_redirects": rules})
    assert check_old_images(base, cand) == []


def test_old_images_need_a_size_in_the_old_name_to_prove_the_original(make_build):
    base = make_build("base", {OLD_WITHOUT_SIZE: b"old"})
    cand = make_build("cand", {"/media/photo.bmp": ORIGINAL, "/_redirects": f"{OLD_WITHOUT_SIZE} /media/photo.bmp\n"})
    detail = "redirects to /media/photo.bmp, but the old name has no source size to compare"
    assert check_old_images(base, cand) == [Finding("old-images", OLD_WITHOUT_SIZE, detail)]


def test_old_images_checks_only_missing_resized_images(make_build):
    base = make_build("base", {OLD: b"", "/media/plain.png": b""})
    cand = make_build("cand", {OLD: b""})
    assert check_old_images(base, cand) == []


@pytest.mark.parametrize(
    "old", [pytest.param(OLD, id="with-size"), pytest.param(OLD_WITHOUT_SIZE, id="without-size")]
)
def test_old_images_reports_resized_names_with_or_without_size(make_build, old):
    """check_paths skips both forms, and anything in a theme folder such as /css/, so only this check reports them."""
    base = make_build("base", {old: b""})
    assert check_old_images(base, make_build("cand", {})) == [Finding("old-images", old, "no redirect")]
