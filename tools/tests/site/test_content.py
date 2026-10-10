"""Article bodies: the heading, link, image and Mermaid render hooks, the content shortcodes, and the parity of article
text and anchors with the baseline."""

import re

from helpers import CONTENT, page_url

# An <a> written as HTML in the Markdown, which the link render hook never sees
RAW_LINK_RE = re.compile(r'<a href="(http[^"]+)"')
SRCSET_RE = re.compile(r"(\S+) (\d+)w")
# ref shortcodes give absolute links to this site, which the link render hook sees as placeholders
SITE = "https://www.nijho.lt/"


def sources(pattern: str) -> dict[str, str]:
    """Map the page of every Markdown file matching pattern to the file's text; the homepage sections are left out."""
    found = {}
    for file in sorted(CONTENT.rglob("*.md")):
        text = file.read_text(encoding="utf-8")
        if not file.is_relative_to(CONTENT / "home") and re.search(pattern, text):
            found[page_url(file) + "index.html"] = text
    return found


def prose(site, path: str):
    root = site.soup(path).select_one(".prose")
    assert root is not None, f"{path} has no .prose"
    return root


def test_ids_parity_clean(failures):
    assert failures("ids") == []


def test_content_parity_clean(failures):
    assert failures("content") == []


def test_heading_anchors(site):
    pages = sources(r"(?m)^#{2,3} ")
    assert pages
    for path in pages:
        for heading in prose(site, path).find_all(["h2", "h3"]):
            anchor = heading.find("a", class_="anchor")
            assert anchor["href"] == "#" + heading["id"], path
            assert anchor["aria-label"] == "Link to this section"


def test_callout_renders_markdown(site):
    pages = sources(r"\{\{% callout")
    assert pages
    rendered = []
    for path, text in pages.items():
        callouts = prose(site, path).select("aside.callout")
        kinds = re.findall(r"\{\{% callout (\w+) %\}\}", text)
        assert [c["class"] for c in callouts] == [["callout", f"callout-{kind}"] for kind in kinds], path
        for callout in callouts:
            assert callout.find("svg", attrs={"aria-hidden": "true"}), path
            assert not re.search(r"`|\]\(|\*\*", callout.get_text()), path
        rendered += callouts
    assert {"callout-note", "callout-warning"} <= {c["class"][1] for c in rendered}
    assert any(c.find("code") for c in rendered) and any(c.find("a") for c in rendered)


def test_figure_srcset_and_lazy(site):
    pages = sources(r"\{\{< figure |!\[")
    assert pages
    kinds = set()
    for path, text in pages.items():
        root = prose(site, path)
        images = [img for img in root.select("img[data-zoomable]") if not img.find_parent(class_="gallery")]
        assert len(images) == len(re.findall(r"\{\{< figure |!\[", text)), path
        assert len(root.select("figure > img")) >= text.count("{{< figure "), path
        for img in images:
            assert img["loading"] == "lazy" and img.has_attr("data-zoomable") and img.has_attr("alt"), path
            src = img["src"]
            if src.startswith("https://"):
                kinds.add("remote")
                assert not img.has_attr("srcset"), path
            elif src.endswith((".svg", ".gif")):
                kinds.add("original")
                assert src in site.files and not img.has_attr("srcset"), path
            else:
                kinds.add("raster")
                candidates = {url: int(width) for url, width in SRCSET_RE.findall(img["srcset"])}
                assert 1 <= len(candidates) <= 3 and len(set(candidates.values())) == len(candidates), path
                assert all(url.endswith(".webp") and url in site.files for url in candidates), path
                assert max(candidates.values()) <= 1200, path
                src_width = max(width for width in candidates.values() if width <= 760)
                assert candidates.get(src) == src_width == int(img["width"]) and int(img["height"]) > 0, path
    assert kinds == {"remote", "original", "raster"}


def test_video_autoplay_loop_attrs(site):
    pages = sources(r"\{\{< video [^>]*autoplay")
    assert pages
    for path, text in pages.items():
        videos = prose(site, path).select("video:has(source)")
        videos = {video.source["src"].rsplit("/", 1)[-1]: video for video in videos}
        for src in re.findall(r'\{\{< video [^>]*src="([^"]+)"', text):
            video = videos[src]
            assert all(video.has_attr(a) for a in ("autoplay", "muted", "playsinline", "loop", "controls")), path
            assert video.source["src"] in site.files and video.source["type"] == "video/mp4", path


def test_toc_open(site):
    pages = sources(r"\{\{< toc >\}\}")
    assert pages
    for path in pages:
        tocs = prose(site, path).select("details.toc")
        assert len(tocs) == 1 and tocs[0].has_attr("open"), path
        assert tocs[0].summary.get_text(strip=True) == "Table of contents"
        assert tocs[0].select("nav#TableOfContents a[href^='#']"), path


def test_external_links_target_blank(site):
    raw = {url for file in CONTENT.rglob("*.md") for url in RAW_LINK_RE.findall(file.read_text(encoding="utf-8"))}
    external = 0
    for path in site.pages:
        root = site.soup(path).select_one(".prose")
        for link in root.find_all("a", href=True) if root else []:
            href = link["href"]
            if href.startswith(SITE):
                continue
            if href.startswith("http") and href not in raw:
                external += 1
                assert link.get("target") == "_blank" and "noopener" in link.get("rel", []), (path, href)
            elif href.startswith(("/", "#")):
                assert not link.has_attr("target"), (path, href)
    assert external > 1000


def test_mermaid_only_where_used(site):
    pages = sources(r"```mermaid")
    assert pages
    for path in site.pages:
        soup = site.soup(path)
        diagrams = soup.select("pre.mermaid")
        loaders = [s for s in soup.find_all("script", type="module") if "/npm/mermaid@" in (s.string or "")]
        if path in pages:
            assert len(diagrams) == pages[path].count("```mermaid") and len(loaders) == 1, path
            assert all(d.get_text().strip() for d in diagrams), path
        else:
            assert diagrams == [] and loaders == [], path


def test_gallery_links_originals_at_baseline_paths(site, baseline):
    pages = sources(r"\{\{< gallery ")
    assert pages
    for path, text in pages.items():
        album = re.search(r'\{\{< gallery album="([^"]+)"', text)[1]
        links = prose(site, path).select(".gallery a")
        assert len(links) == len(list((CONTENT.parent / "assets/media/albums" / album).iterdir())), path
        for link in links:
            assert link["href"] in baseline.files and link["href"] in site.files, link["href"]
            img = link.img
            assert img["src"].endswith(".webp") and img["src"] in site.files
            assert int(img["width"]) <= 350 and int(img["height"]) <= 250
            assert img["loading"] == "lazy" and img.has_attr("data-zoomable")
