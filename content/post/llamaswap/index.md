---
title: "🦙 Switching from Ollama to llama-swap + llama.cpp: the power user's choice"
subtitle: "Why I finally ditched Ollama after upgrading to dual RTX 3090s and needing true control over my local AI models"
summary: "I started writing this post four months ago when a specific model broke in Ollama. I initially went back to Ollama out of laziness, but after upgrading to dual RTX 3090s, I realized that for serious multi-GPU inference and RAM offloading, you need the raw control of llama.cpp. Here is how I manage my new 48GB VRAM setup declaratively with NixOS."
date: 2025-11-29
draft: false
featured: true
authors:
  - admin
tags:
  - llama-cpp
  - llama-swap
  - ollama
  - local-ai
  - llm
  - gguf
  - nixos
  - dual-gpu
  - rtx3090
categories:
  - Technology
  - AI
  - "level:intermediate"
---

{{< toc >}}

## The draft I never published

I started writing this blog post four months ago.
Back then, I was frustrated because a specific model I wanted to try—`gpt-oss-20b`—was completely broken in [Ollama](https://ollama.com/).
I went down the rabbit hole, set up [`llama-swap`](https://github.com/mostlygeek/llama-swap) and [`llama.cpp`](https://github.com/ggml-org/llama.cpp), got the model working perfectly, wrote half this post... and then I stopped.

Why? **Laziness.**
Once the novelty of that specific model wore off, I drifted back to Ollama.
The real convenience of Ollama was never the `ollama run` command—I almost exclusively interact with my models via the API using my own tools like [agent-cli](https://github.com/basnijholt/agent-cli).
The convenience was `ollama pull`.
Being able to grab a model with one command and have it "just work" was great.

But as a [NixOS](/post/proxmox-to-nixos/) user, this imperative convenience is actually a flaw.
I want my system to be declarative.
I want my model configuration committed to git, not hiding in a local database.
So I let convenience win for a while, but it always felt wrong.

But last month, that changed.
I upgraded my hobbyist AI rig by adding a **second RTX 3090**.
Suddenly, I had 48GB of VRAM and a whole new set of problems—and possibilities.
I wanted to run massive models (like `gpt-oss-120b` or `Qwen-3-VL-32B` with a huge context window).
I needed to balance layers between two GPUs.
I needed to spill specific parts of the model into system RAM without crashing.

When you start pushing hardware to its limits, "magic" abstractions like Ollama stop being helpful and start getting in the way.
I realized that `llama.cpp` isn't just a backend; it is *the* place where development happens.
If you want to use split-mode inference, granular CPU offloading, or the latest quantization tricks immediately, there is no alternative.

So, I dusted off this draft, updated my Nix configuration, and I've been running `llama-swap` full-time for a month.
I'm finally ready to vouch for it.

## The original trigger: broken models

Four months ago, my frustration stemmed from compatibility.
I was trying to run `gpt-oss-20b`, a model that required specific chat templates and GGUF handling that Ollama simply broke.
Ollama had forked the inference engine to rush out support, leading to mangled templates and poor performance.
Maintainers of `llama.cpp` even called out the "day-1 support" rush that led to suboptimal, incompatible implementations.

While Ollama has improved since then, the pattern remains: it is always a wrapper that lags behind the core innovation happening in `llama.cpp`.
If you want the latest features *now*, you go to the source.

## The catalyst: dual GPUs and control

With a single GPU, you usually either fit the model or you don't.
With two GPUs (and 64GB of system RAM), things get interesting.
You enter the territory of **heterogeneous inference**.

Ollama tries to handle splitting automatically, but I found myself fighting it.
I wanted to say: *"Put 40 layers on GPU 0, 40 layers on GPU 1, and keep the KV cache here."*
Or: *"This model is slightly too big for VRAM; I want to offload exactly the last 10% to CPU RAM because I have fast DDR5."*

With `llama.cpp` directly, this is just a command line flag.
With `llama-swap`, I can define this behavior per-model in a config file:

```yaml
"qwen2.5-72b-instruct":
  cmd: |
    ${pkgs.llama-cpp}/bin/llama-server
    --hf-repo Qwen/Qwen2.5-72B-Instruct-GGUF
    --hf-file qwen2.5-72b-instruct-q4_k_m.gguf
    --port ${PORT}
    --ctx-size 8192
    --n-gpu-layers 80   # Precise control over offloading
    --split-mode row    # Essential for dual 3090s to maximize bandwidth!
    --main-gpu 0
```

This level of granularity turned my rig from a "black box" into a tunable instrument.
The `--split-mode row` flag alone is a game-changer for dual GPUs, splitting the computation across cards to utilize combined bandwidth, something Ollama exposes poorly or not at all.

## API compatibility and the "switch"

One of the reasons I hesitated to switch was the fear of breaking my existing workflows.
I use [agent-cli](https://github.com/basnijholt/agent-cli) and other custom Python scripts daily.
But it turned out to be a non-issue.
Both Ollama and `llama-swap` (wrapping `llama-server`) expose an OpenAI-compatible API.

Once I adopted the pattern of setting a custom `OPENAI_BASE_URL` in my projects, the backend became irrelevant.
My tools don't care if they are talking to `api.openai.com`, a local Ollama instance, or `llama-swap`.
They just send JSON and get JSON back.
This standardization meant I could swap the entire inference engine underneath my applications without changing a single line of their code.

## My NixOS setup

Since I manage my entire system with Nix, setting up `llama-swap` and pinning `llama-cpp` to the absolute bleeding edge was surprisingly elegant.
I even wrote an [auto-update script](https://github.com/basnijholt/dotfiles/blob/51c7af46e62a7d13b4ff497380c8b58c05ed81c8/configs/nixos/scripts/update_overrides.py) to ensure I'm always on the latest commit.

This is where my [NixOS build cache](/post/nixos-cache/) shines.
Unlike Ollama, which releases every few weeks, `llama.cpp` can have multiple releases *a day*.
My cache server runs this update script automatically, builds the new binaries, and serves them to my workstation.
I get the absolute latest performance improvements without ever compiling source code locally.

Here's my complete configuration (see [`package-overrides.nix`](https://github.com/basnijholt/dotfiles/blob/51c7af46e62a7d13b4ff497380c8b58c05ed81c8/configs/nixos/hosts/pc/package-overrides.nix#L28-L76) and [`ai.nix`](https://github.com/basnijholt/dotfiles/blob/51c7af46e62a7d13b4ff497380c8b58c05ed81c8/configs/nixos/hosts/pc/ai.nix#L360-L380)):

```nix
# Override llama-cpp to latest version with CUDA support
llama-cpp =
  (pkgs.llama-cpp.override {
    cudaSupport = true;
    rocmSupport = false;
    metalSupport = false;
    # Enable BLAS for optimized CPU layer performance (OpenBLAS)
    blasSupport = true;
  }).overrideAttrs
    (oldAttrs: rec {
      version = "7205";
      src = pkgs.fetchFromGitHub {
        owner = "ggml-org";
        repo = "llama.cpp";
        tag = "b${version}";
        hash = "sha256-1CcYbc8RWAPVz8hoxKEmbAgQesC1oGFZ3fhfuU5vmOc=";
        leaveDotGit = true;
        postFetch = ''
          git -C "$out" rev-parse --short HEAD > $out/COMMIT
          find "$out" -name .git -print0 | xargs -0 rm -rf
        '';
      };
      # Enable native CPU optimizations (AVX, AVX2, etc.)
      cmakeFlags = (oldAttrs.cmakeFlags or []) ++ [
        "-DGGML_NATIVE=ON"
      ];
      # Disable Nix's march=native stripping
      preConfigure = ''
        export NIX_ENFORCE_NO_NATIVE=0
        ${oldAttrs.preConfigure or ""}
      '';
    });

# llama-swap from GitHub releases
llama-swap = pkgs.runCommand "llama-swap" { } ''
  mkdir -p $out/bin
  tar -xzf ${
    pkgs.fetchurl {
      url = "https://github.com/mostlygeek/llama-swap/releases/download/v175/llama-swap_175_linux_amd64.tar.gz";
      hash = "sha256-zeyVz0ldMxV4HKK+u5TtAozfRI6IJmeBo92IJTgkGrQ=";
    }
  } -C $out/bin
  chmod +x $out/bin/llama-swap
'';

# Configure llama-swap as a systemd service
systemd.services.llama-swap = {
  description = "llama-swap - OpenAI compatible proxy with automatic model swapping";
  after = [ "network.target" ];
  wantedBy = [ "multi-user.target" ];
  
  serviceConfig = {
    Type = "simple";
    User = "basnijholt";
    Group = "users";
    # Point to your declarative config file
    ExecStart = "${pkgs.llama-swap}/bin/llama-swap --config /etc/llama-swap/config.yaml --listen 0.0.0.0:9292 --watch-config";
    Restart = "always";
    RestartSec = 10;
    
    # Environment for CUDA support
    Environment = [
      "PATH=/run/current-system/sw/bin"
      "LD_LIBRARY_PATH=/run/opengl-driver/lib:/run/opengl-driver-32/lib"
    ];
  };
};
```

## What I gained (and lost)

### Advantages of llama-swap + llama.cpp

- ✅ **Heterogeneous Compute**: Perfectly balance loads between GPUs and CPU RAM.
- ✅ **Bleeding Edge**: I use features (like new quantization types) the day they land in `llama.cpp`.
- ✅ **Zero idle VRAM**: Models unload completely when not in use.
- ✅ **Transparent operation**: No hidden prompts or "helpful" formatting that breaks complex tasks.

### The trade-off

The main trade-off is "laziness."
You can't just `ollama pull new-model` and have it appear.
You have to find the GGUF on HuggingFace, decide on the quantization (Q4_K_M? Q6_K?), and add 5 lines of YAML to your config.

But honestly? That's a feature, not a bug.
It forces you to understand *what* you are running.
It stops you from running a quantized model that is too stupid for your task just because it was the default.
And for a NixOS user, putting that configuration into code instead of a hidden database is exactly how it should be.

## Conclusion: maturing as an AI hobbyist

My switch back to `llama-swap` wasn't about fixing a bug; it was about outgrowing a tool.
Ollama is the "starter bike" of local AI—fantastic for getting rolling.
But when you add a second GPU, start caring about tokens per second, and want to maximize every gigabyte of your 48GB VRAM buffer, you need a manual transmission.

For anyone else building a hobbyist multi-GPU rig: stop fighting the abstraction.
Go to the source. The control is worth it.

---

*Check out my [NixOS configuration](https://github.com/basnijholt/dotfiles/tree/51c7af46e62a7d13b4ff497380c8b58c05ed81c8) for the complete setup!*
