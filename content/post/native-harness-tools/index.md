---
title: "I gave each model the coding tools it was trained on. A single Bash tool won."
subtitle: "Claude got a little cheaper with Claude Code's tools, GPT used up to 31% more tokens with Codex's, and an agent with only one Bash tool used 58 to 76% fewer tokens than the same agent with its normal tools."
summary: "Every model is trained inside its vendor's own coding agent, so I expected it to work best with the same tools. I built tools that match Claude Code and Codex, switched automatically per model, and measured the result. The idea mostly did not work out, and what I found instead surprised me more."
date: 2026-10-10
draft: true
featured: false
authors:
  - admin
tags:
  - ai
  - agentic-coding
  - mindroom
  - model-reviews
categories:
  - AI
  - Software Development
  - level:intermediate
---

A few nights ago, lying in bed, I had what felt like a galaxy-brain idea.
I dictated it into my watch so I would still remember it in the morning.

Every frontier model learns to write code with reinforcement learning (RL), inside its vendor's own coding agent.
Anthropic's models learn in Claude Code, and OpenAI's models learn in Codex.
Every other harness, like [pi](https://github.com/badlogic/pi-mono), [opencode](https://opencode.ai/), or [MindRoom]({{< ref "/post/mindroom" >}}), gives the model its own tools for running commands and editing files.
The models are usually smart enough to figure those out, but not always.
Sometimes a model assumes an edit tool works like the one it was trained with, and uses it wrong.

So the idea was simple: give each model exactly the shell and file-editing tools of its native harness, and switch automatically depending on which model is answering.
Claude would see Claude Code's `Bash`, `Read`, `Edit`, and `Write`.
GPT would see Codex's `exec_command` and `apply_patch`.

My wife did not share my excitement.
So I built it, measured it, and was wrong in a way I find much more interesting than if I had been right.

{{< toc >}}

## What I built

MindRoom is my open-source platform for AI agents that live in Matrix chat rooms.
Its agents get shell and file tools under MindRoom's own names, like `run_shell_command`, `read_file`, and `edit_file`.

In [this pull request](https://github.com/mindroom-ai/mindroom/pull/2766), I added what I call tool dialects.
A model now sees those tools in the shape of the coding agent it was trained in:

| Model | Sees | Instead of |
|---|---|---|
| Claude | `Bash`, `BashOutput`, `KillShell`, `Read`, `Edit`, and `Write`, as in Claude Code | `run_shell_command`, `check_shell_command`, `kill_shell_command`, `read_file`, `edit_file`, and `write_file` |
| GPT | `exec_command`, `write_stdin`, and a freeform `apply_patch`, as in Codex | `run_shell_command`, `check_shell_command`, `edit_file`, and `write_file` |

Inside MindRoom, nothing changes: approvals, hooks, and the stored history keep MindRoom's names.
The translation only happens on the way to and from the model.
That way, a conversation can switch from Claude to GPT halfway through, and each model sees the earlier tool calls in its own shape.
For `apply_patch`, I ported Codex's patch parser and the code that applies patches, together with Codex's own test cases, so a patch from a Codex-trained model applies exactly as it would in Codex.

"Exactly" turned out to be a stretch, though.
The tools have the same names, arguments, and descriptions as in Claude Code and Codex.
But what they return is MindRoom's output, and the system prompt is MindRoom's too.
An earlier version of the pull request also rewrote every tool result to look like the native one.
That was a lot of fragile code, so I removed it before I measured anything.
Keep this in mind for everything below: I tested the tools, not the whole harness.

## How I measured it

I used 12 terminal tasks from an evaluation suite I built for MindRoom.[^tasks]
Each task gives the agent a few files and asks for a result: a report from a CSV file, the first commit in a git history that broke a check, a function renamed across a package, failing tests fixed, and so on.
A hidden check grades the result in a separate container without network access.
Every task ran three times per configuration, so each number below comes from 36 runs.
The agent's commands ran in a Docker container, the way MindRoom runs agents it does not fully trust.

I tested five models: Claude Opus 5.5, Claude Sonnet 5.5, GPT-6 Astra, GPT-6.1 Sol, and GPT-6 Luna.
Almost every configuration solved almost every task, so the interesting number is how many tokens the agent needed to get there.[^tokens]

## Claude got a bit cheaper, GPT got more expensive

{{< plot name="nativeDelta" caption="Change in tokens per task when each model uses its native harness tools instead of MindRoom's, with 95% confidence intervals. The second row caps the shell output at the last 100 lines, like MindRoom's own shell tool does. Hover for values." >}}

With Claude Code's tools, both Claude models used about 9% fewer tokens.
With Codex's tools, GPT-6 Astra used 31% more tokens and GPT-6.1 Sol 19% more.
An earlier run of the same experiment, before some unrelated fixes in the pull request, gave almost the same numbers: 33% more for Astra and 15% more for Sol.
For GPT-6 Luna, the difference was too small to tell apart from noise.

The pass rates barely moved.
Opus, Sonnet, and Sol solved all 36 tasks with either set of tools, and Astra missed one task in some configurations.
Luna solved 33 tasks with MindRoom's tools and 35 with Codex's.
In the earlier run it was the other way around, 35 against 32, so I read that as noise too.

## It is not the longer output

There was one obvious suspect.
MindRoom's own shell tool returns the last 100 lines of a command's output.
For the native tools, I returned everything up to 50 KiB, because that is closer to what Claude Code and Codex do.
More output means more tokens, so I ran everything again with the native tools capped at the same 100 lines.

That is the second row in the chart above.
The cap barely changes anything: Astra still uses 26% more tokens, Sol 15% more, and the Claude models still save about 8%.
It turns out the models hardly ever print more than 100 lines anyway.
In the first run, 3 of Astra's 91 shell results were longer than that, and none of Claude's 223.

## Where the tokens went

Every request to a model sends the whole conversation so far, plus the definition of every tool the model can use.
So the first request of a task shows what a set of tools costs before the model has done any work.

| Model | Requests per task, MindRoom → native | First request in input tokens, MindRoom → native |
|---|---|---|
| Claude Opus 5.5 | 3.94 → 3.94 | 3,696 → 3,218 |
| Claude Sonnet 5.5 | 3.78 → 3.92 | 3,702 → 3,216 |
| GPT-6 Astra | 3.53 → 4.00 | 1,628 → 1,762 |
| GPT-6.1 Sol | 3.72 → 4.00 | 1,628 → 1,762 |
| GPT-6 Luna | 4.86 → 3.86 | 1,628 → 1,762 |

Claude did not work any differently with Claude Code's tools.
It made about the same number of requests, and its savings match the roughly 480 tokens by which the definitions of Claude Code's tools are shorter than MindRoom's.

GPT did work differently.
With Codex's tools, Astra and Sol made 0.3 to 0.5 more requests per task, and each request carried a bit more.
I expected the opposite.
These are the tools these models were trained on, so I thought they would need fewer and more confident steps.

## The mistakes I wanted to prevent barely happened

The whole idea started from models using unfamiliar tools wrong.
In these runs, that did not happen with MindRoom's tools at all: none of the five models made a single tool error in its 36 tasks.
The only model that made tool errors was Luna, and only with the Codex tools: 7 errors in 36 tasks.
Most of them were `read_file` calls with a path relative to the directory Luna had just given `exec_command`.
Codex has no tool for reading files, so Luna had to guess how mine worked, and guessed wrong.
Mixing a model's native tools with tools it has never seen created exactly the kind of mistake I wanted to get rid of.

## Then I tried the opposite: one Bash tool

If tool definitions cost tokens on every request, fewer tools should be cheaper.
With only the shell tool and none of the file tools, the agent used 29 to 40% fewer tokens than with both, and solved the same tasks.[^shellonly]

MindRoom also has a [minimal mode](https://docs.mindroom.chat/tools/agent-cli/), which takes this all the way.
The agent gets a short prompt and a single `bash` tool instead of its normal prompt and tools.
It can still reach its other tools through a command-line program inside that shell, but for these tasks, all it needs is Bash.

Minimal mode only works in chat conversations, so I ran it through Matrix.
Next to it, I ran the same agent with only its shell tool in standard mode, also through Matrix.[^matrix]

{{< plot name="minimalTokens" caption="Tokens per task in Matrix conversations: the same agent with only MindRoom's shell tool, in standard mode and in minimal mode with a single Bash tool. Hover for values." >}}

The minimal agent used 58 to 76% fewer tokens than the same agent in standard mode, for every model.
Its first request dropped from about 4,600 to 1,000 input tokens for Claude, and from about 2,600 to 410 for GPT.
Astra and Sol also needed fewer requests, about 3.0 per task instead of 3.3 to 3.4.
Three of the five models solved one task fewer in minimal mode, mostly the same script-writing task that other configurations also miss now and then.
That is within the noise here, but I will keep an eye on it with harder tasks.

So models that were trained with a carefully designed set of tools did best with almost no tools at all.

## What I changed

By default, the pull request now gives Claude models Claude Code's tools, because they are a little cheaper.
Every other model keeps MindRoom's own tools.
The Codex tools are still there for anyone who wants them, with `tool_dialect: codex` in a model's configuration.
And I am going to use minimal mode a lot more.

## What this does and does not show

- I tested tool names, arguments, and descriptions, not whole harnesses. Codex also has its own system prompt, its own output format, and an interactive terminal, and RL trains all of that together. The full harness might still help; matching only the tools did not.
- The tasks are easy enough that almost every configuration solved all of them. Harder tasks might separate the tool sets on success, not only on cost.
- With 36 runs per configuration, a 15 to 30% difference in tokens is clear, but a difference of one or two solved tasks is not.
- The token counts include cached input, which providers charge much less for, so the difference in cost is smaller than the difference in tokens.
- The same agent uses more tokens in a Matrix conversation than through MindRoom's API, because it gets more context about the conversation. That is why I only compare minimal mode with standard mode in Matrix.

## Why this excites me

My idea was mostly wrong, and I am happy about that.
It means these models generalize much better than I gave them credit for.
They learned with one specific set of tools, and they work just as well with tools they have never seen, as long as those tools are simple and clearly described.
What matters more than familiarity is how much the tools cost, because every tool definition is paid for again on every request.

It also changes how I think about who gets to build the best agents.
If models only worked well in the harness they were trained in, the labs would own the best agents by default.
Instead, the skills seem to carry over to other harnesses.
I suspect the same holds one level up, for how several agents work together.
The labs train their models in their own harness, but if what the models learn transfers this well, a harness built outside the labs, like MindRoom, could get just as good at letting agents collaborate.
That is a hunch, not a result, and testing it is what I want to do next.

## Appendix: how I measured, and all numbers

{{< detail-tag "Show the setup and every configuration" >}}

**Setup**

- Each configuration ran as a separate MindRoom instance with one agent and a fresh Docker container for its commands. The model, the tools, and everything else were fixed in that instance's configuration.
- The native tools and MindRoom's tools ran on the same code: the pull request at commit `d73aafb51`. The capped run changed only the output limit of the native shell tools. The shell-only and minimal-mode runs used MindRoom's main branch at release `v2026.10.228`.
- Tokens per task are the input and output tokens of every model request in that task, from MindRoom's per-request usage logs.
- The confidence intervals come from resampling the three runs of each task 5,000 times, keeping the mix of tasks fixed.

**Native tools against MindRoom's tools (pull request, through MindRoom's API)**

| Model | MindRoom's tools | Native tools | Native tools, 100-line output |
|---|---|---|---|
| Claude Opus 5.5 | 36/36 · 18,943 | 36/36 · 17,244 (−9%) | 36/36 · 17,410 (−8%) |
| Claude Sonnet 5.5 | 36/36 · 17,765 | 36/36 · 16,237 (−9%) | 36/36 · 16,399 (−8%) |
| GPT-6 Astra | 35/36 · 8,250 | 36/36 · 10,807 (+31%) | 35/36 · 10,399 (+26%) |
| GPT-6.1 Sol | 36/36 · 8,873 | 36/36 · 10,534 (+19%) | 36/36 · 10,239 (+15%) |
| GPT-6 Luna | 33/36 · 12,003 | 35/36 · 11,532 (−4%) | 36/36 · 10,816 (−10%) |

**Minimal mode against standard mode (main branch, through Matrix, shell tool only)**

| Model | Standard mode | Minimal mode |
|---|---|---|
| Claude Opus 5.5 | 36/36 · 22,192 | 36/36 · 8,030 (−64%) |
| Claude Sonnet 5.5 | 35/36 · 22,448 | 34/36 · 7,828 (−65%) |
| GPT-6 Astra | 36/36 · 11,429 | 36/36 · 2,798 (−76%) |
| GPT-6.1 Sol | 36/36 · 11,070 | 35/36 · 3,370 (−70%) |
| GPT-6 Luna | 35/36 · 12,568 | 34/36 · 5,219 (−58%) |

Each cell shows tasks solved out of 36, then tokens per task.

{{< /detail-tag >}}

[^tasks]: The 12 tasks come from 12 families: a CSV report, finding the commit that broke a check, renaming an API across a package, counting errors in log files, fixing failing tests, finding files, extracting fields from JSON, writing a shell script, editing a configuration file, counting matching lines in very long command output, unpacking nested archives, and deduplicating and merging data files. I tune MindRoom's agent setup on other instances of these families, and these 12 were held out from that.

[^tokens]: Claude and GPT count tokens differently, so compare the numbers within one model, not across models.

[^shellonly]: This compares the agent with only the shell tool, on MindRoom's main branch, with the agent with shell and file tools from the pull request's first run. Both ran through MindRoom's API on the same tasks. With only the shell tool, Claude Opus 5.5 used 34% fewer tokens, Claude Sonnet 5.5 29%, GPT-6 Astra 29%, GPT-6.1 Sol 31%, and GPT-6 Luna 40%, and the pass rates stayed the same within one task.

[^matrix]: Each run got a fresh chat room with only the agent and MindRoom's router. For minimal mode, I switched the room over with `!mode coder minimal` before sending the task.
