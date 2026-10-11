#!/usr/bin/env bash
# Minimal mode with one native-shaped run tool whose output is capped at the last 100 lines, like minimal Bash.
# Runs from a tree with minimal-native.patch and tail100.patch applied.
set -u
set -a; . /work/rrsi-dialects/vertex.env; set +a
export TMPDIR=/work/tmp RRSI_WORKER_IMAGE=mindroom-rrsi-worker:head RRSI_MINDROOM_TREE=/work/rrsi-minimal/native100
cell() {  # provider model namespace
  echo "[lanes100] $(date +%H:%M:%S) start $2"
  nix-shell /work/rrsi-minimal/native100/shell.nix --run "/work/rrsi-minimal/native100/.venv/bin/python -I /work/rrsi-minimal/matrix_eval_native.py $1 $2 $3 headminimalnative100 3" > "/work/rrsi-minimal/lane-$3.log" 2>&1
  echo "[lanes100] $(date +%H:%M:%S) done $2 rc=$?"
}
{ cell codex gpt-6-astra rrsicastra; cell codex gpt-6.1-sol rrsicsol; cell codex gpt-6-luna rrsicluna; } &
{ cell vertexai_claude claude-sonnet-5-5 rrsicsonnet; cell vertexai_claude claude-opus-5-5 rrsicopus; } &
wait
echo "[lanes100] all done"
