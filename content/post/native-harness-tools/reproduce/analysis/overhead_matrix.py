"""Request profile for the Matrix arms: usage lines from each model's runtime log, grouped by trial room."""
import glob, json, re, statistics
from collections import defaultdict

JOBS = "/work/rrsi-dialects/runs/mindroom_dialects/jobs"
pat = re.compile(r"LLM usage.*?context_input_tokens=(\d+).*?output_tokens=(\d+).*?room_id=(\S+)")
room_label = {}
for f in glob.glob(f"{JOBS}/heldout_*-main*-k3/s*/*/trial.json"):
    label = f.split("heldout_", 1)[1].split("/", 1)[0]
    if "mainshell" in label:
        continue
    room_label[json.load(open(f))["session_id"]] = label
per_room = defaultdict(list)
for log in glob.glob("/work/rrsi-minimal/cells/*/mindroom.log"):
    for line in open(log, errors="replace"):
        m = pat.search(line)
        if m and m.group(3) in room_label and "agent_id=coder" in line:
            per_room[m.group(3)].append((int(m.group(1)), int(m.group(2))))
by_label = defaultdict(list)
for room, reqs in per_room.items():
    by_label[room_label[room]].append(reqs)
print("| cell | requests/trial | first-request input | input/request | output/trial |")
print("|---|---|---|---|---|")
for label in sorted(by_label):
    rows = by_label[label]
    print(f"| {label} | {statistics.mean(len(r) for r in rows):.2f} | {statistics.median(r[0][0] for r in rows):.0f} | "
          f"{statistics.mean(i for r in rows for i, _ in r):.0f} | {statistics.mean(sum(o for _, o in r) for r in rows):.0f} |")
