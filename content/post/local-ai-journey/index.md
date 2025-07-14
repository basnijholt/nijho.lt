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
Then it hit me: I could also use it for gaming, duh.
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

{{% callout note %}}
**TL;DR:** This post is the story of how a quest for gaming turned into a deep dive into local, private AI.
I'll share the two open-source Python packages that came out of it, `agent-cli` and `AIBrain`, and the lessons I learned along the way.
{{% /callout %}}

## 2. The Rocky Road to a Working Setup

Before I could even get to the fun AI stuff, I had to wrestle with the machine itself.
Like many Linux enthusiasts, I started with Pop!_OS, but the infamous NVIDIA driver issues quickly became a roadblock.
After some frustration and a lot of troubleshooting, I made the switch to **NixOS**.
This turned out to be a great decision, providing a stable and reproducible environment that finally tamed the 3090.
Your own mileage may vary, but for me, NixOS was the solid foundation I needed.

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
The vision is to create a "life-OS"—a private, local AI that processes all my personal data (emails, calendar, files, photos) to generate summaries and answer questions.

This project led me to explore the landscape of agentic frameworks.
I started with **CrewAI**, but I quickly found that despite the hype and funding, it had some painful problems.
I decided to switch to **LangGraph**, which felt more robust.
I also chose to avoid **Pydantic AI** because its **Ollama** support is just a wrapper around the OpenAI-compatible API, which doesn't expose all the useful options.

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
