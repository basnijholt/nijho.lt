---
title: "Trying RRSI's self-improving agent harnesses on MindRoom"
subtitle: "Two days of automated harness search on MindRoom: better shell instructions, two bug fixes, and a CLI that wasted a third of its calls"
summary: "Google's RRSI evolves an agent's harness (prompts, tools, config) against a benchmark while guarding against overfitting. I pointed it at MindRoom agents. It did find better instructions, but the most valuable results were the bugs and the CLI friction that the evaluation exposed, and the fixes went into MindRoom itself."
date: 2026-10-02
draft: true
featured: false
authors:
  - admin
tags:
  - ai
  - agents
  - mindroom
  - rrsi
  - evaluation
  - agentic-coding
  - claude-code
  - codex
  - gpt-6
  - open-source
categories:
  - AI
  - open-source
  - level:advanced
---

On September 21, Google Research published [RRSI: Regularized Recursive Self-Improvement of Agent Harnesses](https://arxiv.org/abs/2609.24972), with [code on GitHub](https://github.com/google-research/rrsi).
The idea is simple and appealing.
An agent's capability depends not only on the model but on its harness: the prompts, tools, control flow, memory, and context management around a frozen model.
RRSI lets LLMs edit that harness, evaluates every edit on a benchmark, and keeps only the edits that survive a set of statistical guardrails.

I build [MindRoom]({{< ref "/post/mindroom" >}}), where every agent is defined by a block of YAML: its role, instructions, tools, and a few settings.
That YAML is exactly a harness.
So I pasted the RRSI link into Claude Code and asked: "how to use this with MindRoom?"

Two days, several thousand agent trials, and four merged pull requests later, I have a clear answer.
RRSI works, and it found real improvements.
But the improvements it found in the prompt were the smallest part of the value.
The evaluation harness I had to build for it turned out to be a microscope, and most of what it showed me was wrong with MindRoom itself.

{{< toc >}}

## 1. What RRSI does

RRSI runs a loop of rounds.
In each round, an analyst model reads the failing trajectories and ranks failure modes.
A proposer model drafts two candidate harnesses, each a small set of edits in its own git worktree.
A critic model screens each candidate for anything that smells like memorizing the benchmark: task IDs, specific answers, references to the grader.
Then both candidates are evaluated on the full evolve set, and at most one replaces the incumbent.

What makes it "regularized" is how strict the selection is:

- **A noise floor.** A candidate only counts as better if it beats the incumbent by more than the measured noise of the evaluation, called δ.
- **A cost rule.** If a candidate uses more tokens, the score gain has to pay for them.
- **A shaped rule inside the noise band.** A candidate that is not measurably better survives only by cutting tokens or by adding a new kind of mechanism.
- **An edit budget** that shrinks over time, and **pruning** of components that stop helping.

The paper's point is that unregularized harness search overfits: it memorizes the training tasks, and the gains vanish on new ones.
So every run ends with a held-out set (new instances of the same kinds of task) and, ideally, an out-of-distribution set (new kinds of task).

To plug MindRoom in, I wrote an RRSI `Domain` adapter.
Each candidate harness is merged into a frozen `config.yaml` (the model stays fixed), a fresh MindRoom instance boots per job, and every trial gets fresh storage so memory cannot leak between tasks.
I ran RRSI's own three roles on GPT-6 Astra through my Codex login, and the agent being evolved on GPT-6 Luna.[^setup]

## 2. A toy benchmark finds bugs, not learnings

The first run used 36 small arithmetic and counting tasks, with MindRoom's calculator tool available.
It was quick to build, and it was a mistake.

Evaluating the unchanged harness twice gave 0.833 and 0.875.
That 4-point swing on identical inputs set the noise band at about 0.08, and nothing RRSI proposed beat it.
Six rounds and eleven candidates later, the only accepted change was `markdown: false`, which saved a few percent of tokens.
RRSI did its job: every expensive candidate got rejected, and every "best" evolve score shrank back on the held-out set.

But the run surfaced four MindRoom bugs:

- The calculator silently turned large integers into floats: `multiply(9734184429, 764243911)` came back as `7.439291178414262e+18`.
- The calculator could only do one operation per model round trip, so summing 31 numbers took 31 requests and about 25,000 tokens instead of 684.
- MindRoom's OpenAI-compatible `/v1` endpoint always reported `usage` as zero, which is a problem when RRSI's cost rule runs on token counts.
- Tool-call markers like `🔧 multiply [1]` landed in `/v1` replies and broke clients that expect strict JSON.

When I read this summary, my reaction was: the calculator is a toy tool, why are we optimizing that?
Nobody needs an agent that multiplies.
What MindRoom agents actually do all day is run shell commands.
So we dropped the calculator and moved to the shell.

**Lesson: benchmark the work your agents actually do.**
A toy benchmark is fine as a smoke test of the pipeline, but it will not teach the harness anything useful.

## 3. The shell benchmark

The second benchmark had 12 families of small terminal jobs, each with a hidden check that runs in a throwaway container with no network after the agent finishes:
summarizing a messy CSV, counting errors in a web log, fixing a Python package until its tests pass, finding a commit with `git bisect`, renaming a function across a package, extracting values from JSON, finding files by size, digging through nested archives, writing a small script, changing one value in a config file without touching any other byte, extracting a count from a command that prints megabytes of output, and merging two CSVs.

The agent's shell ran in MindRoom's Docker workers, the same isolation boundary production uses.
That immediately found a fifth bug: in a dedicated worker, `HOME` still pointed at the primary's host home directory, so `cd ~` failed, `git config --global` failed, and the host path leaked into the sandbox.

The first version of the suite was too easy: the unchanged agent passed 97% of trials, leaving nothing to optimize.
I made the tasks harder in the ways real data is hard (inconsistent case and whitespace, quoted fields, files without a trailing newline, comments that look like settings) until the baseline dropped to about 0.9.

Then RRSI ran six rounds.

| Harness | Evolve set (36 tasks × 4 trials) | Held-out set (12 tasks × 4 trials) | Tokens per held-out trial |
|---|---|---|---|
| Original | 0.896 | 0.938 | 8,100 |
| After round 0 | 0.993 | 1.000 | 10,357 |
| After six rounds | 0.986 | 1.000 | 10,221 |

Almost all of the gain came in round 0, from instructions alone.
RRSI kept the same tools and added six general working rules, which read like advice from a careful senior engineer:

- compute relative paths with a path API, not by slicing strings;
- apply filters to the extracted field, not the whole line, and check them on sample records;
- sample large outputs with `head` or `grep`, but compute over the full input;
- keep file boundaries when combining inputs, because a file may lack its final newline;
- when every other byte must stay, replace only the value and read the file back;
- after a rename, search for the old name and run the tests.

What RRSI refused was just as interesting.
Adding the `python` tool cost 21% more tokens for no gain, since the shell already runs Python.
Turning on `compress_tool_results` cost 18 to 21% more, because compressing tool results takes extra model calls, which is more than it saves on short shell output.
The cost rule caught both.

I also made a configuration mistake.
I had set the weight on in-band score changes (`w_s`) to 100, so a 0.7-point "gain", about one trial, outweighed a 4% token increase, and RRSI accepted a change on noise.
RRSI's own coding instance sets that weight to 0 for exactly this reason: inside the noise band, only a cheaper or structurally new harness should win.

## 4. Putting the learnings into the product

The evolved harness is one agent's YAML.
Copying six instructions into every agent would help nobody who writes their own config.

So I distilled the rules into a 140-word "working method" at the end of the description of MindRoom's `run_shell_command` tool.
Every agent with the shell toolkit now sees it whenever the tool schema is sent, with no configuration.[^note]

Then I built eight new kinds of terminal job the search had never seen (SQLite queries, dependency ordering, regex extraction, splitting files, Markdown tables, debugging environment variables, applying diffs, syncing directories) to test whether the note transfers.

| Harness | Out-of-distribution set (24 tasks × 4 trials) | Tokens per trial |
|---|---|---|
| MindRoom before the note | 0.979 | 5,980 |
| With the note | 1.000 | 7,155 |
| Full evolved harness | 0.990 | 8,340 |

The note did not hurt on new kinds of work, and the full evolved harness did not beat it.
On the held-out set it did not help either: 0.938 before and after, because it fixed the config-edit failures but a JSON extraction task started failing twice.
That is the honest result: a modest, general improvement, not a breakthrough.

A rerun with `w_s` set to 0 and a larger set (60 tasks × 3 trials) showed the same shape: a real early gain from instructions (0.928 to 0.989 in two rounds), then three rounds of rejections.
It rediscovered the same rules, plus one more: decode a field's syntax (quotes, case, `yes`/`no` and null sentinels) before filtering on it.

**Lesson: harness search front-loads its gains.**
Both runs got nearly everything in the first two rounds, from general working habits.
After that, RRSI mostly rejects candidates, which is exactly what its guardrails are for.

## 5. Minimal mode, and the question I should have asked

MindRoom has a minimal mode: instead of dozens of tool schemas, the model sees one `bash` tool and a short system message.
Every other toolkit is still available through a `mindroom-agent` CLI inside the shell: `tools search`, `tools describe`, `tools call`.
It exists to keep prompts small for agents with many tools.

`/v1` cannot reach minimal mode, so I drove MindRoom through Matrix instead: a local homeserver, one room per trial, `!mode coder minimal`, the task, and the hidden check after the reply finished.
Getting minimal mode to run on my machine took some plumbing.
The host firewall blocks containers from reaching host ports, so worker traffic to MindRoom went through a relay container and Unix sockets.
My first gateway proxy exposed FastAPI's default `/docs` page, and the worker's isolation probe refused to install the CLI, which is exactly what it should do.

On the 96 shell tasks, the result looked like a clean win for minimal mode:

| | Standard mode | Minimal mode |
|---|---|---|
| Pass rate (216 trials) | 0.944 | 0.958 |
| Tokens per trial | 15,962 | 4,317 |
| Median seconds per trial | 18.7 | 23.2 |

The same accuracy at 27% of the tokens.
I was ready to recommend minimal mode as the default for shell-heavy agents.

Then I asked: "But you said it never used anything else than the shell tool, anyway?"
Right.
Minimal mode's `mindroom-agent` CLI was called zero times in 216 trials.
The comparison showed that a small prompt beats a large prompt for shell-only work, and nothing about the part that makes minimal mode different.

## 6. A benchmark for tools the shell cannot reach

So we built a third benchmark: 48 jobs that each need a MindRoom toolkit running outside the worker, where the shell cannot do the job.
React to a specific earlier message.
Start a thread, or reply inside an existing one.
Read a build number from a thread or a codename from the room's state.
Schedule a one-time or weekly task.
Compute a CSV report and send it as an attachment.
Two toolkits, todo lists and thread tags, appear only in the out-of-distribution set, so the agent has to discover tools it has never needed.

The grader checks the Matrix room, the room state, and MindRoom's stored state, so writing "done" in the reply does not count.

| | Standard mode | Minimal mode |
|---|---|---|
| Pass rate (128 trials) | 0.930 | 0.922 |
| Tokens per trial | 26.9k | 31.5k |
| Uncached input tokens per trial | 4.2k | 12.1k |
| Median seconds per trial | 14 | 46 |
| Tool calls per trial | 2.5 | 9.8 (all `bash`) |

Minimal mode reached a toolkit through the CLI in 126 of 128 trials, including the two toolkits the other tasks never needed.
But it was three times slower and used three times the uncached input.

The interesting part was where those extra calls went.
Of 1,254 `bash` calls, 36% were CLI overhead:

| Overhead | Calls |
|---|---|
| `tools call` returned `queued`, so the model needed a separate `calls wait` | 244 |
| `toolkit.function` names rejected as invalid arguments | 54 |
| `tools describe` called with only a toolkit name | 38 |
| JSON arguments passed without `--json` | 35 |
| `mindroom-agent tools` without an action | 27 |
| Wrong function or argument names, answered with "Tool is unavailable or arguments are invalid" or "Invalid Agent CLI operation" | 51 |

That last row cost real failures: in one trial the model guessed `send` instead of `matrix_message`, got the same vague error three times, and gave up on attaching the file it had computed correctly.

## 7. Fix the product, not the prompt

The obvious next step was to run RRSI on `minimal_instructions`, the text minimal mode puts in the system message.
It would probably have found something like "always wait on the call ID in the same command."
But that would teach one agent to work around a clumsy CLI, and every other agent would keep paying for it.

So I fixed the CLI instead, highest impact first and nothing else:[^pr]

1. `tools call` now waits up to 30 seconds for the result, so a normal call takes one command; `--timeout 0` keeps the old behavior for scripts that submit several calls at once.
2. A wrong function name now says what the toolkit does contain: `Toolkit 'matrix_message' has no function 'send'; its functions: matrix_message`.
3. `toolkit.function` names and a trailing JSON argument are accepted, since that is how models naturally write the call.

Then I reran all 128 minimal-mode trials:

| Minimal mode | Before | After |
|---|---|---|
| Pass rate | 0.922 | 0.930 |
| Tokens per trial | 31.5k | 21.1k |
| `bash` calls per trial | 9.8 | 7.3 |
| Separate `calls wait` round trips | 240 | 0 |

A third fewer tokens, and minimal mode now uses fewer tokens in total than standard mode on tool work too, though still more uncached input.
It is still slower, because every call still goes through the shell.

The rerun also caught a regression from my own fix.
Accepting `toolkit.function` turned an old mistake, `tools call matrix_room.matrix_room '{...}'`, into a misleading error, `No toolkit 'matrix_room.matrix_room'`, 18 times.
Measuring again after fixing turned that into one more small commit.

**Lesson: count the failure classes before choosing a fix.**
The table above is just `grep` over trajectories, and it made the priorities obvious.

## 8. Who did what

Claude Code with Opus 5.5 did nearly all of the work: the domain adapters, the three benchmarks with validated reference solutions, the Matrix driver, every run, and the pull requests.
Each PR was reviewed by two independent models before I merged it: GPT-6 Astra running in a separate worktree through [`agent-cli dev`]({{< ref "/post/parallel-agentic-coding" >}}), and a fresh Opus agent that had not seen the implementation.

They caught real problems that the other one missed.
In the `HOME` fix, both found that my first version broke `HOME` for agents that do have a workspace.
In the usage fix, Opus found that cached input was missing for Claude providers after Astra had already approved it.
In the CLI fix, both found that the friendlier error never reached `tools describe` in production, because the authorization step looks up the name first.
A third bot reviewer on GitHub found one more edge case and also made a claim that was wrong, which is why every review comment gets verified before it gets fixed.

My own contribution was mostly three sentences at the right moments: the calculator is a toy, the comparison never used anything but the shell, and don't overcorrect.
Each of them changed the direction of the work more than any single RRSI round did.

## 9. What I took away

**Measure the noise first.**
Two evaluations of the same harness differed by 4 points on 36 tasks.
Below a few hundred trials, most "improvements" are noise, and RRSI's noise floor is the most important guardrail it has.

**Use tasks that look like the real work, and hide the checks.**
The calculator benchmark taught the harness nothing.
The shell benchmark taught it habits that transferred to new kinds of jobs.

**Expect the first round to do most of the work.**
In both shell runs, general working habits gave nearly all of the gain, and later rounds mostly confirmed that there was nothing left within the noise.

**The evaluation harness is the product.**
Four merged MindRoom PRs came out of this: zero `/v1` usage, the worker `HOME`, the shell working method, and the minimal-mode CLI fixes in [#2530](https://github.com/mindroom-ai/mindroom/pull/2530).[^prs]
None of them was an evolved prompt.
All of them came from building an honest benchmark, running it, and reading the trajectories.

**Ask what a comparison does not test.**
Minimal mode looked four times cheaper until I noticed that the benchmark never exercised the one thing that makes it different.

[^setup]: The frozen policy was GPT-6 Luna (`gpt-6-luna`) through MindRoom's `codex` provider, and RRSI's analyst, proposer, and critic ran on GPT-6 Astra (`gpt-6-astra`) through the same Codex login, which needed a small backend added to RRSI's LLM client. For the shell runs, each candidate was evaluated with 3 or 4 trials per task, and the noise band δ came either from a bootstrap over the trials of one baseline evaluation or from repeated baseline evaluations. One lesson there: two repeated baselines that happen to agree give a δ that is too small. In the 60-task rerun, two baselines landed 0.006 apart and gave δ = 0.011, while the bootstrap on the same data suggested about 0.046.

[^note]: The note ends the `run_shell_command` description: "Working method: inspect inputs first, sampling large files or outputs with head, tail, grep, or wc instead of printing everything, but compute results over the full input. Match filters against the extracted field value, not the whole line, and check them on a few sample records. When combining the lines or words of several text files, do not concatenate them raw [...] When only one value must change, replace just that span and keep every other byte, including comments and spacing. Afterwards verify the result: read outputs back, search for leftover old names after a rename, run available tests, and recheck suspicious results such as a zero count." The first draft said "never concatenate files raw", and both reviewers pointed out that this would discourage legitimate joins of a split file, so the rule now covers only text files. See [#2518](https://github.com/mindroom-ai/mindroom/pull/2518).

[^pr]: The rule I gave was to do the highest-impact fixes first and not to overcorrect. Left out on purpose: listing a toolkit's functions from `tools describe TOOLKIT`, schema details in "Invalid tool arguments" (two occurrences in 128 trials), and a case where redirecting a tool's output to a file hid its error (one occurrence). The most common remaining failure, posting in the wrong thread, happened equally in both modes; it is a model weakness, not a CLI problem.

[^prs]: [#2491](https://github.com/mindroom-ai/mindroom/pull/2491) reports real token usage from `/v1`, [#2493](https://github.com/mindroom-ai/mindroom/pull/2493) keeps the worker's own `HOME`, [#2518](https://github.com/mindroom-ai/mindroom/pull/2518) adds the shell working method, and [#2530](https://github.com/mindroom-ai/mindroom/pull/2530) makes the minimal-mode CLI wait for calls and name a toolkit's functions. The calculator bugs I left alone, since nobody should be using MindRoom's calculator for arithmetic anyway.
