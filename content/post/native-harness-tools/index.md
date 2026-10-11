---
title: "Giving models the tools they were trained with can make them worse"
subtitle: "Today's models don't get more efficient with the tools of their own coding harness, and GPT-6 Astra and Sol use 43 to 59% more tokens with them. What matters is how much the agent sends: a minimal agent used 58 to 76% fewer tokens on these short tasks."
summary: "I assumed every model is trained inside its vendor's own coding agent, so I expected it to work best with the same tools, and best of all in a minimal agent with nothing but its native shell. Over more than 4,000 runs of 12 short terminal tasks, the native tools made only one model clearly more efficient, Claude Opus 4.8, made GPT-6 Astra and Sol use 43 to 59% more tokens, and the minimal agent won on its own."
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

Every frontier model learns to solve coding tasks with tools through reinforcement learning (RL), and I assume that training happens inside its vendor's own coding agent: Anthropic's models in Claude Code, and OpenAI's models in Codex.
That is a big assumption, since the labs do not publish their training environments, but it makes business sense: they sell those agents, so they have every reason to make their models work best in them.
Every other harness, like [pi](https://github.com/badlogic/pi-mono), [opencode](https://opencode.ai/), or my own [MindRoom]({{< ref "/post/mindroom" >}}), gives the model its own tools for running commands and editing files.
The models are usually smart enough to figure those out, but not always.
Sometimes a model assumes an edit tool works like the one it was trained with, and uses it wrong.
This summer, that happened to Claude Opus 4.8 in pi, which I come back to [below](#why-i-believed-it).

So the idea was simple: in MindRoom, give each model the same shell and file-editing tools as its native harness, and switch them automatically depending on which model is answering.
Claude would see Claude Code's `Bash`, `Read`, `Edit`, and `Write`.
GPT would see Codex's `exec_command` and `apply_patch`.
And because the smallest agents do surprisingly well, I would go one step further: a minimal agent whose one tool is the shell each model knows from its training.

I was beyond excited.
I could not really share that excitement locally, because my wife did not care, so I am sharing it with the internet instead.

Then I measured it, and familiar tools did not make the models more efficient.
With only Codex's tools, GPT-6 Astra even used 59% more tokens, and the Claude models saved a little, mostly because the descriptions I wrote for their tools are shorter.
Only one model clearly worked more efficiently with its own tools: Claude Opus 4.8, the model from the pi story.
The models seem to generalize beyond the environment they were trained in, and what still matters is how much the agent sends with every request.

{{% callout note %}}
**What I found**

- Familiar tools did not make the models more efficient: GPT-6 Astra and Sol used 43 to 59% more tokens with only Codex's tools, and the Claude 5.5 models saved 6 to 13%, mostly from shorter tool descriptions.
- Only Claude Opus 4.8, the model whose edits kept failing in pi, clearly worked more efficiently with its own tools.
- What matters is how much the agent sends with every request: a minimal agent with one shell tool and a 12-line prompt used 58 to 76% fewer tokens on these short tasks.
- Giving that minimal agent each model's own shell tool did not make it better.
{{% /callout %}}

{{< toc >}}

## What a harness is

"Harness" gets thrown around a lot, but there is no magic in it.
Every coding agent talks to the model the same way: each request contains a system prompt, the definition of every tool the model may call, and the conversation so far.
When the model answers with a tool call, the harness runs the tool, adds the result to the conversation, and sends everything again.

<figure class="harness-diagram" style="max-width: 460px; margin: 2rem auto;">
<svg viewBox="0 0 380 470" role="img" aria-label="One request holds the system prompt, the tool definitions, and the conversation so far. The model answers with a tool call, the harness runs it, adds the result to the conversation, and sends the whole request again." style="width: 100%; height: auto; font-family: system-ui, sans-serif;">
<defs><marker id="harness-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L8,4 L0,8 z" fill="currentColor"/></marker></defs>
<rect x="10" y="10" width="250" height="210" rx="10" fill="none" stroke="currentColor" stroke-opacity="0.45"/>
<text x="22" y="32" font-size="14" font-weight="700" fill="currentColor">One request to the model</text>
<rect x="22" y="44" width="226" height="48" rx="6" fill="#97bbf5" fill-opacity="0.45"/>
<text x="34" y="64" font-size="13" font-weight="600" fill="currentColor">System prompt</text>
<text x="34" y="81" font-size="11" fill="currentColor" fill-opacity="0.8">who the agent is, how it should work</text>
<rect x="22" y="100" width="226" height="48" rx="6" fill="#97bbf5" fill-opacity="0.45"/>
<text x="34" y="120" font-size="13" font-weight="600" fill="currentColor">Tool definitions</text>
<text x="34" y="137" font-size="11" fill="currentColor" fill-opacity="0.8">name, description, and arguments</text>
<rect x="22" y="156" width="226" height="52" rx="6" fill="#4269d0" fill-opacity="0.35"/>
<text x="34" y="177" font-size="13" font-weight="600" fill="currentColor">Conversation so far</text>
<text x="34" y="194" font-size="11" fill="currentColor" fill-opacity="0.8">the task, every tool call, every result</text>
<path d="M268 46 h6 v100 h-6" fill="none" stroke="currentColor" stroke-opacity="0.6"/>
<text x="281" y="88" font-size="11" fill="currentColor">the same on</text>
<text x="281" y="102" font-size="11" fill="currentColor">every request</text>
<path d="M268 158 h6 v48 h-6" fill="none" stroke="currentColor" stroke-opacity="0.6"/>
<text x="281" y="170" font-size="11" fill="currentColor">grows with</text>
<text x="281" y="184" font-size="11" fill="currentColor">every step</text>
<line x1="135" y1="220" x2="135" y2="246" stroke="currentColor" marker-end="url(#harness-arrow)"/>
<rect x="85" y="250" width="100" height="40" rx="20" fill="currentColor" fill-opacity="0.1" stroke="currentColor" stroke-opacity="0.45"/>
<text x="135" y="275" font-size="13" font-weight="700" text-anchor="middle" fill="currentColor">Model</text>
<line x1="186" y1="270" x2="214" y2="270" stroke="currentColor" stroke-opacity="0.6" marker-end="url(#harness-arrow)"/>
<text x="220" y="274" font-size="11" fill="currentColor" fill-opacity="0.8">or a final answer</text>
<line x1="135" y1="290" x2="135" y2="318" stroke="currentColor" marker-end="url(#harness-arrow)"/>
<rect x="35" y="322" width="200" height="46" rx="6" fill="none" stroke="currentColor" stroke-opacity="0.45"/>
<text x="47" y="341" font-size="13" font-weight="600" fill="currentColor">A tool call</text>
<text x="47" y="358" font-size="11" fill="currentColor" fill-opacity="0.8" font-family="ui-monospace, monospace">Bash: ls data/</text>
<line x1="135" y1="368" x2="135" y2="394" stroke="currentColor" marker-end="url(#harness-arrow)"/>
<rect x="35" y="398" width="200" height="46" rx="6" fill="none" stroke="currentColor" stroke-opacity="0.45"/>
<text x="47" y="417" font-size="13" font-weight="600" fill="currentColor">The harness runs it</text>
<text x="47" y="434" font-size="11" fill="currentColor" fill-opacity="0.8">and adds the result</text>
<path d="M235 421 H355 V199 H264" fill="none" stroke="currentColor" stroke-dasharray="4 3" marker-end="url(#harness-arrow)"/>
<text x="347" y="300" font-size="11" fill="currentColor" text-anchor="middle" transform="rotate(-90 347 300)">sent again, all of it</text>
</svg>
<figcaption>What a coding agent sends with every step. The light parts are the same every time; only the conversation grows.</figcaption>
</figure>

So from the model's side, a harness is three things: its system prompt, its tool definitions, and what comes back when a tool runs.
The first two are just text, so they are easy to copy, and the tool definitions are effectively the harness's API: change them, and the model sees a different harness.
The third is code, which takes more work to copy.

## Why I believed it

Two things convinced me: how well the smallest agents do, and what goes wrong when a model meets unfamiliar tools.

### Smaller agents do better

Pi made its name by being small.
When Mario Zechner [introduced pi](https://mariozechner.at/posts/2025-11-30-pi-coding-agent/) last November, its system prompt and tool definitions together came in below 1,000 tokens, and it had four tools: `read`, `write`, `edit`, and `bash`.
He also wrote that "pi does not and will not support MCP", the Model Context Protocol through which most agents load outside tools.
And he pointed to Terminus 2, a minimal agent from the Terminal-Bench team, which was "holding its own against agents with far more sophisticated tooling".

In August, DeepSeek released [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness), which was [all over Hacker News](https://news.ycombinator.com/item?id=49285244) and the local AI subreddits I read.
Its standard setup comes with a full set of tools.
But for benchmarks, DeepSeek [points to its minimal profile](https://github.com/deepseek-ai/deepseek-harness/blob/d743267388641bc76f17c45ce8b4c231aed1d32c/BENCHMARK.md).
In early September, that profile had [exactly one tool, a persistent `bash`, and a one-line system prompt](https://github.com/deepseek-ai/deepseek-harness/blob/63795eaa5cba78cc0a92d95fccd8db5523d7f050/packages/bundle/sdk-minimal/README.md#L78-L84): "You are a helpful software engineer assistant."
(Ten days later, it already had a second tool, `working_directory`.)
That is what inspired the minimal mode I added to MindRoom in September, which gives an agent a short prompt and a single `bash` tool.

### Models should know their own tools best

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

Staying that small seems to be hard for everyone, and then pi itself switched sides.
Pi 1.0 came out on October 1 and [added MCP after all](https://earendil.com/posts/pi-1-0/), through a sandbox called Codemode that also runs image models and non-LLM models like [Jev]({{< ref "/post/jev-mindroom" >}}).
[The Register](https://www.theregister.com/ai-and-ml/2026/10/02/pi-coding-agent-pulls-a-180-and-adds-mcp-support/5300678) called it a 180.
On [Hacker News](https://news.ycombinator.com/item?id=49926069) and [r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/comments/1wvffcr/pi_10_released_mcp_support_now_included_by_default/), people worried that ["Pi's days as a nice minimal agent TUI are numbered"](https://news.ycombinator.com/item?id=49926549).
What struck me was how the maintainers explained it.
[Armin Ronacher](https://news.ycombinator.com/item?id=49926377) wrote that the models "are trained on their respective harnesses and we're not here to fight their behavior", and [Mario Zechner](https://news.ycombinator.com/item?id=49926840) that "we follow what the models are trained on".
That is exactly the native-tools half of my plan.

My plan combined both: a minimal agent, with each model's native shell as its one tool.
Terminal-Bench also said something I chose to ignore: agents like Terminus 2 do well with tools no model was trained on.
I did not believe that part.
In opencode and pi, I had repeatedly seen models get the edit tool wrong, so I assumed the benchmarks did not carry over to real work.
My belief that a model works best in the harness it was trained in was that strong: I expected the native tools to help, and to help most in a minimal agent with nothing but a shell.

## What I built

MindRoom is my open-source platform for AI agents that live in Matrix chat rooms.
Its agents get shell and file tools under MindRoom's own names, like `run_shell_command`, `read_file`, and `edit_file`.
In [this pull request](https://github.com/mindroom-ai/mindroom/pull/2766), I added what I call tool dialects: a model now sees those tools in the shape of the coding agent it was trained in.

| Model | Sees | Instead of |
|---|---|---|
| Claude | `Bash`, `BashOutput`, `KillShell`, `Read`, `Edit`, and `Write`, as in Claude Code | `run_shell_command`, `check_shell_command`, `kill_shell_command`, `read_file`, `edit_file`, and `write_file` |
| GPT | `exec_command`, `write_stdin`, and a freeform `apply_patch`, as in Codex, and a `kill_shell_command` that takes Codex's `session_id` | `run_shell_command`, `check_shell_command`, `kill_shell_command`, `edit_file`, and `write_file` |

Inside MindRoom, nothing changes: approvals, hooks, and the stored history keep MindRoom's names, and the translation only happens on the way to and from the model.
That gives MindRoom a property I like a lot: a conversation can switch from Claude to GPT halfway through, and each model sees the earlier tool calls in its own shape, as if it had made them in its own harness.

Matching the native harness exactly turned out to be a stretch, though.
Codex has no tool for reading files, so in the pull request, GPT keeps MindRoom's `read_file`, and both keep MindRoom's `grep`, `find_files`, and `ls`, which makes each native set a mix.
For the main comparison, I removed those extra tools, so each model saw only the tools of its own harness.
The tools have the same names and arguments as in Claude Code and Codex, but I wrote short descriptions of my own, because Claude Code's are not openly licensed.
What they return is MindRoom's output, and the system prompt is MindRoom's too.
So keep in mind for everything below: I tested the names and shapes of the tools, not the whole harness.

{{< detail-tag "How the translation works" >}}

- Codex's `apply_patch` is freeform: the model writes the patch as plain text instead of JSON arguments. I ported Codex's patch parser and the code that applies patches, together with Codex's own test cases, so a patch from a Codex-trained model applies exactly as it would in Codex. Its description comes from Codex too, which is openly licensed.
- A switched model sees earlier calls in its own shape only for the tools its own harness also has, like the shell: an edit made with Claude Code's `Edit` stays an `edit_file` call for GPT, which has no matching tool.
- An earlier version of the pull request also rewrote every tool result to look like the native one. That was a lot of fragile code, so I removed it before I measured anything.

{{< /detail-tag >}}

## How I measured it

I used 12 terminal tasks from an evaluation suite I built for MindRoom, like writing a report from a CSV file, finding the commit that broke a check, or fixing failing tests.[^tasks]
A hidden check graded each result, and every setup ran every task three times.
Almost every run passed, so the interesting number is how many tokens the agent needed to get there, cached input included, and cheaper below means fewer tokens.[^tokens]
I tested five current models, Claude Opus 5.5 and Sonnet 5.5, and GPT-6 Astra, GPT-6.1 Sol, and GPT-6 Luna, and later [five older ones](#older-models-only-opus-48-needed-them).
The current Claude models ran with adaptive thinking, where the model decides when to think, and GPT with the reasoning effort the Codex backend picks when none is set.

{{< detail-tag "Details of the setup" >}}

- A small harness sent each task to MindRoom's OpenAI-compatible API as a new conversation, and a hidden check graded the result in a separate container without network access. Every task ran three times per configuration, so each number in this post comes from 36 runs.
- The agent's commands ran in a Docker container, the way MindRoom runs agents it does not fully trust.
- With adaptive thinking, the current Claude models thought before 15 to 25% of their replies, with MindRoom's tools and with the native ones.
- I ran the GPT models through OpenAI's Codex backend, the endpoint the Codex CLI uses, and sent no reasoning effort, so the backend picked one. The GPT-6 models barely reasoned on these tasks: in those runs, only 4 to 12% of their requests had any reasoning tokens, and then 7 to 234 of them.

{{< /detail-tag >}}

## Native tools don't make today's models more efficient

To make the comparison fair, I gave each model only the tools of its own harness, against MindRoom's matching set.[^fair]
For Claude, that is a shell and tools to read, edit, and write files; for GPT, a shell and Codex's `apply_patch`, against MindRoom's tools to edit and write files.

{{< plot name="fairCurrent" caption="Change in tokens per task when each model uses its native harness tools instead of MindRoom's, with 95% confidence intervals: with only the harness's own tools against MindRoom's matching set, and with the mixed set the pull request ships. Claude ran with adaptive thinking, and GPT with the effort Codex picks. Hover for values." >}}

Claude got a little cheaper with Claude Code's tools, but mostly because the descriptions I wrote for them are shorter.
It never even touched the file tools: Opus 5.5 and Sonnet 5.5 did everything in the shell, with either set.

GPT got much more expensive.
With only Codex's tools, GPT-6 Astra used 59% more tokens.
It called `apply_patch` 30 times, as a separate step for edits it otherwise made inside its shell commands, and every extra step resends the whole conversation so far.
I expected the opposite: these are the tools I assumed these models were trained on, so I thought they would need fewer and more confident steps.
The mixed set, the lighter rows, points the same way.

The tool mistakes I wanted to prevent did not happen with MindRoom's tools at all: with its matching set, none of the five models made a single tool error.
The only errors came from the mixed set: next to Codex's tools, Luna had to guess how MindRoom's `read_file` resolves paths, and got it wrong seven times.

{{< detail-tag "The numbers behind this section" >}}

**Fixed part and work.**
Every request to a model sends the whole conversation so far, plus the definition of every tool the model can use.
So I split each task's tokens in two.
The fixed part is the first request's input, which holds the system prompt, the tool definitions, and the task, times the number of requests.
The work is everything else: tool results and the model's replies, counted again with every later request that resends them, so it also grows with the number of steps.
Providers cache most of the fixed part between requests and charge much less for cached input, so it costs less than its share of the tokens suggests.

**Only the harness's own tools.**
With Claude Code's tools, Opus 5.5 used 13% fewer tokens [95% CI −19 to −6%] and Sonnet 5.5 6% fewer [−10 to −1%].
Both came mostly from the definitions: the Claude Code-style set I wrote is about 480 tokens shorter, while the work on top of it grew by 7 and 15%.
With Codex's tools, GPT-6 Astra used 59% more tokens [+53 to +65%] and GPT-6.1 Sol 43% more [+33 to +52%].
They called `apply_patch` 30 and 22 times, where with MindRoom's tools they made only 3 and 6 calls to the file tools, so they needed 4.7 and 4.4 requests per task instead of 3.5 and 3.6 and did 84 and 60% more work.
GPT-6 Luna used about the same with either set, +3% [−8 to +15%], and called `apply_patch` only 8 times.
The pass rates stayed within one or two runs of each other, and no model made a tool error with either set.

**The mixed set, as the pull request ships it.**

{{< plot name="nativeDelta" caption="Change in tokens per task when each model uses its native harness tools instead of MindRoom's, with 95% confidence intervals. The second row caps the native shell output at the last 100 lines, MindRoom's shell default. Claude ran with adaptive thinking, and GPT with the reasoning effort the Codex backend picks when none is set. Hover for values." >}}

With Claude Code's tools, both Claude models used about 9% fewer tokens.
With Codex's tools, GPT-6 Astra used 31% more tokens and GPT-6.1 Sol 19% more.
An earlier run of the same experiment, before some unrelated fixes in the pull request, gave almost the same numbers: 33% more for Astra and 15% more for Sol.
For GPT-6 Luna, the difference was too small to tell apart from noise.
The pass rates barely moved: Opus, Sonnet, and Sol passed all 36 runs with either set of tools, and Astra failed one run in some configurations.
Luna passed 33 runs with MindRoom's tools and 35 with Codex's; in the earlier run it was the other way around, 35 against 32, so I would not read anything into it either.

**It is not the longer output.**
MindRoom's own shell tool returns the last 100 lines of a command's output by default.
For the native tools, I returned everything up to 50 KiB, because that is closer to what Claude Code and Codex do.
So I ran everything again with the native tools capped at the same 100 lines, the second row in the chart above.
The cap barely changes anything: Astra still uses 26% more tokens, Sol 15% more, and the Claude models still save about 8%.
The models hardly ever print more than 100 lines anyway: in the uncapped run, 3 of Astra's 91 shell results and 3 of Sol's 93 were longer than that, and none of Claude's 220.

**Where the tokens went with the mixed set.**

{{< plot name="tokenSplit" caption="Tokens per task with MindRoom's shell and file tools and with the native ones, split into the fixed part (light) and the work the model did on top of it (dark). Claude ran with adaptive thinking, and GPT with the reasoning effort the Codex backend picks when none is set. Hover for the number of requests." >}}

Claude did not work any differently with Claude Code's tools.
It never called a file tool with either set, did everything in the shell, and made about the same number of requests.
Its work changed by 5% or less, and almost all of its savings come from the fixed part: the Claude Code-style definitions I wrote are about 480 tokens shorter than MindRoom's.

GPT did work differently.
With Codex's tools, Astra and Sol edited files with `apply_patch` 17 and 15 times, where with MindRoom's tools they made only 3 and 5 calls to the file tools and did the rest from the shell.
Each patch is a request of its own, which accounts for their 0.3 to 0.5 extra requests per task.
They also did 51% and 24% more work.
And Codex's tools take about 130 more tokens to describe than MindRoom's, because `apply_patch` costs about 270 more than `edit_file` and `write_file` together, so the fixed part grew as well.

**The mistakes.**
None of the five models made a single tool error with MindRoom's tools in its 36 runs.
Partly, the models rarely needed the file tools: the Claude models never called one, and of the GPT models, only Luna used them often.
The only model that made tool errors was Luna, and only with the Codex tools: 7 errors in 36 runs, all of them `read_file` calls with a path relative to the directory Luna had just given `exec_command`.
The made-up fields in pi always appeared inside its nested list of replacements, where the model has to write the JSON for each replacement itself.
MindRoom's `edit_file` is flat, like Claude Code's `Edit`: a path, the old text, and the new text.
So I suspected that keeping the tools as simple as the native ones matters more than matching their exact names.

{{< /detail-tag >}}

## Older models: only Opus 4.8 needed them

The pi story made me wonder whether this used to be different, since Opus 4.8 struggled with pi's edit tool while Opus 4.7 did not.
So I ran the same comparisons on older models that are still available: Claude Opus 4.7, Opus 4.8, and Sonnet 5, and GPT-5.5 and GPT-5.6 Sol.

{{< plot name="fairOlder" caption="Change in tokens per task when the older models use their native harness tools instead of MindRoom's, with 95% confidence intervals: with only the harness's own tools against MindRoom's matching set, and with the mixed set the pull request ships. Opus 4.7 and 4.8 ran without thinking, Sonnet 5 with adaptive thinking, and GPT with the effort Codex picks. Hover for values." >}}

With the mixed set, the older models seemed to prefer their native tools: the older Claude models used 22 to 36% fewer tokens with Claude Code's tools.
But that came from the extra tools the mixed set keeps from MindRoom, `grep`, `find_files`, and `ls`.
Next to MindRoom's other tools, those made the older Claude models take more steps and read more, and next to Claude Code's tools, the models hardly touched them.
With only each harness's own tools, that preference disappears, except for one model.
The exception is the model from the pi story: Opus 4.8 used 19% fewer tokens with Claude Code's tools, more than the shorter descriptions explain, and read files through Bash instead of with a separate tool.
And on the pi story itself: Opus 4.8 and Sonnet 5, the two models that made up fields in pi, made 111 edits with MindRoom's flat `edit_file` across both tests, and none of them failed.

The GPT-5 models did about the same with either set, and unlike GPT-6 Astra and Sol, they barely used `apply_patch`.
So reaching for its native editing tool, and paying for it, is new in that generation.

Familiar tools clearly made exactly one of the ten models I tested more efficient: the one that started it.
The others did as well or better with tools they were presumably not trained on: they seem to generalize beyond the environment they were trained in.

{{< detail-tag "The numbers behind this section" >}}

**Only the harness's own tools.**
With Claude Code's tools, Opus 4.7 used 3% fewer tokens [−12 to +6%], Opus 4.8 19% fewer [−26 to −11%], and Sonnet 5 7% fewer [−29 to +23%], a noisy result.
Opus 4.8 did 17% less work on top of the shorter definitions; it called MindRoom's `read_file` 27 times, but never Claude Code's `Read`.
With Codex's tools, GPT-5.5 used 5% more [−5 to +16%] and GPT-5.6 Sol 3% more [−4 to +11%]; they called `apply_patch` only 3 and 9 times, where with MindRoom's tools they made 20 and 16 calls to the file tools.
The pass rates stayed within one or two runs of each other.
None of the older models made a tool error with MindRoom's matching set; with Codex's, GPT-5.5 sent garbled working directories to `exec_command` 11 times.

**Why the mixed set made them look different.**
The only difference between the two tests is that the mixed set adds MindRoom's `grep`, `find_files`, and `ls` to both sides.
Next to MindRoom's other tools, the older Claude models called `ls` and `grep` 20, 9, and 3 times, took 0.3 to 0.9 more requests per task, and did 35 to 38% more work than without them.
Next to Claude Code's tools, they called them once in total.

**The older models with the mixed set.**

{{< plot name="generations" caption="Change in tokens per task when each model uses its native harness tools instead of MindRoom's, with 95% confidence intervals, oldest models first in each family. Each model's reasoning mode is in parentheses: Opus 4.7 and 4.8 do not think, the other Claude models think adaptively, and GPT uses the effort Codex picks. Hover for values." >}}

Opus 4.7, Opus 4.8, and Sonnet 5 used 22 to 36% fewer tokens with Claude Code's tools.
Unlike for the 5.5 models, that was not just the shorter definitions: they made fewer requests and did 26 to 45% less work on top of the fixed part.
GPT-5.6 Sol used 15% fewer tokens with Codex's tools and did 27% less work, and GPT-5.5 used about the same.
One generation later, the GPT-6 models use up to 31% more with Codex's tools, and the Claude 5.5 models mostly save what the shorter definitions save.
The pass rates stayed within one or two runs of each other for every model.

**How they used the file tools.**
With MindRoom's tools, the older Claude models called `read_file` 24, 29, and 44 times; with Claude Code's, they called `Read` only 3, 1, and 6 times and read files through Bash instead.
GPT-5.6 Sol needed 9 patches where it had made 32 calls to `edit_file` and `write_file`.
Opus 4.8 and Sonnet 5 made 37 and 21 calls to MindRoom's flat `edit_file`, and none of them failed.
That does not prove that pi's nested list caused pi's failures, because I never gave them a nested edit tool, but a flat one did not trigger them.
Their few tool errors were different ones: Sonnet 5 twice polled a background command that did not exist, GPT-5.5 and GPT-5.6 Sol each had one edit whose old text did not match, and GPT-5.5 sent garbled working directories to Codex's `exec_command` seven times.

**Only the shell tools.**

{{< plot name="olderShell" caption="Change in tokens per task when the older models use their native harness tools instead of MindRoom's, with 95% confidence intervals: with shell and file tools, and with only the shell tools. Opus 4.7 and 4.8 ran without thinking, Sonnet 5 with adaptive thinking, and GPT with the effort Codex picks. Hover for values." >}}

The native set mixes a model's own tools with some of MindRoom's, such as `grep`, `ls`, and, for GPT, `read_file`, so I also ran the older models with only the shell tools, in MindRoom's shape and in the native one.
Opus 4.7 then used 10% fewer tokens with the native shell, GPT-5.6 Sol 6% fewer, and GPT-5.5 the same, and almost all of that came from shorter definitions.
Opus 4.8 used 23% fewer tokens, made fewer requests, and did 16% less work.
Sonnet 5's result is too noisy to read: in one run, the native shell returned a 50 KB output early on, and resending it with every later request made that run cost 12 times the median; its median run used 9% fewer tokens with the native shell.

**The reasoning settings.**
Opus 4.7 and 4.8 do not think unless you ask them to, and Sonnet 5 thought before 42% of its replies, against 15 to 25% for the 5.5 models at the same adaptive setting.
The GPT-5 models reasoned before 59 to 76% of their requests, while the GPT-6 models reasoned before only 4 to 12%.
With adaptive thinking and the mixed set, Opus 4.7 and 4.8 thought before 26 to 36% of their replies, and still used 35% and 20% fewer tokens with Claude Code's tools.
For that test, I set `thinking` to `adaptive` in the model's `extra_kwargs`, since these models reject a fixed thinking budget.

I also ran one current model of each family, Claude Sonnet 5.5 and GPT-6 Astra, at low and at high reasoning effort.
For Astra, I set `reasoning_effort` to `low` or `high`; for Sonnet 5.5, `output_config.effort`, which is how the Claude 5.5 models take a reasoning effort.

{{< plot name="effortChange" caption="Change in tokens per task when Claude Sonnet 5.5 and GPT-6 Astra use their native harness tools instead of MindRoom's, at each reasoning effort, with 95% confidence intervals. With no effort set, Sonnet uses adaptive thinking, and Astra the effort Codex picks. Hover for the tokens per task." >}}

Both models passed all 36 runs at every effort with either set of tools, except for one run that Astra failed with MindRoom's tools at its default effort.
A higher effort did not make Codex's tools work better for GPT; it made them worse: at high effort, Astra made 4.5 requests per task with Codex's tools against 3.6 with MindRoom's, and used 45% more tokens.
Even at high effort, though, Astra reasoned before only 10 to 12% of its requests, against 4 to 7% at its default, far below the GPT-5 models.
For Claude, the native tools stayed cheaper at every level, and saved the most at low effort, 19%, where Sonnet thought before only 3 to 4% of its replies.
Sonnet thought about as often at its default as at high effort, so I would not read much into the difference between those two.

{{< /detail-tag >}}

## What does matter: what the agent sends

If the shape of the tools does not matter, what does?
My guess was the other half of my plan: a smaller agent.
Every request to the model resends the system prompt and the definition of every tool, so an agent with a shorter prompt and fewer tools sends less with every step.

### Fewer tools

Fewer tools did help.
With only MindRoom's shell tools and none of its file tools, the agent used about a third fewer tokens and passed about as many runs.
A shell-only agent is also where I still expected the native tools to matter most, because every step goes through the one tool whose shape the model knows best.
They did not: GPT used the same number of tokens with Codex's shell tools, and Claude saved only what its shorter descriptions save.

{{< detail-tag "The numbers behind this section" >}}

{{< plot name="shellOnly" caption="Change in tokens per task, with 95% confidence intervals: with only MindRoom's shell tools instead of all of MindRoom's tools, and with only the native shell tools instead of MindRoom's. Claude ran with adaptive thinking, and GPT with the reasoning effort the Codex backend picks when none is set. Hover for values." >}}

With only MindRoom's three shell tools, for running, checking, and stopping a command, and none of its file tools, the agent used 27 to 41% fewer tokens.
It passed about as many runs: Luna passed 31 instead of 33, too small a difference to tell apart, and the other four models passed all 36.

For the native shape, I gave Claude only Claude Code's `Bash`, `BashOutput`, and `KillShell`, and GPT only Codex's `exec_command` and `write_stdin`, with MindRoom's `kill_shell_command` in Codex's style.
For GPT, the total did not move: Astra, Sol, and Luna used the same number of tokens, within 2%, and made the same number of requests.
Codex's shell tools alone take about 130 fewer tokens to describe than MindRoom's, and GPT spent about as much on extra work.
Claude Sonnet 5.5 used 18% fewer tokens and Claude Opus 5.5 6% fewer, mostly because the Claude Code-style shell tools are shorter to describe than MindRoom's.

{{< /detail-tag >}}

### Minimal mode: one shell tool and a 12-line prompt

MindRoom's [minimal mode](https://docs.mindroom.chat/tools/agent-cli/) takes this all the way.
The agent gets a 12-line prompt and a single `bash` tool instead of its normal prompt and tools.
Its instructions, skills, context files, and memory move behind a command-line program inside that shell, which it can call when it needs them.

The difference starts before the model does anything.
For Claude Sonnet 5.5, the prompt and tool definitions that ride along with every request shrink from 4,285 tokens to 661.[^claudetools]

{{< plot name="promptParts" caption="What every request carries besides the conversation: the system prompt and the tool definitions, in standard and in minimal mode, from each provider's own token counts. Hover for values." >}}

{{< plot name="minimalSplit" caption="Tokens per task in Matrix conversations: the same agent with only MindRoom's shell tools, in standard mode and in minimal mode with its single bash tool, split into the fixed part (light) and the work the model did on top of it (dark). Claude ran with adaptive thinking, and GPT with the reasoning effort the Codex backend picks when none is set. Hover for values." >}}

Each bar splits a task's tokens into the fixed part, the prompt and tool definitions resent with every request, and the work the model did on top of it.
The minimal agent used 58 to 76% fewer tokens than the same agent in standard mode, for every model.
Most of that is input the provider had cached and bills at a fraction of the price, so the bill shrinks less than the token count does.
And the model did not pay for it with extra work: the dark part of the bars stayed about the same or shrank, except for Luna's.
I had also hoped that the smaller agent would need less to do the task itself, but only GPT-6 Astra and Sol did, with slightly fewer steps and about a quarter less output; Claude worked exactly the same in both modes.

These tasks are short, three or four requests each, which is why the prompt weighs so much.
I tried to make them harder so they would take more steps, but the models were so good that they only took about 50% more requests, and for the two models I tried, the pattern stayed the same.
I see no reason why longer tasks would erase the gain: every step a model saves also saves resending the conversation, so on long tasks it counts for more.
In a long session, the growing conversation dominates and the prompt's share of the tokens shrinks, but its saving per request stays: about 3,600 tokens for Claude and 2,200 for GPT.
And a real agent's prompt carries far more instructions, skills, and memory than this test agent's, so it saves more per request.

{{< detail-tag "The numbers behind this section" >}}

**Why Matrix.**
Minimal mode only works in chat conversations, so I ran it through Matrix, next to the same agent with only its shell tools in standard mode.
Each run got a fresh chat room with only the agent, named `coder`, and MindRoom's router, which handles commands like `!mode`; for minimal mode, I switched the room over with `!mode coder minimal` before sending the task.
In a Matrix conversation, the agent also gets context about the room and the conversation, so it uses more tokens than through the API: on the same code, with only the shell tools, Claude Opus 5.5 used 22,192 tokens per task in Matrix against 12,904 through the API.
That is why I compare minimal mode with standard mode in Matrix.

**The prompt.**
In standard mode, the system prompt is 2,295 tokens for Claude Sonnet 5.5 and 1,463 for GPT-6 Astra, and the tool definitions, the shell tools and one for inviting MindRoom's router, add another 1,990 and 867.
In minimal mode, the system prompt is 152 and 97 tokens, and the single `bash` tool adds 509 and 72.
This test agent's standard prompt is about 100 lines only because its own configuration is one role line and one instruction; a real agent's prompt also carries its instructions, skills, context files, and memory, and can run to hundreds of lines, while its minimal prompt stays at 12.
The model receives all of that, plus the task and the room's context, again with every request, so it adds up: in standard mode, about 80% of all tokens were this fixed part.

**The result.**
Its first request dropped from about 4,600 to 1,000 input tokens for Claude, and from about 2,600 to 410 for GPT.
Counting only the uncached input and the output, the minimal agent used 16 to 42% fewer tokens.
Even with the extra context of a Matrix conversation, it used fewer tokens than the agent with only MindRoom's shell tools through the API on the same code: 21 to 52% fewer.

**Is that a fair comparison?**
A shorter prompt saves tokens even if the model then has to work harder, so the real question is whether it had to.
Mostly, it did not: the work stayed the same for both Claude models (1% and 3% less), and went down for Astra and Sol (38% and 13% less), which also needed fewer requests, about 3.0 per task instead of 3.3 to 3.4.
Luna is the exception: it made more requests and did 40% more work in minimal mode, but the shorter prompt still more than paid for that.
Counted per task without the resent conversation, the Claude models wrote and added to the conversation the same in both modes, Astra and Sol wrote about a quarter less and needed 0.2 to 0.4 fewer requests, and Luna added 33% more, mostly longer command output.
Three of the five models failed one more run in minimal mode, mostly on the same script-writing task that other configurations also miss now and then.
That is too small to tell apart here, but I will keep an eye on it with harder tasks.

{{< /detail-tag >}}

### Even with its native shell tool

That leaves the combination I had in mind from the start: the minimal agent, with each model's native shell tool as its only tool.
I patched minimal mode so that its single tool appears as Claude Code's `Bash` for Claude and as Codex's `exec_command` for GPT, with the same 12-line prompt.[^combo]

{{< plot name="minimalNative" caption="Change in tokens per task in minimal mode when its single tool is the model's native shell tool, Claude Code's Bash or Codex's exec_command, instead of MindRoom's bash, with 95% confidence intervals. The second row cuts the native tool's output to the last 100 lines, MindRoom's bash default. Claude ran with adaptive thinking, and GPT with the reasoning effort the Codex backend picks when none is set. Hover for values." >}}

It did not make the minimal agent better for any model.
For Claude, it made little difference: Sonnet used about the same, and Opus a little more.
For GPT, it was clearly worse, mostly because `exec_command` hands back a command's whole output, and in an agent that sends so little else, a few long outputs weigh a lot.
With its output cut to 100 lines, `bash`'s default and the light rows in the chart, only Sol still clearly used more; Astra's and Luna's smaller increases could be chance.

So the whole effect of the combination came from its minimal half: models that were trained with a carefully designed set of tools did best with one tool and almost no prompt, and the tool's native shape did not make it better.

{{< detail-tag "The numbers behind this section" >}}

The single native tool only runs commands, but no current model ever polled or stopped a command in any of these runs, so it lacked nothing they used.
I ran it next to minimal mode with MindRoom's own `bash` on the same code, and once more with the native tool's output cut to the last 100 lines.
That is `bash`'s default, which the GPT models set themselves on every call, more often lower than higher; in the end, the capped native tool and `bash` returned about as much, except for Astra, whose `bash` results were twice as long.

For Claude, Sonnet used 4% fewer tokens with the native tool and Opus 7% more.
For GPT, it was 34 to 46% more tokens, mostly because `exec_command` returns a command's whole output, so the models read 39 to 50 lines per result instead of 20 to 36.
Cut to 100 lines, the native tool cost GPT 5 to 15% more, but only Sol's increase is clearly more than chance; part of it is the definition, which takes about 90 more tokens than `bash` on every request.
In minimal mode, the agent sends so little else that a few long outputs weigh much more than through the API: the cap cut Astra's tokens by about 20% here, against 4% there.
Claude rarely printed more than 100 lines, so I would not read anything into the gap between its two native rows.
The pass rates differed by at most a few runs, too few to tell apart.

{{< /detail-tag >}}

## What I changed

By default, the pull request now gives Claude models Claude Code's tools: today's use 6 to 13% fewer tokens with them, mostly from the shorter descriptions, and Opus 4.8 is clearly more efficient with them.
Every other model keeps MindRoom's own tools, since GPT-6 Astra and Sol used 43 to 59% more tokens with only Codex's tools.
The Codex tools are still there for anyone who wants them, with `tool_dialect: codex` in a model's configuration.
For today's models, the lesson is the shorter descriptions rather than the shape, and MindRoom's own tools could get those too.
And I am going to use minimal mode a lot more, with MindRoom's own `bash`.

## What this does and does not show

- I tested the names and arguments of the tools, not whole harnesses. Claude Code and Codex also have their own tool descriptions, system prompts, and output formats, Codex has an interactive terminal, and RL trains all of that together. The full harness might still help today's models; matching only the tools did not.
- The tasks are easy and short: 97% of all runs passed, with three to seven requests per task on average. Harder, longer tasks might separate the tool sets on success, not only on cost.
- With 36 runs per configuration, a 15 to 30% difference in tokens is clear, but a difference of one or two passed runs is not.
- The confidence intervals cover run-to-run variation on these 12 tasks, not the choice of tasks. Resampling the tasks as well widens them, GPT-6 Astra's +59% to +38 to +81%, and makes Sonnet 5.5's 6% saving indistinguishable from none. Astra and Sol still used more tokens with Codex's tools on every one of the 12 tasks, and the minimal agent used fewer on every task, for every model.
- Most runs used each model's standard reasoning mode, which differs between generations: adaptive thinking for Claude 5 and 5.5, none for Opus 4.7 and 4.8, and the effort Codex picks for GPT. I tried other settings on four models: two current ones at low and high effort, and Opus 4.7 and 4.8 with adaptive thinking.

## Why this excites me

Half of my plan was wrong, and I am happy about that.
The benchmarks I did not believe were right, at least for these models.
It suggests that these models generalize much better than I gave them credit for.
They were trained with one specific set of tools, and on these tasks they did just as well with tools they had presumably never seen in training, as long as those tools were simple and clearly described.
Only Opus 4.8, the model that started all this, still needed its native tools.
What matters more than familiarity is how much the agent sends with every request: the prompt and the definition of every tool.

It also changes how I think about who gets to build the best agents.
If models only worked well in the harness they were trained in, the labs would own the best agents by default.
Instead, the skills seem to carry over to other harnesses.
I suspect the same holds one level up, for how several agents work together.
The labs presumably train their models in their own harness, but if what the models learn transfers this well, a harness built outside the labs, like MindRoom, could get just as good at letting agents collaborate.
That is a hunch, not a result, and testing it is what I want to do next.

## Appendix: how I measured, and the numbers behind the charts

All scripts, the tasks, and one row per trial, with its reasoning setting, are [on GitHub next to this post's source](https://github.com/basnijholt/nijho.lt/tree/main/content/post/native-harness-tools/reproduce).

{{< detail-tag "Show the setup and every configuration" >}}

**Setup**

- Each configuration ran as a separate MindRoom instance with one agent and a fresh Docker container for its commands. The model, the tools, and everything else were fixed in that instance's configuration.
- The tool comparisons ran through MindRoom's OpenAI-compatible API on the pull request at commit `d73aafb51`: the fair sets, the mixed sets with whole and with 100-line output, and both shell-only setups. The capped run changed only the output limit of the native shell tools.
- The minimal-mode runs and their standard-mode comparison ran through Matrix on MindRoom's main branch at release `v2026.10.228`, whose shell tools lack two arguments the pull request added, a working directory and a wait. A shell-only run through the API on that release used within 3% of the pull request's tokens for every model except Luna, which used 8% fewer.
- The combination ran through Matrix on the pull request with an experiment patch that shows minimal mode's single tool in the model's own dialect. On that code, minimal mode with MindRoom's `bash` used within 10% of its tokens on main for every model.
- Tokens per task are the input and output tokens of every model request in that task, from MindRoom's per-request usage logs. The work is what is left after subtracting the fixed part, the first request's input times the number of requests.
- The confidence intervals come from resampling the three runs of each task 5,000 times, keeping the mix of tasks fixed.

Each cell shows passed runs out of 36, then tokens per task; the work columns show how much the work changed with the native tools.

**Fair sets: each harness's own tools against MindRoom's matching set (pull request, through MindRoom's API)**

| Model | Reasoning | MindRoom's set | Harness's own set | Work with the harness's set |
|---|---|---|---|---|
| Claude Opus 5.5 | adaptive thinking | 36/36 · 15,661 | 35/36 · 13,628 (−13%) | +7% |
| Claude Sonnet 5.5 | adaptive thinking | 36/36 · 14,606 | 36/36 · 13,764 (−6%) | +15% |
| GPT-6 Astra | Codex's choice | 36/36 · 7,041 | 36/36 · 11,206 (+59%) | +84% |
| GPT-6.1 Sol | Codex's choice | 36/36 · 7,292 | 36/36 · 10,417 (+43%) | +60% |
| GPT-6 Luna | Codex's choice | 35/36 · 8,425 | 34/36 · 8,638 (+3%) | −5% |
| Claude Opus 4.7 | no thinking | 34/36 · 24,398 | 33/36 · 23,564 (−3%) | +13% |
| Claude Opus 4.8 | no thinking | 33/36 · 24,103 | 34/36 · 19,593 (−19%) | −17% |
| Claude Sonnet 5 | adaptive thinking | 33/36 · 29,781 | 35/36 · 27,833 (−7%) | +9% |
| GPT-5.5 | Codex's choice | 35/36 · 10,819 | 35/36 · 11,353 (+5%) | +2% |
| GPT-5.6 Sol | Codex's choice | 36/36 · 10,624 | 34/36 · 10,991 (+3%) | −5% |

For Claude, both sets have a shell and tools to read, edit, and write files; for GPT, a shell and Codex's `apply_patch` against MindRoom's tools to edit and write files. Neither has MindRoom's `grep`, `find_files`, or `ls`.

**Mixed sets: native tools against MindRoom's tools (pull request, through MindRoom's API; Claude with adaptive thinking, GPT with the effort Codex picks)**

| Model | MindRoom's tools | Native tools | Native tools, 100-line output | Work with native tools |
|---|---|---|---|---|
| Claude Opus 5.5 | 36/36 · 18,943 | 36/36 · 17,244 (−9%) | 36/36 · 17,410 (−8%) | +5% |
| Claude Sonnet 5.5 | 36/36 · 17,765 | 36/36 · 16,237 (−9%) | 36/36 · 16,399 (−8%) | −4% |
| GPT-6 Astra | 35/36 · 8,250 | 36/36 · 10,807 (+31%) | 35/36 · 10,399 (+26%) | +51% |
| GPT-6.1 Sol | 36/36 · 8,873 | 36/36 · 10,534 (+19%) | 36/36 · 10,239 (+15%) | +24% |
| GPT-6 Luna | 33/36 · 12,003 | 35/36 · 11,532 (−4%) | 36/36 · 10,816 (−10%) | +15% |

**Older models, mixed sets: native tools against MindRoom's tools (pull request, through MindRoom's API)**

| Model | Reasoning | MindRoom's tools | Native tools | Work with native tools |
|---|---|---|---|---|
| Claude Opus 4.7 | no thinking | 34/36 · 33,140 | 33/36 · 25,793 (−22%) | −26% |
| Claude Opus 4.8 | no thinking | 33/36 · 32,219 | 34/36 · 23,843 (−26%) | −32% |
| Claude Sonnet 5 | adaptive thinking | 33/36 · 42,349 | 34/36 · 27,120 (−36%) | −45% |
| GPT-5.5 | Codex's choice | 34/36 · 15,007 | 36/36 · 14,419 (−4%) | −11% |
| GPT-5.6 Sol | Codex's choice | 36/36 · 15,062 | 35/36 · 12,809 (−15%) | −27% |

**Older models, only the shell tools: native shape against MindRoom's (pull request, through MindRoom's API; Opus 4.7 and 4.8 without thinking, Sonnet 5 with adaptive thinking, GPT with the effort Codex picks)**

| Model | MindRoom's shell | Native shell |
|---|---|---|
| Claude Opus 4.7 | 33/36 · 17,518 | 33/36 · 15,714 (−10%) |
| Claude Opus 4.8 | 35/36 · 19,183 | 33/36 · 14,686 (−23%) |
| Claude Sonnet 5 | 33/36 · 22,624 | 33/36 · 28,354 (+25%) |
| GPT-5.5 | 36/36 · 9,056 | 36/36 · 9,046 (0%) |
| GPT-5.6 Sol | 36/36 · 9,171 | 34/36 · 8,658 (−6%) |

Sonnet 5's native mean comes from one run that cost 271,106 tokens, after a 50 KB command output; its median is 9% lower with the native shell.

**Opus 4.7 and 4.8 with adaptive thinking, mixed sets: native tools against MindRoom's tools (pull request, through MindRoom's API)**

| Model | Thinking replies | MindRoom's tools | Native tools |
|---|---|---|---|
| Claude Opus 4.7 | 26% and 31% | 35/36 · 35,610 | 33/36 · 23,090 (−35%) |
| Claude Opus 4.8 | 36% and 30% | 33/36 · 25,269 | 33/36 · 20,130 (−20%) |

**Reasoning effort, mixed sets: native tools against MindRoom's tools (pull request, through MindRoom's API)**

| Model | Reasoning effort | MindRoom's tools | Native tools |
|---|---|---|---|
| Claude Sonnet 5.5 | low | 36/36 · 15,154 | 36/36 · 12,330 (−19%) |
| Claude Sonnet 5.5 | default | 36/36 · 17,765 | 36/36 · 16,237 (−9%) |
| Claude Sonnet 5.5 | high | 36/36 · 18,286 | 36/36 · 15,630 (−15%) |
| GPT-6 Astra | low | 36/36 · 8,361 | 36/36 · 10,627 (+27%) |
| GPT-6 Astra | default | 35/36 · 8,250 | 36/36 · 10,807 (+31%) |
| GPT-6 Astra | high | 36/36 · 8,934 | 36/36 · 12,918 (+45%) |

**Only the shell tools (pull request, through MindRoom's API; Claude with adaptive thinking, GPT with the effort Codex picks)**

| Model | All of MindRoom's tools | MindRoom's shell only | Native shell only |
|---|---|---|---|
| Claude Opus 5.5 | 36/36 · 18,943 | 36/36 · 12,926 (−32%) | 36/36 · 12,202 (−6%) |
| Claude Sonnet 5.5 | 36/36 · 17,765 | 36/36 · 12,455 (−30%) | 36/36 · 10,168 (−18%) |
| GPT-6 Astra | 35/36 · 8,250 | 36/36 · 6,025 (−27%) | 36/36 · 6,052 (0%) |
| GPT-6.1 Sol | 36/36 · 8,873 | 36/36 · 6,195 (−30%) | 36/36 · 6,177 (0%) |
| GPT-6 Luna | 33/36 · 12,003 | 31/36 · 7,118 (−41%) | 34/36 · 7,018 (−1%) |

MindRoom's shell alone is compared with all of MindRoom's tools, and the native shell with MindRoom's shell.

**Minimal mode against standard mode (main branch, through Matrix, shell tools only; Claude with adaptive thinking, GPT with the effort Codex picks)**

| Model | Standard mode | Minimal mode |
|---|---|---|
| Claude Opus 5.5 | 36/36 · 22,192 | 36/36 · 8,030 (−64%) |
| Claude Sonnet 5.5 | 35/36 · 22,448 | 34/36 · 7,828 (−65%) |
| GPT-6 Astra | 36/36 · 11,429 | 36/36 · 2,798 (−76%) |
| GPT-6.1 Sol | 36/36 · 11,070 | 35/36 · 3,370 (−70%) |
| GPT-6 Luna | 35/36 · 12,568 | 34/36 · 5,219 (−58%) |

**Minimal mode: the native tool against MindRoom's `bash` (pull request with the experiment patch, through Matrix; Claude with adaptive thinking, GPT with the effort Codex picks)**

| Model | MindRoom's `bash` | Native tool | Native tool, 100-line output |
|---|---|---|---|
| Claude Opus 5.5 | 36/36 · 8,058 | 36/36 · 8,654 (+7%) | 36/36 · 9,123 (+13%) |
| Claude Sonnet 5.5 | 34/36 · 7,787 | 34/36 · 7,514 (−4%) | 34/36 · 8,000 (+3%) |
| GPT-6 Astra | 35/36 · 3,071 | 36/36 · 4,173 (+36%) | 36/36 · 3,359 (+9%) |
| GPT-6.1 Sol | 34/36 · 3,103 | 33/36 · 4,150 (+34%) | 36/36 · 3,575 (+15%) |
| GPT-6 Luna | 34/36 · 4,697 | 34/36 · 6,849 (+46%) | 32/36 · 4,926 (+5%) |

One of Luna's runs with the whole native output counts for passes but not for tokens: the provider reported no usage for one of its requests.

{{< /detail-tag >}}

[^strict]: Armin also found that Anthropic's strict tool mode, which restricts the model's output to the tool's schema, made these failures disappear in his tests. Pi later turned it on for Claude models, and a pi user then [linked a different problem to it](https://github.com/earendil-works/pi/issues/10074#issuecomment-6000381416): in that user's logs, 9.5% of Claude's edits had mangled `\u` escapes for non-ASCII text, such as Korean, with strict mode on, and 1.5% with it off.

[^claudetools]: Anthropic adds its own instructions for tool use to every request that has tools, which is why MindRoom's single `bash` tool costs Claude 509 tokens. I measured all of these numbers by sending each part on its own and reading the input tokens the provider reported.

[^fair]: MindRoom's toolkits accept `exclude_tools`, so both sets drop MindRoom's `grep`, `find_files`, and `ls`, and for GPT also `read_file`, since Codex reads files through the shell. Both keep their shell's tools for checking on and stopping a background command, which no model used in these runs.

[^combo]: The patch is with this post's reproduction scripts. It shows minimal mode's single tool as MindRoom's canonical run function, which the tool dialect then presents as `Bash` or `exec_command`; nothing else about minimal mode changes.

[^tasks]: The 12 tasks come from 12 families: a CSV report, finding the commit that broke a check, renaming an API across a package, counting errors in log files, fixing failing tests, finding files, extracting fields from JSON, writing a shell script, editing a configuration file, counting matching lines in very long command output, unpacking nested archives, and deduplicating and merging data files. I tune MindRoom's agent setup on other instances of these families, and these 12 were held out from that.

[^tokens]: Claude and GPT count tokens differently, so compare the numbers within one model, not across models. Cached input counts in full here, although providers bill it at a fraction of the price, so a bill changes less than the token count.

