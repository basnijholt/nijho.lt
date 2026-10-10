"""The search dialog, view transitions and prefetching in the head, and the 404 page."""

import json

from parity.site import read_utf8

PAGES = ("/index.html", "/post/self-hosting-ai-is-not-cheaper/index.html", "/publication/index.html", "/404.html")


def test_index_json_not_referenced_in_html(site):
    pages = [p for p in site.pages if "index.json" in read_utf8(site.root / p.lstrip("/"))]
    assert pages == []
    bundles = [f for f in site.files if f.startswith("/js/search.") and f.endswith(".js")]
    assert len(bundles) == 1 and "/index.json" in read_utf8(site.root / bundles[0].lstrip("/"))


def test_search_dialog_on_every_page(site):
    for page in PAGES:
        soup = site.soup(page)
        dialog = soup.select_one("dialog#search")
        assert dialog, page
        assert dialog.select_one('input[type="search"][role="combobox"][aria-controls="search-results"]')
        assert dialog.select_one('#search-results[role="listbox"]')
        assert soup.select_one('.site-header button[aria-controls="search"]'), page
        assert soup.select('script[src^="/js/search."]'), page


def test_speculation_rules_and_view_transition_present(site):
    for page in PAGES:
        soup = site.soup(page)
        rules = json.loads(soup.select_one('script[type="speculationrules"]').get_text())
        [rule] = rules["prefetch"]
        assert rule["eagerness"] == "moderate", page
        assert rule["where"]["and"][0] == {"href_matches": "/*"}, page
        skipped = rule["where"]["and"][1]["not"]["href_matches"]
        assert {"/*.xml", "/*.json", "/*.asc", "/*.gif", "/*.png", "/*.jpg", "/*.mp4"} <= set(skipped), page
        styles = "".join(s.get_text() for s in soup.select("head style")).replace(" ", "").replace(";}", "}")
        assert "@media(prefers-reduced-motion:no-preference){@view-transition{navigation:auto}}" in styles


def test_404_has_search_and_links(site):
    soup = site.soup("/404.html")
    assert soup.select_one("main h1").get_text(strip=True) == "Page not found"
    form = soup.select_one('main form[action="/"][method="get"]')
    assert form.select_one('input[type="search"][name="q"]')
    hrefs = {a["href"] for a in soup.select("main a")}
    assert {"/", "/post/", "/project/"} <= hrefs
