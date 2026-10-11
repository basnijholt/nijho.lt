"""Share of model turns with reasoning per API configuration: Claude replies with thinking, GPT requests with reasoning tokens.

Usage: reasoning_rates.py <configuration> ...   (for example claude-opus-4-8-headmindroom-k3)
"""
import glob
import json
import re
import sys

JOBS = "/work/rrsi-dialects/runs/mindroom_dialects/jobs"
REASONING = re.compile(r"reasoning_tokens=(\d+)")
CORRELATION = re.compile(r"correlation_id=(\S+)")

for label in sys.argv[1:]:
    if label.startswith("claude"):
        replies = thinking = 0
        for f in glob.glob(f"{JOBS}/heldout_{label}/s*/*/trial.json"):
            for message in json.load(open(f))["messages"]:
                if message.get("role") == "assistant":
                    replies += 1
                    thinking += bool(message.get("reasoning_content")) or "thinking" in str(message.get("provider_data", ""))
        print(f"{label}: thinking before {thinking} of {replies} replies ({thinking / replies:.0%})")
    else:
        groups = {}
        for line in open(f"{JOBS}/heldout_{label}/_runtime/api.log", errors="replace"):
            if "LLM usage" in line and (c := CORRELATION.search(line)):
                m = REASONING.search(line)
                groups.setdefault(c.group(1), []).append(int(m.group(1)) if m else 0)
        requests = [r for g in list(groups.values())[1:] for r in g]  # drop the worker warm-up
        with_reasoning = [r for r in requests if r > 0]
        span = f", {min(with_reasoning)} to {max(with_reasoning)} tokens" if with_reasoning else ""
        print(f"{label}: reasoning on {len(with_reasoning)} of {len(requests)} requests ({len(with_reasoning) / len(requests):.0%}{span})")
