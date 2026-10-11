#!/usr/bin/env bash
# Two checks of the older-model result on PR #2766 HEAD, through MindRoom's API:
# 1. shell tools only, MindRoom's shape against the native one, so no file tools mix the two;
# 2. Claude Opus 4.7 and 4.8 with adaptive thinking, the default of the 5.5 models, with shell and coding tools.
set -u
CELLS=/work/rrsi-dialects/wt-cells
RUNS=/work/rrsi-dialects/runs
FULL=/work/t3-worktrees/mindroom/t3code-4c676a1b/.venv/bin/python
set -a; . /work/rrsi-dialects/vertex.env; set +a
export RRSI_WORKER_IMAGE=mindroom-rrsi-worker:head RRSI_LLM_BACKEND=codex TMPDIR=/work/tmp UV_CACHE_DIR=/work/cache/uv-bas
K=3
cell() {  # provider model dialect arm tools extra_kwargs-yaml
  local provider=$1 model=$2 dialect=$3 arm=$4 tools=$5 extra=$6
  local label="${model//./_}-$arm-k$K"
  if [ -f "$RUNS/mindroom_dialects/jobs/heldout_$label/eval.json" ]; then echo "[checks] skip $label"; return; fi
  local tool_lines
  tool_lines=$(for t in $tools; do printf '  - %s\n' "$t"; done)
  local sha
  sha=$(flock /work/rrsi-ablation/cells.lock bash -c "
    cat > '$CELLS/domains/mindroom_dialects/base_config.yaml' <<YAML
# Older-model check $label: frozen environment; the adapter merges harness/agent.yaml in as agents.coder.
models:
  default:
    provider: $provider
    id: $model
    tool_dialect: $dialect
$extra
router:
  model: default
memory:
  backend: none
defaults:
  tools: []
YAML
    cat > '$CELLS/domains/mindroom_dialects/harness/agent.yaml' <<YAML
# Tool-dialect A/B: the same agent; the eval driver varies models.default and the tools.
role: Terminal assistant that completes tasks in a Linux shell.
instructions:
  - Complete the user's task.
tools:
$tool_lines
YAML
    git -C '$CELLS' add domains/mindroom_dialects/base_config.yaml domains/mindroom_dialects/harness/agent.yaml
    git -C '$CELLS' -c user.name='Bas Nijholt' -c user.email=bas@nijho.lt commit -q -m 'cell $label' || true
    git -C '$CELLS' rev-parse HEAD")
  echo "[checks] $(date +%H:%M:%S) start $label @ ${sha:0:7}"
  ( cd /work/rrsi-live/rrsi && MINDROOM_PY=$FULL "$FULL" rrsi.py --domain mindroom_dialects --runs "$RUNS" --k "$K" heldout --label "$label" --ref "$sha" ) > "$RUNS-$label.log" 2>&1
  echo "[checks] $(date +%H:%M:%S) done $label rc=$? $(grep -o 'S=[0-9.]*' "$RUNS-$label.log" | tail -1)"
}
shell_lane() {
  for spec in "$@"; do
    provider=${spec%%:*}; rest=${spec#*:}; model=${rest%%:*}; native=${rest#*:}
    cell "$provider" "$model" mindroom headshellmindroom "shell" ""
    cell "$provider" "$model" "$native" headshellnative "shell" ""
  done
}
ADAPTIVE="    extra_kwargs:
      thinking:
        type: adaptive"
thinking_lane() {
  for model in "$@"; do
    cell vertexai_claude "$model" mindroom headmindroom-thinkadaptive "shell coding" "$ADAPTIVE"
    cell vertexai_claude "$model" claude headnative-thinkadaptive "shell coding" "$ADAPTIVE"
  done
}
shell_lane codex:gpt-5.5:codex codex:gpt-5.6-sol:codex &
shell_lane vertexai_claude:claude-opus-4-7:claude vertexai_claude:claude-opus-4-8:claude vertexai_claude:claude-sonnet-5:claude &
thinking_lane claude-opus-4-7 claude-opus-4-8 &
wait
echo "[checks] all done"
