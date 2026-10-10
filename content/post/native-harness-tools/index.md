---
title: "I gave each model the coding tools it was trained on. A single Bash tool won."
subtitle: "Claude got a little cheaper with Claude Code's tools, GPT used up to 31% more tokens with Codex's, and an agent with only one Bash tool used 58 to 76% fewer tokens than the same agent with its normal tools."
summary: "Every model is trained inside its vendor's own coding agent, so I expected it to work best with the same tools. I built tools that match Claude Code and Codex, switched automatically per model, and measured the result. It would have worked for the models of half a year ago, but today's models barely care, and what I found instead surprised me more."
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
This summer, that happened to Claude Opus 4.8 in pi, which I come back to [below](#why-it-went-wrong-in-pi).

So the idea was simple: give each model exactly the shell and file-editing tools of its native harness, and switch automatically depending on which model is answering.
Claude would see Claude Code's `Bash`, `Read`, `Edit`, and `Write`.
GPT would see Codex's `exec_command` and `apply_patch`.

I was beyond excited.
I could not really share that excitement locally, because my wife did not care, so I am sharing it with the internet instead.
I built it, measured it, and was wrong in a way I find much more interesting than if I had been right.

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

I tested five current models, Claude Opus 5.5, Claude Sonnet 5.5, GPT-6 Astra, GPT-6.1 Sol, and GPT-6 Luna, and later [five older ones](#older-models-needed-their-native-tools-more).
Almost every configuration solved almost every task, so the interesting number is how many tokens the agent needed to get there.[^tokens]

I left every model at its provider's default reasoning setting.
For the Claude models, that is adaptive thinking, where the model decides when to think; they thought before 15 to 25% of their replies.
On the Codex backend, GPT's default barely reasoned on these tasks: only 4 to 12% of requests had any reasoning tokens, and then a few dozen to about a hundred.

## Claude got a bit cheaper, GPT got more expensive

{{< plot name="nativeDelta" caption="Change in tokens per task when each model uses its native harness tools instead of MindRoom's, with 95% confidence intervals. The second row caps the shell output at the last 100 lines, like MindRoom's own shell tool does, and the third row gives the model only the shell tool. All models ran at their provider's default reasoning setting: adaptive thinking for Claude, and the Codex backend's default for GPT. Hover for values." >}}

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
These numbers come from the runs at each provider's default reasoning setting.

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
The older models I tested [later](#older-models-needed-their-native-tools-more) made a few errors with either set of tools: Sonnet 5 made two with MindRoom's tools, and GPT-5.5 seven with Codex's.

## Why it went wrong in pi

The case that got me thinking about this was Claude Opus 4.8 in pi.
In July, a pi user reported that [about 20% of its edits failed in some sessions](https://github.com/earendil-works/pi/issues/6278).
Pi's `edit` tool takes a list of replacements, and Opus 4.8 kept adding made-up fields to them, like `in_file`, `matchCase`, or `newText2`.
Claude Sonnet 5 did it too, while Opus 4.7 and older Claude models never did in the same tests.

Armin Ronacher, one of pi's maintainers, [dug into it](https://github.com/earendil-works/pi/issues/6278#issuecomment-4883362982) and compared it with what Claude Code does with the tool calls it receives.
It turns out that Claude Code quietly repairs a lot of them:

- It accepts several names for the same argument, like `old_str` and `old_string`.
- It parses an argument that arrives as a string when it should be an object.
- It fixes broken `\uXXXX` escapes in strings.
- It drops fields it does not know.
- When it cannot parse a call at all, it asks the model to try again.

His hypothesis is that RL itself might be the cause.
If a model is trained in a harness that absorbs these mistakes, a slightly wrong tool call still completes the task and still gets rewarded, so nothing teaches the model not to make it.
Pi [now ignores unknown fields too](https://github.com/earendil-works/pi/commit/a1b336d73e13b53949ff629800081185d3e4694e), just like Claude Code.[^strict]

This is the failure my idea was meant to prevent, and it did not show up in my runs.
I think the shape of the tools explains why.
The made-up fields always appeared inside pi's nested list of replacements, where the model has to write the JSON for each replacement itself.
MindRoom's `edit_file` is flat, like Claude Code's `Edit`: a path, the old text, and the new text.
So matching the exact names of a model's native tools seems to matter much less than keeping the tools as simple as those native tools are.

## Older models needed their native tools more

The pi story made me wonder whether this used to be different.
Opus 4.8 struggled with pi's edit tool while Opus 4.7 did not, and my newest models barely care what shape their tools have.
So I ran the same comparison on older models that are still available: Claude Opus 4.7, Opus 4.8, and Sonnet 5, and GPT-5.5 and GPT-5.6 Sol.

{{< plot name="generations" caption="Change in tokens per task when each model uses its native harness tools instead of MindRoom's, with 95% confidence intervals, oldest models first in each family. Every model ran at its provider's default reasoning setting, given in parentheses. Hover for values." >}}

The older models clearly did better with their native tools.
Opus 4.7, Opus 4.8, and Sonnet 5 used 22 to 36% fewer tokens with Claude Code's tools.
Unlike for the 5.5 models, that was not just the shorter definitions: they made fewer requests and did 26 to 45% less work on top of the fixed part.
GPT-5.6 Sol used 15% fewer tokens with Codex's tools, and GPT-5.5 about the same.
One generation later, the GPT-6 models use up to 31% more with Codex's tools, and the Claude 5.5 models only save what the shorter definitions save.
The pass rates stayed within one or two tasks of each other for every model.

So my idea would have worked half a year ago.
The newest models seem to have learned to use tools they were not trained on as well as their own.

One caveat: the older models did not run with the same reasoning as the new ones.
Opus 4.7 and 4.8 do not think unless you ask them to, and the GPT-5 models reasoned before 58 to 72% of their requests, while the GPT-6 models reasoned before only 4 to 12%.
I look at what the reasoning setting itself changes [below](#does-more-reasoning-change-this).

## Does more reasoning change this?

Everything so far ran at each provider's default reasoning setting.
So I also ran the two models with the clearest effect, Claude Sonnet 5.5 and GPT-6 Astra, at low and at high reasoning effort.[^effort]

| Model | Reasoning effort | MindRoom's tools | Native tools | Change |
|---|---|---|---|---|
| Claude Sonnet 5.5 | low | 15,154 | 12,330 | −19% [−23, −15] |
| Claude Sonnet 5.5 | default | 17,765 | 16,237 | −9% [−15, −1] |
| Claude Sonnet 5.5 | high | 18,286 | 15,630 | −15% [−19, −10] |
| GPT-6 Astra | low | 8,361 | 10,627 | +27% [+20, +34] |
| GPT-6 Astra | default | 8,250 | 10,807 | +31% [+24, +38] |
| GPT-6 Astra | high | 8,934 | 12,918 | +45% [+37, +52] |

Tokens per task, with 95% confidence intervals for the change; both models solved all 36 tasks in every row except one, where Astra with MindRoom's tools solved 35.

More reasoning did not make Codex's tools work better for GPT; it made them worse.
At high effort, Astra made 4.5 requests per task with Codex's tools against 3.6 with MindRoom's, and used 45% more tokens.
For Claude, the native tools stayed cheaper at every level, and saved the most at low effort, where Sonnet also made the fewest requests.
So the reasoning setting changes how many tokens a task takes, but not which tools are cheaper.
Sonnet's default behaved like its high setting, and Astra's default fell between low and high.

## Where minimal mode came from

Before the results, some background on the other half of this experiment.

[Pi](https://github.com/badlogic/pi-mono) made its name by being minimal.
When Mario Zechner [introduced it](https://mariozechner.at/posts/2025-11-30-pi-coding-agent/) last November, its system prompt and tool definitions together came in below 1,000 tokens, and it had four tools: `read`, `write`, `edit`, and `bash`.
He also wrote that "pi does not and will not support MCP", and he pointed to Terminus 2, a minimal agent from the Terminal-Bench team, which was "holding its own against agents with far more sophisticated tooling".

Pi 1.0 came out on October 1 and [added MCP after all](https://earendil.com/posts/pi-1-0/), through a sandbox called Codemode that also runs image models and non-LLM models like [Jev]({{< ref "/post/jev-mindroom" >}}).
[The Register](https://www.theregister.com/ai-and-ml/2026/10/02/pi-coding-agent-pulls-a-180-and-adds-mcp-support/5300678) called it a 180.
On [Hacker News](https://news.ycombinator.com/item?id=49926069) and [r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/comments/1wvffcr/pi_10_released_mcp_support_now_included_by_default/), people worried that ["Pi's days as a nice minimal agent TUI are numbered"](https://news.ycombinator.com/item?id=49926549).
What struck me was how the maintainers explained it.
[Armin Ronacher](https://news.ycombinator.com/item?id=49926377) wrote that the models "are trained on their respective harnesses and we're not here to fight their behavior", and [Mario Zechner](https://news.ycombinator.com/item?id=49926840) that "we follow what the models are trained on".
That is exactly the bet behind my tool dialects.

Then DeepSeek released [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness), which was [all over Hacker News](https://news.ycombinator.com/item?id=49285244) and the local AI subreddits I read.
Its standard setup comes with a full set of tools.
But for benchmarks, DeepSeek [points to its minimal profile](https://github.com/deepseek-ai/deepseek-harness/blob/d743267388641bc76f17c45ce8b4c231aed1d32c/BENCHMARK.md).
In early September, that profile had [exactly one tool, a persistent `bash`, and a one-line system prompt](https://github.com/deepseek-ai/deepseek-harness/blob/63795eaa5cba78cc0a92d95fccd8db5523d7f050/packages/bundle/sdk-minimal/README.md#L78-L84): "You are a helpful software engineer assistant."
That is what inspired MindRoom's minimal mode.
(Ten days later, DeepSeek's profile got a second tool, `working_directory`, so staying that small seems to be hard for everyone.)

Harness benchmarks like these already suggested that a model does not need its own harness to do well, so I was not sure the native tools would help on their own.
But I was sure that a minimal agent with only the native Bash tool would.

## Then I tried the opposite: one Bash tool

If tool definitions cost tokens on every request, fewer tools should be cheaper.
With only the shell tool and none of the file tools, the agent used 29 to 40% fewer tokens than with both, and solved the same tasks.[^shellonly]

This is where I expected the native tools to matter most: a model with nothing but a shell, in exactly the shape it knows from its own harness.
So I also gave Claude only Claude Code's `Bash`, `BashOutput`, and `KillShell`, and GPT only Codex's `exec_command` and `write_stdin`.
For GPT, it made no difference at all: Astra, Sol, and Luna used the same number of tokens, within a percent, and made the same number of requests.
Claude Sonnet 5.5 used 18% fewer tokens and Claude Opus 5.5 6% fewer, mostly because Claude Code's shell tools take fewer tokens to describe than MindRoom's.
The third row of the [first chart](#claude-got-a-bit-cheaper-gpt-got-more-expensive) shows these numbers.
So I was wrong about that too: the shape of the shell tool barely mattered.

MindRoom also has a [minimal mode](https://docs.mindroom.chat/tools/agent-cli/), which takes this all the way.
The agent gets a short prompt and a single `bash` tool instead of its normal prompt and tools.
It can still reach its other tools through a command-line program inside that shell, but for these tasks, all it needs is Bash.

Minimal mode only works in chat conversations, so I ran it through Matrix.
Next to it, I ran the same agent with only its shell tool in standard mode, also through Matrix.[^matrix]

{{< plot name="minimalSplit" caption="Tokens per task in Matrix conversations: the same agent with only MindRoom's shell tool, in standard mode and in minimal mode with a single Bash tool. The light part of each bar is the fixed part (the system prompt, the tool definitions, and the task, resent with every request), the dark part the work the model did on top of that. All models ran at their provider's default reasoning setting. Hover for values." >}}

The minimal agent used 58 to 76% fewer tokens than the same agent in standard mode, for every model.
Its first request dropped from about 4,600 to 1,000 input tokens for Claude, and from about 2,600 to 410 for GPT.
Astra and Sol also needed fewer requests, about 3.0 per task instead of 3.3 to 3.4.
Three of the five models solved one task fewer in minimal mode, mostly the same script-writing task that other configurations also miss now and then.
That is within the noise here, but I will keep an eye on it with harder tasks.

Is that a fair comparison?
Most of the difference is the prompt.
In standard mode, the system prompt is about 100 lines: 2,295 tokens for Claude Sonnet 5.5 and 1,463 for GPT-6 Astra.
The definitions of the shell's tools add another 1,292 and 867 tokens.
In minimal mode, the system prompt is 12 lines, 152 and 97 tokens, and the single `bash` tool adds 363 and 72 tokens.[^claudetools]
The model receives all of that again with every request, so it adds up: in standard mode, about 80% of all tokens were this fixed part.

A shorter prompt saves tokens even if the model then has to work harder, so the real question is whether it did.
To check, I split every task's tokens into the fixed part, which is the first request's input times the number of requests, and the rest: everything the model read and wrote while it worked.
Those are the light and dark parts of the bars in the chart above.
The work stayed the same for both Claude models (1% and 3% less), and went down for Astra and Sol (38% and 13% less).
Luna is the exception: it made more requests and did 40% more work in minimal mode, but the shorter prompt still more than paid for that.

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
- Most runs used each provider's default reasoning setting, which differs between models: Opus 4.7 and 4.8 do not think by default, and the GPT-5 models reasoned far more often than the GPT-6 models. The effort runs show that the setting changes the totals but not which tools are cheaper, but I only ran them for two models.

## Why this excites me

My idea was mostly wrong, and I am happy about that.
It means these models generalize much better than I gave them credit for.
They learned with one specific set of tools, and they work just as well with tools they have never seen, as long as those tools are simple and clearly described.
And that is new: Opus 4.8 and GPT-5.6 Sol still did noticeably better with their native tools.
What matters more than familiarity is how much the tools cost, because every tool definition is paid for again on every request.

It also changes how I think about who gets to build the best agents.
If models only worked well in the harness they were trained in, the labs would own the best agents by default.
Instead, the skills seem to carry over to other harnesses.
I suspect the same holds one level up, for how several agents work together.
The labs train their models in their own harness, but if what the models learn transfers this well, a harness built outside the labs, like MindRoom, could get just as good at letting agents collaborate.
That is a hunch, not a result, and testing it is what I want to do next.

## Appendix: how I measured, and all numbers

All scripts, the tasks, and one row per trial, with its reasoning setting, are [on GitHub next to this post's source](https://github.com/basnijholt/nijho.lt/tree/main/content/post/native-harness-tools/reproduce).

{{< detail-tag "Show the setup and every configuration" >}}

**Setup**

- Each configuration ran as a separate MindRoom instance with one agent and a fresh Docker container for its commands. The model, the tools, and everything else were fixed in that instance's configuration.
- The native tools and MindRoom's tools ran on the same code: the pull request at commit `d73aafb51`. The capped run changed only the output limit of the native shell tools. The shell-only and minimal-mode runs used MindRoom's main branch at release `v2026.10.228`.
- Tokens per task are the input and output tokens of every model request in that task, from MindRoom's per-request usage logs.
- The confidence intervals come from resampling the three runs of each task 5,000 times, keeping the mix of tasks fixed.

**Native tools against MindRoom's tools (pull request, through MindRoom's API, default reasoning)**

| Model | MindRoom's tools | Native tools | Native tools, 100-line output |
|---|---|---|---|
| Claude Opus 5.5 | 36/36 · 18,943 | 36/36 · 17,244 (−9%) | 36/36 · 17,410 (−8%) |
| Claude Sonnet 5.5 | 36/36 · 17,765 | 36/36 · 16,237 (−9%) | 36/36 · 16,399 (−8%) |
| GPT-6 Astra | 35/36 · 8,250 | 36/36 · 10,807 (+31%) | 35/36 · 10,399 (+26%) |
| GPT-6.1 Sol | 36/36 · 8,873 | 36/36 · 10,534 (+19%) | 36/36 · 10,239 (+15%) |
| GPT-6 Luna | 33/36 · 12,003 | 35/36 · 11,532 (−4%) | 36/36 · 10,816 (−10%) |

**Older models: native tools against MindRoom's tools (pull request, through MindRoom's API)**

| Model | Reasoning (provider default) | MindRoom's tools | Native tools |
|---|---|---|---|
| Claude Opus 4.7 | no thinking | 34/36 · 33,140 | 33/36 · 25,793 (−22%) |
| Claude Opus 4.8 | no thinking | 33/36 · 32,219 | 34/36 · 23,843 (−26%) |
| Claude Sonnet 5 | adaptive thinking | 33/36 · 42,349 | 34/36 · 27,120 (−36%) |
| GPT-5.5 | Codex backend default | 34/36 · 15,007 | 36/36 · 14,419 (−4%) |
| GPT-5.6 Sol | Codex backend default | 36/36 · 15,062 | 35/36 · 12,809 (−15%) |

**Only the shell tool: native shape against MindRoom's (pull request, through MindRoom's API, default reasoning)**

| Model | MindRoom's shell | Native shell |
|---|---|---|
| Claude Opus 5.5 | 36/36 · 12,926 | 36/36 · 12,202 (−6%) |
| Claude Sonnet 5.5 | 36/36 · 12,455 | 36/36 · 10,168 (−18%) |
| GPT-6 Astra | 36/36 · 6,025 | 36/36 · 6,052 (0%) |
| GPT-6.1 Sol | 36/36 · 6,195 | 36/36 · 6,177 (0%) |
| GPT-6 Luna | 31/36 · 7,118 | 34/36 · 7,018 (−1%) |

**Minimal mode against standard mode (main branch, through Matrix, shell tool only, default reasoning)**

| Model | Standard mode | Minimal mode |
|---|---|---|
| Claude Opus 5.5 | 36/36 · 22,192 | 36/36 · 8,030 (−64%) |
| Claude Sonnet 5.5 | 35/36 · 22,448 | 34/36 · 7,828 (−65%) |
| GPT-6 Astra | 36/36 · 11,429 | 36/36 · 2,798 (−76%) |
| GPT-6.1 Sol | 36/36 · 11,070 | 35/36 · 3,370 (−70%) |
| GPT-6 Luna | 35/36 · 12,568 | 34/36 · 5,219 (−58%) |

Each cell shows tasks solved out of 36, then tokens per task.

{{< /detail-tag >}}

[^strict]: Armin also found that Anthropic's strict tool mode, which restricts the model's output to the tool's schema, made these failures disappear in his tests. Pi later turned it on for Claude models, and a pi user then [linked a different problem to it](https://github.com/earendil-works/pi/issues/10074#issuecomment-6000381416): in that user's logs, 9.5% of Claude's edits had mangled `\u` escapes for non-ASCII text, such as Korean, with strict mode on, and 1.5% with it off.

[^claudetools]: Anthropic adds its own instructions for tool use to every request that has tools, which is why a single Bash tool costs Claude 363 tokens. I measured all four numbers by sending each part on its own and reading the input tokens the provider reported.

[^effort]: For GPT-6 Astra, I set `reasoning_effort` to `low` or `high`; for Claude Sonnet 5.5, `output_config.effort`, which is how the Claude 5.5 models take a reasoning effort. Even at high effort, Astra reasoned before only 10% of its requests, because these tasks are easy.

[^tasks]: The 12 tasks come from 12 families: a CSV report, finding the commit that broke a check, renaming an API across a package, counting errors in log files, fixing failing tests, finding files, extracting fields from JSON, writing a shell script, editing a configuration file, counting matching lines in very long command output, unpacking nested archives, and deduplicating and merging data files. I tune MindRoom's agent setup on other instances of these families, and these 12 were held out from that.

[^tokens]: Claude and GPT count tokens differently, so compare the numbers within one model, not across models.

[^shellonly]: This compares the agent with only the shell tool, on MindRoom's main branch, with the agent with shell and file tools from the pull request's first run. Both ran through MindRoom's API on the same tasks. With only the shell tool, Claude Opus 5.5 used 34% fewer tokens, Claude Sonnet 5.5 29%, GPT-6 Astra 29%, GPT-6.1 Sol 31%, and GPT-6 Luna 40%, and the pass rates stayed the same within one task.

[^matrix]: Each run got a fresh chat room with only the agent and MindRoom's router. For minimal mode, I switched the room over with `!mode coder minimal` before sending the task.
