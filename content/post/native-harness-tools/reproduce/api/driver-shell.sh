#!/usr/bin/env bash
# Shell-only arm on PR #2766 HEAD: only the shell tool, in MindRoom shape vs the native harness shape.
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
# Shell-only cell $label: frozen environment; the adapter merges harness/agent.yaml in as agents.coder.
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
# Shell-only arm: the same agent with only the shell tool; the eval driver varies models.default.
role: Terminal assistant that completes tasks in a Linux shell.
instructions:
  - Complete the user's task.
tools:
  - shell
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
    cell "$provider" "$model" mindroom headshellmindroom "$FULL"
    cell "$provider" "$model" "$native" headshellnative "$FULL"
  done
}
lane codex:gpt-6-astra:codex codex:gpt-6.1-sol:codex codex:gpt-6-luna:codex &
lane vertexai_claude:claude-opus-5-5:claude vertexai_claude:claude-sonnet-5-5:claude &
wait
echo "[ablation] shell-only all done"
