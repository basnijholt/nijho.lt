"""Shared fixtures: a one-commit git repository, the parity command line and the real baseline build.

Every test runs without the developer's forbidden-word lists and proxies.
"""

import subprocess
from pathlib import Path

import pytest

from helpers import TOOLS, require_hugo, write_build
from parity.__main__ import BASELINE_DIR, main
from parity.build import build_at_commit, resolve_baseline_hugo
from parity.site import Build

PROXY_VARIABLES = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY")


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
    return require_hugo(resolve_baseline_hugo(), "0.123.3", "HUGO_BASELINE_BIN")


@pytest.fixture(scope="session")
def real_baseline(baseline_sha, baseline_hugo) -> Build:
    """The baseline build of tools/parity-baseline.txt, cached where compare-branch keeps it."""
    return Build(build_at_commit(TOOLS.parent, baseline_sha, BASELINE_DIR / baseline_sha, hugo=baseline_hugo))
