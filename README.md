# [nijho.lt](https://www.nijho.lt/)

[![Netlify Status](https://api.netlify.com/api/v1/badges/1b9d8edc-3626-48f1-a6bd-52de691b2fda/deploy-status)](https://app.netlify.com/sites/nijholt/deploys)

My personal website: a blog, my open-source projects, publications and photos.
It is built with [Hugo](https://gohugo.io/) and a theme that lives in this repository, and [Netlify](https://www.netlify.com/) deploys every push to `main`.

## Running it

```bash
devbox run dev      # http://localhost:1313, rebuilds on save, shows drafts
devbox run build    # production build into public/
```

[Devbox](https://www.jetify.com/devbox) provides Hugo 0.165.0, the newest it packages; with Hugo installed some other way, `hugo server -D` does the same.
Netlify builds with Hugo 0.167.0, set in `netlify.toml`, and builds a preview for every pull request.

## Writing

Most pages are a folder with an `index.md` and its images next to it.

| What | Where | Front matter that matters |
|---|---|---|
| Blog post | `content/post/<slug>/` | `title`, `date`, `summary`, `tags`, `categories`, optional `subtitle` |
| Project | `content/project/<slug>/` | `title`, `date`, `summary`, `tags`, `external_link` |
| Publication | `content/publication/<slug>/` | `title`, `date`, `authors`, `publication`, `abstract`, `url_pdf`, `url_code`, `links` |
| Homepage section | `content/home/<id>.md` | `weight` sets the order; the file name is the section's `#id` |
| About me | `content/authors/admin/_index.md` | `role`, `organizations`, `social`, `interests`, `education` |

Images and other switches:

- A file named `featured.*` is the page's image: at the top of the page, in lists and on share cards. `image.placement: 2` makes it as wide as the page, and `image.preview_only: true` keeps it off the page itself. A `thumbnail.*` replaces it in post lists.
- A project's `animated.svg` is shown on its card instead. Cards are sorted by GitHub stars, which the build fetches from the API; without them, newest first.
- `draft: true` hides a page, `math: true` loads MathJax, `commentable: false` turns off the comments, and `private: true` keeps a page out of search engines.

### Shortcodes

| Shortcode | Does |
|---|---|
| `{{% callout note %}}…{{% /callout %}}` | A highlighted note; `warning` for a warning |
| `{{< figure src="x.png" caption="…" >}}` | An image with a caption; images in Markdown get the same treatment |
| `{{< video src="clip.mp4" >}}` | A video, with `clip.jpg` as its poster; add `controls="true"`, `autoplay="true"` or `loop="true"` |
| `{{< plot name="cost" >}}` | An [Observable Plot](https://observablehq.com/plot/) chart from the page's `plots.js` |
| `{{< gallery album="name" >}}` | Thumbnails of `assets/media/albums/name/` |
| `{{< photo-grid >}}` | Photos from `assets/media/photography/` in justified rows; one `<instagram id> \| <alt text>` per line |
| `{{< tooltip text="…" >}}word{{< /tooltip >}}` | Hover text |
| `{{< detail-tag "Summary" >}}…{{< /detail-tag >}}` | A collapsible block |
| `{{< toc >}}` | A table of contents in the text (wide screens show one beside the post anyway) |
| `{{< bleed-svg src="x.svg" >}}` | Artwork whose glow reaches past the text column |
| `{{< demo-clips >}}{{< demo-clip … >}}{{< /demo-clips >}}` | A row of demo recordings, each in a light and a dark version |

A fenced code block with the language `mermaid` renders as a diagram.

## How the theme works

- `layouts/` holds the templates: one per kind of page (`home.html`, `page.html`, `section.html`, `term.html`, ...), separate ones for posts, projects and publications, and the partials, shortcodes and render hooks they use. Each homepage section has a partial in `layouts/_partials/home/`.
- `assets/css/` is plain CSS in cascade layers, from `00-reset.css` to `10-shortcodes.css`, imported by `main.css`. Hugo bundles and minifies it.
- `assets/js/` has one small module per feature: search, the theme menu, the project and publication filters, the contents rail, copy buttons, image zoom and comments. A page loads only the ones it uses.
- `assets/icons/` holds the brand icons, inlined as SVG and used as CSS masks for the Font Awesome markup in the content. Interface icons come from [Phosphor](https://phosphoricons.com/) via `layouts/_partials/ui-icon.html`.
- `config/_default/` has the site settings, the menu and the parameters the templates read (analytics, comments, the repository link).

## URLs to keep

Links to this site exist all over the web, so a change must not move a page:

- Every URL ends in a slash. Folder names with dots or underscores (`/project/rsync-time-machine.py/`, `/publication/phd_thesis/`) and author slugs with dots (`/authors/andrey-e.-antipov/`) stay as Hugo writes them.
- Comments are matched to a post by its path, so a moved post loses its thread.
- Heading anchors are GitHub-style, and the homepage sections keep their IDs (`#about`, `#blog-posts`, `#projects`, `#photography`, `#publications`, `#contact`).
- Files in page folders and `assets/media/` keep their paths, and so does `/bas.asc`.
- When a URL does change, add a redirect to `data/redirects.yaml`. `data/old_images.yaml` sends the image URLs of the previous theme to their files.

## Tools

- `uv run tools/browser_check.py` builds the site and checks it in Chromium: search, the filters, the theme menu, accessibility, page weight, the site without JavaScript and keyboard navigation.
- `uv run tools/contact_map.py` redraws the contact map after the coordinates in `content/home/contact.md` change.

See [tools/README.md](tools/README.md) for the options.
