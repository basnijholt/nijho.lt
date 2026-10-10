"""Read a finished Hugo build: files, pages, sitemap, RSS feeds and Netlify redirects."""

import re
from dataclasses import dataclass
from functools import cache, cached_property
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

from . import ParityError

SITE_ORIGINS = ("https://www.nijho.lt", "http://www.nijho.lt", "//www.nijho.lt")
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
# A Netlify status token: three digits, with ! glued on for a forced rule
STATUS_RE = re.compile(r"(\d{3})(!?)")
# How many redirect rules Build.final_target follows before giving up
REDIRECT_HOPS = 10
# A redirect placeholder: a colon, a letter, then letters, digits or underscores, so :8080 is literal
PLACEHOLDER_RE = re.compile(r":([A-Za-z][A-Za-z0-9_]*)")


def norm_url(url: str) -> str:
    """Turn a www.nijho.lt URL into a root-relative one; leave relative URLs and other hosts unchanged."""
    for origin in SITE_ORIGINS:
        rest = url.removeprefix(origin)
        if rest != url and rest[:1] in ("", "/", "?", "#"):
            return rest if rest.startswith("/") else "/" + rest
    return url


def off_site(url: str) -> bool:
    """Whether a URL has a scheme or a host, so it points away from this site's paths."""
    parts = urlsplit(url)
    return bool(parts.scheme or parts.netloc)


def read_utf8(file: Path) -> str:
    """Return the text of a UTF-8 file; raise ParityError naming it if it is not UTF-8."""
    try:
        return Path(file).read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise ParityError(f"{file}: invalid UTF-8 at byte {e.start}: {e.reason}") from None


def parse_sitemap(xml: str, source: str) -> list[str]:
    """Return the normalized <loc> URLs of a sitemap, in order; raise ParityError naming source if it is not XML."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        raise ParityError(f"{source}: invalid XML: {e}") from None
    return [norm_url(loc.text) for loc in root.iterfind(".//sm:loc", SITEMAP_NS) if loc.text]


@dataclass(frozen=True)
class FeedItem:
    """An RSS item: guid and link normalized, raw_guid as written, text the description as collapsed plain text."""
    title: str
    link: str
    guid: str
    text: str
    raw_guid: str
    pub_date: str


@dataclass(frozen=True)
class Feed:
    """An RSS channel with its link normalized."""
    title: str
    link: str
    items: tuple[FeedItem, ...]


@dataclass(frozen=True)
class Redirect:
    """One _redirects rule."""
    source: str
    target: str
    status: int
    force: bool


class Build:
    """A finished Hugo build; everything is read once, so later changes on disk go unnoticed."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self._soups: dict[str, BeautifulSoup] = {}

    @cached_property
    def files(self) -> frozenset[str]:
        """Every file as a root-relative path."""
        return frozenset("/" + p.relative_to(self.root).as_posix() for p in self.root.rglob("*") if p.is_file())

    @cached_property
    def pages(self) -> tuple[str, ...]:
        """The .html files, sorted."""
        return tuple(sorted(f for f in self.files if f.endswith(".html")))

    @cached_property
    def feeds(self) -> tuple[str, ...]:
        """The index.xml files, sorted."""
        return tuple(sorted(f for f in self.files if f.endswith("index.xml")))

    @cached_property
    def sitemap_locs(self) -> frozenset[str]:
        """The normalized <loc> URLs of /sitemap.xml."""
        sitemap = self.root / "sitemap.xml"
        return frozenset(parse_sitemap(read_utf8(sitemap), str(sitemap)) if sitemap.exists() else ())

    @cached_property
    def redirects(self) -> tuple[Redirect, ...]:
        """The /_redirects rules; the status defaults to 301."""
        file = self.root / "_redirects"
        if not file.exists():
            return ()
        rules = []
        for line in read_utf8(file).splitlines():
            parts = line.split()
            if len(parts) < 2 or parts[0].startswith("#"):
                continue
            status, force = 301, False
            for part in parts[2:]:
                if match := STATUS_RE.fullmatch(part):
                    status, force = int(match[1]), bool(match[2])
                    break
            rules.append(Redirect(parts[0], parts[1], status, force))
        return tuple(rules)

    def soup(self, path: str) -> BeautifulSoup:
        """Parse a page once; callers must not modify the result."""
        if path not in self._soups:
            self._soups[path] = BeautifulSoup(read_utf8(self.root / path.lstrip("/")), "lxml")
        return self._soups[path]

    def feed(self, path: str) -> Feed:
        """Parse an RSS 2.0 feed."""
        file = self.root / path.lstrip("/")
        try:
            channel = ET.parse(file).getroot().find("channel")
        except ET.ParseError as e:
            raise ParityError(f"{file}: invalid XML: {e}") from None
        if channel is None:
            raise ParityError(f"{file} has no <channel>; not an RSS 2.0 feed")
        items = tuple(
            FeedItem(
                title=item.findtext("title", ""),
                link=norm_url(item.findtext("link", "")),
                guid=norm_url(item.findtext("guid", "")),
                text=" ".join(BeautifulSoup(item.findtext("description", ""), "lxml").get_text().split()),
                raw_guid=item.findtext("guid", ""),
                pub_date=item.findtext("pubDate", ""),
            )
            for item in channel.iterfind("item")
        )
        return Feed(channel.findtext("title", ""), norm_url(channel.findtext("link", "")), items)

    def resolves(self, path: str) -> bool:
        """Whether a path serves a file, directly or after redirects, or redirects to another host."""
        target, served = self.final_target(path)
        return served or off_site(target)

    def final_target(self, path: str, hops: int = REDIRECT_HOPS) -> tuple[str, bool]:
        """Follow the rules Netlify applies from path; return where they end and whether a file of this site is served.

        A path that is a file or a directory with index.html, looked up percent-decoded, is served unless its rule is
        forced (!). Otherwise a 3xx or 200 rule leads on to its target path, or ends at a URL on another host; any other
        status ends at the path, and so does running out of hops, which ends a loop.
        """
        decoded = unquote(path)
        rule, target = self.redirect(path)
        exists = decoded in self.files or (decoded.endswith("/") and decoded + "index.html" in self.files)
        if exists and not (rule and rule.force):
            return path, True
        if rule is None or hops == 0 or not (rule.status == 200 or 300 <= rule.status < 400):
            return path, False
        target = norm_url(target)
        if off_site(target):
            return target, False
        return self.final_target(urlsplit(target).path, hops - 1)

    def redirect(self, path: str) -> tuple[Redirect | None, str]:
        """Return the rule Netlify applies to a path and its target with :splat and placeholders filled in.

        That is the first rule whose source matches the raw or the percent-decoded path; (None, "") if none does.
        """
        for rule in self.redirects:
            for candidate in (path, unquote(path)):
                if match := _redirect_regex(rule.source).fullmatch(candidate):
                    return rule, _fill(rule.target, match.groupdict())
        return None, ""


def _fill(target: str, values: dict[str, str]) -> str:
    """Put splat and placeholder values into a redirect target; a placeholder without a value stays as written."""
    return PLACEHOLDER_RE.sub(lambda m: values.get(m[1], m[0]), target)


@cache
def _redirect_regex(source: str) -> re.Pattern[str]:
    """Compile a Netlify redirect source: a trailing * is the splat and :name one path segment, captured by name.

    A repeated name must match the same text again. Any other * is literal, and so is everything else.
    """
    splat = source.endswith("*")
    parts, names = [], set()
    # re.split with one group alternates literal text and placeholder names
    for index, token in enumerate(PLACEHOLDER_RE.split(source.removesuffix("*") if splat else source)):
        if index % 2 == 0:
            parts.append(re.escape(token))
        else:
            parts.append(f"(?P={token})" if token in names else f"(?P<{token}>[^/]+)")
            names.add(token)
    if splat:
        parts.append("(?P=splat)" if "splat" in names else "(?P<splat>.*)")
    return re.compile("".join(parts))
