"""The parity command line: reports, exit codes and error messages."""

from pathlib import Path

import pytest

from helpers import fake_hugo, item, page, rss
from parity.__main__ import candidate_dir
from parity.checks import ALL_CHECKS, HOME_IDS

HOME = page("".join(f'<section id="{id_}"></section>' for id_ in HOME_IDS))
POSTS = {"/index.html": HOME, "/post/a/index.html": page(head="<title>A</title>"), "/post/b/index.html": page()}
COMPARED = "\nCompared 3 page(s) and 0 feed(s)\n"


@pytest.fixture
def base(make_build):
    return make_build("base", POSTS).root


def test_compare_identical_builds_passes(cli, base):
    assert cli("compare", base, base) == (0, COMPARED + "No failures\n", "")


def test_compare_refuses_a_base_that_is_not_a_hugo_build(cli, make_build):
    empty = make_build("empty", {}).root
    assert cli("compare", empty, empty) == (f"Error: {empty}: no index.html; does not look like a Hugo build", "", "")


def test_compare_reports_failures_by_check(cli, base, make_build):
    cand = make_build("cand", {"/index.html": HOME, "/post/a/index.html": page(head="<title>New</title>")}).root
    assert cli("compare", base, cand) == (
        1,
        "\nFailures:\n"
        "\npaths:\n  /post/b/index.html: missing from candidate\n"
        "\nseo:\n  /post/a/index.html: title: 'A' -> 'New'\n" + COMPARED,
        "",
    )


def test_compare_only_runs_the_named_checks(cli, base, make_build):
    cand = make_build("cand", {"/index.html": HOME, "/post/a/index.html": page(head="<title>New</title>")}).root
    assert cli("compare", base, cand, "--only", "ids", "--only", "feeds")[0] == 0
    assert cli("compare", base, cand, "--only", "seo") == (
        1, "\nFailures:\n\nseo:\n  /post/a/index.html: title: 'A' -> 'New'\n" + COMPARED, ""
    )


def test_compare_allow_file_suppresses_findings_and_lists_unused_rules(cli, base, make_build, tmp_path):
    allow = tmp_path / "allow.yaml"
    allow.write_text(
        "- check: paths\n  path: /post/b/index.html\n  reason: moved\n"
        "- check: feeds\n  path: /post/index.xml\n  match: \"guid '/post/x/'\"\n  reason: race\n"
    )
    cand = make_build("cand", {path: POSTS[path] for path in ("/index.html", "/post/a/index.html")}).root
    assert cli("compare", base, cand, "--allow", allow) == (
        0,
        "\nAllowed: 1 findings suppressed\n"
        "\nUnused allow rules: 1\n  feeds /post/index.xml match \"guid '/post/x/'\"\n" + COMPARED + "No failures\n",
        "",
    )


def test_compare_only_lists_unused_rules_of_the_checks_that_ran(cli, base, tmp_path):
    allow = tmp_path / "allow.yaml"
    allow.write_text("- {check: paths, path: /gone.html, reason: r}\n- {check: seo, path: /gone.html, reason: r}\n")
    assert cli("compare", base, base, "--allow", allow, "--only", "seo") == (
        0, "\nUnused allow rules: 1\n  seo /gone.html\n" + COMPARED + "No failures\n", ""
    )


def test_compare_reports_invalid_allow_file_on_one_line(cli, base, tmp_path):
    allow = tmp_path / "allow.yaml"
    allow.write_text("- check: [paths\n")
    assert cli("compare", base, base, "--allow", allow) == (
        f"Error: {allow}: invalid YAML at line 2, column 1: expected ',' or ']', but got '<stream end>'", "", ""
    )


@pytest.mark.parametrize(
    ("args", "message"),
    [
        pytest.param("compare /gone .", "argument BASE: /gone is not a directory", id="missing-base"),
        pytest.param("compare . . --only feed", "argument --only: invalid choice: 'feed'", id="unknown-check"),
        pytest.param("compare . . --allow /gone", "argument --allow: /gone is not a file", id="missing-allow-file"),
        pytest.param("old-images . /gone", "argument CAND: /gone is not a directory", id="missing-cand"),
    ],
)
def test_bad_arguments_exit_2_and_name_the_argument(cli, args, message):
    code, out, err = cli(*args.split())
    assert (code, out) == (2, "")
    assert message in err


def test_compare_branch_names_a_missing_default_allow_file(cli, tmp_path, monkeypatch):
    monkeypatch.setattr("parity.__main__.REPO", tmp_path)
    code, out, err = cli("compare-branch")
    assert (code, out) == (2, "")
    assert f"argument --allow: {tmp_path / 'tools/migration/parity-allow.yaml'} is not a file" in err


def test_compare_branch_names_the_commit_and_both_build_directories(cli, git_repo, tmp_path, monkeypatch):
    repo, sha = git_repo
    (tmp_path / "parity-baseline.txt").write_text(sha[:7] + "\n")
    (tmp_path / "allow.yaml").write_text("")
    monkeypatch.setattr("parity.__main__.REPO", repo)
    monkeypatch.setattr("parity.__main__.BASELINE_SHA_FILE", tmp_path / "parity-baseline.txt")
    monkeypatch.setattr("parity.__main__.BASELINE_DIR", tmp_path / "baselines")
    monkeypatch.setattr("parity.__main__.CANDIDATE_PREFIX", f"{tmp_path}/candidate-")
    hugo = fake_hugo(tmp_path / "hugo", tmp_path / "marker", payload=HOME)

    code, out, err = cli("compare-branch", "--allow", tmp_path / "allow.yaml", "--hugo", hugo, "--baseline-hugo", hugo)

    cand = candidate_dir(repo)
    assert (code, err) == (0, "")
    assert out == (
        f"Baseline: commit {sha[:7]} in {tmp_path / 'baselines' / sha[:7]}\n"
        "Baseline Hugo: hugo v0.0.0 fake\n"
        f"Candidate: working tree in {cand}\n"
        "Candidate Hugo: hugo v0.0.0 fake\n"
        "\nCompared 1 page(s) and 0 feed(s)\nNo failures\n"
    )
    assert (cand / "index.html").exists()


def test_each_repository_has_its_own_candidate_directory():
    first, second = candidate_dir(Path("/home/a/site")), candidate_dir(Path("/home/b/site"))
    assert first != second
    assert first == candidate_dir(Path("/home/a/site"))
    assert str(first).startswith("/tmp/parity-candidate-")


def test_compare_branch_reports_missing_hugo(cli, monkeypatch):
    """An empty HUGO_BASELINE_BIN counts as unset."""
    monkeypatch.setenv("HUGO_BASELINE_BIN", "")
    monkeypatch.setenv("HUGO_BIN", "/nonexistent/hugo")
    assert cli("compare-branch")[0].startswith("Error: cannot run Hugo binary '/nonexistent/hugo'")


def test_baseline_without_sha_file_says_what_to_do(cli, tmp_path, monkeypatch):
    missing = tmp_path / "parity-baseline.txt"
    monkeypatch.setattr("parity.__main__.BASELINE_SHA_FILE", missing)
    expected = f"Error: {missing} not found; restore it, or pass --commit to parity baseline"
    assert cli("baseline", tmp_path / "out") == (expected, "", "")


def test_old_images_prints_yaml_and_counts_skipped_names(cli, make_build, tmp_path, monkeypatch):
    (tmp_path / "config" / "git").mkdir(parents=True)
    (tmp_path / "config" / "git" / "forbidden-words").write_text("secretco\tA test word\n")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    repo = tmp_path / "repo"
    (repo / "assets").mkdir(parents=True)
    (repo / "assets" / "logo.png").write_bytes(b"")
    old = "logo_hu3b5d3c7d207e37dceeedd301e35e2e58_0_1x1_resize_box.png"
    base = make_build("base", {f"/media/{old}": b"", f"/media/secretco_hu{'0' * 32}_10_1x1_resize_box.png": b""})

    code, out, err = cli("old-images", base.root, make_build("cand", {}).root, "--repo", repo)

    assert (code, out) == (0, f"- file: logo.png\n  size: 0\n  names:\n  - {old}\n")
    assert err == "Skipped 1 old image name(s) with a forbidden word; the old-images check will report them\n"


def test_compare_names_a_broken_candidate_feed(cli, make_build):
    base = make_build("base", POSTS | {"/post/index.xml": rss([item("a")])}).root
    cand = make_build("cand", POSTS | {"/post/index.xml": "<rss><channel>"}).root
    assert cli("compare", base, cand) == (
        f"Error: {cand / 'post/index.xml'}: invalid XML: no element found: line 1, column 14", "", ""
    )


def test_an_unexpected_error_keeps_its_traceback(cli, base, monkeypatch):
    def broken(base, cand):
        raise ValueError("a bug")

    monkeypatch.setitem(ALL_CHECKS, "paths", broken)
    with pytest.raises(ValueError, match="a bug"):
        cli("compare", base, base)
