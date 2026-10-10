# Own Hugo Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task with the skill named in **Execution**. Steps use checkbox (`- [ ]`) syntax.

**Execution:** baspowers:subagent-driven-development. 19 tasks with tightly shared template interfaces, and a shipped mistake breaks public URLs, so every task gets a fresh implementer and a fresh reviewer.

**Goal:** Replace the HugoBlox modules with a hand-written Hugo theme that looks like mockup D, keeps every public URL, feed and SEO tag, and proves it with an automated parity check.

**Architecture:** Part A builds `tools/parity`, a Python package that builds the old and new site and diffs them (paths, sitemap, feeds, anchors, SEO tags, article text, old image URLs, internal links, redirects). Part B writes the theme directly in `layouts/` and `assets/` (no modules), test-first: each task adds pytest assertions against a fresh build of the branch, and the parity check against the pinned baseline must end clean apart from the reviewed entries in `tools/parity-allow.yaml`.

**Tech Stack:** Hugo 0.167.0 for the new theme (0.123.3 only to build the baseline), plain modern CSS through `css.Build` (minify, fingerprint), ES modules through Hugo's `js.Build`, Python 3.12+ with uv, pytest, BeautifulSoup + lxml, httpx, Playwright with the system Chromium, axe-playwright-python.

**Spec:** `docs/baspowers/specs/2026-10-09-own-hugo-theme-design.md` (all phases; the Hugo upgrade to 0.167.0 is folded into PR 2). Hugo 0.167 reference for every Part B task: `docs/baspowers/design/hugo-0.167-theme-guide.md` (template paths, removed functions, config renames, `css.Build`, gotchas), verified against the 0.167.0 binary. Design reference: `docs/baspowers/design/2026-10-09-mockup-d/` (`mockup.css`, `home.js`, `post.js`, screenshots); full mockup markup in `~/Work/nijho.lt-worktrees/own-theme-mockups/D-complete/{home-w1,post}.html`.

## Global Constraints

- Work only in the worktree `~/Work/nijho.lt-worktrees/own-theme` (branch `theme`, stacked on `parity-check`). Never write to `~/Work/nijho.lt`; other sessions switch its branch.
- Hugo versions: the new theme targets **Hugo 0.167.0** (`export HUGO_BIN=/tmp/hugo-latest/bin/hugo`); the baseline (old theme at the pinned commit) builds with **0.123.3** (`export HUGO_BASELINE_BIN=/tmp/hugo-bin/hugo`). If either is missing, download `hugo_extended_<version>_linux-amd64.tar.gz` from the gohugoio/hugo GitHub release. Netlify's `HUGO_VERSION` moves to `0.167.0` in Task 19.
- Templates use only the Hugo 0.146+ tree: `layouts/{baseof,home,page,section,taxonomy,term,404}.html`, `layouts/<section>/{page,section}.html`, `layouts/_partials/`, `layouts/_shortcodes/`, `layouts/_markup/`. Never `_default/`, `partials/`, `shortcodes/` or `index.html`; never call `partial "partials/..."`.
- Hugo 0.167 traps (see the guide's gotchas): `pagination.pagerSize` (not `paginate`), `.Summary` is HTML (use `plainify` for text), wrap `resources.GetRemote` in `try`, `site.Pages` (not `site.AllPages`), `hugo.Data`, `site.Language.Locale`, `imaging.jpeg.quality`/`imaging.webp.quality` set to 90, `build.noJSConfigInAssets: true`, front-matter integers are `uint64`.
- Commits are SSH-signed: `SSH_AUTH_SOCK=$(ls ~/.keychain/*.s | head -1) git commit ...`. Never `--no-gpg-sign`.
- A global commit hook rejects some private words, including the name of Bas's employer. Never write it in committed files (tests, allow file, templates, comments); find pages by glob or front matter instead of by slug.
- No content changes: files under `content/` stay untouched.
- No existing URL may disappear. Trailing slashes everywhere. Heading ids stay goldmark `autoHeadingIDType: github`.
- No Hugo modules, no `themes/`, no Node toolchain, no SCSS.
- Fonts self-hosted WOFF2 (SIL OFL): Bricolage Grotesque (headings), Geist (body, UI), Geist Mono (dates, reading times, tags, code). No Google Fonts request.
- Palette. Light: bg `#f5f5f4`, panel `#ebebea`, text `#1a1a19`, muted `#61615f`, accent `#b9431a`. Dark: `#141413`, `#1d1d1c`, `#ededeb`, `#9c9c98`, accent `#ee8257`. One accent only.
- Radii: 14 px for large panels and images, 8 px for buttons, chips and inputs.
- Target browsers: evergreen releases of the last two years (Baseline 2024); content readable without JavaScript.
- Budgets: under 15 KB of own JS (gzip) on a post page; post page under 300 KB and under 20 requests before comments load; homepage under 2 MB.
- Accessibility: no serious or critical axe violations; WCAG AA contrast; visible focus; skip link; `prefers-reduced-motion` respected; no motion on scroll.
- UI copy in sentence case, no em dashes.
- Analytics: GA `G-B50P3BHJ6C` and Plausible `https://plausible.nijho.lt/js/pa-ylHri3AS4w8PLULPjHH4G.js`, production context only. giscus settings stay as in `config/_default/params.yaml` (`mapping: pathname`).
- RSS `guid` text is `.RelPermalink`, byte-identical to today, with `isPermaLink="false"`; `<link>` is absolute.
- `baseURL: https://www.nijho.lt/`; deploy-preview and branch contexts pass `--baseURL "$DEPLOY_PRIME_URL"`.
- Baseline commit for parity: `0a0e6ad` (stored in `tools/parity-baseline.txt`; updated only in Task 19).

## Review Focus

1. Directory names with dots and underscores and author slugs with dots or percent-encoding (`/project/rsync-time-machine.py/`, `/project/nijho.lt/`, `/publication/phd_thesis/`, `/authors/andrey-e.-antipov/`) must render at exactly those paths. Test in Task 7.
2. Featured-image variants: a GIF featured image (not resized), `image.preview_only: true` (hidden on the single page, kept in lists and `og:image`), `image.placement: 2` (wide), a `thumbnail*` file (lists only), no featured image (`og:image` falls back to the 512 px icon). Tests in Tasks 8 and 12.
3. `content/post/advent-of-open-source/retrospective.md` has no front matter; it must still build at the same path with the same `<title>` as the baseline. Test in Task 13.
4. The GitHub star fetch fails (rate limit or offline): the build must succeed and still render all 51 project cards, sorted by date. Test in Task 14.
5. JavaScript disabled: all project cards visible, menu links work, the theme follows the OS, and controls that need JS stay hidden. Test in Task 17.

---

## Part A: parity check (PR 1, merges to `main` on its own)

### Task 1: Tools package, site builder and build loader

**Files:**
- Create: `tools/pyproject.toml`, `tools/parity/__init__.py`, `tools/parity/build.py`, `tools/parity/site.py`, `tools/parity-baseline.txt`
- Create: `tools/tests/conftest.py`, `tools/tests/test_site_loader.py`, `tools/tests/fixtures/mini/` (hand-written mini build: `index.html`, `post/a/index.html`, `post/index.xml`, `sitemap.xml`, `_redirects`)
- Modify: `.gitignore` (add `resources/`, `.hugo_build.lock`, `tools/.venv/`)

**Interfaces:**
- Produces:
  - `parity.build.BuildError(Exception)` carrying Hugo's stderr.
  - `parity.build.build_site(src: Path, out: Path, *, production: bool = True, base_url: str | None = None, env: dict[str, str] | None = None) -> Path`: runs `$HUGO_BIN --gc --minify -s src -d out` (plus `--baseURL` when given). With `production`, sets `HUGO_ENV=production` and `HUGO_ENABLEGITINFO=true`. Raises `BuildError` on a non-zero exit.
  - `parity.build.build_at_commit(repo: Path, commit: str, out: Path) -> Path`: `git worktree add --detach` into a temp dir, `build_site`, `git worktree remove --force`. Writes the full sha to `out/.parity-commit` and reuses `out` when that file already matches.
  - `parity.site.norm_url(url: str) -> str`: strips `https://www.nijho.lt`, `http://www.nijho.lt` and `//www.nijho.lt`; returns relative URLs unchanged; returns other hosts unchanged.
  - `parity.site.FeedItem(title: str, link: str, guid: str, text: str)`, `parity.site.Feed(title: str, link: str, items: list[FeedItem])` (frozen dataclasses; `text` is the description with tags stripped and whitespace collapsed).
  - `parity.site.Redirect(source: str, target: str, status: int, force: bool)` (frozen dataclass).
  - `parity.site.Build(root: Path)` with `files() -> set[str]` (posix paths relative to root, leading `/`), `pages() -> list[str]` (all `.html`), `soup(path: str) -> BeautifulSoup` (cached), `feeds() -> list[str]` (all `index.xml`), `feed(path: str) -> Feed`, `sitemap_locs() -> set[str]` (normalised paths), `redirects() -> list[Redirect]` (parsed `/_redirects`; default status 301; `!` sets `force`), `resolves(path: str) -> bool` (true if `path` is a file, `path + "index.html"` is a file for paths ending in `/`, or a redirect source matches it, including `*` splats and `:placeholder` segments).

- [ ] **Step 1: Write the failing tests** in `tools/tests/test_site_loader.py`:

```python
def test_norm_url():
    assert norm_url("https://www.nijho.lt/post/a/") == "/post/a/"
    assert norm_url("/post/a/") == "/post/a/"
    assert norm_url("https://github.com/x") == "https://github.com/x"

def test_mini_build(mini):  # fixture: Build(tests/fixtures/mini)
    assert "/post/a/index.html" in mini.files()
    assert mini.sitemap_locs() == {"/", "/post/a/"}
    assert mini.feed("/post/index.xml").items[0].guid == "/post/a/"
    assert mini.redirects()[0] == Redirect("/old/", "/post/a/", 301, False)
    assert mini.resolves("/post/a/") and mini.resolves("/old/") and not mini.resolves("/nope/")

def test_resolves_splat(mini):  # fixture _redirects has "/tags/* /tag/:splat 301"
    assert mini.resolves("/tags/python/")

@pytest.mark.slow
def test_build_at_commit_caches(tmp_path, repo_root):
    out = build_at_commit(repo_root, "0a0e6ad", tmp_path / "b")
    assert (out / "index.html").exists() and (out / ".parity-commit").read_text().startswith("0a0e6ad")
```

- [ ] **Step 2: Run, expect failures.** `cd tools && uv run pytest -q` reports import errors for `parity.site`.
- [ ] **Step 3: Implement** `tools/pyproject.toml` (hatchling; package `parity`; deps `beautifulsoup4`, `lxml`, `pyyaml`, `httpx`; dev group `pytest`, `playwright`, `axe-playwright-python`; pytest marker `slow`; `[project.scripts] parity = "parity.__main__:main"`), then `build.py` and `site.py` per the interfaces. Write `0a0e6ad` to `tools/parity-baseline.txt`.
- [ ] **Step 4: Run** `cd tools && uv run pytest -q`. Expect all pass (the slow test builds the baseline once, about a minute).
- [ ] **Step 5: Commit** `git add tools .gitignore && git commit -m "Parity tool: site builder and build loader"`

### Task 2: Path, sitemap and feed checks, plus the allow file

**Files:**
- Create: `tools/parity/checks.py`, `tools/parity/allow.py`, `tools/tests/test_checks_outputs.py`, fixture pairs `tools/tests/fixtures/{base,cand}-*/`

**Interfaces:**
- Consumes: `Build`, `Feed`, `norm_url` (Task 1).
- Produces:
  - `parity.checks.Finding(check: str, path: str, detail: str)` (frozen dataclass).
  - `parity.checks.check_paths(base: Build, cand: Build) -> list[Finding]`: every baseline file matching `PUBLIC_RE` exists in the candidate. `PUBLIC_RE` covers `.html .xml .json .webmanifest .txt .asc .png .jpg .jpeg .gif .svg .webp .mp4 .mov .py .js` plus `/_headers` and `/_redirects`. Excludes `^/(css|js|webfonts|en/js)/` and names containing `_hu` followed by 32 hex digits.
  - `parity.checks.check_sitemap(base, cand)`: the candidate set is a superset of the baseline set, and every candidate loc ending in `/` has `index.html`.
  - `parity.checks.check_feeds(base, cand)`: per baseline feed, the candidate feed exists. Channel `title` and normalised `link` match. The `guid` sets are byte-identical. Normalised `link` sets are equal. `text` matches per guid.
  - `parity.allow.AllowRule(check: str, path: str, match: str | None, reason: str)`.
  - `parity.allow.load_allow(path: Path) -> list[AllowRule]`, from YAML entries with keys `check`, `path` (fnmatch glob), optional `match` (substring of `detail`) and `reason` (required, non-empty).
  - `parity.allow.partition(findings: list[Finding], rules: list[AllowRule]) -> tuple[list[Finding], list[Finding], list[AllowRule]]`: returns failures, allowed, and unused rules.

- [ ] **Step 1: Write failing tests** with tiny fixture pairs, one per rule:
  - `test_paths_missing_page_fails`
  - `test_paths_ignores_fingerprinted_css_and_hu_images`
  - `test_sitemap_superset_and_missing_index_fails` (a loc whose `index.html` is absent fails, which reproduces today's tag-page bug)
  - `test_feed_guid_must_be_byte_identical` (`/post/a/` vs `https://www.nijho.lt/post/a/` fails)
  - `test_feed_link_compared_by_path` (relative vs absolute link passes)
  - `test_allow_partition_and_unused_rules`
  - `test_allow_requires_reason`
- [ ] **Step 2: Run** `cd tools && uv run pytest tests/test_checks_outputs.py -q`. Expect failures.
- [ ] **Step 3: Implement** the three checks and `allow.py`.
- [ ] **Step 4: Run.** Expect pass.
- [ ] **Step 5: Commit** `git commit -m "Parity tool: path, sitemap and feed checks with an allow file"`

### Task 3: Anchor, SEO and article-content checks

**Files:**
- Modify: `tools/parity/checks.py`
- Create: `tools/tests/test_checks_pages.py` + fixtures

**Interfaces:**
- Produces:
  - `parity.checks.article_root(soup) -> Tag | None`: first match of `.prose` (new theme), then `.article-style` (HugoBlox).
  - `parity.checks.HOME_IDS = ("about", "blog-posts", "projects", "photography", "publications", "contact")`.
  - `parity.checks.check_ids(base, cand)`: per baseline page, every `id` inside `article_root`, plus `HOME_IDS` on `/index.html`, exists anywhere in the candidate page.
  - `parity.checks.seo_fields(soup) -> dict[str, str]` with keys:
    - `title`, `description`, `canonical`, `robots`
    - `og:title`, `og:description`, `og:type`, `og:url`, `og:image`
    - `twitter:card`, `twitter:site` (read from `name=` or `property=`)
    - `article:published_time`, `article:modified_time`
    - `feeds` (sorted, comma-joined normalised hrefs of `link[rel=alternate][type="application/rss+xml"]`)
    - `jsonld:@type`, `jsonld:headline`, `jsonld:datePublished`, `jsonld:dateModified`, `jsonld:author` (first JSON-LD object that has a `headline`, else the first object)

    All URL values pass through `norm_url`.
  - `parity.checks.check_seo(base, cand)`: one finding per differing key, `detail = f"{key}: {old!r} -> {new!r}"`.
  - `parity.checks.check_content(base, cand)`: for pages under `/post/`, `/project/` and `/publication/` with an `article_root` in both builds, the visible text matches after collapsing whitespace and dropping heading-anchor `#` glyphs. The counts of `img`, `pre`, `table`, `video` and `details` must also match.

- [ ] **Step 1: Write failing tests:**
  - `test_ids_missing_heading_anchor_fails`
  - `test_ids_home_sections_required`
  - `test_seo_relative_vs_absolute_canonical_equal`
  - `test_seo_twitter_property_vs_name_equal`
  - `test_seo_title_change_reported`
  - `test_content_dropped_callout_text_fails`
  - `test_content_counts_pre_and_table`
- [ ] **Step 2: Run.** Expect failures.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run.** Expect pass.
- [ ] **Step 5: Commit** `git commit -m "Parity tool: anchor, SEO and article-content checks"`

### Task 4: Old-image, internal-link and redirect checks

**Files:**
- Modify: `tools/parity/checks.py`
- Create: `tools/parity/old_images.py`, `tools/tests/test_checks_links.py` + fixtures

**Interfaces:**
- Produces:
  - `parity.checks.check_old_images(base, cand)`: every baseline path containing `_hu<32 hex>` that is absent from the candidate must be the source of a candidate redirect whose target exists in the candidate.
  - `parity.checks.check_internal_links(base, cand)`: every `href` and `src` in candidate HTML that is root-relative or on www.nijho.lt satisfies `cand.resolves(path)` after dropping the query and fragment. Pure `#fragment` links are skipped.
  - `parity.checks.check_redirects(base, cand)`: every baseline `(source, target)` pair is present among the candidate redirects.
  - `parity.checks.ALL_CHECKS: dict[str, Callable[[Build, Build], list[Finding]]]` with keys `paths sitemap feeds ids seo content old-images internal-links redirects`, in that order.
  - `parity.old_images.map_old_images(base: Build, repo: Path, cand: Build) -> dict[str, str]`:
    - For each baseline `_hu` image the candidate lacks, take the md5 in its name. Hugo 0.123 names resizes `<stem>_hu<md5 of source>_...`.
    - Find the source file with that md5 under `content/` or `assets/`.
    - Map to the candidate path that publishes that source: the bundle path for page resources, `/media/<rel>` for `assets/media/<rel>`.
    - Raises `ValueError` listing any image with no source or no published target.
- [ ] **Step 1: Write failing tests:**
  - `test_old_image_needs_redirect_to_existing_file`
  - `test_internal_link_to_missing_page_fails`
  - `test_internal_link_via_splat_redirect_passes`
  - `test_baseline_redirect_dropped_fails`
  - `test_map_old_images_by_source_md5` (fixture: a source file and a fake `_hu<md5>` name)
- [ ] **Step 2: Run.** Expect failures.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run.** Expect pass.
- [ ] **Step 5: Commit** `git commit -m "Parity tool: old-image, internal-link and redirect checks"`

### Task 5: CLI, live sweep and baseline self-test

**Files:**
- Create: `tools/parity/__main__.py`, `tools/parity/live.py`, `tools/parity-allow.yaml` (empty list), `tools/README.md`, `tools/tests/test_cli.py`
- Modify: `devbox.json` (script `"parity": "cd tools && uv run parity compare-branch"`)

**Interfaces:**
- Consumes: everything above.
- Produces the CLI `parity`, with these subcommands:
  - `baseline [--commit SHA] OUT`: defaults to `tools/parity-baseline.txt`.
  - `compare BASE CAND [--allow FILE] [--only CHECK ...]`: prints findings grouped by check, then allowed counts and unused allow rules. Exits 1 on any failure.
  - `compare-branch [--allow FILE]`: builds the baseline into `/tmp/parity-baseline/<sha>` and the working tree into `/tmp/parity-candidate-<hash of the repo path>` (printed in the report header), then runs `compare`.
  - `old-images BASE CAND --repo PATH`: prints YAML for `data/old_images.yaml`.
  - `live --preview URL [--sitemap URL]`: fetches every loc path from both the live site and the preview, with no redirect following and 16 concurrent requests. Each preview status must equal the live status (200, or a 301 with the same normalised `Location`). Exits 1 on any mismatch.
- [ ] **Step 1: Write failing tests:**
  - `test_compare_exit_codes` (uses the Task 2 fixtures through `main(["compare", ...])`)
  - `test_live_status_mismatch`: serve two tiny dirs with `http.server` on random ports, and expect exit 1 when the preview 404s a loc that is live
  - `@pytest.mark.slow test_baseline_self_compare_is_clean`: two separate `build_site` outputs of commit `0a0e6ad` compare with zero findings and an empty allow file
- [ ] **Step 2: Run.** Expect failures.
- [ ] **Step 3: Implement.** `tools/README.md` gets usage for each subcommand plus the `HUGO_BIN` note.
- [ ] **Step 4: Run** `cd tools && uv run pytest -q -m "slow or not slow"`. Expect all pass. Then `devbox run parity` (or `uv run parity compare-branch`) on this branch, which still has the old theme, and expect `0 failures`.
- [ ] **Step 5: Commit** `git commit -m "Parity tool: CLI, live sweep, baseline self-test"`. Then `git branch -f parity-check HEAD`, push `parity-check`, and open PR 1 "Parity check for the theme replacement" with the spec, design reference and `tools/`. Link it with the t3-code `link_pull_request` tool.

### Task 5b: Separate Hugo binaries for baseline and candidate

Added after the decision to target Hugo 0.167.0.

**Files:** Modify `tools/parity/build.py`, `tools/parity/__main__.py`, `tools/README.md`, tests.

**Interfaces:**
- `build_site(..., hugo: str | None = None)` defaults to `$HUGO_BIN`, then `hugo`.
- `build_at_commit(..., hugo: str | None = None)` defaults to `$HUGO_BASELINE_BIN`, then `$HUGO_BIN`, then `hugo`. Its cache marker records the sha plus the Hugo version.
- `baseline` and `compare-branch` build the baseline with the baseline binary and the candidate with `$HUGO_BIN`. Options `--baseline-hugo` and `--hugo` override them, and the report header prints both versions.

- [ ] Tests first (fake hugo scripts), implement, `uv run pytest -q -m "slow or not slow"` green, commit `Parity tool: separate Hugo binaries for baseline and candidate`.

---

## Part B: the theme (PR 2, branch `own-theme` stacked on `parity-check`)

Shared test fixtures, created in Task 6 and used by every later task:

- `tools/tests/site/conftest.py`
  - `site` (session): `Build(build_site(REPO_ROOT, tmp/"cand"))`, built with `$HUGO_BIN` (0.167.0).
  - `baseline` (session): `Build(build_at_commit(REPO_ROOT, sha, Path("/tmp/parity-baseline")/sha))`, built with `$HUGO_BASELINE_BIN` (0.123.3).
  - Absolute helpers from Task 5: `sitemap_locs_without_page(build)` and `broken_internal_links(build)`.
  - `allow` (session): `load_allow(tools/parity-allow.yaml)`.
  - Helper `failures(check: str) -> list[Finding]`: runs `ALL_CHECKS[check](baseline, site)` and returns `partition(...)[0]`.
- Run the site tests with `cd tools && uv run pytest tests/site -q`.

### Task 6: Drop the modules; skeleton templates that render every page

**Files:**
- Delete: `config/_default/module.yaml`, `go.mod`, `go.sum`, and these HugoBlox-specific layouts (port from `git show 0a0e6ad:<path>` where later tasks say so):
  - `layouts/partials/views/*`
  - `layouts/partials/blocks/v1/portfolio.html`
  - `layouts/partials/page_metadata*.html`
  - `layouts/partials/site_footer.html`
  - `layouts/partials/anchored-headings.html`
  - `layouts/partials/analytics/google_analytics.html`
  - `layouts/partials/hooks/**`
  - `layouts/_default/single.html`, `layouts/_default/list.html`
- Move (`git mv`, contents unchanged unless noted): `layouts/partials/functions/` to `layouts/_partials/functions/`; `layouts/shortcodes/` to `layouts/_shortcodes/` (adapted in Task 11). In `github_stars.html`, replace the `.Err` check with `try` (`{{ with try (resources.GetRemote $url) }}{{ with .Err }}{{ warnf ... }}{{ else with .Value }}...`): a failed request must still only warn.
- Modify: `config/_default/hugo.yaml`
  - `baseurl: https://www.nijho.lt/`
  - `pagination: {pagerSize: 100}` (replaces `paginate: 100`, which 0.167 ignores silently)
  - `outputs` for home, section, taxonomy and term, `outputFormats` and `mediaTypes` (guide section 1.3)
  - `markup` (see Step 3)
  - `imaging: {resampleFilter: lanczos, anchor: smart, jpeg: {quality: 90}, webp: {quality: 90}}`
  - `build: {noJSConfigInAssets: true}`
  - `sitemap: {changefreq: weekly}`
  - `security`: the narrowest `allowContent` (or equivalent) setting that lets the `bleed-svg` shortcode keep reading its existing `.html` SVG fragment from a post bundle (guide gotcha 4). That bundle's path contains a hook-blocked word, so the file cannot be renamed or edited.
  - `config/_default/languages.yaml`: `locale: en-us` replaces `languageCode` if 0.167 warns about it.
- Create:
  - `layouts/baseof.html`, `layouts/home.html`, `layouts/page.html`, `layouts/section.html`, `layouts/taxonomy.html`, `layouts/term.html`, `layouts/404.html`
  - `layouts/_partials/head.html`, `layouts/_partials/site-header.html`, `layouts/_partials/site-footer.html`
  - `tools/tests/site/conftest.py`, `tools/tests/site/test_structure.py`

**Interfaces:**
- Produces:
  - Blocks `main` and `head_extra` in `baseof.html`.
  - `<main id="main">`; a skip link to `#main`.
  - `<body class="kind-{{ .Kind }} type-{{ .Type }}">`.
  - Every later template defines `main`.

- [ ] **Step 1: Write failing tests** in `test_structure.py`:

```python
def test_no_modules(repo_root):
    assert not (repo_root / "go.mod").exists() and not (repo_root / "config/_default/module.yaml").exists()

def test_every_baseline_page_exists(site, baseline):
    missing = [p for p in baseline.pages() if p not in site.files()]
    assert missing == []

def test_term_and_project_index_pages_exist(site):
    for p in ["/tags/index.html", "/tag/ai/index.html", "/categories/index.html", "/project/index.html",
              "/publication_types/index.html", "/authors/page/2/index.html"]:
        assert p in site.files()

def test_every_sitemap_loc_has_a_page(site):
    assert sitemap_locs_without_page(site) == []
    assert failures("sitemap") == []
```

- [ ] **Step 2: Run** with `HUGO_BIN=/tmp/hugo-latest/bin/hugo`. Expect failures (modules still present).
- [ ] **Step 3: Implement.**
  - Delete the module files.
  - Port the theme's markup defaults into `hugo.yaml`:
    - `goldmark.renderer.unsafe: true`
    - `goldmark.parser.attribute: {block: true, title: true}`
    - `goldmark.parser.autoIDType: github` (the 0.167 name for `autoHeadingIDType`)
    - `highlight: {noClasses: false, codeFences: true, guessSyntax: true}`
    - `tableOfContents: {startLevel: 2, endLevel: 3}`
  - Output formats: `headers` (`baseName: _headers`) and `redirects` (`baseName: _redirects`), both `mediaType: text/netlify`, `isPlainText`, `notAlternative`; media type `text/netlify` with an empty suffix.
  - Templates render title plus `.Content` or a plain list of `.Pages` links; no styling yet.
- [ ] **Step 4: Run.** Expect pass. Also run `$HUGO_BIN --gc --minify -d /tmp/own-theme-out`, which must exit 0 with no `ERROR` lines.
- [ ] **Step 5: Commit** `git commit -m "Theme: drop HugoBlox modules, skeleton templates for every page kind"`

### Task 7: CSS foundation, fonts, header, footer, theme toggle

**Files:**
- Create:
  - `assets/css/main.css`, `layouts/_partials/head/css.html`
  - `assets/css/00-reset.css`, `01-tokens.css` (palette, `@font-face`, radii, `--max: 1240px`, spacing scale from `mockup.css`), `02-base.css`, `03-layout.css`, `04-components.css` (buttons, chips, cards)
  - `static/fonts/bricolage-grotesque-latin.woff2`, `geist-latin.woff2`, `geist-italic-latin.woff2`, `geist-mono-latin.woff2`
  - `assets/js/theme.js`, `assets/js/nav.js`, `layouts/_partials/theme-menu.html`, `tools/tests/site/test_foundation.py`
- Modify: `layouts/_partials/head.html`, `site-header.html`, `site-footer.html`

**Interfaces:**
- Produces:
  - CSS bundle: `assets/css/main.css` declares `@layer reset, tokens, base, layout, components, prose, syntax, home, pages, icons, shortcodes;` and `@import`s each file with `layer(<name>)`. `layouts/_partials/head/css.html` (called with `partialCached`) builds it with `css.Build (dict "minify" true "targetPath" "css/main.css" "target" (slice "chrome120" "edge120" "firefox117" "safari17.2" "ios17.2")) | fingerprint`, linked with SRI. That target keeps native nesting as written. The numbered file names (`00-reset.css`, ...) stay for readability; `main.css` sets the order.
  - Theme state: `localStorage["theme"]` in `light | dark | auto` (default `auto`); `<html data-theme="light|dark">` is set only when pinned.
  - The inline head script is at most 400 bytes.
  - Header nav: menu entries from `menus.yaml` rendered as `/#<anchor>` links, active state through `aria-current` (`nav.js` tracks the visible homepage section with `IntersectionObserver`). Header at most 72 px tall, nav on one line from 1024 px.
  - Footer: `© <year> Bas Nijholt. Source code on GitHub and builds on Netlify.`, an RSS link, and a back-to-top link.
  - Mobile menu and theme menu use the Popover API.
- [ ] **Step 1: Write failing tests:**
  - `test_css_bundle_fingerprinted_and_nested_rules_survive_minify`: the bundle contains a nested selector from `03-layout.css` (for example `.site-header{` followed by a nested `&` rule) and an `@layer layout{` block, and has no `/* ns-hugo` comments.
  - `test_no_google_fonts`: no `fonts.googleapis.com` in any page.
  - `test_fonts_preloaded`: the two most-used WOFF2 files are preloaded.
  - `test_theme_init_inline_script_before_css`
  - `test_unusual_paths_exist`: `/project/rsync-time-machine.py/index.html`, `/project/nijho.lt/index.html`, `/publication/phd_thesis/index.html`, `/authors/andrey-e.-antipov/index.html`, and every baseline `/authors/*` dir containing `%`.
  - `test_header_has_six_menu_links_and_skip_link`
- [ ] **Step 2: Run.** Expect failures.
- [ ] **Step 3: Implement**, porting values and rules from `mockup.css` sections tokens, base, header, footer and buttons.
  - Fonts: download the OFL variable fonts (Geist and Geist Mono from the vercel/geist-font release, Bricolage Grotesque from google/fonts `ofl/bricolagegrotesque`).
  - Subset each with `uvx --from 'fonttools[woff]' pyftsubset <ttf> --unicodes='U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD' --flavor=woff2 --layout-features='*'`.
  - Add the OFL license texts as `static/fonts/LICENSE-*.txt`.
- [ ] **Step 4: Run.** Expect pass. Screenshot the header in light and dark (`tools/screenshots.py` arrives in Task 17; for now use a one-off Playwright call) and compare against `home-w1-desktop-light.webp`.
- [ ] **Step 5: Commit** `git commit -m "Theme: CSS layers, self-hosted fonts, header, footer, theme menu"`

### Task 8: SEO head

**Files:**
- Create:
  - `layouts/_partials/head/seo.html`, `head/jsonld.html`, `head/icons.html`, `head/analytics.html`
  - `layouts/_partials/functions/page_title.html`, `description.html`, `featured_image.html`, `og_image.html`
  - `static/favicon.ico` (generated from `assets/media/icon.png`, 32 and 48 px)
  - `tools/tests/site/test_seo.py`
- Modify: `layouts/_partials/head.html`, `netlify.toml`, `tools/parity-allow.yaml`

**Interfaces:**
- Produces (partials that return values):
  - `functions/page_title.html` (page) → string: `.Params.seo.title` or `.Title`, plus ` | Bas Nijholt` unless empty or equal to `site.Title`.
  - `functions/description.html` (page) → plain string: `summary` → `abstract` → `.Summary` (regular pages) → `site.Params.marketing.seo.description` → the superuser's `role`, then `plainify | htmlUnescape | chomp`.
  - `functions/featured_image.html` (page) → resource or nil: first `.Resources.ByType "image"` matching `*featured*`, then `.Params.image.filename` in the bundle, then `resources.Get (printf "media/%s" filename)`.
  - `functions/og_image.html` (page) → `dict "url" <absolute URL> "card" "summary"|"summary_large_image"`: on `/authors/admin/` the avatar `Fill "270x270 Center"`; otherwise the featured image original `.Permalink`; otherwise `icon.png` `Fill "512x512 Center"`.
- Head contents: `<title>`, meta description, canonical, `hreflang="en-us"`, robots (`noindex` for `private: true` or when `hugo.Environment` is not `production`), meta author, `og:*` (`og:type` is `profile` on home, `article` on regular pages, `website` otherwise; `og:locale` is `en_US`), `twitter:*` with `name=`, time metas (regular pages: `article:published_time` from `.PublishDate` or `.Date`, `article:modified_time` from `.Lastmod`, format `2006-01-02T15:04:05-07:00`; other kinds: `og:updated_time` from the newest member page's date, omitted when zero), feed `link` on kinds with RSS, icons 32/180/192 plus `/favicon.ico`, manifest, `theme-color` (light `#f5f5f4`, dark `#141413` via `media`), and `rel="me"` `https://fosstodon.org/@basnijholt`.
- JSON-LD:
  - `WebSite` with `SearchAction` plus `Person` on home.
  - `BlogPosting` (posts), `Article` (projects), `ScholarlyArticle` (publications), each with `mainEntityOfPage`, `headline`, `image`, `datePublished`, `dateModified`, `author`, `publisher` (Organization "Bas Nijholt" + icon 192), `description`.
  - `BreadcrumbList` on posts.
- Analytics: port the GA snippet from `git show 0a0e6ad:layouts/partials/analytics/google_analytics.html` and the Plausible snippet from `git show 0a0e6ad:layouts/partials/hooks/head-end/plausible.html`; both only when `hugo.IsProduction`.
- `netlify.toml`: `HUGO_ENV = "production"` only under `[context.production.environment]`. Preview and branch commands add `--baseURL "$DEPLOY_PRIME_URL"`.
- Allow file gets one entry per deliberate change, each with a reason: `og:locale`, twitter `name=`, description plainify (only pages whose baseline description contained Markdown), new JSON-LD types, section `og:updated_time`.
- [ ] **Step 1: Write failing tests** in `test_seo.py`:
  - `test_seo_parity_clean`: `failures("seo") == []`
  - `test_canonical_absolute`
  - `test_description_has_no_markdown_link_syntax` (no `](` in any meta description)
  - `test_og_image_gif_featured_is_original`: a post with `featured.gif` found by glob; its `og:image` ends with `/featured.gif` and is not a `_hu` name
  - `test_og_image_fallback_icon_512_summary`: a post without `featured.*`
  - `test_preview_only_still_in_og_image`: a post with `preview_only: true`, found by front matter
  - `test_jsonld_types_per_kind`
  - `test_analytics_only_in_production` (build once with `production=False`: no gtag, robots `noindex`)
- [ ] **Step 2: Run.** Expect failures.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run.** Expect pass.
- [ ] **Step 5: Commit** `git commit -m "Theme: SEO head, JSON-LD, icons, production-only analytics"`

### Task 9: Feeds, sitemap, robots, manifest, headers, search index, redirects

**Files:**
- Create:
  - `layouts/rss.xml`, `layouts/robots.txt`, `layouts/home.webmanifest`, `layouts/home.headers`, `layouts/home.redirects`, `layouts/home.json`
  - `data/redirects.yaml`, `data/old_images.yaml`, `tools/derive_tag_redirects.py`
  - `tools/tests/site/test_machine_files.py`
- Delete: `static/_redirects`

**Interfaces:**
- Produces:
  - `data/redirects.yaml`: a list of `{from: str, to: str, status: 301|302 (default 301), force: bool (default false)}`. `home.redirects` renders, in order: front-matter `aliases` from `site.Pages` (`site.AllPages` is deprecated; `{{ alias }} {{ page.RelPermalink }}`), then `data/redirects.yaml`, then the old-image redirects. `data/old_images.yaml` is a list of `{file, size, names}` (output of `parity old-images`; Hugo 0.123 names `<stem>_hu<hash>_<size>_...`). For each entry, the template finds every candidate image resource whose basename equals `file` and whose `len .Content` equals `size`: page resources of `site.Pages` plus `resources.Match "media/**"`. For each match it emits `<dir of resource.RelPermalink>/<name> <resource.RelPermalink> 301`, which publishes the original as the target. Hugo 0.167 renames every processed image (`<stem>_hu_<hash>.<ext>`), so all old resize URLs need these rules. It emits `301` plus `!` when `force`.
  - RSS:
    - Channel: title, link, `atom:link rel=self`, description = page title, language `en-us`, copyright `© <year>`, `lastBuildDate`, `image` when `og_image` exists.
    - Items: all `.RegularPages` of the context (home: `site.RegularPages`), no limit, each with `title`, absolute `link`, `pubDate` (`Mon, 02 Jan 2006 15:04:05 -0700`), `<guid isPermaLink="false">{{ .RelPermalink }}</guid>`, and `description` = escaped full `.Content`.
  - `index.json`: keys `objectID date publishdate lastmod expirydate lang permalink relpermalink title summary content authors kind type section tags categories`; page set = regular pages plus the superuser author page, minus drafts, `private`, `searchable: false`; `content` = `.Plain` truncated to 5000.
  - `_headers`: the six security headers on `/*` (copy from `git show 0a0e6ad` build output), `application/rss+xml` for `/index.xml`, `application/manifest+json` for `/manifest.webmanifest`.
- `data/redirects.yaml` content (spec table "Redirects to add"):
  - `/post/glove80-experience/` stays an alias.
  - `/post/llamaswap/ → /post/llama-nixos/`.
  - 24 rules `/post/advent-of-open-source/day_NN/ → /post/advent-of-open-source/NN-<slug>/`, mapping NN to the directory under `content/post/advent-of-open-source/` that starts with `NN-`.
  - `/tags/* → /tag/:splat`, `/categories/* → /category/:splat`.
  - `/publication_types/* → /publication/`, `/publication-type/2/`, `/3/`, `/7/ → /publication/`.
  - `/post/page/* → /post/`, `/project/page/* → /project/`, `/tags/page/* → /tags/`, `/tag/:t/page/* → /tag/:t/`.
  - Old co-author slugs: query `https://web.archive.org/cdx/search/cdx?url=www.nijho.lt/authors/*&output=json&fl=original&collapse=urlkey`, take archived author paths that are not current terms, map each by normalised name to the current slug, and drop any without a confident match.
  - Removed tags: output of `tools/derive_tag_redirects.py d3b3736`. It reads each post's front-matter tags before and after that commit, maps each removed tag to the new tag it most often became, and prints YAML entries for both `/tag/<old>/` and `/tag/<old>/index.xml`. Review the output by hand and delete unconvincing pairs.
  - `https://nijholt.netlify.app/* → https://www.nijho.lt/:splat`, `force: true`.
- `data/old_images.yaml`: the output of `uv run parity old-images /tmp/parity-baseline/<sha> /tmp/parity-candidate-<hash>` (paths from the `compare-branch` header) after the image-producing templates exist. Regenerate it at the end of Tasks 12, 14 and 15 and in Task 19.
- Parity tool change in this task (controller ruling): `check_old_images` proves the final redirect target is the original by Hugo fast hash and byte size (they must equal the hash and size in the old 0.123 name), replacing the stem-name rule, which wrongly flags 3 album images whose 0.123 names lost the stem. Use `hugo_fast_md5_file` on the candidate file.
- [ ] **Step 1: Write failing tests:**
  - `test_old_image_target_identity_by_hash_and_size` (tools/tests, table style: right original passes, same-stem other image fails, the 3 stemless album names pass)
  - `test_feed_parity_clean` (`failures("feeds") == []`)
  - `test_guid_relative_with_ispermalink_false`
  - `test_home_feed_has_every_regular_page`
  - `test_robots_sitemap_absolute`
  - `test_headers_manifest_rule`
  - `test_index_json_schema_and_count` (keys exactly as listed; count equals the baseline's)
  - `test_redirects_parity_clean`
  - `test_redirects_cover_day_nn_and_llamaswap`
  - `test_every_redirect_target_resolves` (root-relative targets satisfy `site.resolves`)
- [ ] **Step 2: Run.** Expect failures.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run.** Expect pass.
- [ ] **Step 5: Commit** `git commit -m "Theme: feeds, machine files, and redirects for old URLs"`

### Task 10: Render hooks and content shortcodes

**Files:**
- Create:
  - `layouts/_markup/render-heading.html`, `render-link.html`, `render-image.html`, `render-codeblock-mermaid.html`
  - `layouts/_shortcodes/callout.html`, `figure.html`, `video.html`, `gallery.html`
  - `assets/css/05-prose.css`, `assets/css/06-syntax.css` (Chroma classes, light and dark from `mockup.css`)
  - `tools/tests/site/test_content.py`
- Modify: `layouts/_shortcodes/toc.html` (rewrite; tracked now)

**Interfaces:**
- Produces:
  - Article body container `<div class="prose">` (the parity `article_root`).
  - Heading hook: `<hN id="{{ .Anchor }}">{{ .Text }} <a class="anchor" href="#{{ .Anchor }}" aria-label="Link to this section">#</a></hN>` for levels 2 and 3; other levels plain with the id.
  - Link hook: `http*` links get `target="_blank" rel="noopener"`.
  - Image hook: same output as `figure` (caption from the title).
  - `callout` `{{% callout note|warning %}}`: `<aside class="callout callout-{{ .Get 0 }}">` + icon + `.Inner | markdownify | emojify`.
  - `figure` (params `src alt caption width`): `<figure id="figure-{{ anchorize caption }}">`. Rasters get `srcset` 400/760/1200 WebP from `Fit` with `src` at 760; SVG and GIF stay original. `loading="lazy"`, `width`/`height`, `data-zoomable`. Lookup order: bundle, then `assets/media/`, then remote.
  - `video` (params `src controls autoplay loop`): honours `autoplay` (adds `muted playsinline`) and `loop`; poster `<stem>.jpg` when present.
  - `gallery` (params `album resize_options`): `Fit "350x250"` WebP thumbnails from `assets/media/albums/<album>/` linking to originals with `data-zoomable`.
  - `toc`: `<details class="toc" open><summary>Table of contents</summary>{{ .Page.TableOfContents }}</details>`.
  - Mermaid fences: `<pre class="mermaid">`; sets `.Page.Store "mermaid" true`.
- [ ] **Step 1: Write failing tests:**
  - `test_ids_parity_clean` (`failures("ids") == []`)
  - `test_content_parity_clean` (`failures("content") == []`)
  - `test_callout_renders_markdown`
  - `test_figure_srcset_and_lazy`
  - `test_video_autoplay_loop_attrs` (the shortcode use with `autoplay` found by grep in content)
  - `test_toc_open`
  - `test_external_links_target_blank`
  - `test_mermaid_only_where_used`
- [ ] **Step 2: Run.** Expect failures.
- [ ] **Step 3: Implement**, porting prose styles from `mockup.css`.
- [ ] **Step 4: Run.** Expect pass.
- [ ] **Step 5: Commit** `git commit -m "Theme: render hooks and content shortcodes"`

### Task 11: Icon shim and site shortcodes

**Files:**
- Create:
  - `assets/icons/*.svg`: Font Awesome Free 6.5.1 and academicons 1.9.4 SVGs for every name used, plus the UI icons used in `mockup.css` (search, sun, moon, star, arrow-right, link, file-pdf, code, database, github-logo, matrix-logo, etc.); `assets/icons/LICENSE.txt` (FA CC BY 4.0, academicons OFL)
  - `layouts/_partials/icon.html`, `layouts/_partials/functions/check_icons.html`
  - `assets/css/09-icons.css.tmpl`, `assets/css/10-shortcodes.css` (port of `assets/scss/custom.scss`)
  - `tools/tests/site/test_icons_shortcodes.py`
- Modify: `layouts/_shortcodes/{tooltip,detail-tag,plot,bleed-svg,demo-clips,demo-clip,photo-grid}.html` (replace `body.dark`/`.dark` with `[data-theme=dark]` plus the `prefers-color-scheme` equivalent, and `.article-style` with `.prose`; `bleed-svg` keeps reading its bundle `.html` fragment under the `security` setting from Task 6, and the test asserts its inline SVG renders)
- Delete: `assets/scss/custom.scss`

**Interfaces:**
- Produces:
  - `partial "icon.html" (dict "name" "github" "pack" "fab" "class" "")` returns inline `<svg class="icon {{class}}" aria-hidden="true">` from `assets/icons/<name>.svg`.
  - `partials/functions/check_icons.html` scans `.RawContent` of `site.AllPages` and the `content/home` and `authors/admin` params for `\b(fa[srb]?|ai) (fa|ai)-([a-z0-9-]+)` and `icon: <name>`. It calls `errorf "icon %q has no SVG in assets/icons/"` for unknown names. It is called once from `baseof.html` with `partialCached`.
  - `09-icons.css.tmpl`, run through `resources.ExecuteAsTemplate`, emits `.fa-<name>,.ai-<name>{--icon:url("data:image/svg+xml;base64,...")}` for every SVG, plus a shared rule `[class*="fa-"],[class*=" ai-"]{display:inline-block;width:1em;height:1em;background:currentColor;mask:var(--icon) center/contain no-repeat}`.
- [ ] **Step 1: Write failing tests:**
  - `test_every_content_icon_has_svg`
  - `test_unknown_icon_fails_build`: copy the repo to tmp, add `<em class="fas fa-not-an-icon">` to a copied post, and expect `build_site` to raise `BuildError` naming it
  - `test_icon_css_contains_github_mask`
  - `test_site_shortcodes_render` (photo-grid has 9 images on home; plot figure present on its post; demo-clip has both light and dark videos)
  - `test_no_body_dark_selectors_left` (grep `assets/css` and `layouts/_shortcodes` for `body.dark`)
- [ ] **Step 2: Run.** Expect failures.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run.** Expect pass. Re-run the Task 10 content and ids tests too.
- [ ] **Step 5: Commit** `git commit -m "Theme: icon shim for Font Awesome markup, site shortcodes ported"`

### Task 12: Post page

**Files:**
- Modify: `assets/js/theme.js` (tell the giscus iframe about theme changes)
- Create:
  - `layouts/post/page.html`
  - `layouts/_partials/post/breadcrumb.html`, `post/meta.html`, `post/featured.html`, `post/author-card.html`, `post/related.html`, `post/share.html`, `post/edit-link.html`
  - `layouts/_partials/comments.html`, `assets/js/toc.js`, `assets/js/code.js`, `assets/js/zoom.js`, `assets/css/08-pages.css` (post part)
  - `tools/tests/site/test_post.py`
- Modify: `layouts/page.html` (used by `/phd-defense/`: title + `.prose`, no meta)

**Interfaces:**
- Consumes: `functions/featured_image.html` (Task 8), `.prose` (Task 10), `icon.html` (Task 11).
- Produces:
  - `partial "post/meta.html" .`: author avatar + name (link `/authors/admin/`), `Published on <date "Jan 2, 2006">`, `· Last updated on <date>` only when lastmod's date differs, `<n> min read` (`.ReadingTime`), category chips linking to `/category/<urlize>/`.
  - `post/featured.html`: hidden when `image.preview_only`. `image.placement: 2` gives class `featured-wide` (`Fit "1200x2500"`), otherwise `Fit "720x2500"`. GIFs are served as the original. Caption from `image.caption | markdownify | emojify`.
  - `post/related.html`: `site.RegularPages.Related .` with `first 5`.
  - `post/share.html`: links for X/Twitter, LinkedIn, email, Mastodon share (`https://mastodonshare.com/?url=`), copy link.
  - `post/edit-link.html`: `https://github.com/basnijholt/nijho.lt/edit/main/content/{{ .File.Path }}` when `editable`.
  - `comments.html`: giscus script with every `data-*` from `site.Params.features.comment.giscus`, `data-mapping="pathname"`, `data-theme` from the current theme. `theme.js` posts `{giscus:{setConfig:{theme}}}` to the iframe on change. Rendered only when `commentable`.
  - `toc.js`: `IntersectionObserver` marks the current contents entry (`aria-current="true"`).
  - `code.js`: adds a copy button to `.highlight pre`.
  - `zoom.js`: opens `[data-zoomable]` images in a `<dialog>` at the largest `srcset` entry.
  - Each script is `js.Build (dict "minify" true "format" "esm" "targetPath" "js/<name>.js") | fingerprint` and is included only when its feature is on the page.
- [ ] **Step 1: Write failing tests:**
  - `test_post_has_breadcrumb_meta_author_related_comments`
  - `test_last_updated_only_when_different`
  - `test_preview_only_hides_featured_on_single`
  - `test_placement_2_is_wide`
  - `test_gif_featured_not_resized` (no `_hu` GIF in `site.files()`)
  - `test_category_and_tag_links_resolve`
  - `test_giscus_only_on_commentable` (absent on `/phd-defense/`)
  - `test_post_js_budget`: gzip size of the post page's own `<script src="/js/...">` files is under 15 000 bytes
- [ ] **Step 2: Run.** Expect failures.
- [ ] **Step 3: Implement**, porting markup and styles from `post.html` and `mockup.css` (breadcrumb, display title, meta row, 720 px column, sticky contents from 1100 px, author card).
- [ ] **Step 4: Run.** Expect pass. Regenerate `data/old_images.yaml`. Compare a screenshot of `/post/self-hosting-ai-is-not-cheaper/` with `post-desktop-light.webp` and `post-desktop-dark.webp`.
- [ ] **Step 5: Commit** `git commit -m "Theme: post page"`

### Task 13: Post lists, taxonomy and author pages

**Files:**
- Create:
  - `layouts/_partials/lists/post-row.html`, `layouts/post/section.html`
  - Rewrite `layouts/taxonomy.html` (taxonomy lists like `/tags/`), `layouts/term.html` (term pages like `/tag/ai/`)
  - `layouts/authors/term.html`, `layouts/authors/taxonomy.html`
  - `tools/tests/site/test_lists.py`

**Interfaces:**
- Produces `partial "lists/post-row.html" .`, the W1 row:
  - left column: `<time>` + `· <n> min read` (mono), title link, category chips
  - right column: full summary (`summary` front matter `markdownify | emojify`, else `.Summary`, which is already HTML in 0.167)
  - far right: thumbnail when the page has `thumbnail*` (`Fit "150x220"`) or a featured image (`Resize "150x"`; GIF original)
  - Used by home (Task 14), `/post/`, terms and author pages.
- Pages:
  - `/post/`: 40 top-level posts plus the advent section entry, newest first, paginated at 100.
  - Advent section: its `.Content`, then its 25 pages.
  - Terms: title, count, feed link, rows.
  - `/authors/admin/`: the about block (reuse `partials/home/about.html` from Task 14; until then a minimal version) plus latest rows.
  - Co-author pages: name plus rows. `/authors/` paginated at 100.
- [ ] **Step 1: Write failing tests:**
  - `test_post_list_counts`
  - `test_advent_page_has_body_and_25_entries`
  - `test_tag_ai_lists_all_ai_posts` (count equals the number of posts whose tags contain `ai`)
  - `test_authors_pagination`
  - `test_retrospective_builds_with_baseline_title` (Review Focus 3)
  - `test_internal_links_clean` (`failures("internal-links") == []`)
- [ ] **Step 2: Run.** Expect failures.
- [ ] **Step 3: Implement**, porting from the W1 section of `mockup.css` (`.blog-item`, `.side`, `.summary`, `.thumb`).
- [ ] **Step 4: Run.** Expect pass.
- [ ] **Step 5: Commit** `git commit -m "Theme: post lists, taxonomy and author pages"`

### Task 14: Homepage

**Files:**
- Create:
  - `layouts/_partials/home/about.html`, `home/blog.html`, `home/projects.html`, `home/photography.html`, `home/publications.html`, `home/contact.html`
  - `layouts/_partials/lists/project-card.html`, `layouts/_partials/lists/publication-item.html`
  - `assets/js/filter.js`, `assets/css/07-home.css`, `assets/media/map-kirkland.webp` (from `docs/baspowers/design/2026-10-09-mockup-d/assets/`)
  - `tools/tests/site/test_home.py`
- Modify: `layouts/home.html`

**Interfaces:**
- Consumes: `lists/post-row.html` (Task 13), `functions/github_stars.html` (existing), `icon.html` (Task 11).
- Produces:
  - `home.html` ranges over `site.GetPage "home"`'s headless resources sorted by `weight` and renders `partial (printf "home/%s.html" <widget name>)` with id = file stem.
  - `home/about.html`: avatar `Fill "540x675 Center"`, name, role + organisation link, body of `content/authors/admin/_index.md`, social icons from `social`, interests (HTML strings rendered `safeHTML`), education courses.
  - `home/blog.html`: 10 newest pages in section `post` as W1 rows, subtitle, "See all blog posts" → `/post/`.
  - `home/projects.html` and `lists/project-card.html`:
    - All projects sorted by stars descending, then date descending.
    - Card image: `animated.svg` if present, else the featured image (`Fit "600x400"` WebP; GIF original; `loading="lazy"`), else the first emoji of the summary on a plate.
    - Card text: title, star count (formatted `3.5k`), summary (`markdownify | emojify`), tags as `data-tags`. The card links to `external_link`.
    - Toolbar: filter buttons from `content/home/projects.md` `filter_button` (`tag` matched case-insensitively against `data-tags`; `*` = all) with counts, a search input, and a sort select (stars, newest, name). The toolbar carries `hidden` until `filter.js` runs.
  - `home/photography.html`: renders the section's `.Content` (keeps `photo-grid`).
  - `home/publications.html` and `lists/publication-item.html`: all publications grouped by year. Each item: title link, authors (first 6, then `and N more, including Bas Nijholt` when he is beyond 6; bold "Bas Nijholt"), venue (`publication_short` or `publication`), month and year, and link chips for `url_pdf`, `url_code`, `url_dataset`, `url_preprint` and `links[]`. Also the section's callout.
  - `home/contact.html`: large email (`content.email`), location (`content.address`), `content.directions`, every `content.contact_links` entry (icon, name, link; the PGP entry links `/bas.asc`), and the map image linking to `https://www.openstreetmap.org/?mlat=<lat>&mlon=<lon>#map=12/<lat>/<lon>` from `content.coordinates`.
  - `filter.js`: filter, search and sort over `[data-tags]` cards with an empty state; reused by `/project/` and `/publication/` (Task 15).
  - Below-the-fold sections get `content-visibility: auto; contain-intrinsic-size: auto 1000px`.
- [ ] **Step 1: Write failing tests:**
  - `test_home_section_ids_in_order`
  - `test_home_counts` (10 post rows, 51 project cards, 15 publications, 9 photos)
  - `test_home_interests_and_education`
  - `test_projects_sorted_by_stars`
  - `test_no_resized_gifs_anywhere`
  - `test_home_weight_under_2mb`: sum of sizes of the home HTML, CSS, JS, fonts and every non-lazy image is under 2 000 000 bytes; lazy images are listed separately
  - `test_build_survives_github_api_failure` (Review Focus 4): `build_site` with `env={"HTTPS_PROXY": "http://127.0.0.1:9", "HTTP_PROXY": "http://127.0.0.1:9", "HUGO_CACHEDIR": str(tmp)}` succeeds, the home has 51 cards, and the order equals date-descending
- [ ] **Step 2: Run.** Expect failures.
- [ ] **Step 3: Implement**, porting from `mockup.css` (intro, `.proj*`, `.pub*`, contact) and `home.js` (filter).
- [ ] **Step 4: Run.** Expect pass. Regenerate `data/old_images.yaml`. Compare screenshots with `home-w1-desktop-{light,dark}.webp` and `home-w1-mobile-light.webp`.
- [ ] **Step 5: Commit** `git commit -m "Theme: homepage with every section"`

### Task 15: Project and publication pages

**Files:**
- Create: `layouts/project/page.html`, `layouts/project/section.html`, `layouts/publication/page.html`, `layouts/publication/section.html`, `tools/tests/site/test_project_publication.py`
- Modify: `assets/css/08-pages.css`

**Interfaces:**
- Consumes: `lists/project-card.html`, `lists/publication-item.html`, `filter.js` (Task 14).
- Produces:
  - Project single: date, featured image (`Fit "720x2500"`), "Go to project site" button (`external_link`), tags.
  - `/project/` (new page): intro plus the full project grid and toolbar.
  - Publication single:
    - Authors linked to `/authors/<urlize>/`, first 20 then "and N more".
    - `January 2006` date, venue, link buttons, abstract.
    - "Publication type" row linking to `/publication-type/<slug>/`.
    - MathJax 3 (`tex-chtml`, inline `$…$` and `\(…\)`, display `$$…$$` and `\[…\]`) only when `math: true`.
  - `/publication/`: all items with search, type and year filters via `filter.js`.
- [ ] **Step 1: Write failing tests:**
  - `test_project_single_has_external_button`
  - `test_project_index_lists_all`
  - `test_publication_authors_truncated_and_linked` (the 162-author paper)
  - `test_mathjax_only_on_math_pages`
  - `test_publication_filters_present`
  - `test_old_images_parity_clean` (`failures("old-images") == []` after regenerating `data/old_images.yaml`)
- [ ] **Step 2: Run.** Expect failures.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run.** Expect pass.
- [ ] **Step 5: Commit** `git commit -m "Theme: project and publication pages"`

### Task 16: Search, view transitions, prefetch, 404

**Files:**
- Create: `layouts/_partials/search.html`, `assets/js/search.js`, `tools/tests/site/test_search_404.py`
- Modify: `layouts/404.html`, `layouts/_partials/head.html`, `assets/css/04-components.css`

**Interfaces:**
- Produces:
  - `search.html`: a `<dialog id="search">` with input and results list. It opens from the header button and the `/` key, closes on Escape.
  - `search.js`: fetches `/index.json` on first open only. It scores title (weight 3), tags (2), summary (1.5) and content (1) by case-insensitive term matches, shows the top 10 with section labels, and handles the arrow keys and Enter. When `location.search` has `?q=`, it opens with that query (matches the JSON-LD `SearchAction`).
  - Head: `<style>@view-transition{navigation:auto}</style>` inside `@media (prefers-reduced-motion: no-preference)`, and a `<script type="speculationrules">` with `{"prefetch":[{"where":{"href_matches":"/*"},"eagerness":"moderate"}]}`.
  - 404: title, search box, links to `/`, `/post/`, `/project/`.
- [ ] **Step 1: Write failing tests:**
  - `test_index_json_not_referenced_in_html` (no page HTML contains `index.json` except inside the search script bundle)
  - `test_speculation_rules_and_view_transition_present`
  - `test_404_has_search_and_links`
- [ ] **Step 2: Run.** Expect failures.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run.** Expect pass.
- [ ] **Step 5: Commit** `git commit -m "Theme: search dialog, view transitions, prefetch, 404"`

### Task 17: Browser tests: behaviour, accessibility, budgets, no-JS, screenshots

**Files:**
- Create:
  - `tools/tests/browser/conftest.py`: session fixture serving the `site` build with `http.server` on a free port; Playwright Chromium at `/run/current-system/sw/bin/chromium`.
  - `tools/tests/browser/test_behaviour.py`
  - `tools/screenshots.py`: CLI `uv run python screenshots.py BUILD_DIR OUT_DIR`, writing the spec's screenshot set for light and dark at 1440 and 390 widths.

**Interfaces:**
- Consumes: every page from Tasks 6 to 16.
- [ ] **Step 1: Write failing tests:**
  - `test_theme_toggle_persists_across_navigation`
  - `test_search_slash_opens_and_finds_post` (type `zfs`, expect a `/post/` result)
  - `test_project_filter_and_search` (filter `homelab` matches the count shown on its button; search `adaptive` shows the Adaptive cards)
  - `test_no_console_errors_on_key_pages`
  - `test_axe_no_serious_or_critical` (home, a post, `/post/`, `/project/`, `/publication/`, `/tag/ai/`, 404; light and dark)
  - `test_post_page_budget` (under 300 KB and under 20 requests before giscus loads, by intercepting requests)
  - `test_no_js` (Review Focus 5): JavaScript disabled, all 51 cards visible, toolbar hidden, menu links navigate, dark scheme emulation gives dark tokens
  - `test_anchor_not_hidden_under_header` (after navigating to a heading anchor, the heading's top is at or below the header's bottom)
  - `test_header_height_and_single_line_nav` (header at most 72 px tall; at 1024 and 1440 px all six menu links share one `offsetTop`)
  - `test_keyboard_reaches_nav_search_and_theme` (Tab from the top reaches the skip link, the six menu links, search and the theme toggle, each with a visible focus outline)
- [ ] **Step 2: Run** `cd tools && uv run pytest tests/browser -q`. Expect the failures that reveal real bugs.
- [ ] **Step 3: Fix** what the failures show (contrast, labels, budgets) in the owning templates and CSS.
- [ ] **Step 4: Run** the browser and site suites. Expect all pass. Generate screenshots for the baseline and the branch with `screenshots.py`.
- [ ] **Step 5: Commit** `git commit -m "Theme: browser tests for behaviour, accessibility, budgets and no-JS"`

### Task 18: Full parity run and allow-file review

**Files:**
- Modify: `tools/parity-allow.yaml`, any template a finding points to

- [ ] **Step 1: Run** `cd tools && uv run parity compare-branch`.
- [ ] **Step 2: Triage every finding.** Fix the template when the change is not one of the spec's Fix items. Add an allow entry with a reason only for spec-listed changes:
  - absolute URLs
  - `og:locale`
  - twitter `name=`
  - plainified descriptions
  - new JSON-LD
  - new term, taxonomy and `/project/` pages
  - dropped theme assets
- [ ] **Step 3: Run** `uv run parity compare-branch` again. Expect `0 failures` and `0 unused allow rules`.
- [ ] **Step 4: Run** the whole suite: `uv run pytest -q -m "slow or not slow" tests tests/site tests/browser`. Expect all pass.
- [ ] **Step 5: Commit** `git commit -m "Theme: parity clean against the baseline"`

### Task 19: Cutover

**Files:**
- Modify:
  - `tools/parity-baseline.txt` (new `main` sha), `data/old_images.yaml`
  - `config/_default/params.yaml` (remove keys no template reads: `appearance`, `header`, `extensions`, `features.search.algolia`, `features.map`, `features.privacy_pack`, `features.syntax_highlighter`, and similar)
  - `README.md` (theme section replaces the Academic theme text)
  - `netlify.toml` (`HUGO_VERSION = "0.167.0"`), `devbox.json` (`hugo@0.167.0`, or the closest packaged version with a note)
- Delete: `assets/jsconfig.json` if tracked, any remaining HugoBlox-only files

- [ ] **Step 1: Rebase.** `git fetch origin && git rebase origin/parity-check` (or `origin/main` once PR 1 merged). For every commit on `origin/main` since `0a0e6ad` touching `layouts/`, `assets/`, `config/` or `static/`, port the behaviour into the new templates and list it in the PR description.
- [ ] **Step 2: Update** `tools/parity-baseline.txt` to the new `origin/main` sha, regenerate `data/old_images.yaml`, and run `uv run parity compare-branch`. Expect `0 failures`.
- [ ] **Step 2b: Netlify build image.** Hugo 0.167 needs Netlify's Ubuntu 24.04 build image. This setting is outside the repo, so the PR description asks Bas to confirm it under Site configuration > Build & deploy > Build image.
- [ ] **Step 3: Remove unused params** with a grep check: each removed key has no match in `layouts/`. Rebuild, then run `uv run pytest -q tests/site`. Expect pass.
- [ ] **Step 4: Push and open PR 2.** Push `own-theme` and open PR 2 "Own Hugo theme" against `parity-check` (or `main`), with:
  - before/after screenshots from `tools/screenshots.py`
  - the parity summary and the allow file
  - the ported-commit list
  - the baseline sha

  Link it with `link_pull_request`. When the Netlify deploy preview is up:
  - Run `uv run parity live --preview <deploy-preview-url>`. Expect `0 mismatches`.
  - Validate `<preview>/index.xml` and `<preview>/post/index.xml` with the W3C feed validator (`https://validator.w3.org/feed/check.cgi?url=`). Expect no errors.
  - Run Google's Rich Results Test on a post, a project and a publication. Expect the JSON-LD to be detected without errors.
  - Open three posts that have giscus threads on the live site and confirm the threads show on the preview.
  - Post the results as a PR comment.
- [ ] **Step 5: Commit** any fixes the preview reveals (`git commit -m "Theme: fixes from the deploy-preview sweep"`). Re-run the live sweep until clean. Merging stays with Bas.
