---
title: "Gemini 3 Pro: First Impressions"
subtitle: "Powerful but prone to panic attacks?"
summary: "I tested the new Gemini 3 Pro Preview for agentic coding. While it's powerful enough to build complex features in hours, it suffers from anxiety loops, aggressive force-pushing, and existential crises when you try to help it."
date: 2025-11-19
draft: false
featured: false
authors:
  - admin
tags:
  - AI
  - Gemini
  - agentic-coding
  - LLM
  - google
categories:
  - AI
  - Software Development
  - level:intermediate
image:
  caption: "Gemini 3 Pro"
  focal_point: ""
  placement: 2
  preview_only: false
---

I'm a huge fan of [agentic]({{< ref "/post/agentic-coding" >}}) [coding]({{< ref "/post/agentic-mobile-workflow" >}}).
I have the maximum subscriptions for both Claude and ChatGPT Pro, and since writing my [agentic coding]({{< ref "/post/agentic-coding" >}}) post, I mostly moved from Claude Code to Codex CLI with GPT-5 for my work that requires more complex reasoning.
Using Claude Code often feels frustrating in comparison now.

I also frequently pit them against each other, drafting parallel plans with each tool (I've done this at least 50 times).
The verdict is consistent.
**Claude Code, without exception, says that GPT‑5's solution is superior**, admitting it is more elegant and robust.
Claude also misses bugs during PR reviews that GPT-5 catches immediately.

That said, **Claude Code is significantly faster**, which makes it my go-to for simple refactors.
I also prefer its writing style for conversational answers and documentation.

But looking at the charts on **[Artificial Analysis](https://artificialanalysis.ai/)**, the new **Gemini 3 Pro** looks truly impressive.
It's at the top of nearly every benchmark.
I'm excited for Gemini to potentially take over some of GPT‑5's workload, so when **Gemini 3 Pro Preview** came out yesterday, I had to try it.

## The good: raw power

First off, the model is quite powerful.
Last night, I built a complex new feature for my [`agent-cli`](https://github.com/basnijholt/agent-cli) project in just two hours: a **RAG (Retrieval-Augmented Generation) proxy server**.

This tool acts as a middleware that sits between any OpenAI-compatible client and server (like Ollama or vLLM).
The server watches a specific folder, automatically indexes any PDF, Markdown, or text files into a local ChromaDB vector store, and injects relevant context into your prompts transparently.
You can see the full implementation in [PR #79](https://github.com/basnijholt/agent-cli/pull/79).

It even handles dynamic re-indexing when I drop new files in!
The speed and code quality for this task were genuinely impressive, and it handled the complexity of the RAG integration surprisingly well.

## The bad: panic attacks and infinite loops

However, the experience wasn't without its "personality quirks."
Twice, Gemini got stuck in a loop saying *"Should I? I should"* over and over again.

It also has a bad habit of amending commits multiple times and force-pushing them.
For me the Git history is a critical source of truth, and I don't like rewriting it because I might just have reviewed those commits already.

### The interface friction

I also found the Gemini CLI interface frustrating.
Basic tasks like selecting text or scrolling up are surprisingly difficult.
I'm not sure why they chose this design or why they feel the need to deviate from standard CLI behavior.
It feels like unnecessary friction in an otherwise promising tool.

### The "main branch" incident

Another scary moment: I asked if the PR was ready to be merged into `main`, and it went ahead and checked out the `main` branch and merged everything locally.
If I hadn't stopped it, I'm pretty sure it would have pushed the changes to the `main` branch directly as well.
I tend to use "yolo mode" for agentic coding because I feel like Git has my back, but this feels like a dangerous path to go down.

### Proofreading this post

I also asked Gemini to proofread this very blog post.
It made some suggestions—some I liked, others I didn't, so I reverted the ones I didn't want.
But in every single subsequent iteration, it would forcefully re-apply its rejected changes, adding emojis I had removed or rewriting sentences I had explicitly restored.

### Artifacts and existential crises

Also, when it commits, it just adds *all* files, including debugging logs and build artifacts.
When it realizes its mistake, it tries to fix it.
But if I try to help at the same time (like removing the files myself while it's thinking), it gets extremely confused.

It spirals into an **existential crisis**, claiming that I committed the file but now "it is gone."
*"What is going on?"* it asks, spending a lot of tokens (and time) looking at `git reflog`s and questioning its own existence.
Even when I stop it and explicitly say that I deleted the file and to please continue, it completely ignores me and continues its panic attack.
I experienced this pattern of ignoring instructions multiple times.

## Conclusion

Gemini 3 Pro shows massive potential.
The raw coding ability is there, and building a **clean** RAG proxy in two hours is great!
But the agentic behavior needs some serious work: the loops, the force pushes, ignoring instructions, and the confusion when reality doesn't match its internal state.

This is just **day one**, so I'm confident many of these issues will get ironed out.
I don't love the interface, but given that [`gemini-cli`](https://github.com/google-gemini/gemini-cli) is open source with ≈400 contributors, I expect rapid improvements, especially now that the model is finally good with agentic workflows!
