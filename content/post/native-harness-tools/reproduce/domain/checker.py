"""Hidden task check, run inside a throwaway container with no network.

Usage: python3 checker.py SPEC_JSON TASK_DIR
The task directory is mounted read-only; anything that must execute agent work
(unit tests, scripts) runs on a private copy. Prints one JSON line
{"pass": bool, "detail": str}.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _read(task: Path, name: str) -> str | None:
    p = task / name
    if p.is_symlink() or not p.is_file():
        return None
    return p.read_text(encoding="utf-8", errors="replace")


def _unchanged(task: Path, files: dict) -> str | None:
    for name, digest in files.items():
        p = task / name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            return f"{name} was modified or removed"
    return None


def _copy(task: Path) -> Path:
    work = Path(tempfile.mkdtemp()) / "work"
    shutil.copytree(task, work, symlinks=True)
    return work


def check(spec: dict, task: Path) -> tuple[bool, str]:
    c = spec["check"]
    kind = c["kind"]
    if kind != "unittest" and (msg := _unchanged(task, c.get("unchanged", {}))) is not None:
        return False, msg
    for pattern in c.get("absent_glob", []):
        if leftovers := sorted(str(p.relative_to(task)) for p in task.rglob(pattern)):
            return False, f"leftover files {leftovers[:3]}"
    if kind == "files_equal":
        present = sorted(p.name for p in task.glob(c["glob"]))
        if present != sorted(c["files"]):
            return False, f"files {present[:5]}... ({len(present)}) vs expected {len(c['files'])}"
        bad = [name for name, body in c["files"].items() if _read(task, name) != body]
        return not bad, f"content differs in {bad[:3]}" if bad else f"{len(present)} files identical"
    if kind == "tree_equal":
        root = task / c["dir"]
        present = {str(p.relative_to(root)): p for p in root.rglob("*") if p.is_file() and not p.is_symlink()}
        if sorted(present) != sorted(c["files"]):
            missing = sorted(set(c["files"]) - set(present))[:3]
            extra = sorted(set(present) - set(c["files"]))[:3]
            return False, f"missing {missing} extra {extra}"
        bad = [rel for rel, body in c["files"].items() if present[rel].read_text(encoding="utf-8") != body]
        return not bad, f"content differs in {bad[:3]}" if bad else f"{len(present)} files identical"
    if kind == "file_equals":
        got = _read(task, c["file"])
        if got is None:
            return False, f"{c['file']} missing"
        return got.strip() == c["expected"], f"{c['file']}={got.strip()[:80]!r} expected {c['expected']!r}"
    if kind == "exact_file":
        got = _read(task, c["file"])
        if got is None:
            return False, f"{c['file']} missing"
        if got == c["expected"]:
            return True, "identical"
        diff = [i for i, (x, y) in enumerate(zip(got.splitlines(), c["expected"].splitlines())) if x != y]
        return False, f"differs at lines {diff[:5]} (len {len(got)} vs {len(c['expected'])})"
    if kind == "lines_equal":
        got = _read(task, c["file"])
        if got is None:
            return False, f"{c['file']} missing"
        lines = [line.strip() for line in got.splitlines() if line.strip()]
        missing = sorted(set(c["expected"]) - set(lines))[:3]
        extra = sorted(set(lines) - set(c["expected"]))[:3]
        return lines == c["expected"], f"{len(lines)} lines vs {len(c['expected'])}; missing {missing} extra {extra}"
    if kind == "csv_equal":
        got = _read(task, c["file"])
        if got is None:
            return False, f"{c['file']} missing"
        rows = [[cell.strip() for cell in row] for row in csv.reader(got.splitlines()) if row]
        bad = [i for i, (x, y) in enumerate(zip(rows, c["expected_rows"])) if x != y][:3]
        return rows == c["expected_rows"], f"{len(rows)} rows vs {len(c['expected_rows'])}; first diffs {bad}"
    if kind == "unittest":
        if (msg := _unchanged(task, c.get("unchanged", {}))) is not None:
            return False, msg
        if (spec_name := c.get("no_identifier")) is not None:
            for path in (task / spec_name["dir"]).rglob("*.py"):
                names = {getattr(n, "id", None) or getattr(n, "name", None) or getattr(n, "attr", None)
                         for n in ast.walk(ast.parse(path.read_text(encoding="utf-8")))}
                names |= {a.name for n in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
                          if isinstance(n, ast.ImportFrom) for a in n.names}
                if spec_name["name"] in names:
                    return False, f"{spec_name['name']} still used in {path.relative_to(task)}"
        work = _copy(task)
        for name, body in c["hidden"].items():
            (work / name).write_text(body, encoding="utf-8")
        r = subprocess.run([sys.executable, "-m", "unittest", "-q", *[Path(n).stem for n in c["hidden"]]],
                           cwd=work, capture_output=True, text=True, timeout=90,
                           env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        return r.returncode == 0, (r.stderr or r.stdout)[-300:].strip()
    if kind == "script_output":
        script = task / c["script"]
        if not script.is_file() or not os.access(script, os.X_OK):
            return False, f"{c['script']} missing or not executable"
        work = _copy(task)
        for i, case in enumerate(c["cases"]):
            case_dir = work / f"case{i}"
            case_dir.mkdir()
            for name, body in case["files"].items():
                (case_dir / name).write_text(body, encoding="utf-8")
            r = subprocess.run([str(work / c["script"]), *case["args"]], cwd=case_dir, input=case["stdin"] or "",
                               capture_output=True, text=True, timeout=30)
            got = "\n".join(line.strip() for line in r.stdout.strip().splitlines())
            if got != case["expected"]:
                return False, f"case {i}: got {got[:80]!r} expected {case['expected']!r} (rc {r.returncode})"
        return True, f"{len(c['cases'])} cases"
    return False, f"unknown check kind {kind}"


if __name__ == "__main__":
    spec = json.loads(Path(sys.argv[1]).read_text())
    try:
        ok, detail = check(spec, Path(sys.argv[2]))
    except Exception as exc:  # noqa: BLE001 - any crash is a failed check
        ok, detail = False, f"checker error: {type(exc).__name__}: {exc}"[:300]
    print(json.dumps({"pass": bool(ok), "detail": detail}))
