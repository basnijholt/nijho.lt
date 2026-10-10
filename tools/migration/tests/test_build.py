"""Building the site with Hugo, run as a fake shell script that records how it was called."""

import re
from pathlib import Path

import pytest

from helpers import fake_hugo, read_marker
from parity.build import BuildError, build_at_commit, build_site, get_hugo_version, resolve_baseline_hugo, resolve_hugo


@pytest.fixture(autouse=True)
def clean_hugo_env(monkeypatch):
    """Start every test without Hugo variables from the developer's shell."""
    for name in ("HUGO_BIN", "HUGO_BASELINE_BIN", "HUGO_ENV"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def marker(tmp_path) -> Path:
    return tmp_path / "marker"


@pytest.mark.parametrize(
    ("env", "given", "hugo", "baseline_hugo"),
    [
        pytest.param({}, None, "hugo", "hugo", id="nothing-set"),
        pytest.param({"HUGO_BIN": ""}, None, "hugo", "hugo", id="empty-hugo-bin"),
        pytest.param({"HUGO_BIN": "/new"}, None, "/new", "/new", id="hugo-bin"),
        pytest.param({"HUGO_BIN": "/new", "HUGO_BASELINE_BIN": ""}, None, "/new", "/new", id="empty-baseline-bin"),
        pytest.param({"HUGO_BIN": "/new", "HUGO_BASELINE_BIN": "/old"}, None, "/new", "/old", id="baseline-bin"),
        pytest.param({"HUGO_BIN": "/new", "HUGO_BASELINE_BIN": "/old"}, "/given", "/given", "/given", id="given"),
    ],
)
def test_hugo_binary_choice(monkeypatch, env, given, hugo, baseline_hugo):
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    assert (resolve_hugo(given), resolve_baseline_hugo(given)) == (hugo, baseline_hugo)


def test_build_site_runs_hugo_bin_for_production(tmp_path, monkeypatch, marker):
    """Production builds get a fresh HUGO_RESOURCEDIR that exists during the build and is removed after."""
    monkeypatch.setenv("HUGO_BIN", fake_hugo(tmp_path / "new-hugo", marker))
    monkeypatch.setenv("HUGO_BASELINE_BIN", fake_hugo(tmp_path / "old-hugo", marker))
    out = build_site(tmp_path / "src", tmp_path / "out")

    recorded = read_marker(marker)
    assert (out / "index.html").read_text() == "test\n"
    assert recorded["name"] == "new-hugo"
    assert recorded["args"] == f"--gc --minify -s {tmp_path / 'src'} -d {out}"
    assert (recorded["HUGO_ENV"], recorded["HUGO_ENABLEGITINFO"]) == ("production", "true")
    assert recorded["resourcedir_exists"] == "yes"
    assert not Path(recorded["HUGO_RESOURCEDIR"]).exists()


def test_build_site_for_development_drops_hugo_env(tmp_path, monkeypatch, marker):
    monkeypatch.setenv("HUGO_ENV", "production")
    build_site(tmp_path / "src", tmp_path / "out", production=False, hugo=fake_hugo(tmp_path / "hugo", marker))

    recorded = read_marker(marker)
    assert recorded["args"].endswith("--environment development")
    assert recorded["HUGO_ENV"] == ""


@pytest.mark.parametrize(
    ("baseline_bin", "expected"),
    [pytest.param("old-hugo", "old-hugo", id="baseline-bin"), pytest.param("", "new-hugo", id="empty-baseline-bin")],
)
def test_build_at_commit_runs_the_baseline_hugo(tmp_path, git_repo, monkeypatch, marker, baseline_bin, expected):
    repo, sha = git_repo
    monkeypatch.setenv("HUGO_BIN", fake_hugo(tmp_path / "new-hugo", marker))
    monkeypatch.setenv("HUGO_BASELINE_BIN", baseline_bin and fake_hugo(tmp_path / baseline_bin, marker))
    build_at_commit(repo, sha, tmp_path / "out")
    assert read_marker(marker)["name"] == expected


def test_build_at_commit_reuses_a_build_of_the_same_commit_and_hugo(tmp_path, git_repo, marker):
    repo, sha = git_repo
    hugo = fake_hugo(tmp_path / "hugo", marker)
    build_at_commit(repo, sha, tmp_path / "out", hugo=hugo)
    marker.unlink()
    build_at_commit(repo, sha, tmp_path / "out", hugo=hugo)
    assert not marker.exists()


def test_build_at_commit_rebuilds_cleanly_for_another_hugo(tmp_path, git_repo, marker):
    repo, sha = git_repo
    out = tmp_path / "out"
    build_at_commit(repo, sha, out, hugo=fake_hugo(tmp_path / "hugo-1", marker, version="0.123.3", payload="v1"))
    assert (out / ".parity-commit").read_text() == f"{sha} hugo v0.123.3 fake\n"
    (out / "stale.html").write_text("only the first build wrote this")

    build_at_commit(repo, sha, out, hugo=fake_hugo(tmp_path / "hugo-2", marker, version="0.167.0", payload="v2"))

    assert (out / ".parity-commit").read_text() == f"{sha} hugo v0.167.0 fake\n"
    assert (out / "index.html").read_text() == "v2\n"
    assert not (out / "stale.html").exists()


def test_missing_hugo_binary_says_what_to_do(tmp_path):
    missing = str(tmp_path / "no-such-hugo")
    hint = "Set HUGO_BIN and HUGO_BASELINE_BIN, or pass --hugo and --baseline-hugo"
    with pytest.raises(BuildError, match=f"no-such-hugo.*{hint}"):
        get_hugo_version(missing)
    with pytest.raises(BuildError, match="no-such-hugo"):
        build_site(tmp_path / "src", tmp_path / "out", hugo=missing)


def test_unknown_commit_says_what_to_do(tmp_path, git_repo, marker):
    repo, _ = git_repo
    message = (
        "unknown commit 'deadbeef'; fetch it, or check the commit given with --commit or in tools/migration/parity-baseline.txt"
    )
    with pytest.raises(BuildError, match=re.escape(message)):
        build_at_commit(repo, "deadbeef", tmp_path / "out", hugo=fake_hugo(tmp_path / "hugo", marker))


def test_failed_baseline_build_is_not_reused(tmp_path, git_repo, marker):
    """Hugo wrote part of the site and failed: no marker, so the next run builds again instead of reusing it."""
    repo, sha = git_repo
    out = tmp_path / "out"
    broken = fake_hugo(tmp_path / "broken-hugo", marker, payload="partial", exit_code=1)
    with pytest.raises(BuildError, match="^Hugo build of .* failed"):
        build_at_commit(repo, sha, out, hugo=broken)
    assert (out / "index.html").read_text() == "partial\n"
    assert not (out / ".parity-commit").exists()

    build_at_commit(repo, sha, out, hugo=fake_hugo(tmp_path / "hugo", marker, payload="full"))
    assert read_marker(marker)["name"] == "hugo"
    assert (out / "index.html").read_text() == "full\n"
    assert (out / ".parity-commit").read_text() == f"{sha} hugo v0.0.0 fake\n"


def test_commit_missing_from_the_repository_says_what_to_do(tmp_path, git_repo, marker):
    """git rev-parse passes any full sha through, so a commit that was never fetched fails at git worktree add."""
    repo, _ = git_repo
    missing = "0123456789abcdef0123456789abcdef01234567"
    message = (
        f"git worktree add of {missing} failed: fatal: invalid reference: {missing}; "
        "fetch it, or check the commit given with --commit or in tools/migration/parity-baseline.txt"
    )
    with pytest.raises(BuildError, match=f"^{re.escape(message)}$"):
        build_at_commit(repo, missing, tmp_path / "out", hugo=fake_hugo(tmp_path / "hugo", marker))
    assert not marker.exists()


def test_failing_hugo_version_is_reported_once(tmp_path):
    hugo = tmp_path / "hugo"
    hugo.write_text("#!/usr/bin/env bash\necho broken >&2\nexit 1\n")
    hugo.chmod(0o755)
    with pytest.raises(BuildError) as error:
        get_hugo_version(str(hugo))
    assert str(error.value) == f"{hugo} version failed: broken"
