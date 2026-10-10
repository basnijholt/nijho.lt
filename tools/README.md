# Parity tool

`parity` compares a build of this site with a build of the baseline commit in `parity-baseline.txt` and reports what the candidate lost or changed.
Run it from `tools/`.

## Hugo binaries

The baseline needs Hugo 0.123.3; the candidate uses a newer Hugo.
`HUGO_BASELINE_BIN` picks the baseline binary and `HUGO_BIN` the candidate binary.
An unset or empty `HUGO_BASELINE_BIN` falls back to `HUGO_BIN`, which falls back to `hugo` on `PATH`.

```bash
mkdir -p /tmp/hugo-bin /tmp/hugo-latest/bin
curl -sL https://github.com/gohugoio/hugo/releases/download/v0.123.3/hugo_extended_0.123.3_linux-amd64.tar.gz | tar -xz -C /tmp/hugo-bin hugo
curl -sL https://github.com/gohugoio/hugo/releases/download/v0.167.0/hugo_extended_0.167.0_linux-amd64.tar.gz | tar -xz -C /tmp/hugo-latest/bin hugo
export HUGO_BASELINE_BIN=/tmp/hugo-bin/hugo HUGO_BIN=/tmp/hugo-latest/bin/hugo
```

## compare-branch

```bash
uv run parity compare-branch [--allow FILE] [--baseline-hugo PATH] [--hugo PATH]
```

Builds the baseline commit into `/tmp/parity-baseline/<sha>` and the working tree into `/tmp/parity-candidate-<hash>`, then runs `compare` on them with `parity-allow.yaml`.
The hash comes from the repository path, so every checkout has its own candidate directory; the header names the commit and both directories.
The baseline build is reused until the commit or the baseline Hugo version changes; the candidate is rebuilt every run.
`devbox run parity` runs this from the repository root; without `HUGO_BIN`, both builds get devbox's Hugo.

## compare

```bash
uv run parity compare BASE CAND [--allow FILE] [--only CHECK]...
```

Prints the failures grouped by check, the number of allowed findings, the allow rules that matched nothing, and the number of pages and feeds compared.
A `BASE` without `index.html` is an error, so an empty or wrong directory cannot pass.
Exits 1 if a failure is left; unused rules do not fail the run, and without `--allow` every finding is a failure.
`--only` takes one check name and can be repeated; only rules for the checks that ran can be unused.

A check fails when:

- `paths`: a baseline page, feed, image or other public file is missing (theme assets and `_hu` resized images are skipped).
- `sitemap`: a baseline loc is missing, or a loc has no `index.html` although the baseline loc had one.
- `feeds`: a baseline feed is missing or differs in channel title or link, in its guids (byte for byte) or item links, or in an item's title, pubDate or text.
- `ids`: an id inside a baseline article body, or a homepage section id, is gone from the page.
- `seo`: a page's `<head>` title, SEO `<meta>` tags, canonical or RSS links, or JSON-LD type, headline, dates or author differ.
- `content`: a post, project or publication lost its article body, its text differs (TOC and heading anchors ignored), or its count of `img`, `pre`, `table`, `video` or `details` changed.
- `old-images`: a baseline `_hu` image is gone, unless the first `_redirects` rule matching its path (splats and placeholders included) is a 3xx and the redirects end at the original: an image file on this site named as the old name before `_hu`, with any image extension.
- `internal-links`: an `href`, `src`, `srcset` or video `poster` points to a site path that does not exist, unless the same link on the same baseline page was already broken.
- `redirects`: a baseline `_redirects` rule (source, target, status and `!`) is missing, or an earlier candidate rule matches its source first.

A text difference in a feed item or an article is one finding per changed run of words, shown with up to three unchanged words on each side, so a `match` copied from one finding allows that run and no other.
A run of more than 12 words shows its first and last six with the count between, and after 20 findings one more counts the rest of the text's differences.

## Allow file

An allow file is a YAML list of expected findings:

```yaml
- check: feeds                     # a check name from the list above
  path: /authors/admin/index.xml   # fnmatch glob for the path before the colon in the report
  match: "guid '/post/advent-of-open-source/'"  # optional substring of the text after the colon
  reason: "Why this difference is expected"
```

A rule allows every finding it matches, so a rule without `match`, or with a wide glob, can hide many differences.
In the glob, `*` also matches `/`.
Copy `match` from the report including the quotes around the path; the closing quote keeps `/post/advent-of-open-source/23-pfapack/` from matching too.
A missing `check`, `path` or `reason`, unknown keys or check names, non-string values and an empty `match` are errors.

## baseline

```bash
uv run parity baseline OUT [--commit SHA] [--baseline-hugo PATH]
```

Builds one commit (default: `parity-baseline.txt`) into `OUT` with the baseline Hugo.
Use an empty directory or an earlier `OUT`; an earlier build is reused when the commit and Hugo version match and wiped otherwise.

## old-images

Hugo 0.123.3 names resized images `<name>_hu<md5>_<size>_...` after the source file, and newer Hugo names them differently.
This prints YAML that maps each such baseline image the candidate lacks to its source file in `content/` or `assets/` of `--repo` (default: this repository):

```bash
uv run parity old-images BASE CAND [--repo DIR]
uv run parity old-images /tmp/parity-baseline/$(cat parity-baseline.txt) /tmp/parity-candidate-<hash> > ../data/old_images.yaml
```

It fails if an old image has no source.
Of identical source files, the one named like the old image wins, else the first by path, `content/` before `assets/`.
Hugo 0.123.3 leaves the name out of images resized from a long file name (`_hu<md5>_...`), so the `old-images` check reports those; allow each with a `match` that names its redirect target.
Names containing a word from the commit hook's lists, `forbidden-words` and `forbidden-words.private` in `~/.config/git/` (or `$XDG_CONFIG_HOME/git/`), are skipped; stderr gives the count, and the `old-images` check reports those images.

## live

```bash
uv run parity live --preview URL [--sitemap https://www.nijho.lt/sitemap.xml]
```

Requests every path in the live sitemap from both sites without following redirects, retrying once after a connection error or timeout.
A path passes when the preview returns 200, or the same 3xx as the live site with the same `Location`; a `Location` on www.nijho.lt or on the preview host compares as a path.
Anything else fails, including a 404 on both sides, and the exit code is 1.
A sitemap without `<loc>` entries is an error.

## Tests

```bash
uv run pytest -m "not slow"
uv run pytest   # also builds the baseline commit (Hugo 0.123.3) and the site (Hugo 0.167.0), skipping without them
```
