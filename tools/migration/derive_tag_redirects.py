"""Print data/redirects.yaml entries for the tags a retag commit removed.

Usage: uv run python derive_tag_redirects.py COMMIT

A tag is removed when no content file has it after COMMIT. Its page and feed redirect to the tag that the posts which
had it carry most often after COMMIT; a tie goes to the tag on fewer pages, the more specific one. Review the output
by hand before adding it to data/redirects.yaml.
"""

import subprocess
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
# Characters Hugo keeps in a term's URL besides letters, digits and marks
URL_PUNCTUATION = set("._-+~@#")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout


def slug(term: str) -> str:
    """Hugo's URL segment for a term: accents removed, lowercased, spaces to one hyphen, other punctuation dropped."""
    term = "".join(c for c in unicodedata.normalize("NFD", term) if not unicodedata.combining(c))
    kept = []
    for word in term.lower().split():
        kept.append("".join(c for c in word if c.isalnum() or c in URL_PUNCTUATION))
    return "-".join(word for word in kept if word)


def tags_at(revision: str) -> dict[str, set[str]]:
    """Map each Markdown file under content/ at revision to the slugs of its front-matter tags."""
    tags = {}
    for path in git("ls-tree", "-r", "--name-only", revision, "content").splitlines():
        if not path.endswith(".md"):
            continue
        parts = git("show", f"{revision}:{path}").split("---", 2)
        front_matter = yaml.safe_load(parts[1]) if len(parts) == 3 else None
        if isinstance(front_matter, dict):
            tags[path] = {slug(str(tag)) for tag in front_matter.get("tags") or []}
    return tags


def tag_redirects(commit: str) -> list[dict[str, str]]:
    before, after = tags_at(f"{commit}^"), tags_at(commit)
    pages = Counter(tag for tags in after.values() for tag in tags)
    entries = []
    for old in sorted(set().union(*before.values()) - pages.keys()):
        became = Counter(new for path, tags in before.items() if old in tags for new in after.get(path, ()))
        if not became:
            continue
        new = min(became, key=lambda tag: (-became[tag], pages[tag], tag))
        entries.append({"from": f"/tag/{old}/", "to": f"/tag/{new}/"})
        entries.append({"from": f"/tag/{old}/index.xml", "to": f"/tag/{new}/index.xml"})
    return entries


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: uv run python derive_tag_redirects.py COMMIT")
    print(yaml.dump(tag_redirects(sys.argv[1]), sort_keys=False), end="")
