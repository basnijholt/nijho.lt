---
title: "Removing the guardrails from my coding agents"
subtitle: "From 'the agent can never merge' to 'the agent can merge when I say so'"
summary: "For a year my hooks hard-blocked agents from amending commits, force-pushing, and merging PRs. With Fable and GPT-5.6 Sol, the guardrails stopped preventing mistakes and started preventing convenience — so I replaced capability restrictions with explicit, auditable, per-action authorization."
date: 2026-07-12
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
  - mindroom
  - matrix
  - open-source
categories:
  - Software Development
  - AI
  - level:intermediate
---

For the past year my [dotfiles](https://github.com/basnijholt/dotfiles) have contained hooks that flat-out forbade my coding agents from doing certain things: `git commit --amend`, `git push --force`, pushing to `main`, and `gh pr merge`. Not because the agents kept screwing them up — mostly because *I* didn't like the idea of an agent doing them. The merge button was mine. History rewrites were mine. The agent proposed; I disposed.

Last week I deleted that policy. Not the hooks — the *philosophy*.

## What changed

Two things, honestly: Fable and GPT-5.6 Sol came out, and I implemented a couple of features that made the old trust model feel silly.

The models got good enough that the guardrails stopped protecting me from mistakes and started protecting me from convenience. When the agent says "the PR is green, all reviewers approved, want me to merge?" and my answer is always "yes, hold on, let me go find the merge button" — the button is the bug.

## The mechanism: explicit approval, not open season

I didn't just delete the hooks. The blocks are still there by default. What I added is an override marker: if a command is prefixed with

```bash
EXPLICITLY_USER_APPROVED_HOOK_OVERRIDE=1 git push --force ...
```

the hook lets it through — but the agent is only allowed to use that prefix when I have *explicitly approved the action in conversation*. The name is deliberately obnoxious. An agent can't stumble into it; it has to consciously assert "the user told me to do this," and that assertion sits right there in the command log if it ever lies.

Some things stay hard-blocked with no override at all — `git add -A`, for instance, because "accidentally commit every untracked file in the repo" is not a trust problem, it's a blast-radius problem. And chained commands can't smuggle a hard-blocked segment past an overridable one: `MARKER git commit --amend && git add -A` still gets rejected, because the non-overridable violation wins.

One implementation note: I had three near-identical copies of this hook — one each for Claude Code, Codex, and Gemini. Unifying them into one shared `git_guard.py` with thin per-tool adapters is what made the override feature a one-day change instead of a three-day one. Deduplicate your guardrails before you start tuning them.

The shift is subtle but real: instead of *capability* restrictions ("the agent can never merge"), I now have *authorization* restrictions ("the agent can merge when I say so"). Which is exactly how you'd treat a competent human collaborator.

## The feature that forced the issue: calling my agent

The other thing I built recently is what made the old model untenable: fully end-to-end encrypted voice calls to my agent, over [Matrix](https://matrix.org). The *exact same* agent I chat with — same memory, same tools, same context — except now I can ring it and talk. It can use whatever model fits the moment, and it actually speaks.

Why this matters for guardrails: last week I was away from my computer, on my phone, with a terminal over a flaky connection and genuinely poor internet. In that situation, "the agent prepares everything and you click the final button" collapses. There is no button. There's barely a keyboard. What works is: stay in one interface, say "merge it," and have the agent do the whole thing.

Staying in one interface is really the point. Every guardrail that forces me to context-switch to a browser to perform a ceremonial click is a tax on exactly the workflows where agents are most valuable — mobile, voice, low-bandwidth, hands-off.

## The takeaway

Guardrails made sense when agents were unreliable interns. As they become competent collaborators, the guardrails should evolve from "never" to "not without asking". Keep hard blocks for irreversible blast-radius mistakes. Convert everything else to explicit, auditable, per-action approval.

I'm giving the agent more. So far, it's giving more back.
