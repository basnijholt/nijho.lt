"""Shared fixtures and builders: small hand-written sites, a fake Hugo and a one-commit git repository.

Every test runs without the developer's forbidden-word lists and proxies.
"""

import re
import shlex
import struct
import subprocess
from pathlib import Path

import pytest

from parity.__main__ import BASELINE_DIR, main
from parity.build import BuildError, build_at_commit, get_hugo_version, resolve_baseline_hugo
from parity.site import Build

TOOLS = Path(__file__).resolve().parents[1]
PROXY_VARIABLES = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY")


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


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch, tmp_path):
    """Hide ~/.config/git (forbidden words) and proxies, which would break requests to the local test servers."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
    for name in PROXY_VARIABLES:
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.lower(), raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")


@pytest.fixture
def make_build(tmp_path):
    """Write a site under tmp_path/<name> and return its Build."""
    return lambda name, files: write_build(tmp_path / name, files)


@pytest.fixture
def cli(capsys):
    """Run the parity command line and return (exit code, stdout, stderr); sys.exit("Error: ...") gives the text."""

    def run(*argv) -> tuple[int | str, str, str]:
        try:
            main([str(arg) for arg in argv])
            code = 0
        except SystemExit as e:
            code = e.code
        out, err = capsys.readouterr()
        return code, out, err

    return run


@pytest.fixture
def git_repo(tmp_path, monkeypatch) -> tuple[Path, str]:
    """A one-commit git repository; returns (repo, full sha)."""
    for name in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"):
        monkeypatch.delenv(name, raising=False)
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()

    git("init")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.com")
    git("config", "core.hooksPath", "/dev/null")
    git("config", "commit.gpgsign", "false")
    (repo / "config.yaml").write_text("baseURL: http://example.com\n")
    git("add", ".")
    git("commit", "-m", "init")
    return repo, git("rev-parse", "HEAD")


@pytest.fixture(scope="session")
def baseline_sha() -> str:
    return (TOOLS / "parity-baseline.txt").read_text().strip()


@pytest.fixture(scope="session")
def baseline_hugo() -> str:
    """The baseline Hugo binary; skips the test unless it runs and reports v0.123.3."""
    hugo = resolve_baseline_hugo()
    try:
        version = get_hugo_version(hugo)
    except BuildError as e:
        pytest.skip(f"needs Hugo 0.123.3 in HUGO_BASELINE_BIN: {e}")
    if not re.match(r"hugo v0\.123\.3\b", version):
        pytest.skip(f"needs Hugo 0.123.3 in HUGO_BASELINE_BIN, but {hugo} is {version}")
    return hugo


@pytest.fixture(scope="session")
def real_baseline(baseline_sha, baseline_hugo) -> Build:
    """The baseline build of tools/parity-baseline.txt, cached where compare-branch keeps it."""
    return Build(build_at_commit(TOOLS.parent, baseline_sha, BASELINE_DIR / baseline_sha, hugo=baseline_hugo))
