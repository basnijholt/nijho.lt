# Own Hugo theme for nijho.lt

Status: draft, 2026-10-09. Branch `own-theme`.

## Understanding

What Bas said:

- The content and the way links work are good; the layout looks dated.
- Replace the theme with one we own, still built with Hugo.
- Every link ever posted or indexed must keep working.
- Everything SEO relies on must still be generated.
- The blog must keep working the same way: tags, categories, and the XML feeds.

Assumptions (correct me if wrong):

- Same hosting (Netlify), same comments (giscus), same analytics (Google Analytics + self-hosted Plausible).
- Same sections and navigation labels: Home, Blog, Projects, Photography, Publications, Contact.
- No content rewrites. Markdown, front matter and page bundles stay as they are, so the many open content branches keep merging cleanly.
- New URLs may be added (for example a `/project/` index or working tag pages); no existing URL may disappear.
- The visual direction is picked from mockups before the design work starts.

Success means: the parity check (below) passes against a build of `main` with the old theme, every URL in the live sitemap returns 200 on the deploy preview, and Bas prefers the new look.

## Why replace the theme

Measured on the live site and a local build of `origin/main` (0a0e6ad):

- HugoBlox `blox-bootstrap` v5.9.7 is the Bootstrap 4 era of Wowchemy and pins Hugo to 0.123.3 (February 2024).
- The homepage transfers 36 MB in 86 requests. About 33 MB comes from five animated GIF project logos that Hugo re-encodes at 550 px wide, which makes them larger than the originals (`lovelace-ios-themes`: 983 KB source, 20 MB served; `adaptive`: 2.3 MB source, 9 MB served).
- Every post page transfers 1.2 MB in 80 requests: 531 KB of scripts (jQuery, Bootstrap, Leaflet for the contact map, Fuse and mark.js for search, publication filtering), 437 KB of web fonts, and the 116 KB search index, fetched on every page view whether or not search is opened.
- 108 of the 511 URLs in the live sitemap return 404 (every `/tag/*/`, `/category/*/`, `/publication-type/*/`, the three taxonomy lists, and `/project/`), and 119 pages link to them. Root cause: an HTML comment on line 1 of `layouts/_default/list.html` (commit `53f32df`, 2024-12-29) stops Hugo from treating it as a `baseof` template, so it renders empty and Hugo writes no file. The feeds still build.
- Every URL the site emits for crawlers is relative (`baseurl: '/'`): canonical, `og:url`, `og:image`, sitemap `<loc>`, the `robots.txt` `Sitemap:` line, RSS links. Relative sitemap URLs violate the protocol and relative `og:image` breaks share cards.
- Of 826 paths the Wayback Machine has archived for the site, 262 return 404 today (details under Redirects).

## Approach

Write our own templates directly in the project (`layouts/`, `assets/`), drop the HugoBlox modules, target the latest Hugo (**0.167.0**, released 2026-09-28; decided 2026-10-09), and prove parity with an automated diff against a build of the old theme on its own Hugo (0.123.3; the old theme does not build on 0.167). Rejected alternatives:

- Restyle HugoBlox in place: cheapest, but keeps the Hugo 0.123.3 pin, jQuery, Bootstrap 4, and the term-page bug.
- Port to a community theme (Blowfish, PaperMod, HugoBlox Tailwind): still a full port of the Wowchemy-specific front matter, shortcodes and widgets, and the result looks like that theme's other sites. We would again depend on someone else's release cycle.

## Architecture

### Layout

No `themes/` directory and no Hugo modules. The site is one-off, so a theme indirection buys nothing. `config/_default/module.yaml`, `go.mod` and `go.sum` are deleted.

```
layouts/                     Hugo 0.146+ template tree only
  baseof.html                shell: <head>, header, main, footer
  home.html page.html section.html taxonomy.html term.html 404.html
  post/ project/ publication/  page.html section.html
  authors/                   term.html taxonomy.html
  _markup/                   render hooks: heading, image, link, codeblock-mermaid
  _partials/
    head/    css.html seo.html jsonld.html icons.html analytics.html
    ...      header, footer, post meta, cards, comments, icon, functions/
  _shortcodes/               ported theme shortcodes + the existing site shortcodes
  rss.xml robots.txt         where the embedded templates differ from today
  home.json                  search index (same schema as today)
  home.headers home.redirects home.webmanifest   (replace blox-plugin-netlify output formats)
assets/
  css/    main.css (@layer order + @import ... layer()), one file per layer, built with css.Build
  js/     theme.js search.js filter.js code.js zoom.js toc.js  (ES modules, one small file per feature)
  icons/  SVGs for the ~30 icons in use
```

### Styling

- Plain modern CSS, no preprocessor: native nesting, `@layer` (reset, tokens, base, layout, components, prose, utilities), custom properties, `light-dark()` with `color-scheme`, container queries for cards, `:has()`, `text-wrap: balance` on headings and `pretty` on paragraphs, `scroll-margin-top` so anchors clear the sticky header, `content-visibility: auto` on below-the-fold homepage sections. `assets/css/main.css` declares the layer order and `@import`s each file with `layer(<name>)`; Hugo's `css.Build` (esbuild, 0.158+) inlines the imports, minifies, and with the target `chrome120 edge120 firefox117 safari17.2 ios17.2` keeps native nesting as written; then `fingerprint`. No Node toolchain, no SCSS.
- Theme tokens: `color-scheme: light dark` by default; `[data-theme=light|dark]` pins it. An inline script in `<head>` applies the stored choice from `localStorage` before first paint, so there is no flash.
- Target browsers: the evergreen releases of the last two years (Baseline 2024). Content stays readable without JavaScript and in older browsers; enhancements degrade, never break.
- Self-hosted WOFF2 fonts, subset to Latin, at most two families plus a monospace. No Google Fonts request.
- Syntax highlighting stays on Hugo's Chroma with CSS classes (`noClasses: false`, unchanged markup). The light and dark code palettes become plain CSS under `[data-theme]` instead of two stylesheets swapped by JS.

### Icons

Content embeds Font Awesome markup directly (`<em class="fab fa-github">` 121 times, `fa-flask` 111, `fa-book` 108, about 20 others once each), and front matter names icons (`icon: github`, `icon_pack: fab`). An icon shim keeps all of it rendering without the 437 KB of icon fonts:

- `partials/icon.html` maps `(pack, name)` to an inline SVG from `assets/icons/`.
- For raw HTML in Markdown, CSS rules give each used `.fa-<name>` / `.ai-<name>` class a `mask-image` of the same SVG, so `<em class="fab fa-github">` keeps showing the GitHub mark in the current text color.
- The build lists every icon class used in `content/` and fails when one has no SVG. Today that is Font Awesome Free 6.5.1 and academicons 1.9.4 names, 336 occurrences, most in `post/setting-up-macos`, `authors/admin` and `home/photography.md`.

### JavaScript

Native platform features instead of libraries: `<dialog>` for search and image zoom, the Popover API for the mobile menu and theme menu, `IntersectionObserver` for the active contents entry, cross-document View Transitions (`@view-transition { navigation: auto; }`, off under `prefers-reduced-motion`), and Speculation Rules to prefetch links on hover (replaces instant.page). Scripts are ES modules bundled by Hugo's built-in esbuild (`js.Build`, minified, fingerprinted), each loaded only on pages that need it, no framework:

| Feature | Today | New |
|---|---|---|
| Theme toggle | Wowchemy JS + jQuery | ~1 KB inline + `theme.js` |
| Search | Fuse + mark.js + jQuery, index fetched on every page | `search.js` fetches `/index.json` on first open only |
| Project filter/sort/search | Isotope + jQuery | `filter.js`, CSS grid, on `/project/` and the homepage only |
| Code copy button | theme JS on every `pre > code` | `code.js`, post pages only |
| Image zoom | medium-zoom on `[data-zoomable]` | `zoom.js`: native `<dialog>` showing the largest size, shared with the gallery |
| Mermaid | mermaid 9.1.3 on 3 posts | same opt-in (current mermaid release), only when a `mermaid` fence is present |
| Gallery lightbox | fancybox 3.5.7 + jQuery, 1 post | `zoom.js` |
| Publication filters | Isotope + jQuery on `/publication/` | `filter.js` (search, type, year) |
| Hide header on scroll | headroom.js | dropped; plain sticky header |
| Contact map | Leaflet on every page | static lazy-loaded map image linking to OpenStreetMap |
| Math | MathJax on `math: true` pages | same opt-in |
| Comments | giscus | giscus, unchanged config and `pathname` mapping |
| Charts | `plot` shortcode loads Observable Plot | unchanged |

Budget: under 15 KB of our own JS (gzip) on a post page, excluding giscus and analytics.

### Images

- Animated GIFs are never resized; templates serve the original file.
- Below-the-fold images get `loading="lazy"` and explicit `width`/`height` to avoid layout shift.
- Hugo 0.167 renames every processed image (`<stem>_hu_<hash>.<ext>` instead of 0.123's `<stem>_hu<md5>_<size>_...`), so every old resize URL gets a 301 (see Redirects and parity check 7).
- `og:image` keeps pointing at the original file in the page bundle (for example `/project/agent-cli/featured.png`), as it does today, so share cards survive image-processing changes.

## Visual direction

Three mockups built with real content (A: editorial, B: engineer's notebook, C: showcase) were reviewed on 2026-10-09. Feedback: the current site still looks better than A and B; C's intro section is the best start; all three dropped too much content. Mockup D follows from that: the current homepage structure with all of its content, C's intro and visual language, and blog posts that use the full page width. **Chosen 2026-10-09: mockup D with blog layout W1 (wide list).**

Design source of truth: `~/Work/nijho.lt-worktrees/own-theme-mockups/D-complete/` (`home-w1.html`, `post.html` and their screenshots). The implementation reproduces it:

- Fonts, self-hosted WOFF2 (all SIL OFL): Bricolage Grotesque for headings, Geist for body and UI, Geist Mono for dates, reading times, tags and code.
- Palette: neutral stone grays, one orange-red accent. Light: background `#f5f5f4`, panel `#ebebea`, text `#1a1a19`, muted `#61615f`, accent `#b9431a`. Dark: `#141413`, `#1d1d1c`, `#ededeb`, `#9c9c98`, accent `#ee8257`.
- Radii: 14 px for large panels and images, 8 px for buttons, chips and inputs.
- Homepage: C-style intro (large avatar, name, role, bio, social icons) with interests and education below; blog posts as W1 rows (date, reading time, title and categories on the left, full summary on the right, thumbnail at the far right when present); projects as an equal-height four-column card grid with tag chips, search and sort; photography in justified rows; publications grouped by year with author lists and link chips; contact with a large email, detail grid and static map.
- Post page: breadcrumb, large display title, subtitle, a meta row (author avatar and name, published and updated dates, reading time, category chips), a reading column of about 720 px with a sticky contents list on the right from about 1100 px, and below the body: tags, share links, edit link, author card, related posts, comments.

These rules hold throughout:

- Rubric: Leonxlnx/taste-skill v2 (commit `18dfc92`) sections 4, 6, 8, 9 and 11, plus its `redesign-skill`, with the preset "Editorial / Blog". Rules from it that do not fit a real blog are excluded: randomised dates, "no emojis" (titles and summaries use them), stock or placeholder images, scroll-triggered animations, hero/CTA and logo-wall rules, cookie banners.
- Neutral palette with exactly one accent; light and dark both first-class; WCAG AA contrast; visible focus states; `prefers-reduced-motion` respected; no motion on scroll.
- Reading measure 65 to 72 characters; navigation on one line at desktop widths; header at most 72 px tall.
- UI copy in plain sentence case, no em dashes (also Bas's own writing rule).
- The homepage keeps every section and every item it has today: about with interests and education, the 10 newest posts with full summaries, all projects with filters, search and sort, all photos, all publications, and the full contact section. The page weight problem is solved by not resizing GIFs and by lazy loading, not by dropping content.
- Content uses the page width: no narrow centre column or left label column on the homepage.

## Output contract

Audited from the HugoBlox 5.9.7 templates, a production-replica build (`HUGO_ENV=production HUGO_ENABLEGITINFO=true`), and the live site. "Keep" means reproduce exactly; "Fix" means a deliberate change, listed in the parity allow file.

### URLs

| Pattern | Kind | Notes |
|---|---|---|
| `/` | home | |
| `/post/`, `/post/<slug>/` | section, page | `slug:` front matter wins over the directory name (`/post/glove80-split-ergonomic-keyboard/`) |
| `/post/advent-of-open-source/`, `/post/advent-of-open-source/<day>/` | nested section | its feed has the days; `/post/index.xml` has direct children only |
| `/project/<slug>/` | page | `/project/` currently 404s (Fix: it gets a page) |
| `/publication/`, `/publication/<slug>/` | section, page | |
| `/phd-defense/` | page | |
| `/authors/`, `/authors/page/2/`, `/authors/page/3/`, `/authors/<name>/` | taxonomy, term | about 265 co-author terms; `/authors/admin/` (posts) and `/authors/bas-nijholt/` (publications) both exist; keep both |
| `/tags/`, `/tag/<t>/` | taxonomy, term | HTML missing today (Fix) |
| `/categories/`, `/category/<c>/` | taxonomy, term | HTML missing today (Fix) |
| `/publication_types/`, `/publication-type/<n>/` | taxonomy, term | HTML missing today (Fix) |
| `<any of the above>index.xml` | RSS | every feed the baseline produces (home, each section, taxonomy list and term), including empty taxonomy-list feeds |
| `/index.json`, `/sitemap.xml`, `/robots.txt`, `/manifest.webmanifest`, `/404.html` | | plus the Netlify config outputs `_headers` and `_redirects` |
| `/post/page/1/` and similar | pagination alias | `noindex` redirect stub; keep |

Trailing slashes everywhere (Netlify 301s the slashless form). The giscus `pathname` mapping depends on exact paths. Directory names with dots and underscores (`/project/rsync-time-machine.py/`, `/project/nijho.lt/`, `/publication/phd_thesis/`) and author slugs with dots or percent-encoding (`/authors/andrey-e.-antipov/`) are kept as Hugo generates them.

Bundle resources keep their paths (`/post/<x>/<file>`, `/project/<x>/<file>`: png, svg, gif, mp4, py, mov), as do `/media/**` files and `/bas.asc`.

Heading ids stay GitHub-style (goldmark `autoHeadingIDType: github`): lowercase, spaces to `-`, punctuation and non-ASCII dropped, duplicates suffixed `-1`, `-2` (so `📖 Origin Story` stays `-origin-story`). The heading render hook uses `.Anchor` unchanged and only adds the visible `#` link. The homepage keeps the section ids `#about`, `#blog-posts`, `#projects`, `#photography`, `#publications`, `#contact`, which old menu links point to.

### `<head>`

| Element | Rule |
|---|---|
| `<title>` | `.Params.seo.title` if set, else `.Title`, plus ` \| Bas Nijholt` unless empty or equal to the site title. Keep. |
| meta description | `summary` → `abstract` → `.Summary` (regular pages) → role "Senior Staff Engineer". Keep the chain; Fix: run it through `plainify` (Markdown leaks today). |
| canonical, `og:url` | `.Permalink`. Fix: absolute (live output is relative because `baseurl: '/'`). |
| `hreflang` | self-referencing `en-us`. Keep. |
| robots | `noindex` only for `private: true` pages and pagination aliases. Keep. |
| `og:type` | `profile` home, `article` regular pages, `website` lists and terms. Keep. |
| `og:site_name`, `og:title`, `og:description` | site title, page title with suffix, same as meta description. Keep. |
| `og:image` + `twitter:card` | author avatar 270² (`summary`) on `/authors/admin/` → bundle `*featured*` original (`summary_large_image`) → `icon.png` 512² (`summary`). Keep. |
| `og:locale` | Fix: `en_US` (today `en-us`). |
| twitter tags | `twitter:site` and `twitter:creator` `@basnijholt`, `twitter:image`. Fix: `name=` instead of `property=`. |
| time | regular pages: `article:published_time`, `article:modified_time` (git lastmod in production); others: `og:updated_time`. Keep. Fix: sections with `_index.md` take their date from the newest child again. |
| JSON-LD | home `WebSite` with `SearchAction` (`/?q={search_term_string}`); posts `BlogPosting`, projects `Article`, with `mainEntityOfPage`, `headline`, `image`, `datePublished`, `dateModified`, `author`, `publisher` (Organization "Bas Nijholt" + icon 192), `description`. Keep. Add: `Person` on the home page, `ScholarlyArticle` for publications, `BreadcrumbList` on posts. |
| feed link | `rel=alternate type=application/rss+xml` on every kind with RSS output. Keep. |
| icons | `icon.png` 32² and apple-touch 180², manifest link, `theme-color`. Add: `/favicon.ico`. |
| `rel=me` | `https://fosstodon.org/@basnijholt` on every page. Keep. |
| meta author | "Bas Nijholt". Keep. |
| analytics | GA `G-B50P3BHJ6C` (site override, with outbound-click tracking) and Plausible, production only. Fix: `netlify.toml` sets `HUGO_ENV = "production"` only in the production context, so previews no longer send analytics, and non-production builds add `<meta name="robots" content="noindex">`. |

### Feeds

One template for every kind. Channel: title (with suffix), link, `atom:link rel=self`, description = title, language `en-us`, copyright `© <year>`, `lastBuildDate`, `image` when the page has an og image. Items: all regular pages of the context, no limit (the home feed is about 130 items, 1.7 MB), title, link, `pubDate`, `guid`, `description` = full escaped `.Content`. Keep all of it; the generator string changes.

`guid` today is the relative path (`<guid>/post/x/</guid>`) because of `baseurl: '/'`. Feed readers identify items by `guid`, so making it absolute would resurface about 130 old items as unread in every subscriber's reader. Decision: emit `.RelPermalink` as the `guid` text, byte-identical to today, with `isPermaLink="false"` so it is valid; `<link>` becomes absolute.

### Sitemap, robots, manifest, headers, redirects, search index

- Sitemap: Hugo's embedded template, `changefreq weekly`, git lastmod, no priority; excludes 404, paginators, aliases and headless pages. Keep. Fix: absolute `<loc>`.
- robots.txt: `User-agent: *` plus `Sitemap:`. Keep, absolute URL.
- manifest: name `Bas Nijholt`, icons 192/512, `display: standalone`, `start_url: /?utm_source=web_app_manifest`. Keep; colors follow the new palette.
- `_headers`: the six security headers on `/*`, `application/rss+xml` for `/index.xml`. Keep. Fix: the manifest rule targets `/manifest.webmanifest`.
- `_redirects`: one 301 per front-matter `alias` (today `/post/glove80-experience/`), plus the generated old-image redirects. The domain rules in `static/_redirects` never deploy (the generated file overwrites them; Cloudflare does that redirect), so that file is deleted.
- `index.json`: same keys (`objectID date publishdate lastmod expirydate lang permalink relpermalink title summary content authors kind type section tags categories`), same page set (regular pages plus the superuser author page, minus drafts, `private`, `searchable: false`). Keep.
- `baseURL`: Fix: `https://www.nijho.lt/` in `hugo.yaml`; deploy-preview and branch contexts pass `--baseURL "$DEPLOY_PRIME_URL"`.

### Redirects to add

From git history and the Wayback CDX index (826 archived paths, each probed live), as 301s in the generated `_redirects`:

| Old | New | Count |
|---|---|---|
| `/post/glove80-experience/` | `/post/glove80-split-ergonomic-keyboard/` | 1 (exists, keep) |
| `/post/llamaswap/` | `/post/llama-nixos/` | 1 |
| `/post/advent-of-open-source/day_NN/` | `/post/advent-of-open-source/NN-<slug>/` | 24 (public 2024-12-01 to 12-29) |
| `/tags/<x>/`, `/categories/<x>/` (2018 to 2021 scheme) | `/tag/<x>/`, `/category/<x>/`, or the mapped tag below | splat rules |
| `/publication_types/<n>/`, `/publication-type/2/`, `/3/`, `/7/` (numeric) | `/publication/` | 4+ |
| `/tag/<removed>/` and `/tag/<removed>/index.xml` for the tags dropped by the 2026-10-09 retag (#117, 305 to 100 terms) | the new tag it most often became on the same posts, derived from the #117 diff | reviewed by hand; terms without a sensible target stay 404 |
| `/authors/<old-slug>/` (co-author names that changed, for example `andrey-e-antipov`) | current slug | 21 |
| `/post/page/*`, `/project/page/*`, `/tags/page/*`, `/tag/*/page/*` | the unpaginated page | splat rules |
| `https://nijholt.netlify.app/*` | `https://www.nijho.lt/:splat` (`301!`) | 1 (it serves a full duplicate of the site today) |

Not preserved: old `*_hu*` image names that were already gone before this work, old fingerprinted `/css/`, `/js/`, `/en/js/`, `/img/` bundles.

The redirect list lives in `data/redirects.yaml` and `index.redirects` renders it together with front-matter aliases and the old-image redirects, so future renames have one obvious place to go.

## Feature inventory

Everything the content relies on today, from the templates and a scan of `content/`. All of it is ported; "Fix" items are deliberate changes.

### Front matter that affects rendering

| Section | Keys |
|---|---|
| post | `title date draft summary subtitle tags categories authors slug aliases`; `image.caption`, `image.placement` (2 = wide 1200 px), `image.preview_only` (hide on the single page), `image.filename`. Cascade on `/post/**`: `reading_time commentable show_related show_breadcrumb editable` |
| project | `title date external_link summary tags` (summaries need `markdownify | emojify`); bundle `featured.*`, `animated.svg` (shown on cards), `thumbnail*` |
| publication | `title date authors (1 to 162 names) publication_types publication publication_short abstract summary url_pdf url_code url_dataset url_preprint links[] math` |
| authors/admin | `title role organizations bio interests (HTML with icons) education.courses social[icon, icon_pack, link]`, `avatar.jpg` |
| home sections | `content/home/*.md`: section order (`weight`), titles, subtitles, the blog list (10 newest posts, "See all blog posts"), project filter buttons, photography body, publications callout, contact data (email, address, links) |
| other | `math: true` (2 publications), `private`, `searchable`, `share: false`, `commentable: false`, `editable: false` (`/phd-defense/`) |

Ignored today and kept ignored: `featured`, `excludeFromList`, `projects`, `image.focal_point`, `description`, `selected`, `header.*`.

### Shortcodes and render hooks

| Name | Uses | Output contract |
|---|---|---|
| `callout` (theme) | 40, `note` 37, `warning` 3, always `{{% %}}` | box with icon, inner Markdown + emoji |
| `figure` (theme) | 24 | `<figure id="figure-<anchorized caption>">`, responsive `srcset` (400/760/1200 WebP) for rasters, originals for SVG/GIF, `width`, lazy loading, zoomable; lookup bundle, then `assets/media/`, then remote |
| `video` (theme) | 3 | `<video>` with optional poster `<name>.jpg`. Fix: honour `autoplay` and `loop` (ignored today) |
| `gallery` (theme) | 1 | grid of Fit 350x250 thumbnails from `assets/media/albums/<album>/`, lightbox to originals |
| `toc` | 23 | `<details>` with `.TableOfContents` (levels 2 to 3). The override in the working tree is untracked, so production uses the theme's version, open by default. Keep "open"; commit the template |
| `ref` (Hugo) | 133 | unchanged |
| site: `tooltip detail-tag plot bleed-svg demo-clips demo-clip photo-grid` | 21 | kept; their theme couplings (`.article-style`, `body.dark`, `svg { fill: currentColor }` workaround) move to the new class and `[data-theme]` names |
| image render hook | 34 Markdown images (31 remote) | same output as `figure` |
| link render hook | all | `http*` links get `target="_blank" rel="noopener"` |
| codeblock `mermaid` hook | 3 posts | `<div class="mermaid">`, loads mermaid on that page only |
| heading anchors | h2/h3 on post singles and `/phd-defense/` | a heading render hook replaces the regex partial; ids unchanged |

Goldmark: `unsafe: true`, attribute blocks on, typographer, footnotes (4 posts), tables (11 files), linkify, emoji (`enableEmoji: true`).

### Pages

| Kind | Features to keep |
|---|---|
| Post single | breadcrumb (Home / Posts / [Advent] / Title), subtitle, "Published on X · Last updated on Y", reading time, categories, featured image with caption (normal or wide), body, tags, share links, edit-on-GitHub link, author card (avatar, name, role, bio, social), related posts (up to 5; tags weight 100, categories 70, threshold 80), giscus |
| Project single | date, featured image, "Go to project site" button, tags. Cards keep linking to `external_link` |
| Publication single | linked authors (first 20, then "and N more"), "Month YYYY", buttons (Preprint, PDF, Code, Dataset, `links[]`), abstract, publication type, publication |
| `/phd-defense/` | plain page, no meta, no share, no comments |
| `/post/`, advent section | compact list: title, summary, meta, thumbnail; the advent page shows its body then its 25 days |
| `/project/` (new) | all projects, star-sorted, with the homepage's search, sort and tag filters |
| `/publication/` | citation list with search, type and year filters |
| `/authors/admin/` | about block plus latest items; co-author pages: name plus latest items; `/authors/` paginated at 100 |
| Tag, category, publication-type pages (new) | title, count, list of pages, feed link |
| Home | about (avatar, name, role, organisation, social icons, bio, interests, education), the 10 newest posts with full summaries, all projects (stars from the GitHub API, search, sort, tag filter, `animated.svg` logos), photography (`photo-grid`), all publications, contact (email, address, directions, PGP key, links, and a static lazy-loaded map image linking to OpenStreetMap) |
| Global | sticky header with the 6 menu items, search (`/` hotkey, results over title, summary, content, tags), three-state theme toggle (light, dark, auto), footer ("© year · Source code on GitHub"), back to top, 404 page |

Fix: giscus follows the site theme toggle, not only the OS setting.

## Parity check (the guarantee)

`tools/parity` (a Python package in the `tools/` uv project) compares two build directories: the **baseline**, built from a pinned `main` commit with the old theme, and the **candidate**, built from the branch. Both are built the way Netlify builds production (`hugo --gc --minify`, `HUGO_ENV=production`, `HUGO_ENABLEGITINFO=true`), each from a fresh resource cache: the baseline with Hugo 0.123.3, the candidate with Hugo 0.167.0. Differences caused by Hugo itself (for example a reading time one minute higher on one post) go in the allow file like any other, with a reason. It exits non-zero on any failure and prints a grouped report. Intentional changes go in `tools/parity-allow.yaml`, one entry per path or field with a reason, so every exception is reviewed in the PR.

| # | Check | Rule |
|---|---|---|
| 1 | Output paths | Every baseline file with a public extension (`.html .xml .json .webmanifest .txt .asc .png .jpg .jpeg .gif .svg .webp .mp4 .mov .py .js` in bundles, plus `_headers` and `_redirects`) exists in the candidate. Excluded: fingerprinted theme assets (`/css/`, `/js/`, `/webfonts/`, `/en/js/`) and hashed image resizes (`*_hu*`, covered by check 7). |
| 2 | Sitemap | Candidate `<loc>` set is a superset of the baseline set, and every candidate `<loc>` maps to an `index.html` that exists (today's tag pages would fail this). |
| 3 | Feeds | For every baseline feed (`index.xml` at any path): the candidate feed exists, channel `title`/`link` match, and the set of item `guid` values (byte-identical) and `link` paths is equal. The visible text of each item `description` (tags stripped, whitespace normalised) must match. |
| 4 | Deep links | For every HTML page, every `id` inside the baseline's article body (headings, footnotes `fn:1`/`fnref:1`, figures `figure-<caption>`) exists in the candidate page, plus the six homepage section ids. |
| 5 | SEO fields | URLs are compared by path, so the relative-to-absolute fix is not a diff. Per page: `<title>`, meta description, canonical, robots, `og:title/description/type/url/image`, `twitter:card/site`, `article:published_time/modified_time`, `rel=alternate` feed links, and JSON-LD `@type`, `headline`, `datePublished`, `dateModified`, `author.name`. Must be equal or listed in the allow file. |
| 6 | Content | Per post, project and publication: the visible text of the article body is equal after whitespace normalisation, and the counts of `img`, `pre`, `table`, `video` and `details` are equal. This catches a shortcode that silently stops rendering. |
| 7 | Old image URLs | Every baseline `*_hu*` image that the candidate no longer produces gets a generated 301 in `_redirects` to an image the candidate publishes from the same source file (matched by the source hash in the `_hu<md5>` name), preferring the original. The check fails if any such path is neither present nor redirected. |
| 8 | Internal links | Every internal `href`/`src` in the candidate resolves to a file in the candidate or a `_redirects` rule. |
| 9 | Redirects | Every baseline `_redirects` rule exists in the candidate, unchanged. |

A second mode, `parity live --preview <url>`, fetches every `<loc>` in the live `https://www.nijho.lt/sitemap.xml` from a Netlify deploy preview and requires 200 (or the same redirect the live site returns). It runs before the cutover merge.

The baseline is regenerated on demand (temporary worktree at the pinned commit, Hugo 0.123.3, output in `/tmp`), never committed.

## Out of scope

Noticed during the audit, left for separate PRs:

- `content/post/advent-of-open-source/retrospective.md` has no front matter (empty `<h1>`, date `0001-01-01`).
- `/authors/admin/` and `/authors/bas-nijholt/` are two pages for the same person; merging them changes URLs.
- About 265 thin co-author pages are indexable; adding `noindex` is an SEO choice, not parity.
- Converting large animated GIFs to video.

## Phases

Phase 0 is PR 1. Phases 1 to 3 are PR 2 (stacked on PR 1), because a half-ported theme can never ship on its own; each task is its own commit there. The Hugo upgrade (formerly phase 4) is part of PR 2: the theme is written for 0.167.0 from the start. The old theme keeps serving production until PR 2 merges.

0. **Parity check.** `tools/parity` plus a baseline-vs-baseline self-test (two builds of the same commit must pass; the only allow rule covers a known Hugo 0.123 race). Merges to `main` on its own; it is useful even if the redesign stops.
1. **Structural port, minimal styling.** All templates, shortcodes, render hooks, feeds, SEO partials, icon shim and output formats, styled just enough to read. Includes `data/redirects.yaml` and the old-image redirects. Goal: parity passes with only the expected allow-file entries (the Fix items in the output contract, plus reviewed Hugo-caused differences). Built with Hugo 0.167.0.
2. **Visual design.** Apply the chosen direction: tokens, typography, homepage, lists, post, project, publication, author, term pages, 404, light and dark, mobile. Screenshot set reviewed by Bas. Parity re-run.
3. **Cutover.** Rebase on `main`, port any layout changes that landed meanwhile, regenerate the baseline at the new `main` and re-run parity, run `parity live` against the deploy preview, merge.
4. **Hugo upgrade.** Folded into PR 2 (decided 2026-10-09). Netlify `HUGO_VERSION` and devbox move to 0.167.0 at cutover; Netlify must use its Ubuntu 24.04 build image. Heading ids were verified identical between 0.123 and 0.167 for all 766 headings on post pages.

## Testing

- Parity check (above) on every PR from phase 1 on; baseline commit recorded in the PR description.
- Screenshot set: home, blog list, a long post with code/table/plots, a project, a publication, an author page, a tag page, 404, search open; desktop and mobile; light and dark. Before/after pairs in the PR.
- Accessibility: axe-core through Playwright on the same pages, no serious or critical violations; keyboard-only pass over nav, search and theme toggle; visible focus; skip link.
- Performance on the deploy preview: post page under 300 KB and under 20 requests before comments load; homepage under 2 MB; Largest Contentful Paint no worse than today.
- Feeds validated with the W3C feed validator; structured data with Google's Rich Results Test on a post, a project and a publication.

## Risks

| Risk | Mitigation |
|---|---|
| A URL or anchor silently disappears | Parity checks 1, 2, 4, 9 and the live sitemap sweep |
| A shortcode or front-matter field renders differently | Parity check 6, per-shortcode fixtures in the screenshot set |
| Layout PRs land on `main` during the port (projects, photography, demo clips were all changed in the last two weeks) | Keep the port on one branch, rebase often, list ported layout commits in the cutover PR |
| giscus threads detach | `mapping: pathname` and paths are unchanged; spot-check three posts with comments on the preview |
| Search results change | Same `index.json` schema; parity check 1 covers the file |
| Old share cards lose their image | Check 7 redirects every old resize URL to the original |
| Scope creep into content changes | Content edits are out of scope; separate PRs |
| Hugo 0.167 behaviour changes (pagination default of 10, HTML summaries, `try` for `GetRemote`, `security.allowContent`, image names) | A verified 0.167 guide for implementers, parity checks, and explicit tests for list sizes and the star-fetch failure path |
