"""Builders shared by the tests: small hand-written sites, RSS and sitemaps, images and a fake Hugo.

They live here rather than in conftest.py because pytest swaps the module named conftest whenever it loads another
conftest.py, such as site/conftest.py, so `from conftest import ...` would pick the wrong file.
"""

import re
import shlex
import struct
from pathlib import Path

import pytest
import yaml

from parity.build import BuildError, get_hugo_version
from parity.site import Build

TOOLS = Path(__file__).resolve().parents[1]
CONTENT = TOOLS.parent / "content"


def write_build(root: Path, files: dict[str, str | bytes]) -> Build:
    """Write files (site path -> content) under root and return the Build."""
    root.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        path = root / rel.lstrip("/")
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
    return Build(root)


def page_url(file: Path) -> str:
    """The URL path of a content page: its bundle directory or file name, or the `slug:` in its front matter."""
    path = file.parent if file.name in ("index.md", "_index.md") else file.with_suffix("")
    text = file.read_text(encoding="utf-8")
    front_matter = yaml.safe_load(text.split("---", 2)[1]) if text.startswith("---") else {}
    if slug := front_matter.get("slug"):
        path = path.with_name(slug)
    return f"/{path.relative_to(CONTENT).as_posix()}/"


def page(body: str = "", *, head: str = "<title>T</title>") -> str:
    return f"<!DOCTYPE html><html><head>{head}</head><body>{body}</body></html>"


def item(slug: str, **overrides: str) -> dict[str, str]:
    """An RSS item for /post/<slug>/ with Hugo's guid and link shapes."""
    return {
        "title": f"Post {slug}",
        "link": f"https://www.nijho.lt/post/{slug}/",
        "guid": f"/post/{slug}/",
        "date": "Mon, 01 Jan 2024 00:00:00 +0000",
        "description": f"Text of {slug}",
    } | overrides


def rss(items: list[dict[str, str]], *, title: str = "Posts", link: str = "https://www.nijho.lt/post/") -> str:
    body = "".join(
        f"<item><title>{i['title']}</title><link>{i['link']}</link><pubDate>{i['date']}</pubDate>"
        f"<guid>{i['guid']}</guid><description>{i['description']}</description></item>"
        for i in items
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?><rss version="2.0"><channel>'
        f"<title>{title}</title><link>{link}</link>{body}</channel></rss>"
    )


def sitemap(paths: list[str]) -> str:
    """A sitemap listing https://www.nijho.lt<path> for each path."""
    urls = "".join(f"<url><loc>https://www.nijho.lt{path}</loc></url>" for path in paths)
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    )


def bmp(width: int, height: int) -> bytes:
    """A deterministic 24-bit BMP image (54-byte header, rows padded to 4 bytes)."""
    row = (3 * width + 3) // 4 * 4
    pixels = bytearray()
    for y in range(height):
        line = bytearray((x * 31 + y * 17 + c * 7) % 256 for x in range(width) for c in range(3))
        pixels += line + bytes(row - len(line))
    header = b"BM" + struct.pack("<IHHI", 54 + len(pixels), 0, 0, 54)
    info = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, len(pixels), 2835, 2835, 0, 0)
    return header + info + bytes(pixels)


def fake_hugo(path: Path, marker: Path, *, version: str = "0.0.0", payload: str = "test", exit_code: int = 0) -> str:
    """Write a fake hugo and return its path.

    `hugo version` prints `hugo v<version>`. A build writes its name, arguments and Hugo environment as key=value
    lines to marker, and payload to <-d>/index.html, then exits with exit_code.
    """
    path.write_text(
        "#!/usr/bin/env bash\n"
        f'if [ "$1" = "version" ]; then echo "hugo v{version} fake"; exit 0; fi\n'
        "{\n"
        f"  echo name={shlex.quote(path.name)}\n"
        '  echo "args=$*"\n'
        '  echo "HUGO_ENV=$HUGO_ENV"\n'
        '  echo "HUGO_ENABLEGITINFO=$HUGO_ENABLEGITINFO"\n'
        '  echo "HUGO_RESOURCEDIR=$HUGO_RESOURCEDIR"\n'
        '  [ -d "$HUGO_RESOURCEDIR" ] && echo "resourcedir_exists=yes"\n'
        f"}} > {shlex.quote(str(marker))}\n"
        "while [ $# -gt 0 ]; do\n"
        f'  if [ "$1" = "-d" ]; then mkdir -p "$2"; echo {shlex.quote(payload)} > "$2/index.html"; fi\n'
        "  shift\n"
        "done\n"
        f"exit {exit_code}\n"
    )
    path.chmod(0o755)
    return str(path)


def read_marker(marker: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in marker.read_text().splitlines())


def require_hugo(hugo: str, version: str, variable: str) -> str:
    """Return hugo; skip the test unless it runs and reports v<version>."""
    try:
        reported = get_hugo_version(hugo)
    except BuildError as e:
        pytest.skip(f"needs Hugo {version} in {variable}: {e}")
    if not re.match(rf"hugo v{re.escape(version)}\b", reported):
        pytest.skip(f"needs Hugo {version} in {variable}, but {hugo} is {reported}")
    return hugo
