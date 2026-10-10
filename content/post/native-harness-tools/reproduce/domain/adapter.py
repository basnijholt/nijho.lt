"""MindRoom shell instance: a MindRoom agent with worker-routed `shell`/`file`
tools, served through MindRoom's OpenAI-compatible API, evolved on realistic
terminal tasks with hidden checks.

The harness is the agent's authored configuration (harness/agent.yaml). Model,
provider, memory, learning and worker routing are frozen in base_config.yaml or
forced here: every code-execution tool runs in a dedicated Docker worker, never
on the host.

Evaluate = one standalone MindRoom API process per job (no Matrix) booted from
the candidate's merged config, with MINDROOM_WORKER_BACKEND=docker and a fresh
storage root, so each job gets its own worker container. Each (task, trial)
copies the task's setup files into a fresh directory of the worker workspace,
sends one POST /v1/chat/completions with its own X-Session-Id, and then runs the
task's hidden check in a throwaway, network-less container that mounts the
trial directory read-only. Trial s of job J lives in
runs/mindroom_shell/jobs/J/s<s>/<task>/trial.json.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
sys.path.insert(0, str(HERE))
from rrsi.domain import Domain          # noqa: E402
from rrsi.evaluate import TaskResult    # noqa: E402
import briefs                            # noqa: E402
import tasks as suite                    # noqa: E402

CFG = json.loads((HERE / "rrsi.json").read_text())
MINDROOM_PY = os.environ.get("MINDROOM_PY", sys.executable)
WORKER_IMAGE = os.environ.get("RRSI_WORKER_IMAGE", CFG.get("worker_image", "mindroom-rrsi-worker:dev"))
AGENT = "coder"
ALLOWED_KEYS = {"role", "instructions", "tools", "markdown", "show_tool_calls", "max_tool_calls_per_turn",
                "compress_tool_results", "compaction"}
ALLOWED_TOOLS = {"shell", "file", "python", "coding"}
WORKER_DIR = "/app/worker/workspace"
TRANSIENT = ("rate limit", "429", "overloaded", "temporarily unavailable", "502", "503", "504",
             "connection error", "timed out")


def index() -> dict:
    if not (suite.DATA / "index.json").exists():
        suite.build()
    return json.loads((suite.DATA / "index.json").read_text())


def _task_dir(task_id: str) -> Path:
    return suite.DATA / "tasks" / task_id


def _leak_pattern() -> str:
    values = set()
    for tid in index()["tasks"]:
        check = json.loads((_task_dir(tid) / "spec.json").read_text())["check"]
        if check["kind"] == "file_equals" and len(check["expected"]) >= 4:
            values.add(check["expected"])
    for old, new in (("fetch_rows", "load_rows"), ("get_items", "list_items"), ("calc_total", "sum_total")):
        values |= {old, new}
    alts = "|".join(re.escape(v) for v in sorted(values, key=len, reverse=True))
    return rf"(?m)^\+.*(?<![\w])({alts})(?![\w])"


# ------------------------------------------------------------------ harness --
def load_harness(root: Path) -> dict:
    agent = yaml.safe_load((root / "domains" / "mindroom_dialects" / "harness" / "agent.yaml").read_text()) or {}
    if not isinstance(agent, dict):
        raise ValueError("harness/agent.yaml must be a mapping")
    if extra := set(agent) - ALLOWED_KEYS:
        raise ValueError(f"harness/agent.yaml keys not evolvable here: {sorted(extra)}; allowed: {sorted(ALLOWED_KEYS)}")
    tools = agent.get("tools") or []
    if not all(isinstance(t, str) for t in tools) or set(tools) - ALLOWED_TOOLS:
        raise ValueError(f"tools must be plain names from {sorted(ALLOWED_TOOLS)}; got {tools}")
    return agent


def write_config(root: Path, out_dir: Path) -> Path:
    agent = load_harness(root)
    cfg = yaml.safe_load((root / "domains" / "mindroom_dialects" / "base_config.yaml").read_text())
    tools = list(agent.get("tools") or [])
    cfg["agents"] = {AGENT: {**agent, "display_name": "Coder", "model": "default", "learning": False,
                             "memory_backend": "none", "include_default_tools": False,
                             "worker_tools": tools, "worker_scope": "shared"}}
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "config.yaml"
    path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
    (out_dir / ".env").write_text("OPENAI_COMPAT_ALLOW_UNAUTHENTICATED=true\n")
    return path


def validate_config(path: Path) -> tuple[bool, str]:
    r = subprocess.run([str(Path(MINDROOM_PY).parent / "mindroom"), "config", "validate", "--path", str(path)],
                       capture_output=True, text=True, timeout=180,
                       env={**os.environ, "MINDROOM_CONFIG_PATH": str(path)})
    return r.returncode == 0, (r.stdout + r.stderr)[-1500:]


# ------------------------------------------------------------------ runtime --
def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _docker_rm_prefix(prefix: str) -> None:
    names = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True).stdout
    victims = [n for n in names.split() if n.startswith(prefix)]
    if victims:
        subprocess.run(["docker", "rm", "-f", *victims], capture_output=True)


class Server:
    """One standalone MindRoom API process (and its Docker worker) for one job."""

    def __init__(self, root: Path, job_dir: Path, job: str):
        self.cfg_dir = job_dir / "_runtime"
        self.storage = self.cfg_dir / "storage"
        self.config = write_config(root, self.cfg_dir)
        self.prefix = "rrsi-" + re.sub(r"[^a-z0-9-]", "-", job.lower())[:30] + "-" + uuid.uuid4().hex[:6]
        self.port = _free_port()
        self.url = f"http://127.0.0.1:{self.port}"
        self.proc: subprocess.Popen | None = None
        self.workspace: Path | None = None

    def __enter__(self) -> "Server":
        env = {**os.environ, "MINDROOM_CONFIG_PATH": str(self.config), "MINDROOM_STORAGE_PATH": str(self.storage),
               "OPENAI_COMPAT_ALLOW_UNAUTHENTICATED": "true", "MINDROOM_WORKER_BACKEND": "docker",
               "MINDROOM_DOCKER_WORKER_IMAGE": WORKER_IMAGE, "MINDROOM_SANDBOX_PROXY_TOKEN": secrets.token_hex(32),
               "MINDROOM_DOCKER_WORKER_NAME_PREFIX": self.prefix}
        log = open(self.cfg_dir / "api.log", "a")
        self.proc = subprocess.Popen(
            [MINDROOM_PY, "-m", "uvicorn", "mindroom.api.main:app", "--host", "127.0.0.1", "--port", str(self.port),
             "--log-level", "warning"],
            cwd=str(self.cfg_dir), env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        deadline = time.time() + 180
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"MindRoom API exited rc={self.proc.returncode}; see {self.cfg_dir / 'api.log'}")
            try:
                r = httpx.get(self.url + "/v1/models", timeout=3)
                if r.status_code == 200 and any(m["id"] == AGENT for m in r.json()["data"]):
                    break
            except httpx.HTTPError:
                pass
            time.sleep(1)
        else:
            self.__exit__()
            raise RuntimeError(f"MindRoom API did not serve {AGENT} within 180s")
        self._warm_worker()
        return self

    def _warm_worker(self) -> None:
        """Start the worker container with one trivial command and locate its workspace on the host."""
        for attempt in range(3):
            try:
                httpx.post(self.url + "/v1/chat/completions", timeout=300,
                           headers={"X-Session-Id": f"warmup-{uuid.uuid4().hex[:8]}"},
                           json={"model": AGENT, "messages": [{"role": "user", "content":
                                 "Run the shell command `mkdir -p trials && pwd` and reply with its output."}]})
            except httpx.HTTPError:
                pass
            found = sorted(self.storage.glob(f"workers/*_{AGENT}-*/workspace"))
            if found:
                self.workspace = found[0]
                (self.workspace / "trials").mkdir(exist_ok=True)
                return
            time.sleep(5 * (attempt + 1))
        raise RuntimeError("worker workspace never appeared; is Docker running and the worker image present?")

    def __exit__(self, *exc) -> None:
        if self.proc and self.proc.poll() is None:
            os.killpg(self.proc.pid, signal.SIGTERM)
            try:
                self.proc.wait(30)
            except subprocess.TimeoutExpired:
                os.killpg(self.proc.pid, signal.SIGKILL)
                self.proc.wait(10)
        _docker_rm_prefix(self.prefix)

    def session_run(self, sid: str) -> dict:
        db = self.storage / "agents" / AGENT / "sessions" / f"{AGENT}.db"
        if not db.exists():
            return {}
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=30)
        try:
            row = con.execute(f"select status, run_data from {AGENT}_sessions_runs where session_id = ? "
                              f"order by run_index desc limit 1", (f"noauth:{sid}",)).fetchone()
        finally:
            con.close()
        if not row:
            return {}
        run = json.loads(row[1])
        return {"status": row[0], "messages": run.get("messages") or [], "metrics": run.get("metrics") or {}}


def hidden_check(trial_dir: Path, task_id: str) -> dict:
    r = subprocess.run(
        ["docker", "run", "--rm", "--network", "none", "--user", "1000:100", "--memory", "1g", "--pids-limit", "256",
         "--entrypoint", "python3", "-v", f"{trial_dir}:/task:ro", "-v", f"{HERE / 'checker.py'}:/check/checker.py:ro",
         "-v", f"{_task_dir(task_id) / 'spec.json'}:/check/spec.json:ro", WORKER_IMAGE,
         "/check/checker.py", "/check/spec.json", "/task"],
        capture_output=True, text=True, timeout=300)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return {"pass": False, "detail": f"checker produced no verdict: {(r.stdout + r.stderr)[-300:]}"}


def _trial_path(runs_dir: Path, job: str, s: int, task_id: str) -> Path:
    return runs_dir / "jobs" / job / f"s{s}" / task_id


def _prompt(task: str, uid: str) -> str:
    return (f"Your task directory is `{WORKER_DIR}/trials/{uid}` (from your shell's starting directory it is "
            f"`trials/{uid}`). All input files are there, and every output file must be written there.\n\n"
            f"Task: {task}\n\nWhen you are done, reply with a one-line summary.")


def _one_trial(server: Server, job: str, s: int, task_id: str, out: Path, prefix: str) -> None:
    task = index()["tasks"][task_id]
    last = ""
    for attempt in range(3):
        uid = f"{task_id}-{uuid.uuid4().hex[:10]}"
        trial_dir = server.workspace / "trials" / uid
        shutil.copytree(_task_dir(task_id) / "setup", trial_dir, symlinks=True)
        sid = f"{job}-s{s}-{uid}"
        t0 = time.time()
        try:
            r = httpx.post(server.url + "/v1/chat/completions", timeout=900, headers={"X-Session-Id": sid},
                           json={"model": AGENT, "messages": [{"role": "user", "content": _prompt(task["task"], uid)}]})
        except httpx.HTTPError as e:
            last = f"{type(e).__name__}: {e}"
            time.sleep(10 * (attempt + 1))
            continue
        if r.status_code != 200:
            last = f"HTTP {r.status_code}: {r.text[:300]}"
            time.sleep(10 * (attempt + 1))
            continue
        body = r.json()
        reply = body["choices"][0]["message"]["content"] or ""
        run = server.session_run(sid)
        if run.get("status") != "COMPLETED" and any(x in reply.lower() for x in TRANSIENT):
            last = f"transient run failure: {reply[:300]}"
            time.sleep(15 * (attempt + 1))
            continue
        verdict = hidden_check(trial_dir, task_id)
        tokens = (body.get("usage") or {}).get("total_tokens") or (run.get("metrics") or {}).get("total_tokens")
        rec = {"task_id": task_id, "family": task["family"], "trial": s, "task": task["task"], "reply": reply,
               "verdict": verdict["detail"], "reward": 1.0 if verdict["pass"] else 0.0,
               "run_status": run.get("status"), "messages": run.get("messages", []), "tokens": tokens,
               "seconds": round(time.time() - t0, 1), "session_id": sid, "trial_dir": str(trial_dir)}
        out.mkdir(parents=True, exist_ok=True)
        (out / "trial.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1))
        print(f"[mindroom_dialects] {prefix} s{s} {task_id}: {'PASS' if verdict['pass'] else 'fail'} "
              f"({tokens} tok, {rec['seconds']}s) {verdict['detail'][:80]}", flush=True)
        return
    print(f"[mindroom_dialects] {prefix} s{s} {task_id}: MISSING after retries ({last})", flush=True)


def run_job(root: Path, runs_dir: Path, job: str, ids: list[str], k: int, prefix: str) -> None:
    todo = [(s, t) for s in range(k) for t in ids if not (_trial_path(runs_dir, job, s, t) / "trial.json").exists()]
    if not todo:
        return
    with Server(Path(root), runs_dir / "jobs" / job, job) as server:
        with ThreadPoolExecutor(max_workers=int(CFG.get("concurrency", 5))) as ex:
            list(ex.map(lambda st: _one_trial(server, job, st[0], st[1], _trial_path(runs_dir, job, st[0], st[1]),
                                              prefix), todo))


# ------------------------------------------------------------------- domain --
def _clip(text, n: int) -> str:
    text = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
    return text if len(text) <= n else text[:n] + f"...[+{len(text) - n} chars]"


class MindRoomDialectsDomain(Domain):
    name = "mindroom_dialects"
    harness_path = "harness"
    source_exts = {".yaml", ".md"}
    briefs = {"analyst": briefs.ANALYST, "digester": briefs.DIGESTER,
              "proposer": briefs.PROPOSER, "critic": briefs.CRITIC}
    component_signals = [
        ("client_tool",     [r"(?m)^[+-]\s*tools\s*:", r"(?m)^[+-]\s*-\s*(shell|file|python)\s*$"]),
        ("control_flow",    [r"(?m)^[+-]\s*max_tool_calls_per_turn\s*:"]),
        ("context_mgmt",    [r"(?m)^[+-].*compress_tool_results", r"(?m)^[+-]\s*compaction\s*:"]),
        ("output_plumbing", [r"(?m)^[+-]\s*markdown\s*:", r"(?m)^[+-]\s*show_tool_calls\s*:"]),
        ("prompt",          [r"(?m)^[+-]\s*role\s*:", r"(?m)^[+-]\s+-\s+(?!(shell|file|python)\s*$)\S"]),
    ]

    def __init__(self):
        families = "|".join(suite.FAMILIES)
        self.critic_patterns = [
            (rf"\b({families})_h?\d+\b", "task id in diff"),
            (r"checker\.py|spec\.json|tasks\.py|expected_rows|test_hidden|hidden check", "grader reference in diff"),
            (r"(?m)^\+\s*(model|provider|memory_backend|learning|worker_tools|worker_scope)\s*:",
             "frozen setting edited"),
            (_leak_pattern(), "task-specific value in diff"),
        ]

    def evolve_ids(self) -> list[str]:
        return list(index()["split"]["evolve"])

    def heldout_ids(self) -> list[str]:
        # MINDROOM_SHELL_HELDOUT=ood selects the out-of-distribution families instead of held-out instances.
        return list(index()["split"][os.environ.get("MINDROOM_SHELL_HELDOUT", "heldout")])

    def smoke_ids(self, incumbent_per_task=None) -> list[str]:
        return list(index()["smoke"])

    def run(self, root, runs_dir, job, ids, k, log_prefix=""):
        run_job(Path(root), Path(runs_dir), job, ids, k, log_prefix or job)

    def score(self, runs_dir, job, ids, k):
        per, fam_hits, fam_n = {}, {}, {}
        for t in ids:
            rewards, toks, missing = [], [], 0
            for s in range(k):
                p = _trial_path(Path(runs_dir), job, s, t) / "trial.json"
                if p.exists():
                    rec = json.loads(p.read_text())
                    rewards.append(float(rec["reward"]))
                    toks.append(rec.get("tokens") or None)
                    fam_hits[rec["family"]] = fam_hits.get(rec["family"], 0) + rec["reward"]
                    fam_n[rec["family"]] = fam_n.get(rec["family"], 0) + 1
                else:
                    missing += 1
                    rewards.append(0.0)
                    toks.append(None)
            per[t] = TaskResult(rewards=rewards, tokens=toks, missing=missing)
        return per, {"family_pass_rate": {f: round(fam_hits[f] / fam_n[f], 3) for f in sorted(fam_n)}}

    def load_trial(self, runs_dir, job, task_id, trial):
        p = _trial_path(Path(runs_dir), job, trial, task_id) / "trial.json"
        return json.loads(p.read_text()) if p.exists() else None

    def render_trace(self, rec, detail=False):
        cap = 3000 if detail else 500
        lines = [f"=== TASK {rec['task_id']} (family {rec['family']}, trial {rec['trial']}) ===", rec["task"],
                 "=== TRAJECTORY (agent session as stored by MindRoom) ==="]
        for i, m in enumerate(rec.get("messages") or []):
            if m.get("tool_calls"):
                calls = "; ".join(f"{c['function']['name']}({c['function'].get('arguments')})" for c in m["tool_calls"])
                lines.append(f"[step {i}] {m.get('role')} tool_calls: {_clip(calls, cap)}")
            if m.get("content"):
                lines.append(f"[step {i}] {m.get('role')}: {_clip(m['content'], cap)}")
        lines += ["=== FINAL REPLY ===", _clip(rec.get("reply") or "", cap),
                  "=== GRADING (hidden check run after the agent finished) ===",
                  f"result: {'PASS' if rec['reward'] else 'FAIL'} | {rec['verdict']}",
                  f"run_status: {rec.get('run_status')} | tokens: {rec.get('tokens')} | seconds: {rec.get('seconds')}"]
        return "\n".join(lines)

    def task_row(self, task_id, rec, tr):
        n_tools = sum(len(m.get("tool_calls") or []) for m in rec.get("messages") or [])
        return (f"{task_id} | family={rec['family']} | mean over trials {tr.mean:.2f} | "
                f"{'PASS' if rec['reward'] else 'FAIL'}: {rec['verdict'][:100]} | tool_calls={n_tools} | "
                f"tokens={rec.get('tokens')} | seconds={rec.get('seconds')}")

    def smoke(self, root, runs_dir, job, ids):
        root, runs_dir = Path(root), Path(runs_dir)
        try:
            path = write_config(root, runs_dir / "jobs" / job / "_validate")
        except Exception as e:  # noqa: BLE001
            return False, {"stage": "harness", "detail": str(e)[:1500]}
        ok, out = validate_config(path)
        if not ok:
            return False, {"stage": "config_validate", "detail": out}
        shutil.rmtree(runs_dir / "jobs" / job, ignore_errors=True)
        try:
            run_job(root, runs_dir, job, ids, 1, job)
        except Exception as e:  # noqa: BLE001
            return False, {"stage": "boot", "detail": str(e)[:1500]}
        done = sum((_trial_path(runs_dir, job, 0, t) / "trial.json").exists() for t in ids)
        if done < len(ids):
            return False, {"stage": "smoke_run", "detail": f"{done}/{len(ids)} trials"}
        return True, {"stage": "smoke_run", "n": done}


DOMAIN = MindRoomDialectsDomain()
