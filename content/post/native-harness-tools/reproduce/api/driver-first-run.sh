#!/usr/bin/env bash
# Tool-dialect A/B: every model x {mindroom, auto} on the 12 held-out mindroom_dialects tasks, one trial each.
set -u
BRANCH=/work/t3-worktrees/mindroom/t3code-4c676a1b
CELLS=/work/rrsi-dialects/wt-cells
RUNS=/work/rrsi-dialects/runs
PY=$BRANCH/.venv/bin/python
set -a; . /work/rrsi-dialects/vertex.env; set +a
export MINDROOM_PY=$PY RRSI_WORKER_IMAGE=mindroom-rrsi-worker:dialects RRSI_LLM_BACKEND=codex TMPDIR=/work/tmp UV_CACHE_DIR=/work/cache/uv-bas
K="${K:-3}"
MODELS="${MODELS:-codex:gpt-6-luna vertexai_claude:claude-sonnet-5-5 codex:gpt-6.1-sol vertexai_claude:claude-opus-5-5 codex:gpt-6-astra}"
for spec in $MODELS; do
  provider=${spec%%:*}; model=${spec#*:}
  for dialect in mindroom auto; do
    label="${model//./_}-$dialect-k$K"
    if [ -f "$RUNS/mindroom_dialects/jobs/heldout_$label/eval.json" ]; then
      echo "[driver] skip $label (done)"; continue
    fi
    cat > "$CELLS/domains/mindroom_dialects/base_config.yaml" <<YAML
# Tool-dialect A/B cell $label: frozen environment; the adapter merges harness/agent.yaml in as agents.coder.
models:
  default:
    provider: $provider
    id: $model
    tool_dialect: $dialect
router:
  model: default
memory:
  backend: none
defaults:
  tools: []
YAML
    git -C "$CELLS" add domains/mindroom_dialects/base_config.yaml
    git -C "$CELLS" -c user.name="Bas Nijholt" -c user.email=bas@nijho.lt commit -q -m "cell $label" || true
    sha=$(git -C "$CELLS" rev-parse HEAD)
    echo "[driver] $(date +%H:%M:%S) start $label @ ${sha:0:7}"
    ( cd /work/rrsi-live/rrsi && "$PY" rrsi.py --domain mindroom_dialects --runs "$RUNS" --k "$K" heldout --label "$label" --ref "$sha" ) > "$RUNS-$label.log" 2>&1
    echo "[driver] $(date +%H:%M:%S) done $label rc=$? $(grep -o 'S=[0-9.]*' "$RUNS-$label.log" | tail -1)"
  done
done
echo "[driver] all cells done"
