#!/usr/bin/env bash
# Two lanes so Codex and Vertex models run side by side; each model gets its own runtime and namespace.
set -u
set -a; . /work/rrsi-dialects/vertex.env; set +a
export TMPDIR=/work/tmp RRSI_WORKER_IMAGE=mindroom-rrsi-worker:main
run_lane() {
  for spec in "$@"; do
    provider=${spec%%:*}; rest=${spec#*:}; model=${rest%%:*}; ns=${rest#*:}
    echo "[lanes] $(date +%H:%M:%S) start $model"
    nix-shell /work/rrsi-minimal/main/shell.nix --run "/work/rrsi-minimal/main/.venv/bin/python -I /work/rrsi-minimal/matrix_eval.py $provider $model $ns 3" > "/work/rrsi-minimal/lane-$ns.log" 2>&1
    echo "[lanes] $(date +%H:%M:%S) done $model rc=$?"
  done
}
run_lane codex:gpt-6-luna:rrsimluna codex:gpt-6.1-sol:rrsimsol codex:gpt-6-astra:rrsimastra &
run_lane vertexai_claude:claude-sonnet-5-5:rrsimsonnet vertexai_claude:claude-opus-5-5:rrsimopus &
wait
echo "[lanes] all done"
