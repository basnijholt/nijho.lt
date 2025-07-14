---
title: "🎮 From Gaming Rig to AI Brain: My Accidental Deep Dive into Local AI"
subtitle: "How I bought a gaming PC with a 3090 but ended up building two local-first Python AI packages instead."
summary: "A personal journey of buying a gaming PC and accidentally falling down the rabbit hole of local, private AI.
I share my experience building agent-cli and AIBrain, the tools I used, and the lessons I learned along the way."
date: 2025-07-14
draft: false
featured: true
authors:
  - admin
tags:
  - python
  - ai
  - llm
  - ollama
  - local-first
  - open-source
  - nixos
categories:
  - Technology
  - Software Development
  - "level:intermediate"
image:
  caption: 'A collage of the technologies that powered my local AI journey.'
  focal_point: 'Center'
  placement: 2
  preview_only: false
---

{{< toc >}}

## 1. Introduction: The Unplayed Games

I've wanted to dabble with local AI for a long time, but I never found it worth it to buy a GPU just for that.
Then it hit me: I could also use it for gaming (duh).
Because I really enjoyed "The Last of Us" series, I thought, "okay why not play this Last of Us game on the PC".
This was the push I needed.
So, a couple of weeks ago, I convinced myself to buy someone's old gaming machine.
After many deep research calls with ChatGPT about the best bang-for-the-buck consumer-grade GPU, I landed on an NVIDIA 3090.
I found a beast of a machine for $1350, and my initial idea was set.

Fast forward four weeks.
I have installed many games, but I have yet to play a single minute.
Instead, I've been on an unexpected and intense journey into the world of local AI.
That gaming rig has been humming away, but not rendering virtual worlds.
It's been training, transcribing, and thinking.

I'm writing this post simply because I am so enthusiastic about this journey.
I've found that local models are surprisingly powerful for specific use cases.
Of course, they aren't going to replace Gemini or Claude for coding, but for many other applications, they work incredibly well.
Lately, I've been so obsessed with this that I'm sleeping significantly less and spending all my free hours working on it.

{{% callout note %}}
**TL;DR:** This post is the story of how a quest for gaming turned into a deep dive into local, private AI.
I'll share the two open-source Python packages that came out of it, [`agent-cli`](https://github.com/basnijholt/agent-cli) and [`AIBrain`](https://github.com/basnijholt/aibrain), and the lessons I learned along the way.
{{% /callout %}}

## 2. The Rocky Road to a Working Setup

Before I could even get to the fun AI stuff, I had to wrestle with the machine itself.
I started with Pop!_OS, which is supposed to be a great out of the box solution that "just works".
However, it's been a long time since I used Linux on the desktop; my experience is almost exclusively with servers.
I quickly installed some of the wrong packages and ended up debugging stuff in Grub.
I got frustrated with the different commands and realized that reproducing the system was going to be a pain.
Since I've grown to love Nix on my Mac with Nix-Darwin, I decided to switch the whole system to **NixOS**.
This has been an amazing decision.
Even though there are many pain points with Nix, I think it is well worth it.

## 3. The First Victory: `agent-cli` 🐍

With a stable system, I quickly got started with a few scripts.
These soon evolved into my first real project of this adventure: [`agent-cli`](https://github.com/basnijholt/agent-cli).

`agent-cli` is a collection of **local-first**, AI-powered command-line agents that run entirely on your machine.
The core philosophy is privacy; your data never leaves your computer.
It's designed for seamless integration with system-wide hotkeys, and I'm now using it constantly.

Instead of typing, I now dictate almost everything.
A quick hotkey, and `agent-cli transcribe` turns my speech into text.
Another hotkey, and `agent-cli autocorrect` cleans it up using a local LLM running on **Ollama**.
It has genuinely streamlined my workflow.

The toolkit includes:
*   `autocorrect`: Fixes grammar and spelling.
*   `transcribe`: Uses a local Whisper model for speech-to-text.
*   `speak`: Converts text to speech with a local TTS engine.
*   `voice-edit`: A voice-powered clipboard assistant.
*   `assistant`: A hands-free voice assistant using a wake word.
*   `chat`: A conversational AI with tool-calling capabilities.

It's been a fantastic success in my personal workflow, and it's all open-source for you to try.

## 4. The Grand Ambition: `AIBrain` 🧠

My second package, [`AIBrain`](https://github.com/basnijholt/aibrain), is a much larger endeavor.
The vision is to create a "life-OS"—a private, local AI that processes all my personal data (emails, calendar, files, photos, messages, browser history, location data) to generate summaries and answer questions.

This project led me to explore the landscape of agentic frameworks.
I started with **CrewAI**, but I quickly found that despite the hype and funding, it had some painful problems (specifically [this issue](https://github.com/crewAIInc/crewAI/issues/3031) where things just fail without any helpful error messages).
I decided to switch to **LangGraph**, which felt more robust.
I also chose to not use **PydanticAI** (which I used in `agent-cli`) because its **Ollama** support is just a wrapper around the OpenAI-compatible API, which doesn't expose all the useful options (I even opened [a PR](https://github.com/ollama/ollama/pull/11249/) in Ollama to make its OpenAI compatible API more feature-complete, but it has not been merged yet).

The core infrastructure of `AIBrain` is ready.
It can index emails, calendar events, and files in various formats (PDF, Excel, PowerPoint, images).
However, I've hit a significant challenge.

{{% callout warning %}}
**The Performance Bottleneck**

When I started processing just a few days' worth of emails, my computer sounded like it was going to catch on fire.
Processing hundreds of gigabytes of personal data is a massive undertaking, and it's clear that my current approach isn't scalable enough.
{{% /callout %}}

## 5. Conclusion: The Journey Continues

This past month has been a whirlwind.
I set out to play games and ended up with two open-source AI packages and a much deeper appreciation for the power sitting in a consumer-grade GPU.
It's incredible what you can achieve with local hardware today.

`agent-cli` is a finished, polished tool that I use daily.
`AIBrain` is a much bigger dream, and I'm still figuring out how to solve the performance puzzle to make it truly practical.

This journey has reinforced my passion for local-first software and open-source development.
The future of personal, private AI is being built right now, not just in large corporate labs, but in the homes of hobbyists tinkering with their gaming rigs.

I'd be curious to hear how others are tackling large-scale local data processing.
Feel free to share your thoughts or ideas!
