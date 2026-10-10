"""The parity command line: compare, compare-branch, baseline, old-images and live."""

import argparse
import hashlib
import itertools
import json
import operator
import shutil
import sys
from pathlib import Path

import httpx
import yaml

from . import ParityError
from .allow import AllowRule, load_allow, partition
from .build import BuildError, build_at_commit, build_site, get_hugo_version, resolve_baseline_hugo, resolve_hugo
from .checks import ALL_CHECKS
from .live import Reply, live_mismatch, live_responses
from .old_images import map_old_images
from .site import Build

REPO = Path(__file__).resolve().parents[2]
BASELINE_SHA_FILE = REPO / "tools/parity-baseline.txt"
BASELINE_DIR = Path("/tmp/parity-baseline")
CANDIDATE_PREFIX = "/tmp/parity-candidate-"
BASELINE_HUGO_HELP = "Hugo for the baseline (default: $HUGO_BASELINE_BIN, else $HUGO_BIN, else hugo)"


def candidate_dir(repo: Path) -> Path:
    """Return the candidate build directory of a repository, named by a hash of its path so no two share one."""
    return Path(CANDIDATE_PREFIX + hashlib.sha256(str(repo).encode()).hexdigest()[:8])


def _baseline_sha() -> str:
    try:
        return BASELINE_SHA_FILE.read_text().strip()
    except FileNotFoundError:
        raise ParityError(f"{BASELINE_SHA_FILE} not found; restore it, or pass --commit to parity baseline") from None


def _report(base: Build, cand: Build, rules: list[AllowRule], only: list[str] | None = None) -> None:
    """Print failures by check, the allowed count, unused rules and what was compared; exit 1 if anything failed."""
    if "/index.html" not in base.files:
        raise ParityError(f"{base.root}: no index.html; does not look like a Hugo build")
    findings = [f for name, check in ALL_CHECKS.items() if not only or name in only for f in check(base, cand)]
    failures, allowed, unused = partition(findings, rules)
    unused = [rule for rule in unused if not only or rule.check in only]
    if failures:
        print("\nFailures:")
        for check, group in itertools.groupby(failures, key=operator.attrgetter("check")):
            print(f"\n{check}:")
            for finding in group:
                print(f"  {finding.path}: {finding.detail}")
    if allowed:
        print(f"\nAllowed: {len(allowed)} findings suppressed")
    if unused:
        print(f"\nUnused allow rules: {len(unused)}")
        for rule in unused:
            match = f" match {json.dumps(rule.match)}" if rule.match is not None else ""
            print(f"  {rule.check} {rule.path}{match}")
    print(f"\nCompared {len(base.pages)} page(s) and {len(base.feeds)} feed(s)")
    if failures:
        sys.exit(1)
    print("No failures")


def _compare(args: argparse.Namespace) -> None:
    rules = load_allow(args.allow) if args.allow else []
    _report(Build(args.base), Build(args.cand), rules, args.only)


def _compare_branch(args: argparse.Namespace) -> None:
    rules = load_allow(args.allow)
    sha = _baseline_sha()
    baseline_hugo, hugo = resolve_baseline_hugo(args.baseline_hugo), resolve_hugo(args.hugo)
    base, cand = BASELINE_DIR / sha, candidate_dir(REPO)
    print(f"Baseline: commit {sha} in {base}")
    print(f"Baseline Hugo: {get_hugo_version(baseline_hugo)}")
    print(f"Candidate: working tree in {cand}")
    print(f"Candidate Hugo: {get_hugo_version(hugo)}")
    build_at_commit(REPO, sha, base, hugo=baseline_hugo)
    shutil.rmtree(cand, ignore_errors=True)
    build_site(REPO, cand, hugo=hugo)
    _report(Build(base), Build(cand), rules)


def _baseline(args: argparse.Namespace) -> None:
    commit = args.commit or _baseline_sha()
    build_at_commit(REPO, commit, args.out, hugo=args.baseline_hugo)
    print(f"Built {commit} into {args.out}")


def _old_images(args: argparse.Namespace) -> None:
    entries, skipped = map_old_images(Build(args.base), args.repo, Build(args.cand))
    print(yaml.dump(entries, sort_keys=False), end="")
    if skipped:
        print(
            f"Skipped {len(skipped)} old image name(s) with a forbidden word; the old-images check will report them",
            file=sys.stderr,
        )


def _describe(reply: Reply) -> str:
    status, location = reply
    return f"{status} -> {location}" if location else str(status)


def _live(args: argparse.Namespace) -> None:
    responses = live_responses(args.sitemap, args.preview)
    failures = [(path, live, preview) for path, live, preview in responses if live_mismatch(live, preview)]
    if failures:
        print("Mismatches found:")
        for path, live, preview in failures:
            print(f"  {path}: live={_describe(live)}, preview={_describe(preview)}")
        sys.exit(1)
    print(f"All {len(responses)} sitemap paths OK on the preview")


def _directory(value: str) -> Path:
    if not Path(value).is_dir():
        raise argparse.ArgumentTypeError(f"{value} is not a directory")
    return Path(value)


def _file(value: str) -> Path:
    if not Path(value).is_file():
        raise argparse.ArgumentTypeError(f"{value} is not a file")
    return Path(value)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="parity", description="Compare Hugo builds of nijho.lt before and after a theme change."
    )
    commands = parser.add_subparsers(metavar="COMMAND", required=True)

    def command(name: str, run, text: str) -> argparse.ArgumentParser:
        sub = commands.add_parser(name, help=text, description=text)
        sub.set_defaults(run=run)
        return sub

    compare = command("compare", _compare, "Report what CAND lost or changed compared with BASE")
    compare.add_argument("base", metavar="BASE", type=_directory, help="baseline build directory")
    compare.add_argument("cand", metavar="CAND", type=_directory, help="candidate build directory")
    compare.add_argument("--allow", metavar="FILE", type=_file, help="allow file of expected findings (default: none)")
    compare.add_argument(
        "--only", metavar="CHECK", action="append", choices=list(ALL_CHECKS),
        help=f"run only this check, one of {', '.join(ALL_CHECKS)}; may be repeated",
    )

    branch = command(
        "compare-branch", _compare_branch,
        f"Build the baseline commit into {BASELINE_DIR}/<sha> and the working tree into "
        f"{CANDIDATE_PREFIX}<hash of the repository path>, then compare them",
    )
    # argparse runs type on string defaults only, so a missing default file is an argument error too
    branch.add_argument(
        "--allow", metavar="FILE", type=_file, default=str(REPO / "tools/parity-allow.yaml"),
        help="allow file (default: tools/parity-allow.yaml)",
    )
    branch.add_argument("--baseline-hugo", metavar="PATH", help=BASELINE_HUGO_HELP)
    branch.add_argument("--hugo", metavar="PATH", help="Hugo for the working tree (default: $HUGO_BIN, else hugo)")

    baseline = command(
        "baseline", _baseline, "Build a commit (default: tools/parity-baseline.txt) into OUT with the baseline Hugo"
    )
    baseline.add_argument(
        "out", metavar="OUT", type=Path, help="an empty directory, or an earlier OUT (reused if commit and Hugo match)"
    )
    baseline.add_argument("--commit", metavar="SHA", help="commit to build (default: tools/parity-baseline.txt)")
    baseline.add_argument("--baseline-hugo", metavar="PATH", help=BASELINE_HUGO_HELP)

    old_images = command(
        "old-images", _old_images, "Print data/old_images.yaml: the source file of every _hu image CAND lacks"
    )
    old_images.add_argument("base", metavar="BASE", type=_directory, help="baseline build directory")
    old_images.add_argument("cand", metavar="CAND", type=_directory, help="candidate build directory")
    old_images.add_argument(
        "--repo", metavar="DIR", type=_directory, default=REPO,
        help="repository with content/ and assets/ (default: this repository)",
    )

    live = command(
        "live", _live,
        "Check every live sitemap path on a preview deploy: "
        "the preview must return 200, or the same 3xx and Location as the live site",
    )
    live.add_argument("--preview", metavar="URL", required=True, help="base URL of the preview deploy")
    live.add_argument(
        "--sitemap", metavar="URL", default="https://www.nijho.lt/sitemap.xml",
        help="live sitemap (default: %(default)s)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    try:
        args.run(args)
    except httpx.RequestError as e:
        sys.exit(f"Error: {e.request.url}: {str(e) or type(e).__name__}")
    except (BuildError, ParityError, httpx.HTTPError) as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()
