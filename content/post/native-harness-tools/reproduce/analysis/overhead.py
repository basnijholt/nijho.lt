"""Per-arm request profile from MindRoom's per-request usage logs: requests per trial, first-request input, output tokens."""
import glob, re, statistics
from collections import OrderedDict, defaultdict

ROOT = "/work/rrsi-dialects/runs/mindroom_dialects/jobs"
pat = re.compile(r"LLM usage.*?context_input_tokens=(\d+) correlation_id=(\S+).*?output_tokens=(\d+)")
print("| cell | requests/trial | first-request input | input/request | output/trial |")
print("|---|---|---|---|---|")
for job in sorted(glob.glob(f"{ROOT}/heldout_*-k3")):
    try:
        lines = open(f"{job}/_runtime/api.log", errors="replace").read().splitlines()
    except FileNotFoundError:
        continue
    trials = OrderedDict()
    for line in lines:
        m = pat.search(line)
        if m:
            trials.setdefault(m.group(2), []).append((int(m.group(1)), int(m.group(3))))
    rows = list(trials.values())[1:]  # drop the worker warm-up request
    if not rows:
        continue
    print(f"| {job.rsplit('heldout_', 1)[1]} | {statistics.mean(len(r) for r in rows):.2f} | "
          f"{statistics.median(r[0][0] for r in rows):.0f} | {statistics.mean(i for r in rows for i, _ in r):.0f} | "
          f"{statistics.mean(sum(o for _, o in r) for r in rows):.0f} |")
