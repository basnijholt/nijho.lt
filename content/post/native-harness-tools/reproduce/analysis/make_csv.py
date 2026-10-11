"""Export the post's measurements from the raw run records: one row per trial, and one row per model request.

This is the only script that reads the runtime logs and trial records; the analysis scripts read the two CSV files.
Usage: make_csv.py [RESULTS_DIR]
"""

import csv
import glob
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

JOBS = "/work/rrsi-dialects/runs/mindroom_dialects/jobs"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "results"
FIELD = re.compile(r"(\w+)=(\S+)")

# label suffix -> (setup, path, code, tool shape, tools)
ARMS = {
    "mindroom": ("MindRoom tools", "API", "PR #2766, first run", "mindroom", "shell + coding"),
    "auto": ("Native tools", "API", "PR #2766, first run", "native", "shell + coding"),
    "mainshell": ("MindRoom shell only", "API", "main v2026.10.228", "mindroom", "shell"),
    "headmindroom": ("MindRoom tools", "API", "PR #2766 d73aafb51", "mindroom", "shell + coding"),
    "headnative": ("Native tools", "API", "PR #2766 d73aafb51", "native", "shell + coding"),
    "headnative100": ("Native tools, 100-line output", "API", "PR #2766 d73aafb51 + tail100.patch", "native", "shell + coding"),
    "headshellmindroom": ("MindRoom shell only", "API", "PR #2766 d73aafb51", "mindroom", "shell"),
    "headshellnative": ("Native shell only", "API", "PR #2766 d73aafb51", "native", "shell"),
    "headfairmindroom": ("MindRoom's matching set, no extras", "API", "PR #2766 d73aafb51", "mindroom", "shell + coding without grep, find_files, ls (and read_file for GPT)"),
    "headfairnative": ("Only the harness's own set", "API", "PR #2766 d73aafb51", "native", "shell + coding without grep, find_files, ls (and read_file for GPT)"),
    "mainmatrixshell": ("Standard mode, shell only", "Matrix", "main v2026.10.228", "mindroom", "shell"),
    "mainminimal": ("Minimal mode, one bash", "Matrix", "main v2026.10.228", "mindroom", "bash"),
    "headminimal": ("Minimal mode, one bash", "Matrix", "PR #2766 d73aafb51 + minimal-native.patch, off", "mindroom", "bash"),
    "headminimalnative": ("Minimal mode, one native run tool", "Matrix", "PR #2766 d73aafb51 + minimal-native.patch", "native", "Bash or exec_command"),
    "headminimalnative100": ("Minimal mode, one native run tool, 100-line output", "Matrix", "PR #2766 d73aafb51 + minimal-native.patch + tail100.patch", "native", "Bash or exec_command"),
}
MODELS = {
    "claude-opus-4-7": "default (no thinking)",
    "claude-opus-4-8": "default (no thinking)",
    "claude-sonnet-5": "default (adaptive thinking)",
    "claude-opus-5-5": "default (adaptive thinking)",
    "claude-sonnet-5-5": "default (adaptive thinking)",
    "gpt-5_5": "default (Codex backend)",
    "gpt-5_6-sol": "default (Codex backend)",
    "gpt-6-astra": "default (Codex backend)",
    "gpt-6_1-sol": "default (Codex backend)",
    "gpt-6-luna": "default (Codex backend)",
}
LABEL = re.compile(r"^(?P<model>.+?)-(?P<arm>" + "|".join(sorted(ARMS, key=len, reverse=True)) + r")(?:-eff(?P<effort>low|high)|-think(?P<think>adaptive))?-k3$")



def usage_lines(path):
    """Yield the fields of every LLM usage line in one runtime log."""
    for line in open(path, errors="replace"):
        if "LLM usage" in line:
            yield dict(FIELD.findall(line))


def request(fields):
    """One request's counts, with input including what the provider served from its cache; None without usage."""
    if fields.get("usage_available") == "False":
        return None
    return {
        "input_tokens": int(fields["context_input_tokens"]),
        "output_tokens": int(fields["output_tokens"]),
        "cache_read_tokens": int(fields.get("cache_read_tokens", 0)),
        "reasoning_tokens": int(fields.get("reasoning_tokens", 0)),
    }


def total(requests):
    return sum(r["input_tokens"] + r["output_tokens"] for r in requests)


# Matrix runs log every request with its trial room.
matrix_requests = defaultdict(list)
for log in glob.glob("/work/rrsi-minimal/cells/*/mindroom.log"):
    for fields in usage_lines(log):
        if fields.get("agent_id") == "coder" and "room_id" in fields:
            matrix_requests[fields["room_id"]].append(request(fields))


def api_requests(label, trials):
    """Return each graded API trial's requests.

    The log lines carry no trial id and the trials ran concurrently, so a trial's request group is the one with its
    token total, which must be unambiguous; this also drops the worker warm-up and attempts cut off by a stream error.
    Two trials with the same total can swap labels, which changes no total.
    """
    groups = defaultdict(list)
    for fields in usage_lines(f"{JOBS}/heldout_{label}/_runtime/api.log"):
        if "correlation_id" in fields:
            groups[fields["correlation_id"]].append(request(fields))
    by_total = defaultdict(list)
    for requests in groups.values():
        if None not in requests:
            by_total[total(requests)].append(requests)
    wanted = Counter(t["tokens"] for t in trials)
    if any(len(by_total[tokens]) != count for tokens, count in wanted.items()):
        raise ValueError(f"{label}: a graded trial does not match exactly one request group by its token total")
    return [by_total[t["tokens"]].pop() for t in trials]


def matrix_trial_requests(label, trials):
    if missing := [t["session_id"] for t in trials if t["session_id"] not in matrix_requests]:
        raise ValueError(f"{label}: no usage logged for trial rooms {missing}")
    return [matrix_requests[t["session_id"]] for t in trials]


def tool_names(messages):
    calls = Counter(
        (call.get("function") or {}).get("name") or call.get("name")
        for m in messages
        if m.get("role") == "assistant"
        for call in m.get("tool_calls") or []
    )
    return ";".join(f"{name}={count}" for name, count in sorted(calls.items()))


trial_rows, request_rows = [], []
for job in sorted(glob.glob(f"{JOBS}/heldout_*-k3")):
    label = job.rsplit("heldout_", 1)[1]
    match = LABEL.match(label)
    if not match or match["model"] not in MODELS:
        continue
    setup, path, code, shape, tools = ARMS[match["arm"]]
    reasoning = f"{match['effort']} (explicit)" if match["effort"] else "adaptive thinking (explicit)" if match["think"] else MODELS[match["model"]]
    trials = [json.load(open(f)) for f in sorted(glob.glob(f"{job}/s*/*/trial.json"))]
    per_trial = matrix_trial_requests(label, trials) if path == "Matrix" else api_requests(label, trials)
    for t, requests in zip(trials, per_trial):
        complete = None not in requests
        if path == "API" and total(requests) != t["tokens"]:
            raise ValueError(f"{label}: the requests of {t['session_id']} do not add up to its recorded tokens")
        messages = t.get("messages") or []
        assistant = [m for m in messages if m.get("role") == "assistant"]
        trial_rows.append({
            "configuration": label,
            "model": match["model"].replace("_", "."),
            "reasoning": reasoning,
            "setup": setup,
            "path": path,
            "code": code,
            "tool_shape": shape,
            "tools": tools,
            "task": t["task_id"],
            "trial": t["trial"],
            "passed": int(float(t["reward"]) >= 1),
            # Empty when the provider reported no usage for one of the trial's requests.
            "tokens": total(requests) if complete else "",
            "requests": len(requests),
            "assistant_turns": len(assistant),
            "thinking_replies": sum(bool(m.get("reasoning_content")) or "thinking" in str(m.get("provider_data", "")) for m in assistant),
            "tool_calls": sum(len(m.get("tool_calls") or []) for m in assistant),
            "tool_call_names": tool_names(messages),
            "tool_errors": sum(1 for m in messages if m.get("role") == "tool" and str(m.get("content", "")).startswith("Error")),
            "seconds": t.get("seconds"),
            "regraded": int(bool(t.get("regraded"))),
        })
        for number, r in enumerate(requests, start=1):
            request_rows.append({
                "configuration": label,
                "task": t["task_id"],
                "trial": t["trial"],
                "request": number,
                **(r or dict.fromkeys(("input_tokens", "output_tokens", "cache_read_tokens", "reasoning_tokens"), "")),
            })

for name, rows in (("trials.csv", trial_rows), ("requests.csv", request_rows)):
    with open(OUT / name, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
incomplete = [f"{r['configuration']} {r['task']} trial {r['trial']}" for r in trial_rows if r["tokens"] == ""]
print(f"wrote {len(trial_rows)} trials from {len({r['configuration'] for r in trial_rows})} configurations and {len(request_rows)} requests to {OUT}")
print(f"trials without complete usage, so without tokens: {incomplete or 'none'}")
