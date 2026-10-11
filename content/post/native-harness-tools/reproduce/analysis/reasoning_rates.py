"""Share of model turns with reasoning per configuration: Claude replies with thinking, GPT requests with reasoning tokens.

Usage: reasoning_rates.py <configuration> ...   (for example claude-opus-4-8-headmindroom-k3)
"""

import sys

import data

for label in sys.argv[1:]:
    if label.startswith("claude"):
        rows = data.trials(label)
        replies = sum(int(t["assistant_turns"]) for t in rows)
        thinking = sum(int(t["thinking_replies"]) for t in rows)
        print(f"{label}: thinking before {thinking} of {replies} replies ({thinking / replies:.0%})")
    else:
        requests = [r["reasoning_tokens"] for trial in data.requests(label) for r in trial]
        with_reasoning = [r for r in requests if r > 0]
        span = f", {min(with_reasoning)} to {max(with_reasoning)} tokens" if with_reasoning else ""
        print(f"{label}: reasoning on {len(with_reasoning)} of {len(requests)} requests ({len(with_reasoning) / len(requests):.0%}{span})")
