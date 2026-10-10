"""Checks that compare a baseline build with a candidate build and report what the candidate lost or changed."""

import copy
import difflib
import html
import json
import re
from collections import Counter
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from pathlib import PurePosixPath
from urllib.parse import unquote, urljoin, urlsplit

from bs4 import BeautifulSoup, Tag

from .old_images import HU_RE, hugo_fast_md5
from .site import UNCOMPARED, Build, Feed, Redirect, norm_url, off_site

PUBLIC_RE = re.compile(
    r"\.("
    r"html|xml|json|webmanifest|txt|asc|"
    r"png|jpg|jpeg|gif|svg|webp|"
    r"mp4|mov|py|js"
    r")$|^/_headers$|^/_redirects$"
)
# Theme assets, whose names change with the theme
EXCLUDE_PREFIXES = ("/css/", "/js/", "/webfonts/", "/en/js/")
CONTENT_PREFIXES = ("/post/", "/project/", "/publication/")
HOME_IDS = ("about", "blog-posts", "projects", "photography", "publications", "contact")
SEO_META = (
    "description", "robots", "og:title", "og:description", "og:type", "og:url", "og:image",
    "twitter:card", "twitter:site", "article:published_time", "article:modified_time",
)
JSONLD_KEYS = ("@type", "headline", "datePublished", "dateModified", "author")
DESCRIPTION_KEYS = ("description", "og:description")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)\s]*\)")
CODE_SPAN_RE = re.compile(r"`([^`]*)`")
# A pair of *, **, _ or __ around words: the opening marker starts a word and the closing one ends it, so snake_case
# and __init__.py keep their underscores
EMPHASIS_RE = re.compile(r"(?<![\w*_])(\*\*|__|\*|_)(?=\S)(.+?)(?<=\S)\1(?![\w*_])(?![.,;:!?)\]]\w)")
TYPOGRAPHY = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "…": "..."})
COUNTED_TAGS = ("img", "pre", "table", "video", "details")
# Elements whose text never runs into the text around them, whatever whitespace the markup has
BLOCK_TAGS = (
    "p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "tr", "pre", "div", "figure", "figcaption",
    "blockquote", "br", "dt", "dd", "details", "summary",
)
RESIZED_RE = re.compile(r"_hu[0-9a-f]{32}")
# text_diff shows up to TEXT_CONTEXT unchanged words around a change, changed runs of up to TEXT_WORDS words in full,
# and TEXT_LINES lines per text
TEXT_CONTEXT, TEXT_WORDS, TEXT_LINES = 3, 12, 20


@dataclass(frozen=True, order=True)
class Finding:
    """One difference: the check that found it, the site path and what changed."""
    check: str
    path: str
    detail: str


def check_paths(base: Build, cand: Build) -> list[Finding]:
    """Report baseline files missing from the candidate.

    Only page, feed, data, image and media files count (PUBLIC_RE). Theme assets are skipped because their names
    change with the theme, and _hu resized images because the old-images check covers them.
    """
    return [
        Finding("paths", path, "missing from candidate")
        for path in sorted(base.files - cand.files)
        if PUBLIC_RE.search(path) and not path.startswith(EXCLUDE_PREFIXES) and not RESIZED_RE.search(path)
    ]


def sitemap_locs_without_page(build: Build) -> list[str]:
    """Return the sorted sitemap locs ending in / without a percent-decoded index.html; a redirect is not a page."""
    return [
        loc for loc in sorted(build.sitemap_locs)
        if loc.endswith("/") and unquote(loc) + "index.html" not in build.files
    ]


def check_sitemap(base: Build, cand: Build) -> list[Finding]:
    """Report baseline locs missing from the candidate sitemap, and candidate locs without index.html
    unless the baseline loc lacked one too.
    """
    gone = base.sitemap_locs - cand.sitemap_locs
    missing = [Finding("sitemap", loc, "missing from candidate sitemap") for loc in gone]
    no_page = set(sitemap_locs_without_page(cand)) - set(sitemap_locs_without_page(base))
    lacking = [Finding("sitemap", loc, f"sitemap entry lacks {unquote(loc)}index.html") for loc in no_page]
    return sorted(missing + lacking)


def check_feeds(base: Build, cand: Build) -> list[Finding]:
    """Report baseline feeds that are missing or differ (see _feed_differences).

    Every difference is its own finding, so an allow rule can target exactly one.
    """
    findings = []
    for path in base.feeds:
        if path not in cand.files:
            findings.append(Finding("feeds", path, "missing from candidate"))
        else:
            details = _feed_differences(base.feed(path), cand.feed(path))
            findings += [Finding("feeds", path, detail) for detail in details]
    return sorted(findings)


def _feed_differences(base: Feed, cand: Feed) -> list[str]:
    """Compare channel title and link, raw guids byte for byte, item links, and per item its title, pubDate and text.

    Text differences are capped per feed like those of one text (see text_diff).
    """
    details = []
    if base.title != cand.title:
        details.append(f"channel title: {base.title!r} -> {cand.title!r}")
    if base.link != cand.link:
        details.append(f"channel link: {base.link!r} -> {cand.link!r}")

    base_guids = Counter(item.raw_guid for item in base.items)
    cand_guids = Counter(item.raw_guid for item in cand.items)
    details += [f"missing guid {guid!r}" for guid in sorted(base_guids.keys() - cand_guids.keys())]
    details += [f"extra guid {guid!r}" for guid in sorted(cand_guids.keys() - base_guids.keys())]
    details += [
        f"duplicate guid: {guid!r} ({count} items)"
        for guid, count in sorted(cand_guids.items())
        if count > 1 and count > base_guids[guid]
    ]

    base_links = {item.link for item in base.items}
    cand_links = {item.link for item in cand.items}
    details += [f"missing link {link!r}" for link in sorted(base_links - cand_links)]
    details += [f"extra link {link!r}" for link in sorted(cand_links - base_links)]

    # Pair items by normalized guid, so an item whose guid only changed host is still compared
    cand_items = {item.guid: item for item in cand.items}
    texts = []
    for guid, old in {item.guid: item for item in base.items}.items():
        new = cand_items.get(guid)
        if new is None:
            continue
        if old.title != new.title:
            details.append(f"item {guid!r} title: {old.title!r} -> {new.title!r}")
        if not _same_instant(old.pub_date, new.pub_date):
            details.append(f"item {guid!r} pubDate: {old.pub_date!r} -> {new.pub_date!r}")
        texts += [f"item {guid!r} {line}" for line in _text_runs(old.text, new.text)]
    return details + _capped(texts)


def _same_instant(base: str, cand: str) -> bool:
    """Whether two RFC 2822 dates name the same instant; unparsable dates must be equal strings."""
    if base == cand:
        return True
    try:
        return parsedate_to_datetime(base) == parsedate_to_datetime(cand)
    except ValueError:
        return False


def text_diff(base: str, cand: str) -> list[str]:
    """Describe every run of words that differs, one line each, so an allow rule matches one run and nothing else.

    After TEXT_LINES lines, one more line counts the rest.
    """
    return _capped(_text_runs(base, cand))


def _capped(lines: list[str]) -> list[str]:
    """Return the first TEXT_LINES text differences, plus a line counting the rest."""
    if len(lines) > TEXT_LINES:
        return lines[:TEXT_LINES] + [f"text: {len(lines) - TEXT_LINES} more differences"]
    return lines


def _text_runs(base: str, cand: str) -> list[str]:
    """Return one line per run of words that differs, with up to TEXT_CONTEXT unchanged words on each side."""
    old, new = base.split(), cand.split()
    opcodes = difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes()
    lines = []
    # SequenceMatcher puts an equal run between any two changed runs, so context never spans another change
    for index, (tag, i1, i2, j1, j2) in enumerate(opcodes):
        if tag == "equal":
            continue
        start = opcodes[index - 1][1] if index else i1
        end = opcodes[index + 1][2] if index + 1 < len(opcodes) else i2
        before, after = old[max(start, i1 - TEXT_CONTEXT) : i1], old[i2 : min(end, i2 + TEXT_CONTEXT)]
        lines.append(
            f"text: {' '.join(before + _shorten(old[i1:i2]) + after)!r} -> "
            f"{' '.join(before + _shorten(new[j1:j2]) + after)!r}"
        )
    return lines


def _shorten(words: list[str]) -> list[str]:
    """Return words; a run longer than TEXT_WORDS keeps its first and last half and counts the words between."""
    if len(words) <= TEXT_WORDS:
        return words
    half = TEXT_WORDS // 2
    return words[:half] + [f"[{len(words) - 2 * half} words]"] + words[-half:]


def article_root(soup: BeautifulSoup) -> Tag | None:
    """Return the article body: .prose in the new theme, .article-style in the old one."""
    return soup.select_one(".prose") or soup.select_one(".article-style")


def check_ids(base: Build, cand: Build) -> list[Finding]:
    """Report ids a candidate page lacks: every id in the baseline article body, and all HOME_IDS on /index.html."""
    findings = []
    for path in base.pages:
        root = article_root(base.soup(path))
        wanted = {tag["id"] for tag in root.find_all(id=True)} if root else set()
        if path == "/index.html":
            wanted.update(HOME_IDS)
        if not wanted:
            continue
        present = {tag["id"] for tag in cand.soup(path).find_all(id=True)} if path in cand.files else set()
        findings += [Finding("ids", path, f"missing ID: {id_}") for id_ in wanted - present]
    return sorted(findings)


def seo_fields(soup: BeautifulSoup, markdown: bool = False) -> dict[str, str]:
    """Return a page's <head> title, SEO_META tags (by name or property), canonical, RSS links and JSON-LD fields.

    The URL values (canonical, og:url, og:image and feeds) are normalized to paths and the descriptions to plain text;
    with markdown, the descriptions are Markdown whose syntax is stripped too.
    """
    fields = {}
    # Inline SVGs in the body have a <title> of their own
    if soup.head and (title := soup.head.find("title")):
        fields["title"] = title.get_text(strip=True)
    for meta in soup.find_all("meta"):
        key = meta.get("name") or meta.get("property")
        if key in SEO_META:
            fields[key] = meta.get("content", "")
    for key in ("og:url", "og:image"):
        if key in fields:
            fields[key] = norm_url(fields[key])
    for key in DESCRIPTION_KEYS:
        if key in fields:
            fields[key] = _plain_text(fields[key], markdown=markdown)
    if canonical := soup.find("link", rel="canonical", href=True):
        fields["canonical"] = norm_url(canonical["href"])
    if feeds := soup.find_all("link", rel="alternate", type="application/rss+xml", href=True):
        fields["feeds"] = ",".join(sorted(norm_url(link["href"]) for link in feeds))
    jsonld = _jsonld(soup)
    for key in JSONLD_KEYS:
        if key in jsonld:
            value = jsonld[key]
            if key == "author" and isinstance(value, dict):
                value = value.get("name", str(value))
            fields[f"jsonld:{key}"] = str(value)
    return fields


def _plain_text(text: str, markdown: bool = False) -> str:
    """Unescape entities, straighten typographic quotes, dashes and ellipses, and collapse whitespace.

    With markdown, also keep only the text of links, code spans and emphasis (see _strip_markdown).
    """
    text = html.unescape(text)
    if markdown:
        text = _strip_markdown(text)
    return " ".join(re.sub(r"-{2,}", "-", text.translate(TYPOGRAPHY)).split())


def _strip_markdown(text: str) -> str:
    """Keep the text of links, code spans and emphasis pairs; code spans keep their * and _ as written."""
    parts = CODE_SPAN_RE.split(MARKDOWN_LINK_RE.sub(r"\1", text))
    return "".join(part if index % 2 else _strip_emphasis(part) for index, part in enumerate(parts))


def _strip_emphasis(text: str) -> str:
    """Remove emphasis pairs (EMPHASIS_RE), outer pairs first, until none is left."""
    while (stripped := EMPHASIS_RE.sub(r"\2", text)) != text:
        text = stripped
    return text


def _jsonld(soup: BeautifulSoup) -> dict:
    """Return the first JSON-LD object with a headline, else the first object, else {}."""
    objects = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(data, dict):
            objects.append(data)
    return next((obj for obj in objects if "headline" in obj), objects[0] if objects else {})


def check_seo(base: Build, cand: Build) -> list[Finding]:
    """Report every seo_fields value that differs on a page both builds have.

    Only the baseline's descriptions are read as Markdown, so Markdown syntax in the candidate's is reported.
    """
    findings = []
    for path in base.pages:
        if path not in cand.files:
            continue
        old, new = seo_fields(base.soup(path), markdown=True), seo_fields(cand.soup(path))
        findings += [
            Finding("seo", path, f"{key}: {old.get(key, '')!r} -> {new.get(key, '')!r}")
            for key in old.keys() | new.keys()
            if old.get(key, "") != new.get(key, "")
        ]
    return sorted(findings)


def _body(root: Tag) -> tuple[str, dict[str, int]]:
    """Return an article body's text and COUNTED_TAGS counts, without the UNCOMPARED parts.

    A space goes around every BLOCK_TAGS element, so whether the markup puts whitespace between two blocks does not
    matter, while a space lost or added next to a link or other inline element does. Highlighted code keeps its text
    as written, because Chroma versions split it into spans at different places.
    """
    root = copy.copy(root)  # Build.soup results are shared
    for tag in root.select(UNCOMPARED):
        tag.decompose()
    for code in root.select("pre.chroma"):
        code.string = code.get_text()
    for tag in root.find_all(BLOCK_TAGS):
        tag.insert_before(" ")
        tag.insert_after(" ")
    return " ".join(root.get_text().split()), {name: len(root.find_all(name)) for name in COUNTED_TAGS}


def check_content(base: Build, cand: Build) -> list[Finding]:
    """Compare the article bodies of posts, projects and publications that both builds have."""
    findings = []
    for path in base.pages:
        if not path.startswith(CONTENT_PREFIXES) or path not in cand.files:
            continue
        base_root = article_root(base.soup(path))
        if base_root is None:
            continue
        cand_root = article_root(cand.soup(path))
        if cand_root is None:
            findings.append(Finding("content", path, "article root missing in candidate"))
            continue
        (base_text, base_counts), (cand_text, cand_counts) = _body(base_root), _body(cand_root)
        findings += [Finding("content", path, line) for line in text_diff(base_text, cand_text)]
        findings += [
            Finding("content", path, f"{tag} count: {base_counts[tag]} -> {cand_counts[tag]}")
            for tag in COUNTED_TAGS
            if base_counts[tag] != cand_counts[tag]
        ]
    return sorted(findings)


def check_old_images(base: Build, cand: Build) -> list[Finding]:
    """Report baseline _hu images the candidate lacks, unless the rule Netlify applies to the old path is a 3xx and the
    redirects end at the original: a file of this site with the source size and Hugo fast md5 in the old name.

    A redirect off the site is reported too: nothing here can tell whether it serves the image.
    """
    findings = []
    for path in sorted(base.files - cand.files):
        name = PurePosixPath(path).name
        if not RESIZED_RE.search(name):
            continue
        rule, _ = cand.redirect(path)
        target, served = cand.final_target(path)
        source = HU_RE.search(name)
        if rule is None:
            detail = "no redirect"
        elif not 300 <= rule.status < 400:
            detail = f"rule for the old URL is a {rule.status}, not a redirect"
        elif off_site(target):
            detail = f"redirects to {target}, which leaves the site"
        elif not served:
            detail = f"redirects to {target}, which does not resolve"
        elif source is None:
            detail = f"redirects to {target}, but the old name has no source size to compare"
        elif not _is_original(cand, target, source[1], int(source[2])):
            detail = f"redirects to {target}, which is not the original ({source[2]} bytes, Hugo fast md5 {source[1]})"
        else:
            continue
        findings.append(Finding("old-images", path, detail))
    return findings


def _is_original(build: Build, path: str, md5: str, size: int) -> bool:
    """Whether path is a file of build with this size in bytes and this Hugo 0.123.3 fast md5."""
    decoded = unquote(path)
    if decoded not in build.files:
        return False
    file = build.root / decoded.lstrip("/")
    return file.stat().st_size == size and hugo_fast_md5(file) == md5


def _link_urls(soup: BeautifulSoup) -> list[str]:
    """Return every URL a page links to or loads: href, src, img and source srcset, and video poster."""
    urls = [tag["href"] for tag in soup.find_all(href=True)]
    urls += [tag["src"] for tag in soup.find_all(src=True)]
    # Hugo's srcset URLs never contain commas, so a plain split is enough
    urls += [
        candidate.split()[0]
        for tag in soup.find_all(["img", "source"], srcset=True)
        for candidate in tag["srcset"].split(",")
        if candidate.strip()
    ]
    urls += [tag["poster"] for tag in soup.find_all("video", poster=True)]
    return urls


def _internal_path(url: str, page: str) -> str | None:
    """Return the site path a URL on page points to, without query or fragment.

    Return None for a bare #fragment, another host or another scheme.
    """
    url = url.strip()
    if not url or url.startswith("#"):
        return None
    url = norm_url(url)
    if off_site(url):
        return None
    return urlsplit(urljoin(page, url)).path


def broken_internal_links(build: Build) -> list[Finding]:
    """Return every link (see _link_urls) to a path on this site that does not resolve."""
    findings = set()
    for page in build.pages:
        for url in _link_urls(build.soup(page)):
            path = _internal_path(url, page)
            if path is not None and not build.resolves(path):
                findings.add(Finding("internal-links", page, f"{path} does not resolve"))
    return sorted(findings)


def check_internal_links(base: Build, cand: Build) -> list[Finding]:
    """Report broken links in the candidate unless the same link on the same baseline page was broken already."""
    return sorted(set(broken_internal_links(cand)) - set(broken_internal_links(base)))


def check_redirects(base: Build, cand: Build) -> list[Finding]:
    """Report baseline redirect rules (source, target, status and force) that the candidate lacks, and those whose
    source another rule than in the baseline matches first.

    A rule shadowed in the baseline may be shadowed by another rule only if the baseline's shadowing rule is gone too.
    """
    findings = set()
    for rule in base.redirects:
        first, _ = cand.redirect(rule.source)
        base_first, _ = base.redirect(rule.source)
        if rule not in cand.redirects:
            findings.add(Finding("redirects", rule.source, f"missing redirect to {_rule_text(rule)}"))
        elif first == base_first:
            continue
        elif base_first == rule:
            detail = f"redirect to {_rule_text(rule)} is shadowed by {first.source} {_rule_text(first)}"
            findings.add(Finding("redirects", rule.source, detail))
        elif base_first in cand.redirects:
            detail = (
                f"redirect to {_rule_text(rule)} was shadowed by {base_first.source} {_rule_text(base_first)}, "
                f"now by {first.source} {_rule_text(first)}"
            )
            findings.add(Finding("redirects", rule.source, detail))
    return sorted(findings)


def _rule_text(rule: Redirect) -> str:
    return f"{rule.target} {rule.status}{'!' if rule.force else ''}"


ALL_CHECKS = {
    "paths": check_paths,
    "sitemap": check_sitemap,
    "feeds": check_feeds,
    "ids": check_ids,
    "seo": check_seo,
    "content": check_content,
    "old-images": check_old_images,
    "internal-links": check_internal_links,
    "redirects": check_redirects,
}
