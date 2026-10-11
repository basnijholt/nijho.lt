#!/usr/bin/env bash
# Earlier models on PR #2766 HEAD: MindRoom's tools vs the native harness tools (shell + coding).
set -u
CELLS=/work/rrsi-dialects/wt-cells
RUNS=/work/rrsi-dialects/runs
FULL=/work/t3-worktrees/mindroom/t3code-4c676a1b/.venv/bin/python
TAIL100=/work/rrsi-ablation/tail100/.venv/bin/python
set -a; . /work/rrsi-dialects/vertex.env; set +a
export RRSI_WORKER_IMAGE=mindroom-rrsi-worker:head RRSI_LLM_BACKEND=codex TMPDIR=/work/tmp UV_CACHE_DIR=/work/cache/uv-bas
K=3
cell() {  # provider model dialect arm python
  local provider=$1 model=$2 dialect=$3 arm=$4 py=$5
  local label="${model//./_}-$arm-k$K"
  if [ -f "$RUNS/mindroom_dialects/jobs/heldout_$label/eval.json" ]; then echo "[ablation] skip $label"; return; fi
  local sha
  sha=$(flock /work/rrsi-ablation/cells.lock bash -c "
    cat > '$CELLS/domains/mindroom_dialects/base_config.yaml' <<YAML
# Earlier-model cell $label: frozen environment; the adapter merges harness/agent.yaml in as agents.coder.
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
    cat > '$CELLS/domains/mindroom_dialects/harness/agent.yaml' <<YAML
# Tool-dialect A/B: the same agent with shell and coding; the eval driver varies models.default.
role: Terminal assistant that completes tasks in a Linux shell.
instructions:
  - Complete the user's task.
tools:
  - shell
  - coding
YAML
    git -C '$CELLS' add domains/mindroom_dialects/base_config.yaml domains/mindroom_dialects/harness/agent.yaml
    git -C '$CELLS' -c user.name='Bas Nijholt' -c user.email=bas@nijho.lt commit -q -m 'cell $label' || true
    git -C '$CELLS' rev-parse HEAD")
  echo "[ablation] $(date +%H:%M:%S) start $label @ ${sha:0:7}"
  ( cd /work/rrsi-live/rrsi && MINDROOM_PY=$py "$py" rrsi.py --domain mindroom_dialects --runs "$RUNS" --k "$K" heldout --label "$label" --ref "$sha" ) > "$RUNS-$label.log" 2>&1
  echo "[ablation] $(date +%H:%M:%S) done $label rc=$? $(grep -o 'S=[0-9.]*' "$RUNS-$label.log" | tail -1)"
}
lane() {
  for spec in "$@"; do
    provider=${spec%%:*}; rest=${spec#*:}; model=${rest%%:*}; native=${rest#*:}
    cell "$provider" "$model" mindroom headmindroom "$FULL"
    cell "$provider" "$model" "$native" headnative "$FULL"
  done
}
lane codex:gpt-5.5:codex codex:gpt-5.6-sol:codex &
lane vertexai_claude:claude-opus-4-7:claude vertexai_claude:claude-opus-4-8:claude vertexai_claude:claude-sonnet-5:claude &
wait
echo "[ablation] earlier models all done"
