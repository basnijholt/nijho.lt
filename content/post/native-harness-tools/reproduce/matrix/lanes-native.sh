#!/usr/bin/env bash
# Minimal mode on the tool-dialect pull request, with minimal Bash and with one native-shaped run tool.
# Two lanes so Codex and Vertex models run side by side; each (model, arm) gets its own runtime and namespace.
# Arms alternate their order between models so neither always runs first.
set -u
set -a; . /work/rrsi-dialects/vertex.env; set +a
export TMPDIR=/work/tmp RRSI_WORKER_IMAGE=mindroom-rrsi-worker:head
cell() {  # provider model namespace arm
  echo "[lanes] $(date +%H:%M:%S) start $2 $4"
  nix-shell /work/rrsi-minimal/native/shell.nix --run "/work/rrsi-minimal/native/.venv/bin/python -I /work/rrsi-minimal/matrix_eval_native.py $1 $2 $3 $4 3" > "/work/rrsi-minimal/lane-$3.log" 2>&1
  echo "[lanes] $(date +%H:%M:%S) done $2 $4 rc=$?"
}
codex_lane() {
  cell codex gpt-6-astra rrsinastra headminimalnative; cell codex gpt-6-astra rrsibastra headminimal
  cell codex gpt-6.1-sol rrsibsol headminimal; cell codex gpt-6.1-sol rrsinsol headminimalnative
  cell codex gpt-6-luna rrsinluna headminimalnative; cell codex gpt-6-luna rrsibluna headminimal
}
vertex_lane() {
  cell vertexai_claude claude-sonnet-5-5 rrsibsonnet headminimal; cell vertexai_claude claude-sonnet-5-5 rrsinsonnet headminimalnative
  cell vertexai_claude claude-opus-5-5 rrsinopus headminimalnative; cell vertexai_claude claude-opus-5-5 rrsibopus headminimal
}
codex_lane & vertex_lane &
wait
echo "[lanes] all done"
