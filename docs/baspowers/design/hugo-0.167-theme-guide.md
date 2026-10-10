# Hugo 0.167 theme guide for nijho.lt (coming from 0.123.3)

Researched 2026-10-09 against Hugo **v0.167.0** (released 2026-09-28), the hugoDocs repo at commit `1f726742` (2026-10-07), and the v0.124.0 to v0.167.0 release notes.

Source tags:
- `[rel vX]`: GitHub release notes for that version (https://github.com/gohugoio/hugo/releases/tag/vX)
- `[docs /path/]`: https://gohugo.io/path/ (read from the hugoDocs `content/en/` tree)
- `[src vX file]`: Hugo source at that tag
- `[verified]`: checked locally with the 0.167.0 binary. Scratch sites are in `/tmp/hugo-research/scratch` (new layout) and `/tmp/hugo-research/scratch-legacy` (old layout, built with both 0.123.3 and 0.167.0).

---

## 0. Binary

- Downloaded `hugo_extended_0.167.0_linux-amd64.tar.gz` to `/tmp/hugo-latest/bin/hugo`. The sha256 matches `hugo_0.167.0_checksums.txt`. Output: `hugo v0.167.0-3fff6fb5…+extended linux/amd64 BuildDate=2026-09-28T14:50:38Z`. It runs on this NixOS machine through nix-ld, because the extended binary is dynamically linked against glibc. `[verified]`
- The standard edition (`/tmp/hugo-latest/std/hugo`) is **statically linked** and needs no nix-ld. It produced identical output and identical processed-image file names (WebP and AVIF included) on the scratch site. `[verified]`
- **Extended still exists**, but it now adds only embedded LibSass, which has been deprecated since 0.153. WebP no longer needs extended, because encode and decode moved to WASM libwebp in 0.153. Deploy support moved to the `withdeploy` archives in 0.137. A planned deprecation of extended landed in 0.161 and was reverted in the same release. `[docs /installation/ editions table]` `[rel v0.153.0]` `[rel v0.137.0]` `[rel v0.161.0 "Revert … Deprecate extended"]`
- For comparison, 0.123.3 extended is at `/tmp/hugo-latest/v0123/hugo`.

---

## 1. Template system (0.146 rewrite)

The template system was reimplemented in **v0.146.0**, with follow-up fixes in 0.146.1 through 0.147.x. `[rel v0.146.0]` `[docs /templates/new-templatesystem-overview/]`

### 1.1 Rules

- `layouts/_default/` is gone in the new model. Its files move up to `layouts/`. `layouts/partials` became `layouts/_partials`, `layouts/shortcodes` became `layouts/_shortcodes`, and render hooks live in `layouts/_markup/`. `[docs /templates/new-templatesystem-overview/]`
- Any `layouts/` directory whose name does not start with `_` is a **page path**, such as `layouts/post/`. Templates there apply to that path and everything below it, and the closest match wins. `_markup`, `_shortcodes` and `baseof.html` can sit at any level. `[docs same]` `[verified: layouts/post/baseof.html applied to /post/ and /post/hello/ only]`
- File-name identifiers:
  - a kind: `home`, `page`, `section`, `taxonomy`, `term`
  - a standard layout: `single`, `list`, `all`
  - a custom `layout` from front matter
  - a language
  - an output format name, such as `rss` or `headers`
  - the media-type suffix

  Examples: `home.rss.xml`, `term.html`. There is no `index.html` home template any more; use `home.html`. `[docs same]`
- Fallbacks: `page.html`, then `single.html`, then `all.html`. For list kinds: `home|section|taxonomy|term.html`, then `list.html`, then `all.html`. `[docs /templates/types/]`
- `taxonomy.html` now matches **only** the taxonomy kind (the list of terms). Use `term.html` for a single term. In 0.123, `_default/taxonomy.html` meant *term* and `terms.html` meant the taxonomy list. `[docs new-templatesystem-overview]`
- **A path match beats a root kind match.** With root `page.html` present:
  - `layouts/project/single.html` won for `/project/p1/`.
  - `layouts/publication/all.html` won for `/publication/pub1/`.
  - A front-matter `layout: foo` picked `layouts/project/foo.html` over everything else.

  `[verified]`
- Base templates: `baseof.html`, with variants named `baseof.<kind|layout>.html`. The old `list-baseof.html` form is now `baseof.list.html`. A template is wrapped by baseof only if it contains nothing but `define` blocks, whitespace and comments. `[docs /templates/types/#base]`
- `_internal/*` templates are gone as a concept: call `{{ partial "opengraph.html" . }}` and so on. The old `{{ template "_internal/opengraph.html" . }}` still renders through a legacy mapping. `[docs new-templatesystem-overview]` `[verified]`
- Partials are looked up by name only, not by kind, path or output format. `partial "footer.section.de.html"` falls back through `footer.section.html`, `footer.de.html` and `footer.html`. `[docs /templates/types/#partial]`
- **Relative partials** (0.167): from inside a partial, `partial "./item.html"` or `partial "../x.html"` resolves relative to the calling partial. This is an error outside partials. `[rel v0.167.0]` `[docs /functions/partials/include/#relative-paths]` `[verified: _partials/card/list.html -> "./item.html"]`
- View templates: `.Render "_views/card"` resolves `layouts/<type>/_views/card.html`, then `layouts/_views/card.html`. Sub-paths are allowed since 0.164, and an optional context argument since 0.166 (`.Render "_views/card" (dict "page" . "class" "x")`). `[docs /methods/page/render/]` `[rel v0.164.0]` `[rel v0.166.0]`
- `layouts/_markup/` may contain only render hooks; anything else is skipped with a WARN. `[rel v0.146.0]` `[verified: HugoBlox's _default/_markup/sitemap.xml -> "skipping template file … unrecognized render hook template"]`
- Template names are case-insensitive since 0.164. `[rel v0.164.0]`

### 1.2 Exact paths for this site (all marked rows verified in `/tmp/hugo-research/scratch`)

| Purpose | Path | Status |
|---|---|---|
| Base | `layouts/baseof.html` | verified |
| Home | `layouts/home.html` | verified |
| Generic regular page (e.g. `/about/`) | `layouts/page.html` (fallback `single.html`) | verified |
| Generic section list (e.g. `/misc/`) | `layouts/section.html` (fallback `list.html`) | verified |
| Post single / list (incl. nested sections like `/post/series/part1/`) | `layouts/post/page.html` / `layouts/post/section.html` | verified |
| Project single / list | `layouts/project/page.html` / `layouts/project/section.html` | verified |
| Publication single / list | `layouts/publication/page.html` / `layouts/publication/section.html` | verified |
| Any taxonomy list (`/tag/`) | `layouts/taxonomy.html` | verified |
| Any term page (`/tag/python/`) | `layouts/term.html` | verified |
| Authors taxonomy list / author term | `layouts/authors/taxonomy.html` / `layouts/authors/term.html` | verified |
| RSS for all kinds | `layouts/rss.xml` (overrides the embedded `rss.xml`) | verified for section |
| RSS per kind | `layouts/home.rss.xml`, `section.rss.xml`, `taxonomy.rss.xml`, `term.rss.xml` | home and term verified |
| RSS for one section | `layouts/post/rss.xml` | verified |
| Home JSON (search index) | `layouts/home.json` + `outputs.home: [..., json]` | verified |
| Web manifest | `layouts/home.webmanifest` + `webappmanifest` output (built in: baseName `manifest`, rel `manifest`) | verified (`/manifest.webmanifest`) |
| Netlify `_headers` / `_redirects` | `layouts/home.headers` / `layouts/home.redirects` (custom output formats, see 1.3) | verified |
| robots.txt | `layouts/robots.txt` + `enableRobotsTXT: true` | verified |
| sitemap | embedded by default; override with `layouts/sitemap.xml` | verified |
| 404 | `layouts/404.html` (uses baseof, kind `404`) | verified |
| Heading hook | `layouts/_markup/render-heading.html` | verified |
| Link hook | `layouts/_markup/render-link.html` | verified |
| Image hook | `layouts/_markup/render-image.html` | verified |
| Mermaid code block | `layouts/_markup/render-codeblock-mermaid.html` (generic: `render-codeblock.html`) | verified |
| Partials | `layouts/_partials/**.html`, called as `partial "dir/name.html"` (never with a `partials/` prefix) | verified |
| Shortcodes | `layouts/_shortcodes/name.html` | verified |
| Content views | `layouts/_views/card.html` or `layouts/<type>/_views/card.html` | docs |

### 1.3 Custom output formats (Netlify), same config as HugoBlox's netlify plugin

```yaml
mediaTypes:
  text/netlify: {delimiter: '', suffixes: ['']}
outputFormats:
  headers:   {baseName: _headers,   isPlainText: true, mediaType: text/netlify, notAlternative: true}
  redirects: {baseName: _redirects, isPlainText: true, mediaType: text/netlify, notAlternative: true}
outputs:
  home: [html, rss, json, webappmanifest, headers, redirects]
  section: [html, rss]
```

Because the suffix is empty, the template is named after the output format: `home.headers`, `home.redirects`. `[verified]` Output-format names in `outputs` are case-insensitive: the legacy `[HTML, RSS, JSON]` also builds. `[verified]`

For the redirects template, `site.AllPages` is deprecated (0.156). On a monolingual site use `range site.Pages` with `.Aliases`. `disableAliases: true` still suppresses the HTML alias files while `.Aliases` stays populated. `[verified]` `[rel v0.156.0]`

### 1.4 Do the old paths still work?

Yes, silently. A legacy tree (`_default/single.html`, `_default/list.html`, `index.html`, `_default/terms.html`, `_default/taxonomy.html`, `partials/`, `shortcodes/`, `_default/_markup/`, `index.json`) rendered identically on 0.123.3 and 0.167.0, with **no deprecation message** even at `--logLevel info`. The old `terms.html`/`taxonomy.html` meaning is also kept inside `_default/`. `[verified]`

They are only a compatibility mapping ("mapping old to new", with a few reported breakages). The docs describe the new tree only. Use the new tree exclusively and do not mix the two. `[docs new-templatesystem-overview]` `[rel v0.146.2 "Fix legacy section mappings"]` `[rel v0.147.4]`

Two legacy constructs do **not** work:
- `partial "partials/x.html"`: WARN "superfluous prefix" followed by ERROR "partial not found". `[verified]`
- `templates.Exists "partials/x.html"` returns `false`. Use `templates.Exists "_partials/x.html"`. `[verified]`

---

## 2. Removed or renamed template functions and methods since 0.123

Each row was run on 0.167 `[verified]` (`/tmp/hugo-research/probe-167.txt`). "Error" means the build fails.

| Old | 0.167 status | Use instead | When |
|---|---|---|---|
| `getJSON`, `getCSV` | **error** "function not defined" | `resources.GetRemote` + `transform.Unmarshal`, wrapped in `try` | removed in 0.156 `[rel v0.156.0]` |
| `resources.ToCSS` | **error** | `css.Sass` (or `css.Build` for plain CSS) | removed in 0.156 |
| `resources.Babel`, `resources.PostCSS` | removed | `js.Babel`, `css.PostCSS` | 0.156 |
| `crypto.FNV32a` | removed | `hash.FNV32a` | 0.156 |
| `.Site.Social` / `site.Author` / `site.Authors` | **error** | `site.Params.social` / `site.Params.author` (the embedded RSS, OpenGraph and Twitter templates read `params.author` and `params.social`) | deprecated in 0.124, removed in 0.156 |
| `.Site.IsServer` | **error** | `hugo.IsServer` (also `hugo.IsDevelopment`, `hugo.IsProduction`) | removed by 0.139 `[rel v0.139.0]` |
| `.Site.LastChange` | **error** | `.Site.Lastmod` | 0.156 |
| `.Site.IsMultiLingual` | **error** | `hugo.IsMultilingual` | 0.156 |
| `.Site.DisqusShortname`, `.Site.GoogleAnalytics` | **error** | `site.Config.Services.Disqus.Shortname`, `site.Config.Services.GoogleAnalytics.ID` | removed by 0.139 |
| `.Sites.First` | removed | `hugo.Sites.Default` | 0.156 |
| `.Hugo`, `.Site.Hugo` | **error** | `hugo.Version` and so on | removed by 0.139 |
| `.RSSLink`, `.UniqueID` | **error** | `with .OutputFormats.Get "rss"`; `.File.UniqueID` (guard with `with .File`) | removed by 0.139 |
| `.NextPage` / `.PrevPage` | **error** | `.Next` / `.Prev` (and `.NextInSection` / `.PrevInSection`) | 0.156 |
| `.Paginator.PageSize` | **error** | `.Paginator.PagerSize` | deprecated 0.128, removed 0.156 |
| resource `.Err` (from `GetRemote`) | **error** "can't evaluate field Err in type resource.Resource". `GetRemote` errors now fail the build. | `{{ with try (resources.GetRemote $u) }}{{ with .Err }}{{ warnf "%s" . }}{{ else with .Value }}…{{ end }}{{ end }}` | 0.141 `[rel v0.141.0]` `[docs /functions/go-template/try/]` |
| `.Site.Data` | WARN deprecated | `hugo.Data` (functionally identical) | 0.156 |
| `.Site.Languages` | WARN deprecated | `.Rotate "language"`, `hugo.Sites`, `site.Language` | 0.156 |
| `.Site.AllPages` | WARN deprecated | monolingual: `site.Pages`; multilingual: `range hugo.Sites` then `.Pages` | 0.156 |
| `.Site.BuildDrafts` | WARN deprecated | no replacement (check `.Draft`) | 0.156 |
| `.Site.Sites`, `.Page.Sites` | WARN deprecated | `hugo.Sites` | 0.156 |
| `.Site.LanguageCode`, `.Language.LanguageCode/LanguageName/LanguageDirection` | WARN deprecated | `.Site.Language.Locale`, `.Language.Locale/Label/Direction` | 0.158 `[rel v0.158.0]` |
| `.IsNode` | WARN deprecated | `.IsBranch` | 0.163 |
| image `.Exif` | WARN deprecated | `.Meta` (EXIF + IPTC, optionally XMP) | 0.155 |
| `.Scratch` | silent alias of `.Store` | `.Store` (also `site.Store`, `hugo.Store`, shortcode `.Store` since 0.139) | 0.138 / 0.139 |
| `resources.PostProcess` | deprecated | `templates.Defer` | 0.164 |
| `{{ return value }}` outside a partial | **error** | `return` without a value works anywhere since 0.166 and now follows control flow (it can sit inside `if`/`range`) | 0.166 `[docs /functions/go-template/return/]` |
| `.Sitemap` (page) | still works: `.Sitemap.ChangeFreq/.Priority/.Disable`; front-matter `sitemap.disable` since 0.125 | n/a | `[verified]` `[rel v0.125.0]` |
| `.Site.MainSections`, `.Site.Params`, `.Site.Home`, `.Site.Taxonomies`, `.Site.Copyright`, `.Site.BaseURL` | still work | n/a | `[verified]` |

New and useful since 0.123:
- `try` (0.141)
- `templates.Current` (0.146, experimental)
- `templates.Defer` (0.128)
- `hugo.Data` / `hugo.Sites` (0.156)
- `.ContentWithoutSummary` and `.Markup "scope"` (0.134)
- `.PageInner` in hooks (0.125)
- `.OutputFormats.Canonical` (0.154.4)
- `reflect.IsPage/IsSite/IsResource/IsImageResource` (0.154) and `reflect.IsImageResourceProcessable`
- partial decorators with `inner` (0.154)
- `strings.ReplacePairs` (0.158), `strings.FirstLower` (0.167)
- `resources.Publish` (0.166), `Pages.IndexOf` (0.166)
- `urls.PathEscape` (0.153)
- `css.ChromaStyles` (0.165)
- `crypto.Hash`, `encoding.HexEncode` (0.164)
- `time.In` (0.146)

`eq 1 1.0` is now `true`, and `in`/`where`/set functions compare numbers exactly (0.167). `[rel v0.167.0]` `[verified]`

**YAML numbers:** since the goccy/go-yaml switch in 0.152, a front-matter `view: 4` reaches templates as **`uint64`**. `printf "%T"` checks against `"int"` break, as HugoBlox's `render_view.html` does. `eq .Params.view 4` still works. `[verified]` `[rel v0.152.0]`

---

## 3. Config keys

| Key in current site / 0.123 | 0.167 | Source |
|---|---|---|
| `paginate: 100` | **Silently ignored**: `pagerSize` stays 10, with no warning. Use `pagination: {pagerSize: 100}`. | removed 0.156 `[rel v0.156.0]` `[verified]` |
| `paginatePath` | Silently ignored. Use `pagination.path`. Also new: `pagination.disableAliases` (0.128). | `[verified]` |
| `languageCode` / `languages.en.languageCode` | WARN deprecated. Use `locale` / `languages.en.locale`. Also `languageName` becomes `label`, `languageDirection` becomes `direction`. | `[rel v0.158.0]` `[verified]` |
| `cascade: [{_target: …}]` | WARN deprecated. Use `target:`. | `[rel v0.156.0]` `[verified]` |
| `imaging.quality: 90` | WARN deprecated. Use `imaging.jpeg.quality`, `imaging.webp.quality`, `imaging.avif.quality`. `hint` and `compression` also move per format. | `[rel v0.163.0]` `[verified]` |
| `markup.goldmark.parser.autoHeadingIDType` | Renamed to `autoIDType` in 0.144. The old key is still accepted silently. Values: `github` (default), `github-ascii`, `blackfriday`. | `[src v0.167.0 markup/goldmark/goldmark_config/config.go]` `[docs /configuration/markup/]` `[verified]` |
| `markup.goldmark.renderHooks.{link,image}.enableDefault` | **error** (removed). Use `useEmbedded: auto/never/always/fallback`. | `[rel v0.148.0]` `[verified]` |
| `markup.highlight` | Unchanged core. `noHl` removed (0.141); `wrapperClass` added (0.140.2); `lineNos` accepts `true/false/"inline"/"table"` (0.156); light/dark Chroma style pairs (0.164). | release notes |
| `markup.tableOfContents` | Same keys: `startLevel` 2, `endLevel` 3, `ordered`. ToC titles are now sanitized and get Goldmark extras applied (0.149). | `[docs /configuration/markup/#table-of-contents]` `[rel v0.149.0]` |
| `footnoteReturnLinkContents` (root) | Dead key: it had no effect with Goldmark even on 0.123. Use `markup.goldmark.extensions.footnote.backlinkHTML` (0.151). | `[verified on 0.123 and 0.167]` `[rel v0.151.0]` |
| `disableAliases: true` (root) | Still works. | `[verified]` |
| `outputs` kinds | `home`, `page`, `section`, `taxonomy`, `term`. `disableKinds` also accepts `404`, `robotstxt`, `rss`, `sitemap`. | `[docs /configuration/all/]` |
| `caches.getresource.maxAge: 1h` | Still valid. Default dir is `:cacheDir/:project`. The `getjson`/`getcsv` caches were removed (0.156). | `[docs /configuration/caches/]` |
| `caches.images` | Default `:resourceDir/_gen`. Hugo's Netlify guide recommends `dir: ':cacheDir/images'` so the image cache persists in `HUGO_CACHEDIR` across builds. | `[docs /host-and-deploy/deploy-to-netlify/]` |
| `security.http.urls` | Defaults hardened in 0.161 and 0.166. Loopback, private, CGNAT and digit-leading hosts are denied, and the resolved address is checked at dial time. `api.github.com` is still allowed. | `[rel v0.161.0]` `[rel v0.166.0]` `[verified: effective config]` |
| `security.allowContent` (new) | `text/html` and `text/org` **content files are denied by default** (0.162 / 0.166). See gotcha 4. | `[rel v0.162.0]` `[docs /configuration/security/]` `[verified]` |
| `minify` | The tdewolff keys stay. CSS minification targets CSS3 (0.149.1). `minify.tdewolff.svg.keepNamespaces: ['', 'x-bind']` is the default (0.159.1). The `--minify` flag maps to `minify.minifyOutput` (0.150.1). | release notes `[verified: effective config]` |
| `related` | Same keys (`threshold`, `includeNewer`, `toLower`, `indices`). New in 0.166: `tokenize`, `minTokenLength`. | `[docs /configuration/related-content/]` |
| `services.rss.limit` | Default `-1` (unlimited); access with `.Site.Config.Services.RSS.Limit`. | `[docs /configuration/services/]` |
| `cleanDestinationDir` (root) | Deprecated in 0.167. Use `build.cleanDestinationDir.enable`. | `[rel v0.167.0]` `[verified]` |
| root `author:` / `social:` | Silently dropped from the config. Move to `params.author` / `params.social`. | `[verified]` |
| root `googleAnalytics`, `disqusShortname` | Still migrated into `services.*`. | `[verified]` |
| `baseURL` | Default is now `https://example.org/` when unset (0.167). | `[rel v0.167.0]` |
| YAML | Duplicate mapping keys are now a **hard error** (`mapping key "security" already defined`). Unquoted `yes/no/on/off/y/n` are now strings, not booleans. YAML anchors and aliases are supported. | `[rel v0.152.0]` `[verified]` |
| `build.noJSConfigInAssets` | Set it to `true`. Otherwise `js.Build` writes `assets/jsconfig.json`, which is why it shows up untracked in git status. | `[docs /functions/js/build/]` `[verified]` |
| `--resourceDir` CLI flag | Gone. Use `HUGO_RESOURCEDIR` or the `resourceDir` config key. | `[verified]` |

Effective 0.167 defaults worth knowing `[verified: hugo config]`:
- `frontmatter.lastmod: [':git', 'lastmod', 'modified', 'date', 'publishdate', 'pubdate', 'published']`. `:git` needs `enableGitInfo` or `HUGO_ENABLEGITINFO=true`. `git` has been in `security.exec.allow` since 0.129.
- `markup.highlight.noClasses: true`, style `monokai`.
- `goldmark.parser.attribute.title: true`.

---

## 4. Image processing

- **File names:** 0.123 wrote `<stem>_hu<md5 of source>_<bytes>_<WxH>_<op>_<filter>_<anchor|…>_<q>.<ext>`, e.g. `test_hub04d6a2…d86_163161_300x0_resize_q90_h2_lanczos_3.webp`. 0.167 writes **`<stem>_hu_<xxhash hex>.<ext>`**, e.g. `test_hu_5d53d3d1af0d9174.webp` and `featured_hu_e2b4b572cc2b1840.jpg`. `[verified on both binaries]`
  - The hash is a hex uint64 **without zero padding**, so it is usually 16 characters but can be 15 (`test_hu_b540018ee6e9638.png`). `[verified]`
  - The hash covers source content, processing options and the **imaging config** (0.142). Changing any `imaging.*` value renames every processed image. `[rel v0.131.0]` `[rel v0.142.0]`
  - The source md5 no longer appears in the name. Old `_hu<32 hex>` URLs cannot be mapped mechanically to new names; take the new names from the built HTML.
- **`len .Content` equals the file size.** PNG: `len .Content` = 163161 = `stat` size. JPG: 70387 = 70387. For non-page resources `.Content` returns the raw bytes as a string. `[verified]` `[docs /methods/resource/content/]`
- **WebP:** encode and decode run through WASM libwebp 1.6 since 0.153 in **all** editions, which fixes the old muted-colour decode bug. Animated WebP is supported, including GIF to WebP and WebP to GIF. `[rel v0.153.0]` `[verified: PNG→webp, webp→jpg, animated GIF→animated WebP (113 frames), animated WebP→animated GIF (113 frames)]`
- **AVIF:** encode and decode since 0.162. Default quality 60, with a per-format `hint` and `compression` (0.163). Encoding an animated source to AVIF produces a static image. `[rel v0.162.0]` `[rel v0.163.0]` `[docs /configuration/imaging/#avif]` `[verified: PNG→avif, avif→png]`
- Processable types: avif, bmp, gif, jpeg, png, tiff, webp. HEIC/HEIF are metadata-only. `[docs /quick-reference/glossary/processable-image/]` `[rel v0.157.0]`
- **Animated GIF:** `.Resize "300x"` on a 113-frame GIF keeps all 113 frames (0.123 also kept animation). `[verified]`
- Image config now lives per format: `imaging.jpeg.quality` (default 75), `imaging.webp.{quality 75, hint photo, method 2, compression lossy, useSharpYuv}`, `imaging.avif.{quality 60, hint, encoderSpeed 10, compression}`. `resampleFilter`, `anchor` and `bgColor` stay top level. `[docs /configuration/imaging/]`
- `.Exif` is deprecated; use `.Meta` (0.155). `[verified]`
- A cold build of the current site on 0.167 (412 processed images) took 40 s with 1.2 GB peak RSS, about the same as 0.123's cold 39.5 s. `[verified]`

---

## 5. CSS and JS pipelines

### 5.1 `css.Build` (new in 0.158, esbuild-backed) `[docs /functions/css/build/]` `[rel v0.158.0]`

- Recursively inlines `@import` from `assets/`. Bare, `./`, `../` and `/root` paths and Node packages are resolved. Remote `@import url(https://…)` is kept as-is.
- An `@import … layer(x)` / `supports()` / media query wraps the imported content in `@layer x {}` / `@supports` / `@media`.
- Options:
  - `minify` (default false)
  - `target` (default unset: **no syntax lowering, no prefixing**)
  - `targetPath`
  - `sourceMap`
  - `loaders` (`file`, `dataurl`, …)
  - `externals`
  - `vars` with `@import "hugo:vars"` (0.160; nested `hugo:vars/<name>` 0.161)
  - `importContext` (0.165)
  - `.Data.Artifacts` for fonts and images copied by the `file` loader (0.165)
- Locally, on two imported files using `@layer`, `layer()` and native nesting `[verified]`:
  - **Without `target`, nesting is preserved** and the output is minified: `@layer reset,base,components;@layer components{.a{color:red;.b{color:green}}}@layer components{.b2{margin:0 auto;>p{margin:0}}}@layer base{body{color:#000;& a{color:#00f}.card{padding:1rem;&:hover{color:red}}}}`
  - `target: [chrome120, edge120, firefox117, safari17.2, ios17.2]` also **preserves** nesting.
  - The docs' "baseline" target `[chrome115 edge115 firefox116 ios16.4 opera101 safari16.4]` **lowers** nesting to flat selectors (`.a .b{…}`, `body .card:hover{…}`).
  - With `minify` off, the output contains comments with **absolute build paths** (`/* ns-hugo-imp:/tmp/…/a.css */`). Always minify published CSS.
- `resources.Concat | minify` also keeps nesting (`.a{color:red;& .b{color:green}}`), but it resolves no `@import` and adds no `layer()` wrapping. `[verified]`

**Recommended pattern** for several plain CSS files with nesting and `@layer`:

```css
/* assets/css/main.css */
@layer reset, tokens, base, layout, components, prose, utilities;
@import "./reset.css" layer(reset);
@import "./tokens.css" layer(tokens);
@import "./components/card.css" layer(components);
/* … */
```

```go-html-template
{{/* layouts/_partials/head/css.html, called via partialCached "head/css.html" . */}}
{{ with resources.Get "css/main.css" }}
  {{ $opts := dict
    "minify" true
    "targetPath" "css/main.css"
    "target" (slice "chrome120" "edge120" "firefox117" "safari17.2" "ios17.2")
  }}
  {{ with . | css.Build $opts | fingerprint }}
    <link rel="stylesheet" href="{{ .RelPermalink }}" integrity="{{ .Data.Integrity }}" crossorigin="anonymous">
  {{ end }}
{{ end }}
```

Leave `target` off, or pick browsers that support relaxed nesting, if nesting should ship as written. Set it lower only if lowering is wanted.

### 5.2 Other CSS functions

- `css.Sass`: Dart Sass binary only. LibSass (extended edition) has been deprecated since 0.153.
- `css.TailwindCSS`: v4, needs the npm-installed CLI. The standalone binary has been unsupported since 0.161, and Tailwind was removed from the default `security.exec.allow` in 0.165.

Neither is needed here. `[rel v0.153.0]` `[rel v0.161.0]` `[rel v0.165.0]`

### 5.3 JS

- `js.Build` (esbuild) options:
  - `format` (`iife` default; `esm`)
  - `minify`
  - `target` (es2015…es2025, esnext; default esnext)
  - `params`
  - `externals`
  - `defines`
  - `drop` (0.144)
  - `loaders` / `platform` / `sourcesContent` (0.140)
  - `importContext` (0.165)

  `[docs /functions/js/build/]`
- Verified: `format: esm` + `minify` bundled `main.js` → `./util.js` into `function e(o){console.log(\`hello ${o}\`)}document.addEventListener("DOMContentLoaded",()=>e("world"));` and tree-shook the unused export. `[verified]`
- Serve the result with `<script type="module" src=…>`. `fingerprint` gives `.Data.Integrity` (SHA-256 by default).
- `js.Batch` (0.140) builds code-split bundle groups with runners. It is overkill for a few modules; use one `js.Build` entry per page type instead. `[docs /functions/js/batch/]`

---

## 6. Content and rendering features

- **Summaries (0.134 rewrite):** manual, front-matter and automatic summaries are all **HTML**. Automatic summaries are cut at block boundaries, not mid-sentence plain text, and since 0.167 they never end inside an open list or blockquote. Use `{{ .Summary | plainify }}` for plain text. `.ContentWithoutSummary` is new. `[rel v0.134.0]` `[rel v0.134.2]` `[rel v0.150.0]` `[rel v0.167.0]` `[docs /content-management/summaries/]`
  - Verified on the same post: 0.123 returned plain text (`list item one … list item two …` flattened). 0.167 returned `<p>…</p><ul><li>…</li></ul><p>…</p>`.
  - Across the real site's `index.json`, 3 of 134 summaries differ. `[verified]`
- **`.ReadingTime`:** now `ceil(words/212)` (CJK `/500`), previously effectively `/213` and `/501` (0.166 fix #15206). On the real site, 1 of 68 posts changed: `self-hosting-ai-is-not-cheaper` went from 22 to 23 min. `[rel v0.166.0]` `[verified]`
- **Heading IDs:** with `autoIDType: github`, `.Anchor` gives `📖 Origin Story` → `-origin-story`, `1,400 commits, rewritten in minutes for $2.50` → `1400-commits-rewritten-in-minutes-for-250`, and `Vertical column‑stagger` (U+2011) → `vertical-columnstagger`. These are identical to 0.123. Duplicates get `-1`. `anchorize` agrees, and `.Fragments.Identifiers` / `.TableOfContents` use the same IDs.
  - All **766 heading IDs** across the real site's post pages are identical between 0.123 and 0.167 builds. `[verified]`
  - 0.144 stopped putting link destinations into auto IDs of headings that contain links. This did not affect this site. `[rel v0.144.0]`
- **Render hooks:**
  - Heading context: `Anchor`, `Attributes`, `Level`, `Ordinal` (0.160), `Page`, `PageInner` (0.125), `PlainText`, `Position` (0.160), `Text`.
  - Image hook: adds `IsBlock`, which needs `markup.goldmark.parser.wrapStandAloneImageWithinParagraph: false`, plus `Ordinal`. All `Text` values are `template.HTML` (0.134).
  - New hook types: blockquote with GitHub/Obsidian alerts (0.132/0.134), passthrough (0.132), table (0.134; a user table hook beats the embedded one since 0.167).
  - Since 0.141, render hooks fall back only to the HTML output-format template.
  - `[docs /render-hooks/headings/]` `[docs /render-hooks/images/]` `[docs /render-hooks/code-blocks/]`
- **Security:** 0.125.3, 0.139.4 and 0.159.2 escaped titles, attributes and dangerous URLs in the embedded hooks. Custom link and image hooks should escape too: `{{ .Destination | safeURL }}` only for trusted content. `[rel v0.159.2]`
- **`.Store`:** state set from a hook, e.g. `.Page.Store.Set "hasMermaid" true` in `render-codeblock-mermaid.html`, is visible in the page template only **after** content has rendered. Call `.Content`, `.TableOfContents` or `.Fragments` first, then test `.Store.Get`. `[verified]`
- **`.RenderShortcodes`:** context-marker leaks and indentation bugs fixed (0.137, 0.139, 0.160.1). `[rel v0.160.1]`
- **`partialCached`:** deadlock-key fix (0.149); `templates.Defer` is rejected inside it (0.162). `[rel v0.149.0]` `[rel v0.162.0]`
- **`.Lastmod` with Git:** `enableGitInfo` (or `HUGO_ENABLEGITINFO`) plus the default `:git` front-matter order. `.GitInfo` returns a pointer (nil-safe with `with`), `Ancestor` was renamed `Parent`, and `Ancestors` was added (0.148). `[rel v0.148.0]` `[verified: GitInfo nil when disabled]`
- **Related content:** `site.RegularPages.Related .` works. The default indices are keywords, date and tags; the site's own config overrides them. `[verified]`

---

## 7. Embedded SEO, RSS and sitemap templates (0.167 vs 0.123)

All templates are embedded under `tpl/tplimpl/embedded/templates/` (`/_partials/` for partials). Call them with `partial "opengraph.html" .`, `partial "schema.html" .`, `partial "twitter_cards.html" .`, `partial "pagination.html" .` and `partial "google_analytics.html" .`. `[src v0.167.0]` `[verified]`

- **opengraph.html** (rewritten in 0.125, refined since):
  - Uses `plainify` on title and description, and `og:locale` from `site.Language.Locale`.
  - `og:site_name` comes from `site.Title`; 0.123 used `site.Params.title`.
  - Adds up to 6 `article:tag` entries from tags.
  - `og:image` comes from the `images` front matter, else a bundle resource matching `*feature*`, then `{*cover*,*thumbnail*}`, else `site.Params.images[0]`. Global assets are allowed since 0.162.
  - Social keys come from `site.Params.social.facebook_app_id` / `facebook_admin`.
  - `[src v0.167.0 _partials/opengraph.html]` `[rel v0.125.0]` `[rel v0.162.0]`
- **twitter_cards.html:** `summary_large_image` when a page image exists, else `summary`. `twitter:site` comes from `site.Params.social.twitter`. `[src v0.167.0]`
- **schema.html:** microdata `itemprop` meta tags only (name, description, dates, wordCount, image, keywords). It is **not JSON-LD**; write your own JSON-LD partial if you want it. `[src v0.167.0]`
- **rss.xml** changes since 0.123:
  - `<pubDate>` uses `.PublishDate` (0.125; it was `.Date`).
  - `<language>` uses `site.Language.Locale` (0.158).
  - `<generator>Hugo</generator>`.
  - The `site.Author` fallback was removed; it now reads only `params.author.{name,email}` or a string.
  - Unchanged: `<guid>` is `.Permalink` (no `isPermaLink` attribute), `lastBuildDate` is the newest `.Lastmod` of the feed's pages, the description is `.Summary | transform.XMLEscape` (now HTML, see section 6), and the limit comes from `services.rss.limit` (default −1).
  - `[src v0.123.3 vs v0.167.0 rss.xml]` `[rel v0.125.0]`
- **sitemap.xml:** ranges `where .Pages "Sitemap.Disable" "ne" true` (front-matter `sitemap.disable`, 0.125), uses `.AllTranslations` and `.Language.Locale` for hreflang (0.162), and drops the self `xhtml:link`. `[src diff]` `[rel v0.162.0]`
- **robots.txt:** `User-agent: *` plus a trailing newline (0.146). `[src]`
- **RSS and sitemap templates are executed with `html/template`.** HTML comments are stripped and a literal `<?xml …?>` is escaped to `&lt;?xml`. Emit it with `{{ printf "<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?>" | safeHTML }}`, as the embedded templates do. `[verified]`

---

## 8. Netlify

- `HUGO_VERSION = "0.167.0"` in `netlify.toml` `[build.environment]` is supported: Netlify installs any released Hugo version named there. Hugo's own Netlify guide uses exactly `HUGO_VERSION = "0.167.0"`, `GO_VERSION = "1.27.1"` and `NODE_VERSION = "24.21.0"`. `[docs /host-and-deploy/deploy-to-netlify/]` `[Netlify docs: build/frameworks/framework-setup-guides/hugo, configure-builds/available-software-at-build-time]`
- The site must use Netlify's current build image (Ubuntu 24.04 Noble). Hugo 0.149+ failed on the old image. `[rel v0.149.0 note]` `[Netlify available-software page]`
- **Dart Sass is not preinstalled**; Hugo's guide downloads it in the build command. We don't need it.
- Go is preinstalled (`GO_VERSION`, default `1.x`). It is only needed for Hugo Modules, which the hand-written theme can drop together with `go.mod`.
- Suggested build command, following Hugo's guide: `hugo build --gc --minify --baseURL "${URL}"`. Also add `caches.images.dir: ':cacheDir/images'` so the existing `HUGO_CACHEDIR=/opt/build/cache/hugo` keeps processed images between deploys. `[docs same]`

---

## 9. The current HugoBlox site on 0.167

Built a detached worktree of `own-theme` HEAD with 0.167.0 (now removed). The worktree is gone; the error logs are `/tmp/hugo-research/site-build.log` and `site-build2.log`. `[verified]`

**The unchanged site does not build.** Errors, in the order they appeared once each previous one was patched:

1. `blox-bootstrap/v5@v5.9.7/layouts/shortcodes/table.html:29:1": parse of template failed: … function "getCSV" not defined` (getCSV removed in 0.156).
2. `content/post/<bundle>/entangled-cores.html: access denied: "text/html" is not whitelisted in policy "security.allowContent"` (0.162). This is an `.html` SVG fragment inside a leaf bundle.
3. `layouts/partials/functions/github_stars.html:15:15 … can't evaluate field Err in type resource.Resource` (our own partial; `.Err` was replaced by `try`).
4. `blox-bootstrap … partials/comments.html … partial "partials/comments/giscus.html" not found` (the `partials/` prefix is no longer resolved).

After patching those four, it builds: 830 pages, 412 processed images, exit 0. It still prints WARNs:
- `cascade._target` deprecated
- `imaging.quality` deprecated
- `languages.en.languageCode` deprecated
- `blox-seo … _default/_markup/sitemap.xml: unrecognized render hook template`
- `Failed to locate view at partials/views/%!s(uint64=4).html`: the YAML-uint64 issue in HugoBlox's `printf "%T"` check

Also noted while testing a YAML config edit: a duplicated top-level `security:` key is a hard error.

---

## 10. Gotchas when coming from 0.123

1. **`paginate: 100` and `paginatePath` are silently ignored.** Without `pagination.pagerSize: 100` every paginated list drops to 10 per page. `[verified]`
2. **Summaries are HTML now** (`<p>`, `<ul>`), so card snippets need `.Summary | plainify`. RSS `<description>` is escaped HTML. `[verified]`
3. **Use `taxonomy.html` for `/tag/` and `term.html` for `/tag/x/`.** The 0.123 meaning of `_default/taxonomy.html` (term) is gone in the new tree. `[docs]`
4. **`.html` files under `content/` are refused** (`security.allowContent`). The bundle SVG `entangled-cores.html` either needs `security.allowContent: ['.*']` (this opts back into HTML-as-content, which is an XSS risk only for untrusted content) or a rename to `.svg`. After a rename, `bleed-svg` can use `(.Page.Resources.Get "entangled-cores.svg").Content` instead of `readFile`. `[verified]`
5. **Never prefix partial names with `partials/`. `templates.Exists` needs `_partials/…`.** `[verified]`
6. **Wrap every `resources.GetRemote` in `try`.** Errors fail the build otherwise, and loopback or private hosts are refused. `[verified]`
7. **YAML:** front-matter integers are `uint64`, duplicate keys are fatal, and `yes`/`no`/`on`/`off` are strings. Compare numbers with `eq`/`lt`, not `printf "%T"`. `[verified]` `[rel v0.152.0]`
8. **Image URLs change** to `<stem>_hu_<hash>.<ext>` and change again whenever `imaging.*` config changes. The parity tool's `_hu<32-hex md5>` logic only describes the 0.123 baseline. `[verified]`
9. **`imaging.quality` becomes `imaging.jpeg.quality` / `imaging.webp.quality`.** The defaults differ: WebP 75, AVIF 60. Set them explicitly to keep 90. `[verified]`
10. **`css.Build` without `target` ships nesting as written.** The docs' "baseline" target lowers it. Unminified output leaks absolute paths in comments. `[verified]`
11. **`return VALUE` only works in partials.** Bare `return` follows control flow since 0.166: code after a conditional `return` now runs when the branch is not taken. `[rel v0.166.0]`
12. **`.Store` flags set by render hooks** are only readable after `.Content`, `.TableOfContents` or `.Fragments` has run. `[verified]`
13. **Set `build.noJSConfigInAssets: true`**, or `js.Build` keeps writing `assets/jsconfig.json`. `[verified]`
14. **Use `site.Language.Locale`** for `<html lang>`, `og:locale` and similar; `LanguageCode` is deprecated. Replace `site.AllPages` with `site.Pages` and `.Site.Data` with `hugo.Data`. `[verified]`
15. **RSS, sitemap and JSON templates are html/template.** Comments vanish, and `<?xml` must go through `safeHTML`. `[verified]`
16. **`footnoteReturnLinkContents` was already dead.** Use `markup.goldmark.extensions.footnote.backlinkHTML`. `[verified]`
17. **`ReadingTime` can be one minute higher** (one post on this site). `[verified]`
18. **`--resourceDir` is gone**; use `HUGO_RESOURCEDIR`. `[verified]`
19. **Pre-existing, not a 0.167 change:** `baseurl: '/'` makes every permalink, RSS `<link>`, sitemap `<loc>` and `og:url` relative. This is true on production today (`https://www.nijho.lt/index.xml` has `<link>/</link>`) and stays true on 0.167. Set an absolute `baseURL` or pass `--baseURL "${URL}"`. `[verified: live feed and 0.167 build]`

## Appendix: local artefacts

- Binaries: `/tmp/hugo-latest/bin/hugo` (0.167 extended), `/tmp/hugo-latest/std/hugo` (0.167 standard, static), `/tmp/hugo-latest/v0123/hugo` (0.123.3)
- New-layout scratch site: `/tmp/hugo-research/scratch` (probe output in `public/post/hello/index.html`)
- Legacy-layout scratch site: `/tmp/hugo-research/scratch-legacy` (`public-123/` vs `public-167/`)
- API probe: `/tmp/hugo-research/tools/probe.sh` + `exprs.txt` → `/tmp/hugo-research/probe-167.txt`
- Old-site outputs: `/tmp/hugo-research/site-public-123` (0.123, unmodified) and `/tmp/hugo-research/site-public` (0.167, 4 patches)
- Release notes: `/tmp/hugo-research/notes/all.md`
- Docs: `/tmp/hugo-research/hugoDocs/content/en`
- Embedded templates: `/tmp/hugo-research/embedded/{v123,v167}`
