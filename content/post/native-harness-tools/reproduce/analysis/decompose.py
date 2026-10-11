"""Split tokens per trial into a fixed part (first-request input, resent on every request) and the rest of the conversation."""
import statistics

import data


def row(label):
    trials = data.requests(label)
    fixed = [r[0]["input_tokens"] * len(r) for r in trials]
    total = [sum(x["input_tokens"] + x["output_tokens"] for x in r) for r in trials]
    work = [t - f for t, f in zip(total, fixed)]
    return {
        "first": statistics.median(r[0]["input_tokens"] for r in trials),
        "requests": statistics.mean(len(r) for r in trials),
        "total": statistics.mean(total),
        "fixed": statistics.mean(fixed),
        "work": statistics.mean(work),
    }


CURRENT = ["claude-opus-5-5", "claude-sonnet-5-5", "gpt-6-astra", "gpt-6_1-sol", "gpt-6-luna"]
OLDER = ["claude-opus-4-7", "claude-opus-4-8", "claude-sonnet-5", "gpt-5_5", "gpt-5_6-sol"]
PAIRS = [
    ("Matrix: standard → minimal (main, shell only)", "mainmatrixshell", "mainminimal", CURRENT),
    ("API: MindRoom's matching set → only the harness's own tools", "headfairmindroom", "headfairnative", CURRENT + OLDER),
    ("API: MindRoom tools → native tools (shell + coding)", "headmindroom", "headnative", CURRENT),
    ("API: MindRoom tools → native tools (shell + coding), older models", "headmindroom", "headnative", OLDER),
    ("API: MindRoom shell → native shell (shell only)", "headshellmindroom", "headshellnative", CURRENT),
]
for title, a, b, models in PAIRS:
    print(f"\n### {title}\n")
    print("| Model | First request | Requests | Fixed part | Work part | Total |")
    print("|---|---|---|---|---|---|")
    for m in models:
        x, y = row(f"{m}-{a}-k3"), row(f"{m}-{b}-k3")
        f = lambda k, fmt="{:,.0f}": f"{fmt.format(x[k])} → {fmt.format(y[k])}"
        dw = (y["work"] / x["work"] - 1) * 100
        print(f"| {m} | {f('first')} | {f('requests', '{:.2f}')} | {f('fixed')} | {f('work')} ({dw:+.0f}%) | {f('total')} |")
