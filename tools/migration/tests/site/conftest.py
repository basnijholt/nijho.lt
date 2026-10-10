"""Fixtures for tests of the real site: this working tree built with Hugo 0.167.0, and the baseline build.

Tests that use either build are marked slow and skip when its Hugo binary is unavailable.
"""

from pathlib import Path

import pytest

from helpers import REPO, TOOLS, require_hugo
from parity.allow import AllowRule, load_allow, partition
from parity.build import build_site, resolve_hugo
from parity.checks import ALL_CHECKS, Finding
from parity.site import Build


HERE = Path(__file__).parent


def pytest_collection_modifyitems(items):
    for item in items:
        if item.path.is_relative_to(HERE) and {"site", "baseline"} & set(item.fixturenames):
            item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO


@pytest.fixture(scope="session")
def site(repo_root, tmp_path_factory) -> Build:
    """The working tree built for production with HUGO_BIN, which must be Hugo 0.167.0."""
    hugo = require_hugo(resolve_hugo(), "0.167.0", "HUGO_BIN")
    return Build(build_site(repo_root, tmp_path_factory.mktemp("site") / "public", hugo=hugo))


@pytest.fixture(scope="session")
def baseline(real_baseline) -> Build:
    return real_baseline


@pytest.fixture(scope="session")
def allow() -> list[AllowRule]:
    return load_allow(TOOLS / "parity-allow.yaml")


@pytest.fixture(scope="session")
def failures(baseline, site, allow):
    """Return a function that runs one parity check of site against baseline and returns what the allow file
    does not cover.
    """

    def run(check: str) -> list[Finding]:
        return partition(ALL_CHECKS[check](baseline, site), allow)[0]

    return run
