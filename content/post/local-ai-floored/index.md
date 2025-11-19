---
title: "My local GPUs are beating last year's SOTA models"
subtitle: "Running Qwen3-VL-32B on my own hardware and beating the cloud"
summary: "I bought a second GPU and discovered that local vision models like Qwen3-VL-32B can now identify niche books on my shelf better than GPT-4. A look at how local AI is catching up to and even surpassing cloud giants."
date: 2025-11-19
draft: false
featured: true
authors:
  - admin
tags:
  - AI
  - Local-LLM
  - GPU
  - Hardware
  - Qwen
  - Open-Source
  - Privacy
categories:
  - AI
  - Hardware
  - level:intermediate
image:
  caption: "Artificial Analysis Intelligence Index showing Qwen3-VL-32B-Instruct's performance"
  focal_point: "Smart"
  placement: 2
  preview_only: false
---

{{< toc >}}

## 1. The "Exploding Head" Moment

I've been exploring [local AI]({{< ref "/post/local-ai-journey" >}}) for a while now, originally buying an RTX 3090 for "gaming" (which, let's be honest, was just a cover story for running LLMs).
But recently, I bought a second GPU 3090 to run even bigger models, and the capabilities I'm seeing on my own hardware are actually insane.
It’s not just "good for a local model" anymore—it is genuinely competing with the state-of-the-art cloud models of just last year.

The moment that absolutely floored me happened yesterday.
I loaded up **[Qwen3-VL-32B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-32B-Instruct)**, a vision-language model that just came out this month.
It's large, but it fits comfortably across my two GPUs.

I decided to give it a real-world test.
I took a photo of my bookcase—a messy, chaotic collection of spines—and just asked it to explain what it saw.

**It literally told me exactly about every single book.**

We aren't talking about recognizing "Harry Potter" here.
It identified:
- Books that were **only sold in the Netherlands**.
- Extremely **niche quantum transport textbooks** (the kind only a few thousand people in the world own).
- Old **Finnish folklore books** with obscure covers.

It was actually insane that this was running entirely on my computer, with no data leaving my house.
In my experience, even GPT-4 often hallucinates or speaks in generalities with complex images like this.
Qwen nailed it.

## 2. The Data Backs It Up

It turns out my anecdotal experience isn't unique.
If you look at the **[Artificial Analysis Intelligence Index](https://artificialanalysis.ai/models/qwen3-vl-32b-reasoning?models=gpt-oss-20b%2Cgpt-oss-120b%2Cgpt-5-1%2Cgpt-5-1-non-reasoning%2Cgpt-5-low%2Cgpt-5-codex%2Cllama-4-maverick%2Cgemini-3-pro%2Cgemini-2-5-pro%2Cgemini-2-5-flash-preview-09-2025-reasoning%2Cclaude-4-5-sonnet-thinking%2Cclaude-4-5-haiku-reasoning%2Cgrok-4-fast-reasoning%2Cgrok-4%2Cqwen3-235b-a22b-instruct-2507-reasoning%2Cqwen3-vl-32b-reasoning%2Cqwen3-vl-235b-a22b-reasoning%2Co1%2Cgpt-4-1%2Cgpt-4o-chatgpt%2Cclaude-3-7-sonnet-thinking&intelligence=artificial-analysis-intelligence-index)**, we are witnessing a historic crossover point.

Open-weights models that you can run locally are now outperforming the cloud giants in key metrics.
The index shows **Qwen3-VL-32B** (and its reasoning variants) standing toe-to-toe with, and often beating:
- **Claude 3.7 Sonnet**
- **GPT-5.1 (non-reasoning)**
- **GPT-4o**
- **Gemini 2.5 Pro**

This is the model that essentially set off the AI revolution, and now I have something *more powerful* running on my own rig.

## 3. Privacy, Speed, and Economics

There's a funny realization I had while watching the tokens stream in.
I’m still glad to be paying $200 a month because the state‑of‑the‑art models are currently better than what you can run locally.
However, local models are catching up.
There are now some models that compete at the absolute top, but running them on simple consumer‑grade GPUs at home is not feasible.

Don't get me wrong—I'm still a power user who pays for the absolute bleeding edge (like [Codex CLI with GPT-5]({{< ref "/post/agentic-coding" >}})).
I am no longer satisfied with "GPT-4 level" results for my coding work and would much rather pay $200 for even better models.
But for a huge chunk of use cases, **local is becoming king**.

### The Speed Factor
It's not just about privacy (though knowing my photos aren't training OpenAI's next model is nice).
It's about speed.
I'm getting about **200 tokens per second** on my dual-GPU setup.
That is roughly **4x faster** than what I typically get from the cloud APIs during peak hours.
It feels instantaneous.
Conversations flow naturally without that awkward "thinking" pause that reminds you you're talking to a server farm in Virginia.

## 4. Conclusion: I Need More GPUs

We've reached a tipping point.
Local AI isn't the "dumber but private" alternative anymore.
For many tasks, it is the **smarter, faster, and private** alternative.

The fact that I can run a vision model that recognizes obscure Dutch literature better than the world's leading cloud API is mind-blowing.
It makes me wonder what will be possible on consumer hardware in another year.

The only downside?
Now I definitely need more GPUs.
