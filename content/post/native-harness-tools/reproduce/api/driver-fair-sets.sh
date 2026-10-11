#!/usr/bin/env bash
# Fair tool sets on PR #2766 HEAD, through MindRoom's API: no MindRoom extras in either arm.
# Claude: shell + read/edit/write (Claude Code: Bash, Read, Edit, Write); GPT: shell + edit/write (Codex: exec_command + apply_patch).
set -u
CELLS=/work/rrsi-dialects/wt-cells
RUNS=/work/rrsi-dialects/runs
FULL=/work/t3-worktrees/mindroom/t3code-4c676a1b/.venv/bin/python
set -a; . /work/rrsi-dialects/vertex.env; set +a
export RRSI_WORKER_IMAGE=mindroom-rrsi-worker:head RRSI_LLM_BACKEND=codex TMPDIR=/work/tmp UV_CACHE_DIR=/work/cache/uv-bas
K=3
cell() {  # provider model dialect arm exclude-list
  local provider=$1 model=$2 dialect=$3 arm=$4 exclude=$5
  local label="${model//./_}-$arm-k$K"
  if [ -f "$RUNS/mindroom_dialects/jobs/heldout_$label/eval.json" ]; then echo "[fair] skip $label"; return; fi
  local sha
  sha=$(flock /work/rrsi-ablation/cells.lock bash -c "
    cat > '$CELLS/domains/mindroom_dialects/base_config.yaml' <<YAML
# Fair-set cell $label: frozen environment; the adapter merges harness/agent.yaml in as agents.coder.
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
# Tool-dialect A/B with each harness's own set and nothing else.
role: Terminal assistant that completes tasks in a Linux shell.
instructions:
  - Complete the user's task.
tools:
  - shell
  - coding:
      exclude_tools: [$exclude]
YAML
    git -C '$CELLS' add domains/mindroom_dialects/base_config.yaml domains/mindroom_dialects/harness/agent.yaml
    git -C '$CELLS' -c user.name='Bas Nijholt' -c user.email=bas@nijho.lt commit -q -m 'cell $label' || true
    git -C '$CELLS' rev-parse HEAD")
  echo "[fair] $(date +%H:%M:%S) start $label @ ${sha:0:7}"
  ( cd /work/rrsi-live/rrsi && MINDROOM_PY=$FULL "$FULL" rrsi.py --domain mindroom_dialects --runs "$RUNS" --k "$K" heldout --label "$label" --ref "$sha" ) > "$RUNS-$label.log" 2>&1
  echo "[fair] $(date +%H:%M:%S) done $label rc=$? $(grep -o 'S=[0-9.]*' "$RUNS-$label.log" | tail -1)"
}
gpt_lane() {
  for model in "$@"; do
    cell codex "$model" mindroom headfairmindroom "read_file, grep, find_files, ls"
    cell codex "$model" codex headfairnative "read_file, grep, find_files, ls"
  done
}
claude_lane() {
  for model in "$@"; do
    cell vertexai_claude "$model" mindroom headfairmindroom "grep, find_files, ls"
    cell vertexai_claude "$model" claude headfairnative "grep, find_files, ls"
  done
}
gpt_lane gpt-6-astra gpt-6.1-sol gpt-6-luna gpt-5.5 gpt-5.6-sol &
claude_lane claude-opus-5-5 claude-sonnet-5-5 &
claude_lane claude-opus-4-7 claude-opus-4-8 claude-sonnet-5 &
wait
echo "[fair] all done"
