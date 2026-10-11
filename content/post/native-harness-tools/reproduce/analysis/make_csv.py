"""Export one row per trial for every configuration in the post, with the reasoning setting on every row."""

import csv
import glob
import json
import re
import sys
from collections import defaultdict

JOBS = "/work/rrsi-dialects/runs/mindroom_dialects/jobs"
OUT = sys.argv[1] if len(sys.argv) > 1 else "trials.csv"

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

# Matrix runs keep the true per-request totals in each model's runtime log, grouped by trial room.
usage = re.compile(r"LLM usage.*?input_tokens=(\d+).*?output_tokens=(\d+)")
room = re.compile(r"room_id=(\S+)")
matrix_tokens = defaultdict(int)
for log in glob.glob("/work/rrsi-minimal/cells/*/mindroom.log"):
    for line in open(log, errors="replace"):
        m, r = usage.search(line), room.search(line)
        if m and r and "agent_id=coder" in line:
            matrix_tokens[r.group(1)] += int(m.group(1)) + int(m.group(2))

rows = []
for job in sorted(glob.glob(f"{JOBS}/heldout_*-k3")):
    label = job.rsplit("heldout_", 1)[1]
    match = LABEL.match(label)
    if not match or match["model"] not in MODELS:
        continue
    setup, path, code, shape, tools = ARMS[match["arm"]]
    reasoning = f"{match['effort']} (explicit)" if match["effort"] else "adaptive thinking (explicit)" if match["think"] else MODELS[match["model"]]
    for f in sorted(glob.glob(f"{job}/s*/*/trial.json")):
        t = json.load(open(f))
        messages = t.get("messages") or []
        tokens = matrix_tokens.get(t["session_id"]) if path == "Matrix" else t.get("tokens")
        rows.append({
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
            "tokens": tokens,
            "assistant_turns": sum(1 for m in messages if m.get("role") == "assistant"),
            "tool_calls": sum(len(m.get("tool_calls") or []) for m in messages if m.get("role") == "assistant"),
            "tool_errors": sum(1 for m in messages if m.get("role") == "tool" and str(m.get("content", "")).startswith("Error")),
            "seconds": t.get("seconds"),
            "regraded": int(bool(t.get("regraded"))),
        })

with open(OUT, "w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print(f"wrote {len(rows)} trials from {len({r['configuration'] for r in rows})} configurations to {OUT}")
