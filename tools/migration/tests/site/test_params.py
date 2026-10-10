"""Links and scripts that come from config/_default/params.yaml follow it."""

import pytest

from helpers import require_hugo
from parity.build import build_site, resolve_hugo
from parity.site import Build


@pytest.mark.slow
def test_footer_edit_link_and_analytics_follow_params(repo_root, tmp_path):
    hugo = require_hugo(resolve_hugo(), "0.167.0", "HUGO_BIN")
    env = {
        "HUGO_PARAMS_FEATURES_REPOSITORY_URL": "https://example.org/repo",
        "HUGO_PARAMS_FEATURES_DEPLOYS": "https://example.org/deploys",
        "HUGO_PARAMS_MARKETING_ANALYTICS_PLAUSIBLE": "https://example.org/stats.js",
        "HUGO_CACHEDIR": str(tmp_path / "cache"),
    }
    build = Build(build_site(repo_root, tmp_path / "public", hugo=hugo, env=env))
    home = build.soup("/index.html")
    footer = [a["href"] for a in home.select(".site-footer a")]
    assert "https://example.org/repo" in footer and "https://example.org/deploys" in footer
    assert home.select('script[src="https://example.org/stats.js"]')
    edit = build.soup("/post/agentic-coding/index.html").select_one("a.edit")["href"]
    assert edit == "https://example.org/repo/edit/main/content/post/agentic-coding/index.md"
