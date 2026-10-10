"""Checks on the real baseline build (slow: builds tools/parity-baseline.txt with Hugo 0.123.3 if not cached)."""

from xml.etree import ElementTree as ET

import pytest

from conftest import TOOLS
from parity.allow import load_allow, partition
from parity.build import build_at_commit
from parity.checks import ALL_CHECKS, check_feeds, sitemap_locs_without_page
from parity.site import Build

ADVENT = "/post/advent-of-open-source/"

pytestmark = pytest.mark.slow


def without_items(xml: bytes, guids: set[str]) -> bytes:
    root = ET.fromstring(xml)
    channel = root.find("channel")
    for element in channel.findall("item"):
        if element.findtext("guid") in guids:
            channel.remove(element)
    return ET.tostring(root, encoding="utf-8")


def test_advent_allow_rule_does_not_hide_removed_feed_items(real_baseline, make_build):
    """Dropping the 24 advent day items and one other post from the real admin feed fails."""
    feed = "/authors/admin/index.xml"
    xml = (real_baseline.root / feed.lstrip("/")).read_bytes()
    guids = [element.findtext("guid") for element in ET.fromstring(xml).iter("item")]
    days = {g for g in guids if g.startswith(ADVENT) and g != ADVENT}
    other = next(g for g in guids if not g.startswith(ADVENT))
    assert len(days) == 24

    base = make_build("base", {feed: xml})
    cand = make_build("cand", {feed: without_items(xml, days | {other})})
    failures, allowed, _ = partition(check_feeds(base, cand), load_allow(TOOLS / "parity-allow.yaml"))

    assert allowed == []
    expected = sorted(f"missing {kind} {guid!r}" for guid in days | {other} for kind in ("guid", "link"))
    assert [f.detail for f in failures] == expected


def test_percent_encoded_sitemap_loc_has_its_page(real_baseline):
    """The author page with a non-ASCII slug is listed percent-encoded and exists decoded."""
    loc = "/authors/william-hvidtfelt-padk%C3%A6r-nielsen/"
    assert loc in real_baseline.sitemap_locs
    assert loc not in sitemap_locs_without_page(real_baseline)


def test_rebuilt_baseline_matches_itself(real_baseline, baseline_sha, baseline_hugo, tmp_path):
    """A fresh build of the baseline commit has no failures against the cached one, so the checks are stable."""
    rebuilt = Build(build_at_commit(TOOLS.parent, baseline_sha, tmp_path / "rebuilt", hugo=baseline_hugo))
    findings = [finding for check in ALL_CHECKS.values() for finding in check(real_baseline, rebuilt)]
    failures, _, _ = partition(findings, load_allow(TOOLS / "parity-allow.yaml"))
    assert failures == []
