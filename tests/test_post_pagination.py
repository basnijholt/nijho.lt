import re
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
POST_COUNT = 101
EXPECTED_FIRST_PAGE_POSTS = 100


class PostPaginationTests(unittest.TestCase):
    def build_fixture_site(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        tmp_path = Path(tmp.name)
        content_dir = tmp_path / "content"

        self.write_post_index(content_dir / "post" / "_index.md")
        for post_number in range(POST_COUNT):
            self.write_post(
                content_dir / "post" / f"post-{post_number:03d}" / "index.md",
                post_number,
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

    def write_post_index(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("---\ntitle: Posts\n---\n", encoding="utf-8")

    def write_post(self, path: Path, post_number: int) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                [
                    "---",
                    f"title: Post {post_number:03d}",
                    f"date: 2025-01-{(post_number % 28) + 1:02d}T00:00:00Z",
                    "draft: false",
                    "---",
                    "",
                    f"Fixture post {post_number:03d}.",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def test_post_list_shows_100_posts_before_paginating(self) -> None:
        public_dir = self.build_fixture_site()

        first_page = (public_dir / "post" / "index.html").read_text(encoding="utf-8")
        stream_items = re.findall(r'class="?media stream-item view-compact"?', first_page)

        self.assertEqual(len(stream_items), EXPECTED_FIRST_PAGE_POSTS)
