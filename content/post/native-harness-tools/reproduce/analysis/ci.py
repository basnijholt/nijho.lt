"""Task-stratified bootstrap 95% CI for the relative token change between two configurations, and Fisher's exact test on passes.

Prints the change in all tokens and in tokens without the input the provider served from its cache.
A trial without complete usage counts for passes but not for tokens.
Usage: ci.py <base>,<other> ...
"""

import random
import sys
from collections import defaultdict
from math import comb

import data


def load(configuration, uncached):
    by_task = defaultdict(list)
    rows = data.trials(configuration)
    complete = [t for t in rows if t["tokens"]]
    for t, requests in zip(complete, data.requests(configuration)):
        cached = sum(r["cache_read_tokens"] for r in requests) if uncached else 0
        by_task[t["task"]].append(float(int(t["tokens"]) - cached))
    return by_task, sum(int(t["passed"]) for t in rows), len(rows), len(rows) - len(complete)


def fisher(a, n, b, m):
    k = a + b
    def p(x): return comb(n, x) * comb(m, k - x) / comb(n + m, k)
    obs = p(a)
    return sum(p(x) for x in range(max(0, k - m), min(n, k) + 1) if p(x) <= obs + 1e-12)


def ci(base, other, reps=5000, seed=0):
    rng = random.Random(seed)
    if set(base) != set(other):
        raise ValueError(f"the two configurations cover different tasks: {sorted(set(base) ^ set(other))}")
    tasks = sorted(base)
    # Sorting each task's runs makes the draws depend only on the measured values, not on the order they were read in.
    base, other = {t: sorted(base[t]) for t in tasks}, {t: sorted(other[t]) for t in tasks}
    def total(sample):  # mean tokens of each task, summed over tasks, so a task that lost a trial keeps its weight
        return sum(sum(runs) / len(runs) for runs in sample.values())
    point = total(other) / total(base) - 1
    draws = []
    for _ in range(reps):
        b, o = {}, {}
        for t in tasks:  # resample trials within each task, keeping the task mix fixed
            b[t] = [rng.choice(base[t]) for _ in base[t]]
            o[t] = [rng.choice(other[t]) for _ in other[t]]
        draws.append(total(o) / total(b) - 1)
    draws.sort()
    return point, draws[int(0.025 * reps)], draws[int(0.975 * reps)]


if __name__ == "__main__":
    for base_label, other_label in (pair.split(",") for pair in sys.argv[1:]):
        for uncached in (False, True):
            b, bp, bn, bx = load(base_label, uncached)
            o, op, on, ox = load(other_label, uncached)
            point, lo, hi = ci(b, o)
            note = f"; {bx + ox} trial(s) without complete usage left out of tokens" if bx + ox else ""
            print(f"{other_label} vs {base_label} ({'uncached' if uncached else 'total'}): tokens {point:+.0%} [95% CI {lo:+.0%}, {hi:+.0%}]; "
                  f"pass {op}/{on} vs {bp}/{bn}, Fisher p={fisher(op, on, bp, bn):.2f}{note}")
