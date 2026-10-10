"""Split tokens per trial into a fixed part (first-request input, resent on every request) and the work the model did."""
import glob, json, re, statistics
from collections import Counter, OrderedDict, defaultdict

JOBS = "/work/rrsi-dialects/runs/mindroom_dialects/jobs"
pat = re.compile(r"LLM usage.*?input_tokens=(\d+).*?output_tokens=(\d+)")
corr = re.compile(r"correlation_id=(\S+)")
room = re.compile(r"room_id=(\S+)")


def api_trials(label):
    groups = OrderedDict()
    for line in open(f"{JOBS}/heldout_{label}/_runtime/api.log", errors="replace"):
        m, c = pat.search(line), corr.search(line)
        if m and c:
            groups.setdefault(c.group(1), []).append((int(m.group(1)), int(m.group(2))))
    # Keep the request groups of graded trials, which drops the worker warm-up and attempts cut off by a stream error.
    wanted = Counter(json.load(open(f))["tokens"] for f in glob.glob(f"{JOBS}/heldout_{label}/s*/*/trial.json"))
    trials = []
    for requests in groups.values():
        total = sum(i + o for i, o in requests)
        if wanted[total]:
            wanted[total] -= 1
            trials.append(requests)
    return trials


matrix = defaultdict(list)
for log in glob.glob("/work/rrsi-minimal/cells/*/mindroom.log"):
    for line in open(log, errors="replace"):
        m, r = pat.search(line), room.search(line)
        if m and r and "agent_id=coder" in line:
            matrix[r.group(1)].append((int(m.group(1)), int(m.group(2))))


def matrix_trials(label):
    rooms = [json.load(open(f))["session_id"] for f in glob.glob(f"{JOBS}/heldout_{label}/s*/*/trial.json")]
    return [matrix[r] for r in rooms if r in matrix]


def row(label, path):
    trials = api_trials(label) if path == "API" else matrix_trials(label)
    fixed = [r[0][0] * len(r) for r in trials]
    total = [sum(i + o for i, o in r) for r in trials]
    work = [t - f for t, f in zip(total, fixed)]
    return {
        "first": statistics.median(r[0][0] for r in trials),
        "requests": statistics.mean(len(r) for r in trials),
        "total": statistics.mean(total),
        "fixed": statistics.mean(fixed),
        "work": statistics.mean(work),
    }


CURRENT = ["claude-opus-5-5", "claude-sonnet-5-5", "gpt-6-astra", "gpt-6_1-sol", "gpt-6-luna"]
OLDER = ["claude-opus-4-7", "claude-opus-4-8", "claude-sonnet-5", "gpt-5_5", "gpt-5_6-sol"]
PAIRS = [
    ("Matrix: standard → minimal (main, shell only)", "Matrix", "mainmatrixshell", "mainminimal", CURRENT),
    ("API: MindRoom tools → native tools (shell + coding)", "API", "headmindroom", "headnative", CURRENT),
    ("API: MindRoom tools → native tools (shell + coding), older models", "API", "headmindroom", "headnative", OLDER),
    ("API: MindRoom shell → native shell (shell only)", "API", "headshellmindroom", "headshellnative", CURRENT),
]
for title, path, a, b, models in PAIRS:
    print(f"\n### {title}\n")
    print("| Model | First request | Requests | Fixed part | Work part | Total |")
    print("|---|---|---|---|---|---|")
    for m in models:
        x, y = row(f"{m}-{a}-k3", path), row(f"{m}-{b}-k3", path)
        f = lambda k, fmt="{:,.0f}": f"{fmt.format(x[k])} → {fmt.format(y[k])}"
        dw = (y["work"] / x["work"] - 1) * 100
        print(f"| {m} | {f('first')} | {f('requests', '{:.2f}')} | {f('fixed')} | {f('work')} ({dw:+.0f}%) | {f('total')} |")
