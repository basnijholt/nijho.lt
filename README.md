# [nijho.lt](http://www.nijho.lt/)

[![Netlify Status](https://api.netlify.com/api/v1/badges/1b9d8edc-3626-48f1-a6bd-52de691b2fda/deploy-status)](https://app.netlify.com/sites/nijholt/deploys)

This is my personal website, built with [Hugo](https://gohugo.io/) and hosted on [Netlify](https://www.netlify.com/).

See the builds on Netlify [here](https://app.netlify.com/sites/nijholt/deploys?filter=main).


## Local Development

This project uses [Devbox](https://www.jetify.com/devbox) for a reproducible development environment.

### Setup

1. [Install Devbox](https://www.jetify.com/devbox/docs/installing_devbox/)
2. Run the development server:
   ```bash
   devbox run dev
   ```

The site will be available at http://localhost:1313 and will automatically rebuild when you make changes.

### Available Scripts

- `devbox run dev` - Start development server with drafts enabled
- `devbox run build` - Build for production
- `devbox run build:preview` - Build including future-dated posts

## Theme

The theme lives in this repository; there is no theme module.
Netlify builds with Hugo 0.167.0 (`netlify.toml`); devbox has 0.165.0, the newest version it packages.

- `layouts/`: Hugo templates, one per page kind (`home.html`, `page.html`, `section.html`, `taxonomy.html`, `term.html`), with `post/`, `project/` and `publication/` versions where those pages differ, and `_partials/`, `_shortcodes/` and `_markup/` (render hooks).
- `layouts/_partials/home/`: one partial per homepage section. `content/home/` sets the order (`weight`) and the text of each section, and a section's file name is its ID (`#projects`).
- `assets/css/`: plain CSS in cascade layers, imported by `main.css` and bundled by Hugo's `css.Build`.
- `assets/js/`: small ES modules, each loaded only on the pages that use it (search, theme menu, project and publication filters, contents rail, copy buttons, image zoom, comments).
- `assets/icons/`: brand icons as SVG, used inline and as CSS masks for the Font Awesome markup in the content.
- `assets/media/map.webp`: the contact map, drawn around the coordinates in `content/home/contact.md` by `tools/contact_map.py`.

`tools/browser_check.py` tests a build in Chromium and `tools/contact_map.py` redraws the contact map; see [tools/README.md](tools/README.md).
`tools/migration/` checked the switch from the old theme (no URL, feed or page went missing) and can be deleted once the switch has settled.
