---
title: "Frontier-level dictation on your iPhone keyboard, self-hosted"
subtitle: "Fast, private iPhone dictation from my home GPU, even from a bar in the Netherlands"
summary: "A small Docker recipe for running Diction's streaming gateway against Qwen3-ASR through Agent CLI, plus a test from a bar in the Netherlands, an ocean away from the GPU."
date: 2026-09-22
draft: false
featured: false
authors:
  - admin
tags:
  - diction
  - agent-cli
  - qwen
  - speech-to-text
  - self-hosting
  - ios
  - docker
  - ai
categories:
  - AI
  - Self-Hosting
  - level:intermediate
image:
  caption: ""
  focal_point: ""
  placement: 2
  preview_only: false
---

On a recent month-long trip visiting family in Europe, I did a lot of work from my phone, using [my mobile coding workflow]({{< ref "/post/agentic-mobile-workflow" >}}).
It still boggles my mind that real, productive work from a phone is possible now.
Most of that work is talking to coding agents, and the built-in iOS dictation is garbage for that.
I had an iOS Shortcut that sent recordings to [Agent CLI](https://github.com/basnijholt/agent-cli), [my local AI toolbox]({{< ref "/post/auto-install-extras" >}}), running at home instead.
The problem was that the recording screen takes over the whole display, so I could not see the thing I was commenting on.
The transcript then landed in my clipboard, and I had to paste it myself.

So I threw my principles overboard and installed [Wispr Flow](https://wisprflow.ai), a voice keyboard for iOS.
I loved it instantly.
iOS does not let keyboards use the microphone, so the keyboard's button hands off to the Wispr Flow app, which keeps recording in the background.
I was less happy about that, since it meant a closed-source app always had the microphone open and sent my voice to their servers.
I was on the free plan, so I was probably the product.
I also hit the free weekly word limit very quickly, and started looking for an alternative.

That is how I found [Diction](https://apps.apple.com/app/id6759807364), which has since become my favorite app when I'm away from my laptop.
It works the same way, background recording included.
The difference is that it has a self-hosted mode with an open-source gateway, so my voice goes to a machine I own instead of their servers.

I run the [gateway](https://github.com/DictionLabs/Diction) on my home machine in the U.S., reachable only over my private network.
The gateway streams audio to Agent CLI, which runs Alibaba's [`Qwen/Qwen3-ASR-1.7B-hf`](https://huggingface.co/Qwen/Qwen3-ASR-1.7B-hf) on an RTX 3090 behind an OpenAI-compatible transcription endpoint.
There is no LLM cleanup step, so Diction's Writing Style and Tones features do not work with this setup.
I don't miss them: Qwen's raw transcription is already good enough for me.

## 1. Why Qwen?

For the longest time I used [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) with Whisper large-v3.
Whisper is still the default choice for most people, but many newer models beat it.
I tried some of them, including NVIDIA's [Parakeet](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3).
Parakeet is fast, but it cannot take custom instructions.
Those instructions are how Diction's **My Words** feature biases a transcription toward specialized names.

At the start of September, I looked at the [Hugging Face Open ASR Leaderboard](https://huggingface.co/spaces/hf-audio/open_asr_leaderboard), which tests speech-to-text models on the same recordings and ranks them.
The score is the word error rate (WER): the share of words a model gets wrong, counting words it swaps, drops, or makes up.
Lower is better, and a WER of 4% means about one wrong word in every 25.
The test recordings range from audiobooks and podcasts to meetings and earnings calls, so the average says more than any single clean benchmark.

These are the averages on the public English test sets as of September 19, 2026:

| Model | WER | Can I run it at home? |
|---|---|---|
| Zoom Scribe v2 Pro | 3.6% | No, paid API (#1 overall) |
| ElevenLabs Scribe v2 | 4.0% | No, paid API |
| **Qwen3-ASR 1.7B** | **4.3%** | **Yes, Apache-2.0** |
| AssemblyAI Universal-3.5 Pro | 4.3% | No, paid API |
| NVIDIA Parakeet TDT 0.6B v3 | 4.9% | Yes |
| OpenAI Whisper large-v3 | 5.8% | Yes |

I picked the best model on the board whose weights you can download: Qwen3-ASR 1.7B.
It lands within a point of the best paid API, which is what I mean by frontier-level.
Since I maintain Agent CLI, I told an agent to add a Qwen backend, and shortly afterward [it had landed](https://github.com/basnijholt/agent-cli/pull/636) and was running on my server.

Agent CLI's transcription server loads a model on the first request and unloads it after an idle timeout, so the model only takes VRAM while I use it.
The same process serves an OpenAI-compatible API, which the Diction gateway talks to, and the [Wyoming protocol](https://www.home-assistant.io/integrations/wyoming/) that Home Assistant uses for local voice.

## 2. The recipe

You need an NVIDIA GPU with the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html), Docker Compose 2.30 or newer, and a private route from your iPhone to the server.
I use Headscale, but Tailscale or plain WireGuard works just as well.
Do not expose the gateway to the public internet.

### Add Agent CLI

Save the following as `Dockerfile.agent-cli` in an empty directory.
It starts with the CUDA image from Agent CLI and adds the Transformers dependencies needed for Qwen:

```dockerfile
FROM ghcr.io/basnijholt/agent-cli-whisper:latest-cuda

USER root

ARG AGENT_CLI_VERSION=0.103.0

RUN uv pip install \
      --python /app/.venv/bin/python \
      --upgrade \
      "agent-cli[whisper-transformers]==${AGENT_CLI_VERSION}"

RUN apt-get update \
    && apt-get install --yes --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*

USER whisper
```

### Add the Diction gateway

Save this as `compose.yaml` next to the Dockerfile.
It points Diction's gateway at Agent CLI's transcription port.
`WHISPER_TTL` raises the idle timeout from the default five minutes to a day, so dictation rarely waits for a reload:

```yaml
services:
  asr:
    image: agent-cli-whisper-qwen:0.103.0
    build:
      context: .
      dockerfile: Dockerfile.agent-cli
      args:
        AGENT_CLI_VERSION: "0.103.0"
    environment:
      WHISPER_MODEL: Qwen/Qwen3-ASR-1.7B-hf
      WHISPER_EXTRA_ARGS: --backend transformers
      WHISPER_TTL: "86400"
      WHISPER_LOG_LEVEL: info
      WHISPER_DEVICE: cuda
    volumes:
      - model-cache:/home/whisper/.cache
    gpus: all
    restart: unless-stopped

  gateway:
    image: dictionlabs/gateway:v13.0
    depends_on:
      - asr
    environment:
      CUSTOM_BACKEND_URL: http://asr:10301
      CUSTOM_BACKEND_MODEL: Qwen/Qwen3-ASR-1.7B-hf
      CUSTOM_BACKEND_CANONICAL_ID: Qwen/Qwen3-ASR-1.7B-hf
      CUSTOM_BACKEND_NEEDS_WAV: "true"
    ports:
      - "8080:8080"
    restart: unless-stopped

volumes:
  model-cache:
```

### Start it and connect the app

Build and start both services:

```bash
docker compose up -d --build
```

The first transcription downloads Qwen into the `model-cache` volume, so that request can take a few minutes.
`docker compose logs -f` shows the progress.

On the iPhone, go to **Settings → General → Keyboard → Keyboards → Add New Keyboard → Diction**.
Tap Diction in the keyboard list, enable **Allow Full Access**, and grant microphone access when prompted.
Then open Diction, go to **Preferences → Mode → Self-Hosted**, enter `http://<private-server-ip>:8080`, and tap **Test connection**.

{{% callout note %}}
**A small upstream detour:** Diction's **My Words** feature was not reaching the ASR backend during streaming, so I opened [Diction PR #20](https://github.com/DictionLabs/Diction/pull/20) to forward those words as the transcription prompt.
With the fix, package names such as `PipeFunc` and `MindRoom` come back with the correct spelling and capitalization.
It shipped in gateway v13.0, which is why the Compose file needs at least that version.
{{% /callout %}}

On my machine, Qwen3-ASR 1.7B uses about 4.7 GiB of GPU memory and roughly 3 GiB of system memory while loaded.

## 3. The bar test

A day later, I met a friend in a bar in the Netherlands and wanted to let him try it.

He was already on my tailnet for some of my other self-hosted services, so his phone only needed an ACL change to reach the gateway.
I opened the terminal app on my phone, connected to an agent, and dictated that change.
In less than a minute, Diction was connected and working on his phone.
His speech crossed the Atlantic, was transcribed by Qwen on my home GPU, and appeared back in the app with barely any delay.

That moment sold the whole setup to me.
I was in a bar without a laptop, and I used dictation to grant access to the dictation service.
