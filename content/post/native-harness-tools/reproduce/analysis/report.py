"""Summarize the tool-dialect A/B: pass rate, tokens, tool calls, tool errors, and seconds per cell."""

import ast
import glob
import json
import statistics
import sys

ROOT = "/work/rrsi-dialects/runs/mindroom_dialects/jobs"
rows = []
for job in sorted(glob.glob(f"{ROOT}/heldout_*")):
    label = job.rsplit("heldout_", 1)[1]
    trials = [json.load(open(f)) for f in sorted(glob.glob(f"{job}/s*/*/trial.json"))]
    if not trials:
        continue
    calls, errors = [], []
    for trial in trials:
        try:
            messages = ast.literal_eval(trial["messages"]) if isinstance(trial["messages"], str) else trial["messages"]
        except (ValueError, SyntaxError):
            messages = []
        calls.append(sum(len(m.get("tool_calls") or []) for m in messages if m.get("role") == "assistant"))
        errors.append(sum(1 for m in messages if m.get("role") == "tool" and str(m.get("content", "")).startswith("Error")))
    passed = sum(float(t["reward"]) >= 1 for t in trials)
    rows.append({
        "cell": label,
        "pass": f"{passed}/{len(trials)}",
        "rate": round(passed / len(trials), 3),
        "tokens_mean": round(statistics.mean(float(t["tokens"]) for t in trials)),
        "tool_calls_mean": round(statistics.mean(calls), 2),
        "tool_errors": sum(errors),
        "seconds_mean": round(statistics.mean(float(t["seconds"]) for t in trials), 1),
    })
print("| cell | pass | rate | tokens (mean) | tool calls (mean) | tool errors | seconds (mean) |")
print("|---|---|---|---|---|---|---|")
for r in rows:
    print(f"| {r['cell']} | {r['pass']} | {r['rate']} | {r['tokens_mean']} | {r['tool_calls_mean']} | {r['tool_errors']} | {r['seconds_mean']} |")
