"""The site builds without Hugo modules and has every page the baseline has."""

from parity.checks import sitemap_locs_without_page


def test_no_modules(repo_root):
    assert not (repo_root / "go.mod").exists() and not (repo_root / "config/_default/module.yaml").exists()


def test_every_baseline_page_exists(site, baseline):
    missing = [p for p in baseline.pages if p not in site.files]
    assert missing == []


def test_term_and_project_index_pages_exist(site):
    for p in ["/tags/index.html", "/tag/ai/index.html", "/categories/index.html", "/project/index.html",
              "/publication_types/index.html", "/authors/page/2/index.html"]:
        assert p in site.files


def test_every_sitemap_loc_has_a_page(site, failures):
    assert sitemap_locs_without_page(site) == []
    assert failures("sitemap") == []
