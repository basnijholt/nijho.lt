"""Minimal-mode arms on the tool-dialect pull request: minimal Bash, or one native-shaped run tool.

The native arm sets MINDROOM_EXPERIMENT_MINIMAL_RUN_TOOL=1 (see minimal-native.patch), so minimal mode presents the
canonical `run_shell_command`, which the tool dialect shows as Claude Code's `Bash` or Codex's `exec_command`.

Each (task, trial) gets a fresh room with the coder and the router; minimal trials first send `!mode coder minimal`.
The trial is graded by the RRSI domain's hidden check, and its record lands where report.py reads the API-path cells.
Usage: matrix_eval_native.py <provider> <model> <namespace> <headminimal|headminimalnative|headminimalnative100> [k] [--capture]
"""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
import uuid
from pathlib import Path

import httpx
import nio
import yaml

os.environ.setdefault("RRSI_WORKER_IMAGE", "mindroom-rrsi-worker:head")
sys.path.insert(0, "/work/rrsi-dialects/wt-cells/domains/mindroom_dialects")
import adapter  # noqa: E402

sys.path.insert(0, "/work/rrsi-minimal")
import mclient  # noqa: E402

# The capped native arm runs from a tree that also has tail100.patch applied.
MAIN = Path(os.environ.get("RRSI_MINDROOM_TREE", "/work/rrsi-minimal/native"))
PY = MAIN / ".venv" / "bin" / "python"
RUNS = Path("/work/rrsi-dialects/runs/mindroom_dialects/jobs")
EVAL_USER, EVAL_PASSWORD = "rrsievaluser", os.environ.get("RRSI_EVAL_PASSWORD", "change-me")
CONCURRENCY = 5
# Minimal turns store CANCELLED between Bash windows and rewrite the same run row when the turn ends.
TERMINAL = {"COMPLETED", "ERROR"}
USED_ROOMS: set[str] = set()


def write_config(cell_dir: Path, provider: str, model: str, namespace: str, tool_dialect: str, capture: bool) -> Path:
    cfg = {
        "models": {"default": {"provider": provider, "id": model, "tool_dialect": tool_dialect}},
        "router": {"model": "default", "accept_invites": True},
        "memory": {"backend": "none"},
        "defaults": {"tools": []},
        "agents": {
            "coder": {
                "display_name": "Coder",
                "role": "Terminal assistant that completes tasks in a Linux shell.",
                "instructions": ["Complete the user's task."],
                "model": "default",
                "tools": ["shell"],
                "worker_tools": ["shell"],
                "worker_scope": "shared",
                "include_default_tools": False,
                "learning": False,
                # Minimal mode needs an agent workspace; file memory provides it in both arms.
                "memory_backend": "file",
                "thread_mode": "room",
                "accept_invites": True,
                "access": {"current_room_members": False, "members_of_rooms": [], "users": [f"@{EVAL_USER}:matrix.localhost"]},
            },
        },
        "mindroom_user": {"username": f"{namespace}user", "display_name": "RRSI Eval"},
        "room_defaults": {"join_policy": "invite", "listed": False},
        "matrix_space": {"enabled": False},
    }
    if capture:
        cfg["debug"] = {"log_llm_requests": True, "llm_request_log_dir": str(cell_dir / "llm_requests")}
    path = cell_dir / "config.yaml"
    path.write_text(yaml.safe_dump(cfg, sort_keys=False))
    return path


class Runtime:
    def __init__(self, cell_dir: Path, namespace: str, config: Path, native_run_tool: bool):
        self.cell_dir, self.namespace, self.config = cell_dir, namespace, config
        self.native_run_tool = native_run_tool
        self.storage = cell_dir / "storage"
        self.prefix = f"rrsi-mx-{namespace}"
        self.proc: subprocess.Popen | None = None
        self.coder = f"@mindroom_coder_{namespace}:matrix.localhost"
        self.router = f"@mindroom_router_{namespace}:matrix.localhost"
        self.port = adapter._free_port()

    def __enter__(self) -> Runtime:
        # Fresh Matrix state per run: stored accounts would keep an earlier namespace's bot IDs.
        shutil.rmtree(self.storage, ignore_errors=True)
        env = {**os.environ, "MINDROOM_CONFIG_PATH": str(self.config), "MINDROOM_STORAGE_PATH": str(self.storage),
               "MINDROOM_NAMESPACE": self.namespace, "MATRIX_HOMESERVER": mclient.HS, "MATRIX_SSL_VERIFY": "false",
               "MINDROOM_WORKER_BACKEND": "docker", "MINDROOM_DOCKER_WORKER_IMAGE": os.environ["RRSI_WORKER_IMAGE"],
               "MINDROOM_DOCKER_WORKER_NAME_PREFIX": self.prefix, "MINDROOM_SANDBOX_PROXY_TOKEN": secrets.token_hex(32),
               "MINDROOM_API_KEY": secrets.token_hex(24), "TMPDIR": "/work/tmp"}
        env.pop("OPENAI_COMPAT_ALLOW_UNAUTHENTICATED", None)
        env.pop("MINDROOM_EXPERIMENT_MINIMAL_RUN_TOOL", None)
        if self.native_run_tool:
            env["MINDROOM_EXPERIMENT_MINIMAL_RUN_TOOL"] = "1"
        log = open(self.cell_dir / "mindroom.log", "w")
        self.proc = subprocess.Popen(
            ["nix-shell", str(MAIN / "shell.nix"), "--run", f"exec {PY.parent / 'mindroom'} run --api-port {self.port}"],
            cwd=str(self.cell_dir), env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            return self._wait_ready()
        except BaseException:
            self.__exit__()
            raise

    def _wait_ready(self) -> Runtime:
        deadline = time.time() + 300
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"mindroom exited rc={self.proc.returncode}; see {self.cell_dir / 'mindroom.log'}")
            lines = (self.cell_dir / "mindroom.log").read_text(errors="replace").splitlines()
            if any("agent_setup_complete" in line and "agent=coder" in line for line in lines):
                state = (self.storage / "matrix_state.yaml").read_text()
                assert f"username: {self.coder[1:].split(':')[0]}" in state, "coder account does not match namespace"
                return self
            time.sleep(2)
        raise RuntimeError("runtime did not finish setting up the coder in 300s")

    def __exit__(self, *exc) -> None:
        if self.proc and self.proc.poll() is None:
            os.killpg(self.proc.pid, signal.SIGTERM)
            try:
                self.proc.wait(60)
            except subprocess.TimeoutExpired:
                os.killpg(self.proc.pid, signal.SIGKILL)
                self.proc.wait(10)
        adapter._docker_rm_prefix(self.prefix)

    def workspace(self) -> Path:
        return self.storage / "agents" / "coder" / "workspace"

    def runs(self, room_id: str) -> list[tuple[str, str]]:
        db = self.storage / "agents" / "coder" / "sessions" / "coder.db"
        if not db.exists():
            return []
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=30)
        try:
            return con.execute("select status, run_data from coder_sessions_runs where session_id = ? order by run_index",
                               (room_id,)).fetchall()
        except sqlite3.OperationalError:
            return []
        finally:
            con.close()


def prompt(task: str, uid: str) -> str:
    """Return the API harness prompt with this runtime's workspace path."""
    return adapter._prompt(task, uid).replace(adapter.WORKER_DIR, "/app/worker/agents/coder/workspace")


async def wait_text(client: nio.AsyncClient, room: str, sender: str, t0: int, needle: str, seconds: int) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        for msg in await mclient.messages_from(client, room, sender, t0):
            if needle in str(msg.get("content", {}).get("body", "")):
                return True
        await asyncio.sleep(2)
    return False


async def one_trial(rt: Runtime, client: nio.AsyncClient, label: str, mode: str, s: int, task_id: str) -> None:
    out = RUNS / f"heldout_{label}" / f"s{s}" / task_id
    if (out / "trial.json").exists():
        return
    task = adapter.index()["tasks"][task_id]
    last = ""
    for attempt in range(3):
        uid = f"{task_id}-{uuid.uuid4().hex[:10]}"
        trial_dir = rt.workspace() / "trials" / uid
        trial_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(adapter._task_dir(task_id) / "setup", trial_dir, symlinks=True)
        try:
            room = await mclient.new_room(client, [rt.coder, rt.router], f"{label}-s{s}-{uid}")
            if room in USED_ROOMS:
                raise RuntimeError(f"room {room} was already used by another trial")
            USED_ROOMS.add(room)
            if mode == "minimal":
                t0 = int(time.time() * 1000)
                await mclient.send(client, room, "!mode coder minimal")
                if not await wait_text(client, room, rt.router, t0, "uses `minimal` mode", 120):
                    raise RuntimeError("mode command not confirmed")
            started = time.time()
            await mclient.send(client, room, prompt(task["task"], uid))
            status, run = "", {}
            while time.time() - started < 900:
                rows = rt.runs(room)
                if rows and rows[-1][0] in TERMINAL:
                    status, run = rows[-1][0], json.loads(rows[-1][1])
                    break
                await asyncio.sleep(2)
            else:
                raise TimeoutError("run never finished")
        except Exception as exc:  # noqa: BLE001 - any trial failure is retried, then reported as missing
            last = f"{type(exc).__name__}: {exc}"
            await asyncio.sleep(10 * (attempt + 1))
            continue
        reply = str(run.get("content") or "")
        if status != "COMPLETED" and any(x in reply.lower() for x in adapter.TRANSIENT):
            last = f"transient run failure: {reply[:300]}"
            await asyncio.sleep(15 * (attempt + 1))
            continue
        verdict = await asyncio.to_thread(adapter.hidden_check, trial_dir, task_id)
        metrics = run.get("metrics") or {}
        rec = {"task_id": task_id, "family": task["family"], "trial": s, "task": task["task"], "reply": reply,
               "verdict": verdict["detail"], "reward": 1.0 if verdict["pass"] else 0.0, "run_status": status,
               "messages": run.get("messages", []), "tokens": metrics.get("total_tokens"),
               "input_tokens": metrics.get("input_tokens"), "output_tokens": metrics.get("output_tokens"),
               "seconds": round(time.time() - started, 1), "session_id": room, "trial_dir": str(trial_dir), "mode": mode}
        out.mkdir(parents=True, exist_ok=True)
        (out / "trial.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1))
        print(f"[matrix_eval] {label} s{s} {task_id}: {'PASS' if verdict['pass'] else 'fail'} "
              f"({rec['tokens']} tok, {rec['seconds']}s) {verdict['detail'][:80]}", flush=True)
        return
    print(f"[matrix_eval] {label} s{s} {task_id}: MISSING after retries ({last})", flush=True)


async def run_cell(rt: Runtime, label: str, mode: str, k: int) -> None:
    ids = adapter.MindRoomDialectsDomain().heldout_ids()
    queue: asyncio.Queue[tuple[int, str]] = asyncio.Queue()
    for s in range(k):
        for task_id in ids:
            queue.put_nowait((s, task_id))

    async def worker() -> None:
        # Each worker has its own client (a shared one handed two workers the same new room), all on one cached token.
        client = await mclient.client_for(EVAL_USER, EVAL_PASSWORD)
        try:
            while not queue.empty():
                s, task_id = queue.get_nowait()
                await one_trial(rt, client, label, mode, s, task_id)
        finally:
            await client.close()

    await (await mclient.client_for(EVAL_USER, EVAL_PASSWORD)).close()  # cache the token before workers start
    await asyncio.gather(*(worker() for _ in range(CONCURRENCY)))


def main() -> None:
    # SIGTERM unwinds through the runtime's context manager, so the MindRoom process and its workers stop too.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    capture = "--capture" in sys.argv
    argv = [a for a in sys.argv[1:] if a != "--capture"]
    provider, model, namespace, arm = argv[:4]
    k = int(argv[4]) if len(argv) > 4 else 3
    assert arm in {"headminimal", "headminimalnative", "headminimalnative100"}, arm
    assert (arm == "headminimalnative100") == MAIN.name.endswith("native100"), "capped arm needs RRSI_MINDROOM_TREE=.../native100"
    native = arm.startswith("headminimalnative")
    # Claude models already default to the Claude dialect; GPT needs Codex's shapes named explicitly.
    tool_dialect = ("claude" if provider == "vertexai_claude" else "codex") if native else "auto"
    cell_dir = Path("/work/rrsi-minimal/cells") / f"{model.replace('.', '_')}-{arm}{'-capture' if capture else ''}"
    cell_dir.mkdir(parents=True, exist_ok=True)
    config = write_config(cell_dir, provider, model, namespace, tool_dialect, capture)
    with Runtime(cell_dir, namespace, config, native) as rt:
        label = f"{model.replace('.', '_')}-{arm}{'capture' if capture else ''}-k{k}"
        print(f"[matrix_eval] start {label}", flush=True)
        asyncio.run(run_cell(rt, label, "minimal", k))
        print(f"[matrix_eval] done {label}", flush=True)


if __name__ == "__main__":
    main()
