"""Build the site with Hugo, from a source directory or from a git commit."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

COMMIT_HINT = "fetch it, or check the commit given with --commit or in tools/migration/parity-baseline.txt"


class BuildError(Exception):
    """A git or Hugo step failed; the message says which."""


def resolve_hugo(hugo: str | None = None) -> str:
    """Return the candidate Hugo: hugo, else $HUGO_BIN, else hugo on PATH; empty values count as unset."""
    return hugo or os.environ.get("HUGO_BIN") or "hugo"


def resolve_baseline_hugo(hugo: str | None = None) -> str:
    """Return the baseline Hugo: hugo, else $HUGO_BASELINE_BIN, else resolve_hugo(); empty values count as unset."""
    return hugo or os.environ.get("HUGO_BASELINE_BIN") or resolve_hugo()


def _run_hugo(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    except OSError as e:
        raise BuildError(
            f"cannot run Hugo binary {cmd[0]!r}: {e.strerror or e}. "
            "Set HUGO_BIN and HUGO_BASELINE_BIN, or pass --hugo and --baseline-hugo"
        ) from e


def get_hugo_version(hugo: str) -> str:
    """Return the output of `hugo version`."""
    result = _run_hugo([hugo, "version"])
    if result.returncode:
        raise BuildError(f"{hugo} version failed: {result.stderr.strip()}")
    return result.stdout.strip()


def build_site(
    src: Path, out: Path, *, production: bool = True, env: dict[str, str] | None = None, hugo: str | None = None
) -> Path:
    """Build src into out and return out.

    Every build gets an empty HUGO_RESOURCEDIR: a stale resources/_gen changes the names of chained image derivatives.
    """
    cmd = [resolve_hugo(hugo), "--gc", "--minify", "-s", str(src), "-d", str(out)]
    with tempfile.TemporaryDirectory(prefix="hugo-resources-") as resource_dir:
        build_env = os.environ | {"HUGO_RESOURCEDIR": resource_dir}
        if production:
            build_env |= {"HUGO_ENV": "production", "HUGO_ENABLEGITINFO": "true"}
        else:
            build_env.pop("HUGO_ENV", None)
            cmd += ["--environment", "development"]
        result = _run_hugo(cmd, env=build_env | (env or {}))
    if result.returncode:
        raise BuildError(f"Hugo build of {src} failed:\n{result.stderr}")
    return Path(out)


def build_at_commit(repo: Path, commit: str, out: Path, *, hugo: str | None = None) -> Path:
    """Build a commit of repo into out with the baseline Hugo and return out.

    out/.parity-commit records the commit and Hugo version: a matching build is reused, any other is wiped first.
    """
    out = Path(out)
    marker = out / ".parity-commit"
    hugo = resolve_baseline_hugo(hugo)
    result = subprocess.run(["git", "rev-parse", commit], cwd=repo, capture_output=True, text=True)
    if result.returncode:
        raise BuildError(f"unknown commit {commit!r}; {COMMIT_HINT}")
    sha = result.stdout.strip()
    stamp = f"{sha} {get_hugo_version(hugo)}"
    if marker.exists():
        if marker.read_text().strip() == stamp:
            return out
        shutil.rmtree(out)

    with tempfile.TemporaryDirectory(prefix="parity-build-") as tmp:
        worktree = Path(tmp) / "worktree"
        add = subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree), sha], cwd=repo, capture_output=True, text=True
        )
        if add.returncode:
            raise BuildError(f"git worktree add of {sha} failed: {add.stderr.strip()}; {COMMIT_HINT}")
        try:
            build_site(worktree, out, hugo=hugo)
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=repo, capture_output=True)
    marker.write_text(stamp + "\n")
    return out
