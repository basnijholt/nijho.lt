"""Icons for the Font Awesome and academicons markup in content, and the site's own shortcodes."""

import re

import pytest
import yaml

from helpers import CONTENT, TOOLS, require_hugo
from parity.build import BuildError, build_site, resolve_hugo
from parity.site import Build, read_utf8

REPO = TOOLS.parent
ICONS = REPO / "assets/icons"
# The pattern layouts/_partials/functions/content_icons.html uses, with only the icon name captured
ICON_CLASS_RE = re.compile(r"\b(?:fa[srb]?|ai) (?:fa|ai)-([a-z0-9-]+)")
FRONT_MATTER_ICON_RE = re.compile(r"^\s*-?\s*icon:\s*[\"']?([a-z0-9-]+)", re.MULTILINE)
MODIFIERS = {"fw", "lg", "2x", "3x", "li"}


def content_icon_names() -> set[str]:
    names = set()
    for file in CONTENT.rglob("*.md"):
        text = file.read_text(encoding="utf-8")
        names |= set(ICON_CLASS_RE.findall(text)) | set(FRONT_MATTER_ICON_RE.findall(text))
    return names - MODIFIERS


def test_every_content_icon_has_svg():
    names = content_icon_names()
    assert {"github", "google-scholar", "matrix", "university"} <= names
    assert sorted(n for n in names if not (ICONS / f"{n}.svg").exists()) == []


def mini_site(repo_root, root, page_body: str) -> Build:
    """Build a one-page site with this repo's icon partials, CSS pipeline and icons."""
    hugo = require_hugo(resolve_hugo(), "0.167.0", "HUGO_BIN")
    config = yaml.safe_load((repo_root / "config/_default/hugo.yaml").read_text(encoding="utf-8"))
    site_config = {"baseURL": "https://example.org/", "markup": config["markup"], "build": config["build"]}
    site_config["disableKinds"] = ["taxonomy", "term", "rss", "sitemap"]
    (root / "hugo.yaml").write_text(yaml.safe_dump(site_config), encoding="utf-8")
    for name in ("_partials/icon.html", "_partials/functions/content_icons.html", "_partials/head/css.html"):
        (root / "layouts" / name).parent.mkdir(parents=True, exist_ok=True)
        (root / "layouts" / name).write_text((repo_root / "layouts" / name).read_text(encoding="utf-8"))
    (root / "layouts/home.html").write_text(
        '{{ partial "head/css.html" . }}<p id="icon">{{ partial "icon.html" (dict "name" "github" "class" "big") }}</p>'
    )
    (root / "layouts/page.html").write_text("{{ .Content }}")
    for directory in ("assets/icons", "assets/css"):
        (root / directory).mkdir(parents=True)
        for file in (repo_root / directory).iterdir():
            (root / directory / file.name).write_bytes(file.read_bytes())
    (root / "content/post").mkdir(parents=True)
    (root / "content/post/index.md").write_text(f"---\ntitle: Post\n---\n\n{page_body}\n", encoding="utf-8")
    return Build(build_site(root, root / "public", production=False, hugo=hugo))


def test_unknown_icon_fails_build(repo_root, tmp_path):
    with pytest.raises(BuildError, match="not-an-icon"):
        mini_site(repo_root, tmp_path, '<em class="fas fa-not-an-icon fa-fw"></em>')


def test_icon_partial_inlines_svg(repo_root, tmp_path):
    build = mini_site(repo_root, tmp_path, '<em class="fab fa-github fa-fw"></em>')
    svg = build.soup("/index.html").select_one("#icon > svg")
    assert svg["class"] == ["icon", "big"]
    assert svg["aria-hidden"] == "true"
    assert svg.select_one("path")["d"]


def stylesheet(site: Build) -> str:
    href = site.soup("/index.html").select_one('link[rel="stylesheet"]')["href"]
    return (site.root / href.lstrip("/")).read_text(encoding="utf-8")


def test_icon_css_masks_content_icons(site):
    css = stylesheet(site)
    for name in ("github", "flask", "book", "university"):
        assert re.search(rf"\.fa-{name}\{{--icon:url\(", css), name
    assert ".ai-google-scholar{--icon:url(" in css
    assert "mask:var(--icon)" in css
    # Icons that only front matter names are inline SVGs, not CSS
    assert ".fa-matrix{" not in css and ".fa-key{" not in css


def pages_containing(site: Build, text: str) -> list[str]:
    return [page for page in site.pages if page.startswith("/post/") and text in read_utf8(site.root / page[1:])]


def test_site_shortcodes_render(site):
    plot = site.soup("/post/self-hosting-ai-is-not-cheaper/index.html")
    assert plot.select("figure.plot-figure .plot-container")
    tips = site.soup("/post/btrfs-to-zfs/index.html").select(".prose span.hover-tip[data-tooltip]")
    assert len(tips) == 5
    details = site.soup("/post/homelab-explained/index.html").select(".prose details > summary")
    assert len(details) >= 6
    clips = pages_containing(site, "demo-clip")
    assert len(clips) == 1
    figures = site.soup(clips[0]).select(".demo-clips figure")
    assert len(figures) == 3
    for figure in figures:
        assert figure.select_one("video.demo-clip-light") and figure.select_one("video.demo-clip-dark")
    bleed = pages_containing(site, "svg-bleed")
    assert len(bleed) == 1
    assert site.soup(bleed[0]).select_one(".svg-bleed-stage > svg")


def test_no_old_theme_selectors_left():
    files = [*(REPO / "assets/css").glob("*.css"), *(REPO / "layouts/_shortcodes").glob("*.html")]
    leftovers = [
        f"{file.name}: {pattern}"
        for file in files
        for pattern in ("body.dark", ".dark ", "article-style", "custom.scss", "scss/")
        if pattern in file.read_text(encoding="utf-8")
    ]
    assert leftovers == []
    assert not (REPO / "assets/scss").exists()
