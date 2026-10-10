"""Hugo 0.123.3's fast md5 and the mapping of old resized-image names to their sources."""

import re

import pytest

from helpers import bmp, write_build
from parity import ParityError
from parity.old_images import hugo_fast_md5, map_old_images

# Hugo 0.123.3 resize names for bmp() images, from a scratch site with {{ (resources.Get "<name>.bmp").Resize "2x" }}
HUGO_NAMES = {
    "tiny": ((1, 1), "tiny_huef01278f6fd4dab58bf0962a073f7ca6_58_2x0_resize_box.bmp"),
    "small": ((16, 16), "small_hu3e42b460547f9240314cce9a8a6e4c9d_822_2x0_resize_box.bmp"),
    "edge": ((8, 84), "edge_hu116d1d7274d7f07e9cb0fc3b1ab15b81_2070_2x0_resize_box.bmp"),
    "large": ((32, 32), "large_hu58135d141fa25fa5f4e7071595f164d1_3126_2x0_resize_box.bmp"),
}
SMALL = HUGO_NAMES["small"][1]


@pytest.mark.parametrize("name", HUGO_NAMES)
def test_hugo_fast_md5_matches_hugo_output_names(tmp_path, name):
    """Sizes under 64, 64 to 2048, 2049 to 2111, and 2112 bytes or more all hash like Hugo."""
    (width, height), hugo_name = HUGO_NAMES[name]
    _, digest, size = hugo_name.split("_")[:3]
    path = tmp_path / f"{name}.bmp"
    path.write_bytes(bmp(width, height))
    assert (hugo_fast_md5(path), path.stat().st_size) == (digest.removeprefix("hu"), int(size))


def test_hugo_fast_md5_of_empty_file(tmp_path):
    """Go's first read hits EOF, and Hugo still hashes the zeroed 64-byte buffer once."""
    empty = tmp_path / "empty"
    empty.write_bytes(b"")
    assert hugo_fast_md5(empty) == "3b5d3c7d207e37dceeedd301e35e2e58"  # md5 of 64 zero bytes


def sites(tmp_path, old_names, sources, kept=(), folder="/media"):
    """Return (base, repo, cand): base has <folder>/<old name> for each name, cand only the kept ones."""
    repo = tmp_path / "repo"
    for rel, data in sources.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_bytes(data)
    (repo / "content").mkdir(parents=True, exist_ok=True)
    base = write_build(tmp_path / "base", {f"{folder}/{name}": b"resized" for name in old_names})
    cand = write_build(tmp_path / "cand", {f"{folder}/{name}": b"resized" for name in kept})
    return base, repo, cand


@pytest.mark.parametrize(
    ("source", "folder"),
    [pytest.param("content/post/x", "/post/x", id="page-bundle"), pytest.param("assets/media", "/media", id="assets")],
)
def test_map_old_images_finds_source_by_md5_and_size(tmp_path, source, folder):
    second = SMALL.replace("_2x0_", "_4x0_")
    kept = SMALL.replace("_2x0_", "_8x0_")
    sources = {f"{source}/small.bmp": bmp(16, 16)}
    base, repo, cand = sites(tmp_path, [second, SMALL, kept], sources, kept=[kept], folder=folder)
    assert map_old_images(base, repo, cand) == ([{"file": "small.bmp", "size": 822, "names": [SMALL, second]}], [])


def test_map_old_images_without_source_is_an_error(tmp_path):
    """Same md5, other size: the old name carries the source's size, so this source is not it."""
    wrong_size = SMALL.replace("_822_", "_823_")
    base, repo, cand = sites(tmp_path, [wrong_size, "plain.png"], {"assets/media/small.bmp": bmp(16, 16)})
    message = f"1 old image(s) without a source in content/ or assets/ (is --repo the repository root?): {wrong_size}"
    with pytest.raises(ParityError, match=f"^{re.escape(message)}$"):
        map_old_images(base, repo, cand)


@pytest.mark.parametrize("file", ["forbidden-words", "forbidden-words.private"])
@pytest.mark.parametrize(
    "old_name",
    [
        pytest.param("secretco-logo" + SMALL.removeprefix("small"), id="in-old-name"),
        pytest.param(HUGO_NAMES["tiny"][1].removeprefix("tiny"), id="in-source-of-a-stemless-name"),
    ],
)
def test_map_old_images_skips_names_with_forbidden_words(tmp_path, monkeypatch, file, old_name):
    """Words match case-insensitively in the old name or its source's name; a skipped name is only in the skipped
    list."""
    config = tmp_path / "config" / "git"
    config.mkdir(parents=True)
    (config / file).write_text("# comment\n\nSecretCo\tA test word\n")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    sources = {"assets/media/small.bmp": bmp(16, 16), "assets/media/secretco-logo.bmp": bmp(1, 1)}
    base, repo, cand = sites(tmp_path, [old_name, SMALL], sources)
    assert map_old_images(base, repo, cand) == ([{"file": "small.bmp", "size": 822, "names": [SMALL]}], [old_name])


@pytest.mark.parametrize(
    ("make", "reason"),
    [
        pytest.param(lambda path: path.write_bytes(b"word\xff\tA reason\n"), "invalid UTF-8", id="not-utf8"),
        pytest.param(lambda path: path.mkdir(), "Is a directory", id="directory"),
    ],
)
def test_map_old_images_names_an_unreadable_word_list(tmp_path, monkeypatch, make, reason):
    config = tmp_path / "config" / "git"
    config.mkdir(parents=True)
    make(config / "forbidden-words")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    base, repo, cand = sites(tmp_path, [SMALL], {"assets/media/small.bmp": bmp(16, 16)})
    with pytest.raises(ParityError, match=f"^{re.escape(str(config / 'forbidden-words'))}: .*{reason}"):
        map_old_images(base, repo, cand)


def test_map_old_images_lists_a_name_once_when_two_folders_lose_it(tmp_path):
    repo = tmp_path / "repo"
    (repo / "assets").mkdir(parents=True)
    (repo / "assets" / "small.bmp").write_bytes(bmp(16, 16))
    base = write_build(tmp_path / "base", {f"/post/a/{SMALL}": b"", f"/project/a/{SMALL}": b""})
    cand = write_build(tmp_path / "cand", {})
    assert map_old_images(base, repo, cand) == ([{"file": "small.bmp", "size": 822, "names": [SMALL]}], [])


def test_map_old_images_gives_the_old_name_to_every_name_of_identical_sources(tmp_path):
    """The entries do not say where the old image was, so each name an identical source has gets it."""
    copies = ["content/a/large.bmp", "content/b/small.bmp", "content/c/small.bmp", "assets/x.bmp"]
    base, repo, cand = sites(tmp_path, [SMALL], dict.fromkeys(copies, bmp(16, 16)))
    assert map_old_images(base, repo, cand) == (
        [{"file": file, "size": 822, "names": [SMALL]} for file in ("large.bmp", "small.bmp", "x.bmp")], []
    )
