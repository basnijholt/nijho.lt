# Reproducing "Giving models the tools they were trained with can make them worse"

Everything I ran for the post, as I ran it, plus one row per trial in `results/trials.csv` and one row per model request in `results/requests.csv`.
The analysis scripts read only those two files, so they run anywhere; the scripts that run the experiments use the absolute paths of my machine (`/work/...`); change them to yours.

## What was measured

- **Tasks:** 12 held-out terminal tasks, one from each of 12 families, in `domain/heldout-tasks.tar.gz`.
  Each task gives the agent a few files; a hidden check (`domain/checker.py`) grades the result in a container without network access.
  A script-writing task passes only if the script prints the expected output and exits successfully.
  Every configuration ran each task three times, so every configuration has 36 trials.
- **Agent:** one MindRoom agent named `coder` with MindRoom's `shell` and `coding` tools (or only `shell`, or `coding` without some of its functions), its commands running in a Docker worker.
- **Minimal mode:** the same agent in a Matrix room after `!mode coder minimal`, with MindRoom's single `bash` tool, or, for the combination, with one native-shaped run tool from `matrix/minimal-native.patch`.
- **Tokens:** input plus output tokens over every model request of a trial, from MindRoom's per-request `LLM usage` log lines, with input including what the provider served from its cache.
  For the API path, these equal the usage the API reports; for Matrix, they come per trial room from the runtime log.
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
| Minimal mode with a native tool | `d73aafb51` plus `matrix/minimal-native.patch`, and `api/tail100.patch` for the 100-line arm; minimal mode with `bash` ran on the same code with the patch's flag off |
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
   The adapter accepts a tool as a plain name or as a name with `exclude_tools`, which MindRoom applies to that toolkit.
   - `driver-first-run.sh`: MindRoom tools against native tools (the first run), current models.
   - `driver-main-shell.sh`: MindRoom main with only the shell tool.
   - `driver-pr-head.sh`: MindRoom tools, native tools, and native tools with 100-line output, on `d73aafb51`.
   - `driver-fair-sets.sh`: each harness's own tools against MindRoom's matching set, on `d73aafb51`, for all ten models; `exclude_tools` drops `grep`, `find_files`, and `ls` from `coding`, and for GPT also `read_file`.
   - `driver-shell.sh`: only the shell tool, in MindRoom's shape and in the native shape.
   - `driver-earlier.sh`: the same comparison on Claude Opus 4.7, Opus 4.8, and Sonnet 5, and GPT-5.5 and GPT-5.6 Sol.
   - `driver-effort.sh`: GPT-6 Astra and Claude Sonnet 5.5 at low and high reasoning effort.
   - `driver-older-checks.sh`: the older models with only the shell tools, and Claude Opus 4.7 and 4.8 with adaptive thinking.
5. For minimal mode, start the homeserver and run `matrix/lanes.sh`, which calls `matrix/matrix_eval.py` once per model.
   Each trial gets a fresh room with the agent and MindRoom's router; minimal trials send `!mode coder minimal` first.
   Set `RRSI_EVAL_PASSWORD` for the test user it registers.
   For the combination, apply `matrix/minimal-native.patch` to the pull request (and `api/tail100.patch` in a second tree for the 100-line arm), then run `matrix/lanes-native.sh` and `matrix/lanes-native100.sh`, which call `matrix/matrix_eval_native.py`.
   The patch only acts when `MINDROOM_EXPERIMENT_MINIMAL_RUN_TOOL=1`, which the harness sets for the native arms.
6. Export the measurements with `analysis/make_csv.py`, the only script that reads the runtime logs and trial records.
   It writes `results/trials.csv` and `results/requests.csv`, and stops when a trial has no logged usage or cannot be matched to its requests.
   API log lines carry no trial id and the trials ran concurrently, so each trial's requests are the request group with its token total; every total matches exactly one group, and the three pairs of trials that share a total can swap labels in `requests.csv`, which changes no total.
   A trial with a request the provider reported no usage for keeps its pass but gets no tokens; there is one, a GPT-6 Luna run with the native tool in minimal mode.
7. Analyze with the scripts in `analysis/`, which read only those two files:
   - `ci.py <base>,<other> ...`: the relative token change with a 95% bootstrap interval, resampling the runs within each task, in total and without the input the provider served from its cache, and Fisher's exact test on passes;
   - `decompose.py`: the fixed part (first-request input times requests) and the rest of every trial, with requests per trial and the first request's input;
   - `reasoning_rates.py <configuration> ...`: how often Claude thought before a reply, and how often GPT reasoned before a request.
8. `probes/count_parts.py` measures the system prompt and the tool definitions on their own and together, from the provider's reported input tokens, counting cached input once whichever way the provider reports it; it reads the prompts that `matrix/capture.py` records with MindRoom's `debug.log_llm_requests`.

## Notes

- During one run, the host's disk filled up, and five hidden checks failed with `No space left on device` although the agent had finished.
  I reran those five checks on the unchanged task directories; they are marked `regraded` in `results/trials.csv`.
- Claude's Matrix runs store only output tokens in MindRoom's run metrics, so the Matrix numbers come from the per-request log lines, which have the full input.
- With 36 trials per configuration, a difference of one or two solved tasks is too small to tell apart from chance.
- The first grader accepted a script that printed the expected output and then exited with an error; regrading all 351 script-writing trials with the exit status required changed no verdict.
