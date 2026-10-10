"""Allow files: YAML lists of expected findings that do not fail a run."""

import fnmatch
from dataclasses import dataclass
from pathlib import Path

import yaml

from . import ParityError
from .checks import ALL_CHECKS, Finding
from .site import read_utf8

ALLOW_KEYS = ("check", "path", "match", "reason")


@dataclass(frozen=True)
class AllowRule:
    """One allow-file entry; a match of None allows any detail."""
    check: str
    path: str
    match: str | None
    reason: str


def load_allow(path: Path) -> list[AllowRule]:
    """Read an allow file; raise ParityError naming the entry (counted from 1) on any problem."""
    try:
        data = yaml.safe_load(read_utf8(path))
    except yaml.YAMLError as e:
        mark, problem = getattr(e, "problem_mark", None), getattr(e, "problem", None)
        where = f" at line {mark.line + 1}, column {mark.column + 1}" if mark else ""
        raise ParityError(f"{path}: invalid YAML{where}: {problem or ' '.join(str(e).split())}") from None
    if data is None:
        return []
    if not isinstance(data, list):
        raise ParityError(f"{path}: expected a list of rules, got {type(data).__name__}")

    rules = []
    for number, entry in enumerate(data, start=1):
        where = f"{path}: entry {number}"
        if not isinstance(entry, dict):
            raise ParityError(f"{where}: expected a mapping, got {type(entry).__name__}")
        unknown = sorted(str(key) for key in entry if key not in ALLOW_KEYS)
        if unknown:
            raise ParityError(f"{where}: unknown key(s) {', '.join(unknown)}; allowed: {', '.join(ALLOW_KEYS)}")
        for key, value in entry.items():
            if not isinstance(value, str):
                raise ParityError(f"{where}: {key!r} must be a string, got {type(value).__name__}")
        for key in ("check", "path", "reason"):
            if not entry.get(key, "").strip():
                raise ParityError(f"{where}: missing or empty {key!r}")
        if entry["check"] not in ALL_CHECKS:
            raise ParityError(f"{where}: unknown check {entry['check']!r}; known: {', '.join(ALL_CHECKS)}")
        if "match" in entry and not entry["match"]:
            raise ParityError(f"{where}: empty 'match' would match every detail; omit the key instead")

        rules.append(AllowRule(entry["check"], entry["path"], entry.get("match"), entry["reason"].strip()))
    return rules


def partition(findings: list[Finding], rules: list[AllowRule]) -> tuple[list[Finding], list[Finding], list[AllowRule]]:
    """Split findings into failures and allowed findings, and return the unused rules.

    Each finding is credited to the first rule that matches it; rules credited with nothing are returned as unused.
    """
    failures, allowed, credited = [], [], set()
    for finding in findings:
        index = next((i for i, rule in enumerate(rules) if _matches(finding, rule)), None)
        if index is None:
            failures.append(finding)
        else:
            allowed.append(finding)
            credited.add(index)
    return failures, allowed, [rule for i, rule in enumerate(rules) if i not in credited]


def _matches(finding: Finding, rule: AllowRule) -> bool:
    return (
        finding.check == rule.check
        and fnmatch.fnmatch(finding.path, rule.path)
        and (rule.match is None or rule.match in finding.detail)
    )
