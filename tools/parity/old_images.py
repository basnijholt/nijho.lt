"""Map Hugo 0.123.3 resized-image names to their source files."""

import hashlib
import os
import re
from collections import defaultdict
from pathlib import Path

from . import ParityError
from .site import Build

# Hugo 0.123.3 resized images: <stem>_hu<fast md5 of the source>_<source size in bytes>_<options>.<ext>
HU_RE = re.compile(r"_hu([0-9a-f]{32})_(\d+)_")
# Hugo 0.123.3 helpers.MD5FromReaderFast reads 8 chunks of 64 bytes, all but the first at offset 2048
_CHUNKS, _PEEK, _SEEK = 8, 64, 2048


def hugo_fast_md5(path: Path) -> str:
    """Return the md5 that Hugo 0.123.3 puts in the _hu<md5> names of images resized from this file.

    Go reads into one reused 64-byte buffer and hashes the whole buffer after every read, stopping after a
    short one. So stale bytes are hashed too: a file of 64 to 2048 bytes hashes its first 64 bytes twice,
    and an empty file hashes 64 zero bytes.
    """
    with open(path, "rb") as f:
        head = f.read(_PEEK)
        f.seek(_SEEK)
        tail = f.read(_PEEK)
    md5, buffer = hashlib.md5(), bytearray(_PEEK)
    for chunk in [head] + [tail] * (_CHUNKS - 1):
        buffer[: len(chunk)] = chunk
        md5.update(buffer)
        if len(chunk) < _PEEK:
            break
    return md5.hexdigest()


def _forbidden_words() -> list[str]:
    """Return the casefolded words of the commit hook's lists (one word<TAB>reason per line)."""
    config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "git"
    words = []
    for file in (config / "forbidden-words", config / "forbidden-words.private"):
        if file.exists():
            lines = (line.strip() for line in file.read_text(encoding="utf-8").splitlines())
            words += [line.split("\t")[0].casefold() for line in lines if line and not line.startswith("#")]
    return words


def map_old_images(base: Build, repo: Path, cand: Build) -> tuple[list[dict], list[str]]:
    """Map each _hu image the candidate lacks to its source in content/ or assets/, by fast md5 and size.

    Of identical sources, the one named as the old name before _hu wins, since the old-images check wants that name;
    else the first by path, content/ first. Returns the data/old_images.yaml entries and the old names skipped for
    holding a word from the commit hook's lists, which would block committing the output; the old-images check reports
    those images.
    """
    words = _forbidden_words()
    sources = defaultdict(list)
    for folder in ("content", "assets"):
        for file in sorted((repo / folder).rglob("*")):
            if file.is_file():
                sources[hugo_fast_md5(file), file.stat().st_size].append(file)

    names, skipped, missing = defaultdict(list), [], []
    for name in sorted({Path(path).name for path in base.files - cand.files}):
        if not (match := HU_RE.search(name)):
            continue
        size = int(match[2])
        found = sources.get((match[1], size))
        source = min(found, key=lambda file: file.stem != name[: match.start()]).name if found else None
        if any(word in name.casefold() for word in words):
            skipped.append(name)
        elif source is None:
            missing.append(name)
        else:
            names[source, size].append(name)
    if missing:
        raise ParityError(
            f"{len(missing)} old image(s) without a source in content/ or assets/ "
            f"(is --repo the repository root?): {', '.join(missing)}"
        )
    return [{"file": file, "size": size, "names": old} for (file, size), old in sorted(names.items())], skipped
