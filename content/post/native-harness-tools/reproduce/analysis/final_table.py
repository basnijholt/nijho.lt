"""One table for every arm: pass rate from trial records, tokens summed from MindRoom's per-request usage logs."""
import glob, json, re, statistics
from collections import OrderedDict, defaultdict

JOBS = "/work/rrsi-dialects/runs/mindroom_dialects/jobs"
pat = re.compile(r"LLM usage.*?input_tokens=(\d+).*?output_tokens=(\d+)")
corr = re.compile(r"correlation_id=(\S+)")
room = re.compile(r"room_id=(\S+)")


def trials(label):
    return [json.load(open(f)) for f in sorted(glob.glob(f"{JOBS}/heldout_{label}/s*/*/trial.json"))]


def api_requests(label):
    groups = OrderedDict()
    for line in open(f"{JOBS}/heldout_{label}/_runtime/api.log", errors="replace"):
        m, c = pat.search(line), corr.search(line)
        if m and c:
            groups.setdefault(c.group(1), []).append((int(m.group(1)), int(m.group(2))))
    return list(groups.values())[1:]  # drop the worker warm-up


matrix = defaultdict(list)
for log in glob.glob("/work/rrsi-minimal/cells/*/mindroom.log"):
    for line in open(log, errors="replace"):
        m, r = pat.search(line), room.search(line)
        if m and r and "agent_id=coder" in line:
            matrix[r.group(1)].append((int(m.group(1)), int(m.group(2))))

ARMS = [("mindroom", "API", "shell + coding (branch default)"), ("auto", "API", "harness dialect (Claude Code / Codex)"),
        ("mainshell", "API", "main, shell only"), ("mainmatrixshell", "Matrix", "main, shell only"),
        ("mainminimal", "Matrix", "main, minimal mode (one bash)")]
MODELS = ["claude-opus-5-5", "claude-sonnet-5-5", "gpt-6-astra", "gpt-6_1-sol", "gpt-6-luna"]
print("| model | arm | path | pass | tokens/trial (logs) | tokens/trial (reported) | requests/trial | first request input |")
print("|---|---|---|---|---|---|---|---|")
for model in MODELS:
    for arm, path, desc in ARMS:
        label = f"{model}-{arm}-k3"
        ts = trials(label)
        if not ts:
            continue
        reqs = api_requests(label) if path == "API" else [matrix[t["session_id"]] for t in ts if t["session_id"] in matrix]
        passed = sum(t["reward"] >= 1 for t in ts)
        print(f"| {model} | {desc} | {path} | {passed}/{len(ts)} | {statistics.mean(sum(i + o for i, o in r) for r in reqs):,.0f} | "
              f"{statistics.mean(float(t['tokens'] or 0) for t in ts):,.0f} | {statistics.mean(len(r) for r in reqs):.2f} | "
              f"{statistics.median(r[0][0] for r in reqs):,.0f} |")
