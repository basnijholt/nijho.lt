# Tools

Standalone [uv](https://docs.astral.sh/uv/) scripts; `uv run` installs what each one declares at its top.
`migration/` holds the tooling for the theme switch and can go once that has settled (see its README).

## Browser checks

```bash
uv run tools/browser_check.py [BUILD_DIR] [--screenshots OUT_DIR [--no-checks]]
```

Serves a build (by default, a fresh production build of the working tree with `$HUGO_BIN`, else `hugo`) and checks it in Chromium (`$CHROMIUM`, default `/run/current-system/sw/bin/chromium`): the theme menu, search, the project filters, console errors, axe accessibility in light and dark, the weight of a plain post, the homepage without JavaScript, menu links and anchors under the sticky header, the header layout, list text width and keyboard focus.
Exits 1 if a check fails.
`--screenshots` also saves the key pages in light and dark at 1440 and 390 px wide; with `--no-checks` it only does that.

## Contact map

```bash
uv run tools/contact_map.py [--zoom 10]
```

Draws `assets/media/map.webp`, the homepage's contact map, from OpenStreetMap tiles centered on `content.coordinates` in `content/home/contact.md`.
The page puts its marker at the center of the image, so run this after changing the coordinates.
