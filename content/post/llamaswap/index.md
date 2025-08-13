---
title: "🦙 Switching from Ollama to llama-swap + llama.cpp: A Journey to Better Local AI"
subtitle: "How incompatible GGUF models and development frustrations led me to a more flexible local LLM setup with llama-swap and llama.cpp"
summary: "After hitting compatibility issues with Ollama's GGUF model support and growing frustrated with its development approach, I switched to llama-swap + llama.cpp for a more transparent and flexible local AI setup that actually works with the models I want to use."
date: 2025-08-13
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
  - self-hosting
  - open-source
categories:
  - Technology
  - AI
  - "level:intermediate"
---

{{< toc >}}

## The Breaking Point: When gpt-oss Performed Terribly

I've been running local AI models on my RTX 3090 machine for months now, primarily using Ollama as my model server.
It worked well enough for the standard models (Llama, Mistral, Qwen), but recently I hit a wall that made me reconsider my entire setup.
I loaded up the promising `gpt-oss-20b` model, expecting great things based on the hype.
Instead, I got responses that were barely coherent.
The model was performing so poorly that I initially wrote it off as just another overhyped release.

But then I started digging.
On the LocalLLaMA subreddit, I found thread after thread of users reporting the same issue: models that should be performing well were giving terrible results in Ollama.
The culprit? Incorrect prompt templates and chat formats.
Ollama was mangling the input in ways that destroyed model performance.
Users who tried the exact same GGUF files in llama.cpp reported dramatically better results.

Even worse, benchmarks were showing that Ollama had significant performance overhead compared to running llama.cpp directly.
We're talking 20-30% slower inference speeds for the same models on the same hardware.

{{% callout warning %}}
**The Frustration:** When a tool that claims to be "the easiest way to run large language models locally" makes good models perform terribly due to incorrect templating and adds unnecessary performance overhead, it's time to look for alternatives.
{{% /callout %}}

## Discovering the Alternative: llama-swap + llama.cpp

After some research and experimentation, I discovered a more elegant solution: [llama-swap](https://github.com/gianlucatruda/llama-swap) combined with [llama.cpp](https://github.com/ggerganov/llama.cpp).
This combination not only fixes the template issues but also offers something Ollama struggles with: true model hot-swapping with automatic VRAM management.

### What is llama-swap?

llama-swap is a lightweight service that sits in front of llama.cpp, providing:

- **Automatic model loading/unloading**: Models are loaded into VRAM on-demand and unloaded after a configurable TTL
- **OpenAI-compatible API**: Drop-in replacement for any tool expecting an OpenAI-style endpoint
- **Zero VRAM usage when idle**: Unlike Ollama, which keeps models loaded, llama-swap frees your GPU completely when not in use
- **Support for multiple model configurations**: Easy switching between different models and quantizations

### Why llama.cpp Directly?

Going directly to llama.cpp (through llama-swap) has several advantages:

- **Correct prompt templates**: Models actually work as intended with proper formatting
- **Better performance**: No abstraction overhead, 20-30% faster inference than Ollama
- **Transparency**: You know exactly what's running and how
- **Flexibility**: Full control over model parameters, context sizes, and hardware utilization

## My NixOS Setup

Since I manage my entire system with Nix, setting up llama-swap was surprisingly elegant.
Here's my complete configuration:

```nix
# Override llama.cpp to get the latest version with CUDA support
llama-cpp = pkgs.llama-cpp.override {
  cudaSupport = true;
  cudaPackages = pkgs.cudaPackages_12;
};

# Configure llama-swap as a systemd service
systemd.services.llama-swap = {
  description = "llama-swap model server";
  after = [ "network.target" ];
  wantedBy = [ "multi-user.target" ];
  
  serviceConfig = {
    Type = "simple";
    ExecStart = "${pkgs.llama-swap}/bin/llama-swap";
    Restart = "always";
    User = "basnijholt";
    Environment = [
      "LLAMA_CPP_BIN=${llama-cpp}/bin/llama-server"
      "MODELS_PATH=/home/basnijholt/.cache/llama-swap/models"
      "HOST=0.0.0.0"
      "PORT=11434"  # Same as Ollama for compatibility
      "MODEL_TTL=3600"  # Unload models after 1 hour
    ];
  };
};
```

The beauty of this setup is that it's completely declarative.
One `nixos-rebuild switch` and I have a working llama-swap server with the latest llama.cpp, CUDA acceleration enabled, and automatic model management.

## Model Configuration

llama-swap uses a simple YAML configuration for models.
Here's my setup with a mix of coding, reasoning, and general-purpose models:

```yaml
models:
  # Small, fast models for quick tasks
  - name: qwen2.5-coder:3b
    path: models/qwen2.5-coder-3b-instruct-q8_0.gguf
    context_size: 32768
    
  - name: llama3.2:3b
    path: models/llama-3.2-3b-instruct-q8_0.gguf
    context_size: 131072
    
  # Coding specialists
  - name: qwen2.5-coder:14b
    path: models/qwen2.5-coder-14b-instruct-q5_k_m.gguf
    context_size: 32768
    
  - name: qwen2.5-coder:32b
    path: models/qwen2.5-coder-32b-instruct-q4_k_m.gguf
    context_size: 32768
    gpu_layers: 35  # Partial offloading for larger model
    
  # Reasoning models
  - name: qwq:32b
    path: models/qwq-32b-preview-q4_k_m.gguf
    context_size: 32768
    gpu_layers: 30
    
  # And yes, gpt-oss works perfectly!
  - name: gpt-oss:20b
    path: models/gpt-oss-20b-q5_k_m.gguf
    context_size: 8192
```

## The Migration Experience

Switching from Ollama to llama-swap was surprisingly smooth:

1. **API Compatibility**: Since both expose OpenAI-compatible endpoints, my existing tools ([agent-cli](https://github.com/basnijholt/agent-cli), LibreChat) worked immediately
2. **Better Resource Usage**: My GPU is completely free when not actively running inference
3. **Model Flexibility**: I can now run any GGUF model without worrying about compatibility
4. **Performance**: Direct llama.cpp access means I get all the latest optimizations

{{% callout note %}}
**Performance Tip**: With llama-swap's TTL feature, I set models to unload after 1 hour.
This means my 24GB RTX 3090 is available for other tasks (like that game of The Last of Us I still haven't played) when I'm not actively using AI.
{{% /callout %}}

## What I Gained (and Lost)

### Advantages of llama-swap + llama.cpp

- ✅ **Correct prompt handling**: Models actually perform as designed
- ✅ **20-30% faster inference**: Direct llama.cpp beats Ollama's overhead
- ✅ **Zero idle VRAM usage**: Models completely unload when not in use
- ✅ **Full control**: Direct access to all llama.cpp parameters
- ✅ **Transparent operation**: I know exactly what's happening under the hood

### What I Miss from Ollama

- ❌ **Automatic model downloading**: With Ollama, `ollama pull` was convenient
- ❌ **Built-in model library**: Now I manually download from HuggingFace
- ❌ **Modelfile abstractions**: These were nice for quick experiments

But honestly? These conveniences aren't worth the compatibility headaches and opaque development process.

## Performance and Resource Usage

One unexpected benefit has been the improved resource management.
Here's a typical day with both setups:

**Ollama**: Keeps models loaded, my 24GB VRAM often had 18-20GB occupied even when idle

**llama-swap**: Truly dynamic loading means:
- Idle: 0GB VRAM used
- Active (small model): 3-5GB for a 3B parameter model
- Active (large model): 15-20GB for a 32B parameter model
- Automatic unloading after my 1-hour TTL

This dynamic management means I can actually use my GPU for other tasks without having to manually stop services.

## Conclusion: Sometimes Simpler is Better

My switch from Ollama to llama-swap + llama.cpp reinforced something I've learned repeatedly in my open-source journey: sometimes going closer to the source gives you more flexibility and fewer headaches.
While Ollama aims to be user-friendly, its abstraction layer introduced compatibility issues and opacity that ultimately made my workflow worse, not better.

With llama-swap and llama.cpp, I have a setup that:
- Works with every model I want to try
- Manages resources intelligently
- Integrates perfectly with my NixOS configuration
- Gives me full visibility and control

For those hitting similar Ollama limitations or just wanting more control over their local AI setup, I highly recommend giving llama-swap a try.
The initial setup might require a bit more configuration, but the flexibility and reliability are worth it.

And yes, `gpt-oss-20b` actually performs like it should now.
The difference is night and day.

---

*Check out my [NixOS configuration](https://github.com/basnijholt/dotfiles/tree/flake) for the complete llama-swap setup, and feel free to reach out if you're considering making the switch!*