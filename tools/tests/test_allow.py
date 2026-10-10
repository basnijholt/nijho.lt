"""Allow files: loading and validating rules, and splitting findings with them."""

import re

import pytest

from conftest import TOOLS, item, rss
from parity import ParityError
from parity.allow import AllowRule, load_allow, partition
from parity.checks import Finding, check_feeds

FINDING = Finding("content", "/post/abc/index.html", "img count: 2 -> 1")


@pytest.mark.parametrize(
    "rule",
    [
        pytest.param(AllowRule("content", "/post/abc/index.html", None, "r"), id="exact-path"),
        pytest.param(AllowRule("content", "/post/*", None, "r"), id="glob-path"),
        pytest.param(AllowRule("content", "/post/abc/index.html", "img count", "r"), id="match-in-detail"),
    ],
)
def test_partition_allows_finding_the_rule_matches(rule):
    assert partition([FINDING], [rule]) == ([], [FINDING], [])


@pytest.mark.parametrize(
    "rule",
    [
        pytest.param(AllowRule("content", "/post/abc/index.html", "pre count", "r"), id="match-not-in-detail"),
        pytest.param(AllowRule("content", "/post/abc/index.html", "IMG COUNT", "r"), id="match-in-other-case"),
        pytest.param(AllowRule("seo", "/post/abc/index.html", None, "r"), id="other-check"),
        pytest.param(AllowRule("content", "/post/a", None, "r"), id="path-prefix"),
    ],
)
def test_partition_fails_finding_the_rule_does_not_match(rule):
    assert partition([FINDING], [rule]) == ([FINDING], [], [rule])


def test_partition_credits_the_first_matching_rule_and_returns_the_rest_unused():
    other = Finding("seo", "/index.html", "title: 'A' -> 'B'")
    first, duplicate = AllowRule("content", "/post/*", None, "r"), AllowRule("content", "/post/*", None, "r")
    unrelated = AllowRule("paths", "/x.html", None, "r")
    assert partition([other, FINDING], [first, duplicate, unrelated]) == ([other], [FINDING], [duplicate, unrelated])


def test_advent_rules_allow_only_the_section_item(make_build):
    """The race rule in parity-allow.yaml allows the advent section item, never a day item or another post."""
    feed = "/authors/admin/index.xml"
    day = item("d", guid="/post/advent-of-open-source/01-day/", link="/post/advent-of-open-source/01-day/")
    base = make_build("base", {feed: rss([item("advent-of-open-source"), day, item("other")])})
    cand = make_build("cand", {feed: rss([])})

    failures, allowed, unused = partition(check_feeds(base, cand), load_allow(TOOLS / "parity-allow.yaml"))

    assert [f.detail for f in allowed] == [
        "missing guid '/post/advent-of-open-source/'",
        "missing link '/post/advent-of-open-source/'",
    ]
    assert [f.detail for f in failures] == [
        "missing guid '/post/advent-of-open-source/01-day/'",
        "missing guid '/post/other/'",
        "missing link '/post/advent-of-open-source/01-day/'",
        "missing link '/post/other/'",
    ]
    assert unused == []


VALID = "- {check: paths, path: /a.html, reason: ok}\n"


def write_allow(tmp_path, text):
    path = tmp_path / "allow.yaml"
    path.write_text(text)
    return path


def test_load_allow_reads_rules(tmp_path):
    rules = load_allow(write_allow(tmp_path, VALID + "- {check: feeds, path: /x, match: m, reason: ' r '}"))
    assert rules == [AllowRule("paths", "/a.html", None, "ok"), AllowRule("feeds", "/x", "m", "r")]
    assert load_allow(write_allow(tmp_path, "# nothing yet\n")) == []


@pytest.mark.parametrize(
    ("text", "message"),
    [
        pytest.param("check: paths\n", "expected a list of rules, got dict", id="not-a-list"),
        pytest.param(VALID + "- just a string\n", "entry 2: expected a mapping", id="not-a-mapping"),
        pytest.param(VALID + "- {check: feeds, path: /x, matches: m, reason: r}", "entry 2: unknown key", id="typo"),
        pytest.param(VALID + "- {check: feeds, path: /x, match: 1, reason: r}", "entry 2: 'match' must be a string",
                     id="number"),
        pytest.param(VALID + "- {path: /x, reason: r}", "entry 2: missing or empty 'check'", id="missing-check"),
        pytest.param(VALID + "- {check: feeds, reason: r}", "entry 2: missing or empty 'path'", id="missing-path"),
        pytest.param(VALID + "- {check: feeds, path: /x, reason: ' '}", "entry 2: missing or empty 'reason'",
                     id="blank-reason"),
        pytest.param(VALID + "- {check: feed, path: /x, reason: r}", "entry 2: unknown check 'feed'", id="check-name"),
        pytest.param(VALID + "- {check: feeds, path: /x, match: '', reason: r}", "entry 2: empty 'match'", id="empty"),
    ],
)
def test_load_allow_rejects_bad_files(tmp_path, text, message):
    path = write_allow(tmp_path, text)
    with pytest.raises(ParityError, match=f"^{re.escape(f'{path}: {message}')}"):
        load_allow(path)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        pytest.param(
            VALID + "- check: [paths\n",
            "invalid YAML at line 3, column 1: expected ',' or ']', but got '<stream end>'",
            id="syntax",
        ),
        pytest.param(
            VALID + "- \x01\n",
            'invalid YAML: unacceptable character #x0001: special characters are not allowed in "<unicode string>", '
            "position 46",
            id="no-position-mark",
        ),
    ],
)
def test_load_allow_reports_invalid_yaml_on_one_line(tmp_path, text, message):
    path = write_allow(tmp_path, text)
    with pytest.raises(ParityError) as error:
        load_allow(path)
    assert str(error.value) == f"{path}: {message}"


def test_load_allow_names_a_file_that_is_not_utf8(tmp_path):
    path = tmp_path / "allow.yaml"
    path.write_bytes(VALID.encode() + b"# caf\xe9\n")
    message = f"{path}: invalid UTF-8 at byte 49: invalid continuation byte"
    with pytest.raises(ParityError, match=f"^{re.escape(message)}$"):
        load_allow(path)
