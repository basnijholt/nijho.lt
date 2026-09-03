---
title: "Self-hosting Diction with Agent CLI and Qwen"
subtitle: "Fast, private iPhone dictation from my home GPU—even from a bar in the Netherlands"
summary: "A small Docker recipe for running Diction's streaming gateway against Qwen3-ASR through Agent CLI, plus the moment it proved itself while I was away from my laptop."
date: 2026-09-03
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

[Diction](https://apps.apple.com/app/id6759807364) has quickly become my favorite app while on vacation and away from my laptop.
It adds a voice keyboard to iOS, so I can dictate into any app without recording audio, running a Shortcut, waiting, copying, and pasting.
It is the next iteration of [my mobile coding workflow]({{< ref "/post/agentic-mobile-workflow" >}}), replacing its iOS Shortcut and clipboard dance with a keyboard that is always available.

I self-host its [open-source gateway](https://github.com/DictionLabs/Diction) on my home machine in the U.S.
The gateway streams audio to [`agent-cli`](https://github.com/basnijholt/agent-cli), which exposes an OpenAI-compatible transcription endpoint backed by [Qwen3-ASR 1.7B](https://huggingface.co/Qwen/Qwen3-ASR-1.7B-hf).
There is no LLM cleanup step: Qwen's raw transcription is already good enough for me.

{{% callout note %}}
**The entire path:** Diction on my iPhone → private VPN → Diction gateway → Agent CLI → Qwen3-ASR on my RTX 3090.
{{% /callout %}}

## 1. Why Qwen?

For the longest time I used [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) with Whisper large-v3.
I also experimented with other speech models, including NVIDIA's [Parakeet](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3).
Parakeet is fast, but it cannot take custom instructions.
Those instructions are how Diction's **My Words** feature biases a transcription toward specialized names.

Two days before writing this, I checked the [Hugging Face Open ASR Leaderboard](https://huggingface.co/spaces/hf-audio/open_asr_leaderboard), where Qwen3-ASR caught my attention.
I told an agent to implement support for it in Agent CLI, and shortly afterward [the new backend had landed](https://github.com/basnijholt/agent-cli/pull/636) and was running on my server.
I maintain Agent CLI and have [written about how it grew from a voice helper into a local AI toolbox]({{< ref "/post/auto-install-extras" >}}), so adding a Transformers-based ASR backend was a natural fit.

## 2. The recipe

You need an NVIDIA GPU with the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html), Docker Compose, and a private route from your iPhone to the server.
I use a Headscale-managed network, but Tailscale or plain WireGuard works just as well.

Create an empty directory for the stack:

```bash
mkdir diction-qwen
cd diction-qwen
```

### Add Agent CLI

Save the following as `Dockerfile.agent-cli`.
It starts with the CUDA image from Agent CLI and adds the Transformers dependencies needed for Qwen:

```dockerfile
FROM ghcr.io/basnijholt/agent-cli-whisper:latest-cuda

USER root

ARG AGENT_CLI_VERSION=0.103.0

RUN uv pip install \
      --python /app/.venv/bin/python \
      --upgrade \
      "agent-cli[whisper-transformers]==${AGENT_CLI_VERSION}" \
    && /app/.venv/bin/python -c \
      "import importlib.metadata as m; import librosa, torch, transformers; assert m.version('agent-cli') == '${AGENT_CLI_VERSION}'"

RUN apt-get update \
    && apt-get install --yes --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*

USER whisper
```

### Add the Diction gateway

Save this as `compose.yaml` next to the Dockerfile.
It starts Agent CLI on its OpenAI-compatible transcription port and points Diction's streaming gateway at it.
The `gpus: all` line lets Docker select the NVIDIA GPU:

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
    image: diction-gateway:streaming-custom-words-66227175
    build:
      context: https://github.com/basnijholt/Diction.git#596573529f0d291c7845447e4eb061c2db2532d6:gateway
      args:
        IMAGE_REF: pr-20-5965735
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

Build the images, start both services, and check the gateway:

```bash
docker compose up -d --build
docker compose logs -f
curl http://localhost:8080/health
```

The first start downloads Qwen into the `model-cache` volume.
Once the model is ready, open Diction and go to **Preferences → Mode → Self-Hosted**, enter `http://<private-server-ip>:8080`, and tap **Test connection**.

I route this endpoint through my existing reverse proxy, but only clients on my private network can reach it.
Do not put it directly on the public internet; use something like Tailscale, Headscale, or WireGuard, or protect it at your reverse proxy.

The pinned gateway build above includes [Diction PR #20](https://github.com/DictionLabs/Diction/pull/20), which forwards the app's **My Words** list during streaming.
That made package names such as `PipeFunc` and `MindRoom` come back with the correct spelling and capitalization in my live test.
Once the fix is part of an official Diction release, the custom build can be replaced by `dictionlabs/gateway:latest`.

On my machine, Qwen3-ASR 1.7B uses about **4.7 GiB of GPU memory** and roughly **3 GiB of system memory** while loaded.
Keeping the model warm makes the interaction feel immediate.

## 3. The bar test

Yesterday I met a friend in a bar in the Netherlands and wanted to let him try it.
My server—and the RTX 3090 doing the transcription—was at home in the U.S.

I opened the terminal app on my phone, connected to an agent, and dictated an instruction to update the network ACLs so his phone could reach the gateway.
In literally less than a minute, Diction was connected and working on his phone.
His speech crossed the Atlantic, was transcribed by Qwen on my home GPU, and appeared back in the app with incredibly low latency.

That moment sold the whole setup to me.
It was not a carefully prepared demo: I was in a bar, had no laptop, and used dictation itself to grant access to the dictation service.

Diction behaves like a normal keyboard, while I retain control over where the audio goes and which model handles it.

The only feature I intentionally leave out is AI rewriting.
Writing Style and Tones need a generative LLM cleanup stage, which this minimal setup does not run.
For my use, fast streaming transcription plus **My Words** is the better trade-off.
