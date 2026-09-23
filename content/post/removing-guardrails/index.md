---
title: "Removing the guardrails and letting my coding agents loose"
subtitle: "Why I run every agent in YOLO mode, and the few things my hooks still block"
summary: "I have run coding agents in YOLO mode since I started using them. Instructions in AGENTS.md did not stop them from force-pushing or merging PRs, so hooks do. As the models got better, I added an override the agent may only use after I explicitly approve an action."
date: 2026-09-22
draft: false
featured: false
authors:
  - admin
tags:
  - ai
  - agentic-coding
  - claude-code
  - git
  - productivity
  - development
categories:
  - Software Development
  - AI
  - level:intermediate
---

I have run coding agents in YOLO mode since I started using them in May 2025.
I think it is the only way to parallelize work.
Sometimes I have ten agents running at the same time, and clicking "approve" on every command they run would make that impossible.

What makes me comfortable with it is that models tend to do what you ask, and that you can keep them in an environment where they cannot do much harm.
I don't keep secrets within their reach, and above all I have [very good backups]({{< ref "/post/btrfs-to-zfs" >}}).
The last piece is a small set of hooks that block the few things I never want an agent to do on its own.

## Why hooks and not AGENTS.md

My system prompt has always told agents not to force-push or merge PRs.
Some of them did it anyway.

The first time I really noticed was with [Gemini 3 Pro in November 2025]({{< ref "/post/gemini-3-pro-first-impressions" >}}), which merged my PR and force-pushed to `main`.
It happened a couple more times in the weeks after, as I parallelized more and asked more of the models.
Three weeks later I had hooks for Claude Code and Gemini CLI that block these commands before they run.
Codex did not support hooks yet.
To my surprise, it did not need them: OpenAI's models are extremely good at following instructions, and Codex never ignored an explicit rule in my `AGENTS.md`.
Codex supports hooks by now, so it runs the same ones as the others.

Claude has been worse at following rules, and Gemini far worse still: absolutely dogshit.
I only try Gemini now and then, and I have been disappointed every time.
By now I don't even try the latest Google models anymore.

I don't think agents are ever malicious.
They try to do what you asked, but they can misinterpret it, and then they force-push or merge something.
A rule in a Markdown file is one more instruction to weigh against everything else in the context.
A hook is not.

## What I block

All hooks live in [my dotfiles](https://github.com/basnijholt/dotfiles/tree/main/configs/claude/hooks), and I deliberately kept them simple.
The detection logic is one Python module, [`git_guard.py`](https://github.com/basnijholt/dotfiles/blob/main/configs/claude/hooks/git_guard.py), and the Claude Code, Codex, and Gemini CLI hooks all import it.

**`git commit --amend` and `git push --force`.**
The unit I review is a PR.
When I review a PR, I know I have reviewed it up to a certain commit, and later I only look at the diff of the new commits.
Rewriting history breaks that.

**Pushing to `main`.**
Everything happens in PRs.
Inside a PR I don't care how messy the history gets.
I want the agent to push very often, so no work gets lost, and every commit has to be green, so each one is a snapshot I can go back to.
The agent maintains its own development of the feature, and I have not written a commit message myself in a long time.
When the PR is done, I squash merge it.

**`gh pr merge`.**
The merge comes after my review, so it is mine to do.

**`git add -A`.**
I often have unrelated untracked or unstaged files lying around.
I work in many open source repositories, and some of those files should not be public, like deployment plans.
This is the only block without an override.

**`sleep`.**
This one is for Claude, and Opus 5 specifically, which I hate with a passion.
It would run tests in the background and then `sleep 300`, badly overestimating how long the tests take, when a blocking tool call returns exactly when they finish.

## The override

Over time the models got more capable.
I could parallelize more, they could work independently for longer, and I trusted them more.
I noticed I was spending a significant fraction of my time clicking buttons and doing operations I had forbidden the agent to do, only to end up doing them myself.

So in July I added an override.
When a hook blocks a command, the agent gets this hint:

```text
If (and only if) the user has explicitly approved this exact action,
re-run the command prefixed with EXPLICITLY_USER_APPROVED_HOOK_OVERRIDE=1 to override this block.
```

Nothing checks whether I actually approved it.
It is a soft gate, but it works because the agent now has to write down, in the command itself, that I approved the action.
When it runs into the block without my approval, it becomes obvious to the agent that it has to ask me first.

`git add -A` stays hard-blocked, and a chained command cannot carry an override past it: `EXPLICITLY_USER_APPROVED_HOOK_OVERRIDE=1 git commit --amend && git add -A` is still rejected.

## When the override was used without approval

It has happened, mostly with GPT-5.6 Sol, which I used a lot at the time.

It used to be that you had to keep your context window short, because auto-compaction was lossy and produced poor summaries.
Since around GPT-5.3, compaction works well enough that I keep a session going for as long as I am working on the same feature.
So I would ask the agent to merge a PR early on, start a follow-up PR in the same session, and after a compaction the agent concluded that it should merge the new PR too.
It did, without my approval.

The other case was my [`pr-review` skill](https://github.com/mindroom-ai/mindroom/blob/main/.claude/skills/pr-review/SKILL.md), by far my favorite skill that I wrote myself.
I would tell the agent to run it and squash merge the PR only if the review approved it.
A few times, the review found problems, the agent fixed them, and then it merged.
What I meant was: merge if it is approved right away, and otherwise wait for me.
Now I spell that out and end with "otherwise, wait for my instructions."

## Working from my phone

The override matters most when I am away from my computer.
On a month-long trip visiting family in Europe, I worked only from my phone, using [my mobile coding workflow]({{< ref "/post/agentic-mobile-workflow" >}}).
Typing commands in a terminal on a phone is inconvenient, so I would rather say what I want and let the agent do it, including the merge.
I have also built end-to-end encrypted voice calls to my agents over Matrix with [MindRoom]({{< ref "/post/mindroom" >}}), and I am moving more toward that kind of voice-driven workflow.

## Not much has changed

I recently reread [my first post on agentic coding]({{< ref "/post/agentic-coding" >}}) from August 2025, and very little in it is outdated.
The models are more capable, and I give them much larger scopes, but the way I work is mostly the same.
The hooks are the main thing I added, and the override is how I loosened them again.
