"""Task-stratified bootstrap 95% CI for the token change between two Matrix cells, and Fisher's exact test on passes.

Matrix trial records store run metrics that hold only output tokens for Claude, so tokens come from each model's
runtime log, per trial room, both in total and without the input the provider served from its cache.
Usage: ci_matrix.py <base>,<other> ...
"""
import glob
import json
import re
import sys
from collections import defaultdict

from ci import ci, fisher

JOBS = "/work/rrsi-dialects/runs/mindroom_dialects/jobs"
FIELD = re.compile(r"(\w+)=(\S+)")

usage = defaultdict(lambda: defaultdict(int))
for log in glob.glob("/work/rrsi-minimal/cells/*/mindroom.log"):
    for line in open(log, errors="replace"):
        if "LLM usage" in line and "agent_id=coder" in line:
            fields = dict(FIELD.findall(line))
            room = usage[fields["room_id"]]
            for key in ("context_input_tokens", "cache_read_tokens", "output_tokens"):
                room[key] += int(fields.get(key, 0))


def load(label, uncached):
    by_task = defaultdict(list)
    passes = total = 0
    for f in glob.glob(f"{JOBS}/heldout_{label}/s*/*/trial.json"):
        t = json.load(open(f))
        u = usage[t["session_id"]]
        tokens = u["context_input_tokens"] + u["output_tokens"] - (u["cache_read_tokens"] if uncached else 0)
        by_task[t["task_id"]].append(float(tokens))
        passes += t["reward"] >= 1
        total += 1
    return by_task, passes, total


for base_label, other_label in (pair.split(",") for pair in sys.argv[1:]):
    for uncached in (False, True):
        b, bp, bn = load(base_label, uncached)
        o, op, on = load(other_label, uncached)
        point, lo, hi = ci(b, o)
        kind = "uncached" if uncached else "total"
        print(f"{other_label} vs {base_label} ({kind}): tokens {point:+.0%} [95% CI {lo:+.0%}, {hi:+.0%}]; "
              f"pass {op}/{on} vs {bp}/{bn}, Fisher p={fisher(op, on, bp, bn):.2f}")
