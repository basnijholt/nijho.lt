"""Task-stratified bootstrap 95% CI for the relative token change between two cells, and Fisher's exact test on passes."""
import glob, json, random, sys
from collections import defaultdict
from math import comb

JOBS = "/work/rrsi-dialects/runs/mindroom_dialects/jobs"


def load(label):
    by_task = defaultdict(list)
    passes = total = 0
    for f in glob.glob(f"{JOBS}/heldout_{label}/s*/*/trial.json"):
        t = json.load(open(f))
        by_task[t["task_id"]].append(float(t["tokens"]))
        passes += t["reward"] >= 1
        total += 1
    return by_task, passes, total


def fisher(a, n, b, m):
    k = a + b
    def p(x): return comb(n, x) * comb(m, k - x) / comb(n + m, k)
    obs = p(a)
    return sum(p(x) for x in range(max(0, k - m), min(n, k) + 1) if p(x) <= obs + 1e-12)


def ci(base, other, reps=5000, seed=0):
    rng = random.Random(seed)
    tasks = sorted(set(base) & set(other))
    def ratio(sample_b, sample_o):
        return sum(sample_o) / sum(sample_b) - 1
    point = ratio([x for t in tasks for x in base[t]], [x for t in tasks for x in other[t]])
    draws = []
    for _ in range(reps):
        b, o = [], []
        for t in tasks:  # resample trials within each task, keeping the task mix fixed
            b += [rng.choice(base[t]) for _ in base[t]]
            o += [rng.choice(other[t]) for _ in other[t]]
        draws.append(ratio(b, o))
    draws.sort()
    return point, draws[int(0.025 * reps)], draws[int(0.975 * reps)]


if __name__ == "__main__":
    for base_label, other_label in (pair.split(",") for pair in sys.argv[1:]):
        b, bp, bn = load(base_label)
        o, op, on = load(other_label)
        point, lo, hi = ci(b, o)
        print(f"{other_label} vs {base_label}: tokens {point:+.0%} [95% CI {lo:+.0%}, {hi:+.0%}]; "
              f"pass {op}/{on} vs {bp}/{bn}, Fisher p={fisher(op, on, bp, bn):.2f}")
