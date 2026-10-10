# Reproducing "I gave each model the coding tools it was trained on"

Everything I ran for the post, as I ran it, plus one row per trial in `results/trials.csv`.
The scripts use the absolute paths of my machine (`/work/...`); change them to yours.

## What was measured

- **Tasks:** 12 held-out terminal tasks, one from each of 12 families, in `domain/heldout-tasks.tar.gz`.
  Each task gives the agent a few files; a hidden check (`domain/checker.py`) grades the result in a container without network access.
  Every configuration ran each task three times, so every configuration has 36 trials.
- **Agent:** one MindRoom agent named `coder` with MindRoom's `shell` and `coding` tools (or only `shell`), its commands running in a Docker worker.
- **Tokens:** input plus output tokens over every model request of a trial, from MindRoom's per-request `LLM usage` log lines.
  For the API path, these equal the usage the API reports; for Matrix, the analysis scripts read them per trial room from the runtime log.
- **Reasoning:** every configuration ran at its provider's default reasoning setting, except the effort runs, which set it explicitly.
  `results/trials.csv` has a `reasoning` column on every row:
  - `default (adaptive thinking)`: Claude Sonnet 5, Opus 5.5, and Sonnet 5.5, which think when they decide to;
  - `default (no thinking)`: Claude Opus 4.7 and 4.8, which do not think unless asked;
  - `default (Codex backend)`: GPT models with no reasoning effort sent, so the Codex backend's default applies;
  - `low (explicit)` and `high (explicit)`: the effort runs, with `reasoning_effort` for GPT and `output_config.effort` for Claude.

## Versions

| Part | Version |
|---|---|
| MindRoom with tool dialects | [PR #2766](https://github.com/mindroom-ai/mindroom/pull/2766) at commit `d73aafb51` (the first run used the branch a day earlier) |
| Native tools with 100-line output | `d73aafb51` plus `api/tail100.patch` |
| MindRoom main | release `v2026.10.228` (commit `1c594efa1`) |
| Worker images | `ghcr.io/mindroom-ai/mindroom:v2026.10.222` with the matching `src/mindroom` copied in (`worker/`); the dependencies did not change between these versions |
| Benchmark runner | [google-research/rrsi](https://github.com/google-research/rrsi) at commit `be50316e1db0`, with `domain/` as `domains/mindroom_dialects` |
| Matrix homeserver | `ghcr.io/mindroom-ai/mindroom-tuwunel:latest`, with open registration, on a local port |

## Steps

1. Clone rrsi, copy `domain/` to `domains/mindroom_dialects/`, and unpack `domain/heldout-tasks.tar.gz` into `domains/mindroom_dialects/data/`.
   `tasks.py` can also generate the tasks, but `git_archaeology` then gets new commit hashes.
2. Check out MindRoom at the versions above, run `uv sync --all-extras` in each, and build the worker images from `worker/`.
3. Put the model credentials where MindRoom finds them: the Codex CLI login for `provider: codex`, and the environment for Vertex AI for `provider: vertexai_claude` (the drivers source a local `vertex.env` with the project and region, which is not included).
4. Run a driver from `api/` for the API-path configurations.
   Each driver writes `base_config.yaml` (see `domain/base_config.example.yaml`) and `harness/agent.yaml` for one configuration, commits them, and runs `rrsi.py heldout` on that commit.
   - `driver-first-run.sh`: MindRoom tools against native tools (the first run), current models.
   - `driver-main-shell.sh`: MindRoom main with only the shell tool.
   - `driver-pr-head.sh`: MindRoom tools, native tools, and native tools with 100-line output, on `d73aafb51`.
   - `driver-shell.sh`: only the shell tool, in MindRoom's shape and in the native shape.
   - `driver-earlier.sh`: the same comparison on Claude Opus 4.7, Opus 4.8, and Sonnet 5, and GPT-5.5 and GPT-5.6 Sol.
   - `driver-effort.sh`: GPT-6 Astra and Claude Sonnet 5.5 at low and high reasoning effort.
5. For minimal mode, start the homeserver and run `matrix/lanes.sh`, which calls `matrix/matrix_eval.py` once per model.
   Each trial gets a fresh room with the agent and MindRoom's router; minimal trials send `!mode coder minimal` first.
   Set `RRSI_EVAL_PASSWORD` for the test user it registers.
6. Analyze with the scripts in `analysis/`:
   - `ci.py <base>,<other> ...`: the relative token change with a 95% bootstrap interval, and Fisher's exact test on passes;
   - `decompose.py`: the fixed part (first-request input times requests) and the work part of every trial;
   - `overhead.py` and `overhead_matrix.py`: requests per trial and the first request's input;
   - `make_csv.py`: `results/trials.csv`.
7. `probes/count_parts.py` measures the system prompt and the tool definitions on their own, from the provider's reported input tokens; it reads the prompts that `matrix/capture.py` records with MindRoom's `debug.log_llm_requests`.

## Notes

- During one run, the host's disk filled up, and five hidden checks failed with `No space left on device` although the agent had finished.
  I reran those five checks on the unchanged task directories; they are marked `regraded` in `results/trials.csv`.
- Claude's Matrix runs store only output tokens in MindRoom's run metrics, so the Matrix numbers come from the per-request log lines, which have the full input.
- With 36 trials per configuration, a difference of one or two solved tasks is noise.
