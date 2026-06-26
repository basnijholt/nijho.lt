import html
import re
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class PostMetadataDateTests(unittest.TestCase):
    def build_fixture_site(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        tmp_path = Path(tmp.name)
        content_dir = tmp_path / "content"

        self.write_post(
            content_dir / "post" / "updated-post" / "index.md",
            """
            ---
            title: Updated post
            date: 2025-01-02T03:04:00Z
            lastmod: 2025-02-03T04:05:00Z
            draft: false
            ---

            This post has an original date and a later update date.
            """,
        )
        self.write_post(
            content_dir / "post" / "unchanged-post" / "index.md",
            """
            ---
            title: Unchanged post
            date: 2025-03-04T03:04:00Z
            draft: false
            ---

            This post only has its original date.
            """,
        )

        public_dir = tmp_path / "public"
        result = subprocess.run(
            [
                "devbox",
                "run",
                "hugo",
                "--contentDir",
                str(content_dir),
                "--destination",
                str(public_dir),
                "--buildFuture",
                "--quiet",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
        )
        return public_dir

    def write_post(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")

    def article_metadata_text(self, public_dir: Path, slug: str) -> str:
        page = public_dir / "post" / slug / "index.html"
        markup = page.read_text(encoding="utf-8")
        match = re.search(
            r'<div class="?article-metadata"?>(.*?)</div>',
            markup,
            re.S,
        )
        self.assertIsNotNone(match, f"article metadata not found in {page}")
        without_tags = re.sub(r"<[^>]+>", " ", match.group(1))
        return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()

    def test_updated_post_shows_original_and_updated_dates(self) -> None:
        public_dir = self.build_fixture_site()

        metadata = self.article_metadata_text(public_dir, "updated-post")

        self.assertIn("Published on 2025-01-02", metadata)
        self.assertIn("Last updated on 2025-02-03", metadata)

    def test_unchanged_post_keeps_single_date(self) -> None:
        public_dir = self.build_fixture_site()

        metadata = self.article_metadata_text(public_dir, "unchanged-post")

        self.assertIn("2025-03-04", metadata)
        self.assertNotIn("Published on", metadata)
        self.assertNotIn("Last updated on", metadata)
