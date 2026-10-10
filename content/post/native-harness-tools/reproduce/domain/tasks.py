"""Deterministic terminal tasks for the MindRoom shell instance.

Twelve families of small, realistic shell jobs (data wrangling, log forensics,
bug fixing, git archaeology, refactoring, scripting, archives, config edits,
long command output). Every task gets a fresh directory of input files and a
hidden check that the grader runs in a throwaway container after the agent
finishes. The evolve and held-out splits draw different instances of the same
families. `python3 tasks.py` (re)builds data/ from scratch.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os
import random
import shutil
import string
import subprocess
import tarfile
import textwrap
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
N_EVOLVE, N_HELDOUT = 5, 1

REGIONS = ["north", "south", "east", "west", "central"]
PRODUCTS = ["anvil", "bolt", "cable", "drill", "easel", "funnel", "gasket", "hinge"]
NAMES = ["Ada", "Bram", "Cleo", "Dev", "Esme", "Fynn", "Gia", "Hugo", "Ines", "Joss", "Kai", "Lior",
         "Mira", "Nils", "Oona", "Pip", "Quill", "Rafe", "Sami", "Tova"]
WORDS = ["river", "stone", "cloud", "ember", "maple", "orbit", "pixel", "quartz", "sable", "tidal",
         "umber", "vivid", "willow", "zephyr", "harbor", "lantern", "meadow", "nectar"]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ------------------------------------------------------------------ families --
def csv_report(r: random.Random, d: Path) -> dict:
    rows, revenue = [], {}
    for _ in range(r.randint(180, 260)):
        region = r.choice(REGIONS)
        shown = r.choice([region, region.upper(), region.title(), f" {region}", f"{region.title()} "])
        units, cents = r.randint(1, 40), r.randint(150, 250_000)
        price = f"{cents // 100}.{cents % 100:02d}"
        if r.random() < 0.3:
            price = f"${cents // 100:,}.{cents % 100:02d}"
        status = r.choices(["completed", "refunded", "pending"], [80, 12, 8])[0]
        units_text = "" if r.random() < 0.04 else str(units)
        rows.append([f"2026-03-{r.randint(1, 28):02d}", shown, r.choice(PRODUCTS), units_text, price, status])
        if status == "completed" and units_text:
            revenue[region] = revenue.get(region, 0) + units * cents
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(["date", "region", "product", "units", "unit_price", "status"])
    w.writerows(rows)
    (d / "sales.csv").write_bytes(b"\xef\xbb\xbf" + buf.getvalue().encode())
    ordered = sorted(revenue.items(), key=lambda kv: (-kv[1], kv[0]))
    expected = [["region", "revenue"]] + [[k, f"{v // 100}.{v % 100:02d}"] for k, v in ordered]
    task = ("sales.csv is an export of sales. Write report.csv with the header `region,revenue` and one row per "
            "region giving its total revenue (units times unit_price, summed over completed sales only; skip rows "
            "with no units) with exactly two decimals and no thousands separators, sorted by revenue from highest "
            "to lowest. Region names are case-insensitive and may carry stray spaces; report them in lowercase.")
    return {"task": task, "check": {"kind": "csv_equal", "file": "report.csv", "expected_rows": expected}}


def log_errors(r: random.Random, d: Path) -> dict:
    proxies = [f"10.{r.randint(0, 9)}.{r.randint(0, 255)}.{r.randint(1, 254)}" for _ in range(6)]
    clients = [f"{r.randint(11, 220)}.{r.randint(0, 255)}.{r.randint(0, 255)}.{r.randint(1, 254)}" for _ in range(70)]
    lines, hits = [], set()
    for _ in range(r.randint(1600, 2200)):
        utc = datetime(2026, 3, 12, r.randint(7, 13), r.randint(0, 59), r.randint(0, 59), tzinfo=timezone.utc)
        local = utc.astimezone(timezone(timedelta(hours=r.choice([0, 0, 1, 2, -5, -8]))))
        status = r.choices([200, 201, 301, 404, 500, 502, 503], [50, 5, 5, 10, 3, 2, 2])[0]
        client = r.choice(clients)
        proxied = r.random() < 0.4
        remote, xff = (r.choice(proxies), f'"{client}, {r.choice(proxies)}"') if proxied else (client, '"-"')
        path = r.choice(["/", "/api/items", "/login", "/static/app.js", "/api/orders"])
        lines.append((utc, f'{remote} - - [{local.strftime("%d/%b/%Y:%H:%M:%S %z")}] "GET {path} HTTP/1.1" '
                           f'{status} {r.randint(100, 9000)} {xff}'))
        if 500 <= status < 600 and utc.hour == 10:
            hits.add(client)
    lines.sort()
    text = [line for _, line in lines]
    for _ in range(12):
        text.insert(r.randrange(len(text)), r.choice(["-", "garbage line", '10.0.0.1 - - [bad] "GET /" 500']))
    _write(d / "access.log", "\n".join(text) + "\n")
    task = ("access.log is a web server log in Common Log Format with one extra final field: the quoted "
            "X-Forwarded-For value, or \"-\" when absent. Timestamps carry their own UTC offsets. For requests "
            "that came through the proxy, the first address in X-Forwarded-For is the real client; otherwise the "
            "client is the remote address at the start of the line. Ignore malformed lines. How many distinct "
            "clients received at least one 5xx response between 10:00:00 and 10:59:59 UTC (inclusive)? Write just "
            "that number to answer.txt.")
    return {"task": task, "check": {"kind": "file_equals", "file": "answer.txt", "expected": str(len(hits))}}


_TEXTKIT = """\"\"\"Small text helpers.\"\"\"


def chunk(items, size):
    \"\"\"Split items into consecutive lists of at most `size` elements.\"\"\"
    return [items[i:i + size] for i in range(0, len(items) - 1, size)]


def slugify(title):
    \"\"\"Lowercase words joined by single hyphens; other characters are dropped.\"\"\"
    words = "".join(c if c.isalnum() or c.isspace() else " " for c in title).split(" ")
    return "-".join(words)
"""

_DURATIONS = """\"\"\"Duration parsing.\"\"\"

import re

_UNITS = {"h": 3600, "m": 600, "s": 1}


def parse_duration(text):
    \"\"\"'1h30m15s' -> seconds; each unit is optional but they appear in h, m, s order.\"\"\"
    total = 0
    for value, unit in re.findall(r"(\\d+)([hms])", text.strip().lower()):
        total += int(value) * _UNITS[unit]
    return total
"""


def fix_tests(r: random.Random, d: Path) -> dict:
    n = r.choice([5, 7, 9])  # odd, so the visible test exposes the chunk bug
    title = f"  {r.choice(WORDS).title()}, {r.choice(WORDS)}!  {r.choice(WORDS).upper()}  "
    expected_slug = "-".join("".join(c if c.isalnum() or c.isspace() else " " for c in title).lower().split())
    h, m = r.randint(1, 5), r.randint(1, 59)
    _write(d / "textkit" / "__init__.py", "")
    _write(d / "textkit" / "core.py", _TEXTKIT)
    _write(d / "textkit" / "durations.py", _DURATIONS)
    visible = textwrap.dedent(f"""\
        import unittest

        from textkit.core import chunk, slugify
        from textkit.durations import parse_duration


        class TextkitTest(unittest.TestCase):
            def test_chunk_keeps_every_item(self):
                self.assertEqual(chunk(list(range({n})), 2)[-1], {list(range(n))[-1:]!r})

            def test_slugify(self):
                self.assertEqual(slugify({title!r}), {expected_slug!r})

            def test_parse_duration(self):
                self.assertEqual(parse_duration("{h}h{m}m"), {h * 3600 + m * 60})


        if __name__ == "__main__":
            unittest.main()
        """)
    _write(d / "tests" / "test_textkit.py", visible)
    _write(d / "tests" / "__init__.py", "")
    k = r.randint(3, 7)
    hidden = textwrap.dedent(f"""\
        import unittest

        from textkit.core import chunk, slugify
        from textkit.durations import parse_duration


        class HiddenTest(unittest.TestCase):
            def test_chunk(self):
                self.assertEqual(chunk(list(range({k * 3 + 1})), {k}), [list(range({k * 3 + 1}))[i:i + {k}] for i in range(0, {k * 3 + 1}, {k})])
                self.assertEqual(chunk([], 3), [])
                self.assertEqual(chunk([1], 3), [[1]])

            def test_slugify(self):
                self.assertEqual(slugify("Hello,   World"), "hello-world")
                self.assertEqual(slugify("  A--B  c "), "a-b-c")
                self.assertEqual(slugify({title!r}), {expected_slug!r})

            def test_parse_duration(self):
                self.assertEqual(parse_duration("2h"), 7200)
                self.assertEqual(parse_duration("45m"), 2700)
                self.assertEqual(parse_duration("1h1m1s"), 3661)
                self.assertEqual(parse_duration(" 90S "), 90)
        """)
    task = ("This directory holds a small Python package `textkit` with a unittest suite in tests/. The tests "
            "fail. Fix the bugs in textkit so that `python3 -m unittest discover -s tests -t .` passes. Do not "
            "change the tests.")
    return {"task": task, "check": {"kind": "unittest", "hidden": {"test_hidden.py": hidden},
                                    "unchanged": {"tests/test_textkit.py": hashlib.sha256(visible.encode()).hexdigest()}}}


def _git(d: Path, *args: str, date: str) -> str:
    env = {**os.environ, "GIT_AUTHOR_NAME": "Dev", "GIT_AUTHOR_EMAIL": "dev@example.com",
           "GIT_COMMITTER_NAME": "Dev", "GIT_COMMITTER_EMAIL": "dev@example.com",
           "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date, "GIT_CONFIG_GLOBAL": "/dev/null",
           "GIT_CONFIG_SYSTEM": "/dev/null"}
    out = subprocess.run(["git", "-c", "commit.gpgsign=false", "-c", "init.defaultBranch=main", *args],
                         cwd=d, env=env, capture_output=True, text=True, check=True)
    return out.stdout.strip()


_PRICING_GOOD = """def total(items, discount=0.0):
    \"\"\"Sum price * quantity over items, then apply a fractional discount.\"\"\"
    subtotal = sum(price * qty for price, qty in items)
    return round(subtotal * (1 - discount), 2)
"""

_PRICING_BAD = """def total(items, discount=0.0):
    \"\"\"Sum price * quantity over items, then apply a fractional discount.\"\"\"
    lines = [price * qty * (1 - discount) for price, qty in items]
    return round(sum(lines) * (1 - discount), 2)
"""


def git_archaeology(r: random.Random, d: Path) -> dict:
    repo = d / "shop"
    repo.mkdir()
    _git(repo, "init", "-q", date="2025-01-01T09:00:00+00:00")
    n = r.randint(32, 44)
    bad_at = r.randint(10, n - 8)
    items = [(round(r.randint(100, 5000) / 100, 2), r.randint(1, 6)) for _ in range(3)]
    discount = r.choice([0.1, 0.15, 0.2, 0.25])
    expected_total = round(sum(p * q for p, q in items) * (1 - discount), 2)
    _write(repo / "check.py", f"from pricing import total\n\nresult = total({items!r}, discount={discount})\n"
                              f"assert result == {expected_total!r}, result\nprint('ok', result)\n")
    expected = None
    for i in range(n):
        body = _PRICING_BAD if i >= bad_at else _PRICING_GOOD
        _write(repo / "pricing.py", f"# pricing helpers (rev {i % 7})\n" + body)
        _write(repo / "utils.py", f"VERSION = '1.{i}'\n\n\ndef banner():\n    return 'shop ' + VERSION\n")
        _write(repo / "CHANGELOG.md", "".join(f"- release 1.{j}\n" for j in range(i + 1)))
        date = f"2025-02-{i // 2 + 1:02d}T{10 + i % 2}:{i:02d}:00+00:00"
        _git(repo, "add", "-A", date=date)
        _git(repo, "commit", "-q", "-m", r.choice(["Refactor helpers", "Update changelog", "Tidy code",
                                                  "Bump version", "Small cleanups"]), date=date)
        if i == bad_at:
            expected = _git(repo, "rev-parse", "HEAD", date=date)
    task = ("shop/ is a git repository. Running `python3 check.py` inside it passed at the first commit but "
            "fails at the latest commit. Find the first commit at which it fails and write that commit's full "
            "40-character hash to answer.txt (outside the repository, in this task directory).")
    return {"task": task, "check": {"kind": "file_equals", "file": "answer.txt", "expected": expected}}


def rename_api(r: random.Random, d: Path) -> dict:
    old, new = r.choice([("fetch_rows", "load_rows"), ("get_items", "list_items"), ("calc_total", "sum_total")])
    pkg = d / "store"
    _write(pkg / "__init__.py", f"from store.db import {old}, {old}_cached\n")
    _write(pkg / "db.py", f'LOG_PREFIX = "{old}:"\n\n\ndef {old}(table):\n    """Return the rows of a table."""\n'
                          f'    return [{{"table": table, "n": i}} for i in range(3)]\n\n\n'
                          f'def {old}_cached(table):\n    """Cached variant; a different function."""\n'
                          f'    return {old}(table)\n')
    names = r.sample(["report", "export", "audit", "sync"], 3)
    _write(pkg / f"{names[0]}.py", f"from store.db import {old}\n\n\ndef {names[0]}_0():\n"
                                    f'    return len({old}("t0"))\n')
    _write(pkg / f"{names[1]}.py", f"from store import db\n\n\ndef {names[1]}_1():\n"
                                    f'    return len(db.{old}("t1"))\n')
    _write(pkg / f"{names[2]}.py", f"from store.db import {old}_cached\n\n\ndef {names[2]}_2():\n"
                                    f'    return len({old}_cached("t2"))\n')
    notes = f"The helper `{old}` is used by every module; `{old}_cached` wraps it.\n"
    _write(d / "NOTES.md", notes)
    hidden = textwrap.dedent(f"""\
        import importlib
        import pkgutil
        import unittest

        import store
        from store import db
        from store.db import {new}, {old}_cached


        class RenameTest(unittest.TestCase):
            def test_rename(self):
                self.assertEqual(len({new}("x")), 3)
                self.assertEqual(len({old}_cached("x")), 3)
                self.assertFalse(hasattr(db, "{old}"))
                self.assertEqual(db.LOG_PREFIX, "{old}:")
                for mod in pkgutil.iter_modules(store.__path__):
                    module = importlib.import_module("store." + mod.name)
                    for attr in dir(module):
                        if attr.endswith(("_0", "_1", "_2")):
                            self.assertEqual(getattr(module, attr)(), 3)
        """)
    task = (f"Rename the Python function `{old}` in the `store` package to `{new}`, updating its definition and "
            f"every import, attribute access and call so the package keeps working. Only that function: "
            f"`{old}_cached` is a different function and keeps its name. Do not change string literals or "
            f"NOTES.md.")
    return {"task": task, "check": {"kind": "unittest", "hidden": {"test_hidden.py": hidden},
                                    "no_identifier": {"dir": "store", "name": old},
                                    "unchanged": {"NOTES.md": hashlib.sha256(notes.encode()).hexdigest()}}}


def json_extract(r: random.Random, d: Path) -> dict:
    users, expected = [], set()
    for i in range(r.randint(50, 80)):
        name = f"{r.choice(NAMES)}{i % 37}"
        addresses = [f"{name}.{j}@{r.choice(['Example.com', 'mail.TEST', 'corp.io'])}" for j in range(r.randint(1, 3))]
        primary = r.randrange(len(addresses))
        active_raw = r.choice([True, False, "yes", "no", "true", "false", True])
        plan_raw = r.choice(["pro", "Pro ", " PRO", "free", "team", None, "missing", "pro"])
        user = {"id": i, "name": name, "active": active_raw}
        if plan_raw != "missing":
            user["plan"] = plan_raw
        if len(addresses) == 1 and r.random() < 0.5:
            user["email"] = addresses[0]
        else:
            user["emails"] = [{"address": a, "primary": j == primary} for j, a in enumerate(addresses)]
        users.append(user)
        active = active_raw is True or active_raw in ("yes", "true")
        if active and isinstance(plan_raw, str) and plan_raw.strip().lower() == "pro":
            expected.add(addresses[primary if "emails" in user else 0].lower())
    _write(d / "users.json", json.dumps({"users": users}, indent=2))
    task = ("users.json lists user records exported from two systems, so formats vary: `active` is a boolean or "
            "a yes/no/true/false string, `plan` may have stray case or spaces or be missing or null, and a user "
            "has either one `email` string or an `emails` list in which exactly one entry is marked primary. "
            "Write emails.txt with the primary email of every active user on the pro plan, lowercased, without "
            "duplicates, sorted alphabetically, one per line.")
    return {"task": task, "check": {"kind": "lines_equal", "file": "emails.txt", "expected": sorted(expected)}}


def find_files(r: random.Random, d: Path) -> dict:
    expected, made = [], []
    for i in range(r.randint(50, 75)):
        folder = Path(*r.sample(["app", "logs", "old", "tmp", "srv", ".cache"], r.randint(1, 3)))
        base = r.choice([f"file{i}", f"web server {i}", f"job-{i}"])
        ext = r.choice([".log", ".log", ".LOG", ".log.gz", ".txt", ".json"])
        size = r.choice([r.randint(100, 5000), r.randint(20_000, 90_000), 20480, 20481])
        rel = folder / f"{base}{ext}"
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_bytes(b"x" * size)
        made.append(rel)
        if ext == ".log" and size > 20480:
            expected.append(str(rel))
    for j, target in enumerate(r.sample([m for m in made if m.suffix == ".log"], 2) if sum(
            m.suffix == ".log" for m in made) >= 2 else []):
        link = d / "links" / f"alias{j}.log"
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(Path("..") / target)
    task = ("Write big_logs.txt listing every regular file (not symlinks) whose name ends in `.log` (lowercase, "
            "exactly) anywhere under this directory, including hidden directories, that is larger than 20480 "
            "bytes. Give paths relative to this directory, sorted alphabetically, one per line. Do not list "
            "big_logs.txt itself.")
    return {"task": task, "check": {"kind": "lines_equal", "file": "big_logs.txt", "expected": sorted(expected)}}


def nested_archive(r: random.Random, d: Path) -> dict:
    code = "".join(r.choices(string.ascii_uppercase + string.digits, k=12))
    inner = io.BytesIO()
    with tarfile.open(fileobj=inner, mode="w:xz") as t:
        blob = gzip.compress(f"{code}\n".encode(), mtime=0)
        info = tarfile.TarInfo("deep/code.txt.gz")
        info.size, info.mtime = len(blob), 0
        t.addfile(info, io.BytesIO(blob))
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w") as z:
        for i in range(r.randint(3, 6)):
            z.writestr(f"docs/readme{i}.txt", f"nothing here {i}\n")
        z.writestr("notes/code.md", f"The code is not {''.join(r.choices(string.ascii_uppercase, k=12))}.\n")
        z.writestr("layers/layer2.tar.xz", inner.getvalue())
    with tarfile.open(d / "data.tar.gz", "w:gz") as t:
        for name, payload in (("bundle/payload.zip", zbuf.getvalue()),
                              ("bundle/code.txt.bak", f"decoy {r.randint(1, 999)}\n".encode())):
            info = tarfile.TarInfo(name)
            info.size, info.mtime = len(payload), 0
            t.addfile(info, io.BytesIO(payload))
    task = ("data.tar.gz contains archives nested inside each other. The innermost archive holds a compressed "
            "file named code.txt.gz with a 12-character code. Write just the code to answer.txt. Other files that "
            "mention a code are decoys.")
    return {"task": task, "check": {"kind": "file_equals", "file": "answer.txt", "expected": code}}


def _top3(texts: list[str]) -> str:
    counts: dict[str, int] = {}
    for text in texts:
        for w in "".join(c.lower() if c.isalpha() else " " for c in text).split():
            counts[w] = counts.get(w, 0) + 1
    return "\n".join(f"{w} {n}" for w, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:3])


def write_script(r: random.Random, d: Path) -> dict:
    def text() -> str:
        words = [r.choice(WORDS[:8]) for _ in range(r.randint(30, 60))]
        out = " ".join(w.upper() if r.random() < 0.2 else w for w in words)
        return out.replace(" ", r.choice([" ", ", ", ". ", "\n", "'s "]), 6)
    a, b, c = text(), text(), text()
    cases = [{"files": {"one.txt": a}, "args": ["one.txt"], "stdin": None, "expected": _top3([a])},
             {"files": {"one.txt": a, "two.txt": b}, "args": ["one.txt", "two.txt"], "stdin": None,
              "expected": _top3([a, b])},
             {"files": {}, "args": [], "stdin": c, "expected": _top3([c])}]
    _write(d / "sample.txt", a)
    task = ("Create an executable shell script `wordfreq.sh` in this directory. `./wordfreq.sh [FILE...]` must "
            "count words across all given files, or read standard input when no file is given, and print the "
            "three most frequent words, one per line as `word count`, most frequent first and ties broken "
            "alphabetically. Words are maximal runs of letters (anything else separates words), compared "
            "case-insensitively and printed in lowercase. sample.txt is an example input.")
    return {"task": task, "check": {"kind": "script_output", "script": "wordfreq.sh", "cases": cases}}


def config_edit(r: random.Random, d: Path) -> dict:
    client, old_server, tls = r.randint(5000, 7000), r.randint(2000, 4000), r.randint(4400, 4499)
    new = r.randint(8000, 9999)
    tpl = ("# deployment settings\n[client]\nhost = 0.0.0.0\nport = {client}\n\n[server]\nhost = 127.0.0.1\n"
           "# port = 1111   (old default)\nport = {server}   ; listen port\nworkers = {w}\n\n[server.tls]\n"
           "port = {tls}\n\n[metrics]\nport = {m}\n")
    w, m = r.randint(2, 16), r.randint(9100, 9200)
    _write(d / "settings.ini", tpl.format(client=client, server=old_server, tls=tls, w=w, m=m))
    expected = tpl.format(client=client, server=new, tls=tls, w=w, m=m)
    task = (f"In settings.ini, change the active port of the [server] section to {new}. Every other byte of the "
            f"file, including comments, spacing and the other sections, must stay exactly the same.")
    return {"task": task, "check": {"kind": "exact_file", "file": "settings.ini", "expected": expected}}


def long_output(r: random.Random, d: Path) -> dict:
    seed = r.randint(1, 10**6)
    suffix = r.choice("0123456789abcdef")
    script = textwrap.dedent(f"""\
        import random

        rng = random.Random({seed})
        for i in range(80000):
            print(f"line {{i}}: ok checksum={{rng.getrandbits(32):08x}} status={{rng.choice(['WARN', 'INFO', 'DEBUG'])}}")
        """)
    _write(d / "scan.py", script)
    rng, count = random.Random(seed), 0
    for _ in range(80000):
        checksum, status = f"{rng.getrandbits(32):08x}", rng.choice(["WARN", "INFO", "DEBUG"])
        count += status == "WARN" and checksum.endswith(suffix)
    task = (f"Run `python3 scan.py`. It prints a very large amount of output. How many printed lines have "
            f"status=WARN and a checksum ending in `{suffix}`? Write just that count to answer.txt.")
    return {"task": task, "check": {"kind": "file_equals", "file": "answer.txt", "expected": str(count)}}


def dedupe_merge(r: random.Random, d: Path) -> dict:
    ids = r.sample(range(1, 400), r.randint(40, 60))
    a_ids = set(r.sample(ids, len(ids) * 2 // 3))
    b_ids = set(ids) - a_ids | set(r.sample(sorted(a_ids), len(a_ids) // 3))

    def row(i: int, src: str) -> tuple[list[str], list[str]]:
        name = f"{r.choice(NAMES)} {r.choice(WORDS).title()}"
        email = f"{name.split()[0]}.{i}@{src}.Example"
        shown_id = f"{i:03d}" if src == "a" and r.random() < 0.5 else str(i)
        pad = r.choice(["", " ", "  "])
        return [f"{pad}{shown_id}", f"{name}{pad}", f"{pad}{email}"], [str(i), name, email.lower()]

    a = {i: row(i, "a") for i in sorted(a_ids)}
    b = {i: row(i, "b") for i in sorted(b_ids)}
    for name, rows, eol, bom in (("customers_a.csv", a, "\n", b""), ("customers_b.csv", b, "\r\n", b"\xef\xbb\xbf")):
        order = [shown for shown, _ in rows.values()]
        r.shuffle(order)
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator=eol)
        w.writerow(["id", "name", "email"])
        w.writerows(order)
        (d / name).write_bytes(bom + buf.getvalue().encode())
    merged = {**{i: clean for i, (_, clean) in a.items()}, **{i: clean for i, (_, clean) in b.items()}}
    expected = [["id", "name", "email"]] + [merged[i] for i in sorted(merged)]
    task = ("customers_a.csv and customers_b.csv list customers by id; some ids appear in both, and the files "
            "differ in formatting (zero-padded ids, stray spaces, line endings, a byte-order mark). Write "
            "merged.csv with the header `id,name,email` containing each customer exactly once: ids as plain "
            "integers, every field trimmed, emails lowercased. When an id is in both files, use the row from "
            "customers_b.csv. Sort rows by id numerically.")
    return {"task": task, "check": {"kind": "csv_equal", "file": "merged.csv", "expected_rows": expected}}


FAMILIES = {"csv_report": csv_report, "log_errors": log_errors, "fix_tests": fix_tests,
            "git_archaeology": git_archaeology, "rename_api": rename_api, "json_extract": json_extract,
            "find_files": find_files, "nested_archive": nested_archive, "write_script": write_script,
            "config_edit": config_edit, "long_output": long_output, "dedupe_merge": dedupe_merge}


# ------------------------------------------------- out-of-distribution families --
# Different kinds of jobs that never enter the evolve split; they test whether evolved
# working habits transfer beyond the families the harness was searched on.
def sqlite_query(r: random.Random, d: Path) -> dict:
    import sqlite3
    countries = r.sample(["NL", "DE", "FR", "US", "JP", "BR", "KE", "IN"], 5)
    db = sqlite3.connect(d / "shop.db")
    db.execute("create table customers (id integer primary key, name text, country text)")
    db.execute("create table orders (id integer primary key, customer_id integer, amount_cents integer, "
               "status text, created text)")
    totals: dict[str, int] = {}
    for cid in range(1, r.randint(40, 70)):
        country = r.choice(countries)
        db.execute("insert into customers values (?, ?, ?)", (cid, f"{r.choice(NAMES)} {cid}", country))
        for _ in range(r.randint(0, 6)):
            amount, status = r.randint(500, 90_000), r.choice(["paid", "paid", "refunded", "pending"])
            created = f"{r.choice([2024, 2025, 2025, 2026])}-{r.randint(1, 12):02d}-{r.randint(1, 28):02d}"
            db.execute("insert into orders (customer_id, amount_cents, status, created) values (?, ?, ?, ?)",
                       (cid, amount, status, created))
            if status == "paid" and created.startswith("2025"):
                totals[country] = totals.get(country, 0) + amount
    db.commit()
    db.close()
    best = max(sorted(totals), key=lambda c: totals[c])
    task = ("shop.db is a SQLite database of customers and orders (amounts in cents). Which customer country had "
            "the highest total amount of paid orders created in 2025? Write `COUNTRY,TOTAL` to answer.txt, with "
            "TOTAL in whole currency units and exactly two decimals (for example `NL,1234.50`).")
    return {"task": task, "check": {"kind": "file_equals", "file": "answer.txt",
                                    "expected": f"{best},{totals[best] // 100}.{totals[best] % 100:02d}"}}


def dependency_order(r: random.Random, d: Path) -> dict:
    import heapq
    names = r.sample([f"{w}-{x}" for w in WORDS for x in ("build", "test", "lint", "pack")], r.randint(14, 22))
    deps = {n: sorted(r.sample(names[:i], min(i, r.randint(0, 3)))) for i, n in enumerate(names)}
    shuffled = dict(r.sample(sorted(deps.items()), len(deps)))
    _write(d / "tasks.json", json.dumps(shuffled, indent=2))
    indeg = {n: len(v) for n, v in deps.items()}
    users: dict[str, list[str]] = {n: [] for n in deps}
    for n, v in deps.items():
        for p in v:
            users[p].append(n)
    heap = [n for n, k in indeg.items() if k == 0]
    heapq.heapify(heap)
    order = []
    while heap:
        n = heapq.heappop(heap)
        order.append(n)
        for u in users[n]:
            indeg[u] -= 1
            if indeg[u] == 0:
                heapq.heappush(heap, u)
    task = ("tasks.json maps each task name to the list of tasks it depends on. Write order.txt with every task "
            "name, one per line, in an order where each task comes after all of its dependencies; whenever several "
            "tasks are ready at the same time, take the alphabetically smallest first.")
    return {"task": task, "check": {"kind": "lines_equal", "file": "order.txt", "expected": order}}


def regex_extract(r: random.Random, d: Path) -> dict:
    good, chunks = set(), []
    for _ in range(r.randint(60, 90)):
        kind = r.random()
        if kind < 0.45:
            ip = ".".join(str(r.randint(0, 255)) for _ in range(4))
            good.add(ip)
            token = ip
        elif kind < 0.6:
            token = ".".join(str(r.randint(0, 255)) for _ in range(3)) + f".{r.randint(256, 999)}"
        elif kind < 0.7:
            token = ".".join(str(r.randint(1, 255)) for _ in range(3)) + f".0{r.randint(1, 9)}"
        elif kind < 0.8:
            token = ".".join(str(r.randint(0, 255)) for _ in range(3))
        elif kind < 0.9:
            token = ".".join(str(r.randint(0, 255)) for _ in range(5))
        else:
            token = f"v{r.randint(1, 9)}.{r.randint(0, 9)}.{r.randint(0, 9)}"
        chunks.append(r.choice(["host {} up", "from {} at noon", "[{}]", "addr={};", "({}),", "{}"]).format(token))
    _write(d / "notes.txt", "\n".join(" ".join(chunks[i:i + 4]) for i in range(0, len(chunks), 4)) + "\n")
    expected = sorted(good, key=lambda ip: tuple(int(x) for x in ip.split(".")))
    task = ("notes.txt is free text that mentions network addresses. Write ips.txt listing every valid IPv4 "
            "address that appears as a standalone token (not part of a longer dotted sequence): exactly four "
            "decimal octets, each 0-255, with no leading zeros (a lone `0` is fine). List each address once, "
            "sorted numerically, one per line.")
    return {"task": task, "check": {"kind": "lines_equal", "file": "ips.txt", "expected": expected}}


def split_file(r: random.Random, d: Path) -> dict:
    size = r.choice([200, 250, 300])
    rows = [f"{i},{r.choice(NAMES)},{r.randint(1, 999)}" for i in range(1, r.randint(1100, 1700))]
    header = "id,name,score"
    _write(d / "data.csv", "\n".join([header, *rows]) + "\n")
    files = {f"part_{n + 1:03d}.csv": "\n".join([header, *rows[i:i + size]]) + "\n"
             for n, i in enumerate(range(0, len(rows), size))}
    task = (f"Split data.csv into files of at most {size} data rows each, named part_001.csv, part_002.csv, and "
            f"so on, in the original row order. Every part starts with the same header line as data.csv. Leave "
            f"data.csv unchanged.")
    return {"task": task, "check": {"kind": "files_equal", "files": files, "glob": "part_*.csv",
                                    "unchanged": {"data.csv": hashlib.sha256(
                                        ("\n".join([header, *rows]) + "\n").encode()).hexdigest()}}}


def markdown_table(r: random.Random, d: Path) -> dict:
    rows = []
    for i in range(r.randint(8, 14)):
        rows.append([f"SKU-{r.randint(100, 999)}{i}", f"{r.choice(WORDS).title()} {r.choice(PRODUCTS)}",
                     str(r.randint(0, 500)), f"{r.randint(100, 99_999) / 100:.2f}"])
    with open(d / "inventory.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sku", "name", "qty", "price"])
        w.writerows(rows)
    lines = ["| sku | name | qty | price |", "| --- | --- | ---: | ---: |"]
    lines += [f"| {' | '.join(row)} |" for row in sorted(rows)]
    task = ("Convert inventory.csv into a Markdown table in table.md: a header row `| sku | name | qty | price |`, "
            "then a separator row that left-aligns the text columns with `---` and right-aligns the numeric "
            "columns (qty, price) with `---:`, then one row per item sorted by sku, with cells separated by ` | ` "
            "and each line starting with `| ` and ending with ` |`. Copy values exactly as they appear in the CSV.")
    return {"task": task, "check": {"kind": "exact_file", "file": "table.md", "expected": "\n".join(lines) + "\n"}}


def env_debug(r: random.Random, d: Path) -> dict:
    n = r.randint(20, 60)
    values = [r.randint(1, 100) for _ in range(n)]
    _write(d / "inputs" / "values.txt", "\n".join(map(str, values)) + "\n")
    factor = r.randint(2, 9)
    app = textwrap.dedent("""\
        import os
        from pathlib import Path

        data_dir = Path(os.environ["DATA_DIR"])
        factor = int(os.environ["SCALE_FACTOR"])
        mode = os.environ["REPORT_MODE"]
        values = [int(line) for line in (data_dir / "values.txt").read_text().split()]
        total = sum(v * factor for v in values)
        Path("result.txt").write_text(f"{mode}:{total}\\n")
        """)
    run = "#!/usr/bin/env bash\nset -euo pipefail\ncd \"$(dirname \"$0\")\"\nsource ./settings.env\npython3 app.py\n"
    _write(d / "app.py", app)
    _write(d / "run.sh", run)
    (d / "run.sh").chmod(0o755)
    (d / "settings.env").write_bytes(f"export DATA_DIR=./input\r\nSCALE_FACTOR={factor}\nexport REPORT_MODE=summary\n"
                                     .encode())
    task = ("`./run.sh` should write result.txt but it fails. Fix settings.env so that `./run.sh` succeeds and "
            "writes result.txt; do not edit run.sh or app.py. Run it to produce result.txt.")
    digest = lambda text: hashlib.sha256(text.encode()).hexdigest()  # noqa: E731
    return {"task": task, "check": {"kind": "file_equals", "file": "result.txt",
                                    "expected": f"summary:{sum(v * factor for v in values)}",
                                    "unchanged": {"app.py": digest(app), "run.sh": digest(run)}}}


def diff_apply(r: random.Random, d: Path) -> dict:
    lines = [f"    step_{i} = compute({i}, {r.randint(1, 99)})" for i in range(30)]
    before = "def pipeline():\n" + "\n".join(lines) + "\n    return step_29\n"
    target = r.randint(4, 12)
    second = r.randint(18, 26)
    after_lines = list(lines)
    after_lines[target] = after_lines[target].replace("compute(", "compute_fast(")
    after_lines[second] = after_lines[second] + "  # checked"
    after = "def pipeline():\n" + "\n".join(after_lines) + "\n    return step_29\n"
    # The working copy drifted: one context line near the first hunk now uses a tab.
    drifted = list(lines)
    drifted[target - 1] = drifted[target - 1].replace("    ", "\t", 1)
    working = "def pipeline():\n" + "\n".join(drifted) + "\n    return step_29\n"
    expected = "def pipeline():\n" + "\n".join(
        [drifted[target - 1] if i == target - 1 else line for i, line in enumerate(after_lines)]) + "\n    return step_29\n"
    import difflib
    patch = "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), "a/pipeline.py",
                                         "b/pipeline.py", n=3))
    _write(d / "pipeline.py", working)
    _write(d / "fix.patch", patch)
    task = ("fix.patch was made against an older pipeline.py. Apply its changes to pipeline.py. Part of it no "
            "longer applies cleanly because pipeline.py has drifted slightly (whitespace); make that change by "
            "hand instead, keeping the drifted lines as they are. Leave no .orig or .rej files behind.")
    return {"task": task, "check": {"kind": "exact_file", "file": "pipeline.py", "expected": expected,
                                    "absent_glob": ["*.rej", "*.orig"]}}


def dir_sync(r: random.Random, d: Path) -> dict:
    expected = {}
    for i in range(r.randint(20, 35)):
        rel = Path(r.choice(["", "img", "docs", "docs/old", "data"])) / f"f{i}.{r.choice(['txt', 'md', 'csv'])}"
        content = f"version {r.randint(1, 3)} of {rel}\n"
        (d / "src" / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / "src" / rel).write_text(content)
        state = r.choice(["missing", "same", "different"])
        if state != "missing":
            (d / "backup" / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / "backup" / rel).write_text(content if state == "same" else content.replace("version", "draft"))
        expected[str(rel)] = content
    for j in range(r.randint(2, 5)):
        rel = Path("archive") / f"extra{j}.txt"
        (d / "backup" / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / "backup" / rel).write_text(f"keep me {j}\n")
        expected[str(rel)] = f"keep me {j}\n"
    task = ("Update backup/ from src/: copy every file from src/ that is missing in backup/ or whose content "
            "differs, keeping relative paths. Do not delete or change files that exist only in backup/, and do "
            "not modify src/.")
    return {"task": task, "check": {"kind": "tree_equal", "dir": "backup", "files": expected}}


OOD_FAMILIES = {"sqlite_query": sqlite_query, "dependency_order": dependency_order, "regex_extract": regex_extract,
                "split_file": split_file, "markdown_table": markdown_table, "env_debug": env_debug,
                "diff_apply": diff_apply, "dir_sync": dir_sync}
N_OOD = 3


def build_ood() -> dict:
    """Add the out-of-distribution tasks (split `ood`) without touching the existing ones."""
    index = json.loads((DATA / "index.json").read_text())
    index["split"]["ood"] = []
    for fam, fn in OOD_FAMILIES.items():
        for i in range(N_OOD):
            tid = f"{fam}_o{i}"
            shutil.rmtree(DATA / "tasks" / tid, ignore_errors=True)
            setup = DATA / "tasks" / tid / "setup"
            setup.mkdir(parents=True)
            spec = fn(random.Random(f"{tid}-v1"), setup)
            spec["family"] = fam
            (DATA / "tasks" / tid / "spec.json").write_text(json.dumps(spec, indent=1))
            index["tasks"][tid] = {"family": fam, "task": spec["task"]}
            index["split"]["ood"].append(tid)
    tmp = DATA / "index.json.tmp"
    tmp.write_text(json.dumps(index, indent=1))
    tmp.replace(DATA / "index.json")
    return index


def build() -> dict:
    """Build every task's setup directory and check spec under data/."""
    shutil.rmtree(DATA, ignore_errors=True)
    split = {"evolve": [], "heldout": []}
    tasks = {}
    for fam, fn in FAMILIES.items():
        for part, n, tag in (("evolve", N_EVOLVE, ""), ("heldout", N_HELDOUT, "h")):
            for i in range(n):
                tid = f"{fam}_{tag}{i}"
                setup = DATA / "tasks" / tid / "setup"
                setup.mkdir(parents=True)
                spec = fn(random.Random(f"{tid}-v2"), setup)
                spec["family"] = fam
                (DATA / "tasks" / tid / "spec.json").write_text(json.dumps(spec, indent=1))
                tasks[tid] = {"family": fam, "task": spec["task"]}
                split[part].append(tid)
    index = {"tasks": tasks, "split": split, "smoke": ["csv_report_0", "fix_tests_0"]}
    (DATA / "index.json").write_text(json.dumps(index, indent=1))
    return index


if __name__ == "__main__":
    idx = build()
    idx = build_ood()
    print(f"built {len(idx['tasks'])} tasks ({len(idx['split']['evolve'])} evolve, "
          f"{len(idx['split']['heldout'])} held-out, {len(idx['split']['ood'])} out-of-distribution) in {DATA}")
