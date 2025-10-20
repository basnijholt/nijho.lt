---
title: "📱 Agentic Phone Coding: WireGuard, Blink Shell, and My Self-Hosted AI Stack"
subtitle: "A reproducible voice-driven workflow using Mosh, Zellij, FasterWhisper, Ollama, and my agent-cli server to build software from an iPhone without sending code to SaaS."
summary: "My fully self-hosted mobile development loop: WireGuard from an iPhone into my NixOS machine, persistent Blink/Mosh sessions, a systemd-managed agent-cli server, and an iOS Shortcut that turns speech into clean code with FasterWhisper and Ollama."
date: 2025-10-19
draft: true
featured: false
authors:
  - admin
tags:
  - agentic-coding
  - ai
  - workflow
  - ios
  - self-hosting
  - nixos
  - wireguard
  - blink
  - zellij
  - ollama
  - faster-whisper
  - agent-cli
categories:
  - Software Development
  - AI
  - level:intermediate
image:
  caption: ""
  focal_point: "Smart"
  placement: 2
  preview_only: false
---

I am dictating this post at ten kilometers altitude on a flight home from Mexico, Blink Shell open on my iPhone while an agentic assistant running on my NixOS box shapes my sentences in real time.
I am currently a little addicted to agentic coding: as soon as an idea pops into my head, I want to ship it immediately, even if that means hacking from a cramped seat in the sky.
This is the workflow I have been refining after the experiments I described in [my agentic coding write-up]({{< ref "/post/agentic-coding" >}}) and the self-hosted AI obsession in [my local AI journey]({{< ref "/post/local-ai-journey" >}}).
It is a personal, open stack: no code or transcripts touch a proprietary endpoint, and everything runs on the same NixOS box that also powers my homelab.

At the moment, the glue for all of this is [Code](https://github.com/just-every/code), a fast-moving fork of Codex CLI.
My agentic tooling changes almost monthly—whenever a better local option appears, I happily swap it in—but today this stack captures what actually gets work done from the phone.

{{% callout note %}}
**TL;DR:** I connect my iPhone to my home network over **WireGuard**, stay logged in with **Blink Shell** plus **Mosh** for resilient SSH, manage terminals with **Zellij**, and run my own [`agent-cli`](https://github.com/basnijholt/agent-cli) server under **systemd**. An iOS Shortcut records my voice, ships audio to the server for **FasterWhisper** transcription, runs text clean-up with **Ollama**, and returns the result directly into my mobile clipboard so I can paste commands or commit messages instantly.
{{% /callout %}}

{{< toc >}}

## 1. The Motivation: Ship Features the Moment Ideas Arrive

Earlier this year I noticed a pattern: I would get a new idea, feel an overwhelming urge to implement it right away, and then fight with whatever device I had nearby.
I tried glossy remote IDEs again, including **Happy CLI** and a few browser-based editors, but every option either forced me through a third-party API or broke the moment the connection hiccupped.
That friction is what pushed me toward a phone-first, self-hosted workflow that can keep up with my agentic-coding impulses.

This post is based on the way I develop software today.
Your mileage may vary, but if you also care about privacy, open tooling, and reproducible environments, I think there are useful pieces here.

## 2. Constraints and Trade-offs

I approached the project with a few hard requirements:

- **Zero proprietary relays:** Audio, source code, and shell history stay on my hardware.
- **Resilient sessions:** I want to lock my phone, board a plane, and resume where I left off.
- **Voice-friendly:** Dictation should be fast enough that I do not reach for a laptop.
- **Reproducible config:** The entire stack must live in my [dotfiles]({{< ref "/post/dotfiles" >}}) and [NixOS configuration](https://github.com/basnijholt/dotfiles/tree/main/configs/nixos).

To give you a sense of what I tried, here is the short comparison that convinced me to roll my own:

| Approach | Pros | Why I moved on |
| --- | --- | --- |
| Cloud IDEs (Codespaces, Devpod) | Slick editors, good specs | Ran afoul of my private repos and required shuttling secrets |
| Happy CLI | Native iOS app with AI helpers | Relay sits outside my homelab and I cannot audit the pipeline |
| iSH + SSH (my old setup) | Worked everywhere | Slow, no mosh, missing modern terminal features |
| Phone VNC | Visual parity | Latency and battery drain, awkward text selection |

The stack below gives me the resilience of Mosh, the ergonomics of Zellij, and full control over the AI layer.

## 3. Layer 1: WireGuard From the Router

I terminate WireGuard on my router so every device in the house (and on the road) can dial home with the same config.

- **Server:** MikroTik router running WireGuard peers managed via Nix (the router module lives in my dotfiles, but it is private for now).
- **Client:** The WireGuard iOS app with `On-Demand` rules so the tunnel flips on whenever I am off trusted Wi-Fi.
- **DNS:** All mobile sessions resolve through my Pi-hole, so `git.nijho.lt` and internal services resolve instantly.

This gives Blink a local-LAN address for my desktop `nixos-builder`, without hairpin NAT or double SSH jumps.

## 4. Layer 2: Blink Shell + Mosh for Durable Sessions

Blink Shell is my daily driver on iOS because it supports real keyboard shortcuts, Face ID auth, and custom URL schemes for Shortcuts.

- I launch sessions using `mosh bas@nixos-builder -- zellij attach -c phone`.
- Mosh smooths over spotty LTE and keeps my session alive when the phone sleeps.
- Blink's [shortcuts integration](https://blink.sh/docs/shortcuts/) lets me trigger the "Dictate to clipboard" automation right inside the terminal.

If you have ever lost a long REPL session to a dropped train tunnel, Mosh feels like magic.

## 5. Layer 3: Zellij Layouts Instead of tmux

In an earlier draft of this post I accidentally wrote "tmux" out of muscle memory, but I fully switched to **Zellij** months ago.

- `zellij` handles pane management, status bars, and plugin hints far better on a phone display.
- My mobile-friendly keybindings sit in [`configs/zellij/config.kdl`](https://github.com/basnijholt/dotfiles/blob/8f6bf0b7219195a46a3e010d3538e1e449634db7/configs/zellij/config.kdl), so Blink renders clean borders and sensible shortcuts on the small screen.
- I sync all plugins and keymaps through the same dotfiles pipeline I described in [Terminal Ninja]({{< ref "/post/terminal-ninja" >}}).

Because Zellij renders well inside Blink, I get clear borders and no weird emoji alignment issues.

## 6. Layer 4: A systemd-managed `agent-cli` Server

The heart of the workflow is a long-lived background service that exposes transcription, rewrite, and command helpers via a secure UNIX socket.

```ini
# /etc/systemd/system/agent-cli-server.service
[Unit]
Description=agent CLI server
After=network-online.target

[Service]
User=bas
Group=users
WorkingDirectory=/home/basnijholt/repos/agent-cli
Environment="OLLAMA_HOST=127.0.0.1:11434"
ExecStart=/home/basnijholt/.local/bin/agent-cli server --config /home/basnijholt/.config/agent-cli/server.toml
Restart=on-failure
RestartSec=3
RuntimeMaxSec=0

[Install]
WantedBy=default.target
```

I manage that file declaratively with NixOS (`systemd.services.agent-cli-server`), so rebuilding the machine pins the correct binary and config checksum.
The server speaks JSON-RPC over a local socket; my Shortcut pushes audio files into `/run/agent-cli/inbox`, and the service publishes cleaned-up text to a redis channel and clipboard helper.

If you want to peek at the actual configuration I use, the code lives in [`configs/nixos/modules/user.nix`](https://github.com/basnijholt/dotfiles/blob/8f6bf0b7219195a46a3e010d3538e1e449634db7/configs/nixos/modules/user.nix#L29-L40), which keeps the `uvx agent-cli server` user service alive with the right dependencies.

The models run on the same box:

- **FasterWhisper** (medium.en) via [`faster-whisper-server`](https://github.com/guillaumekln/faster-whisper) behind a UNIX socket for instant transcriptions.
- **Ollama** hosting `llama3.1:70b` for rewrite/edit prompts plus `qwen2.5-coder` when I want a second opinion.
- Optional `rtx` acceleration so the GPU stays warm for consecutive dictations.

Because it is all local, latency stays below 600 ms for typical dictation snippets.

## 7. Layer 5: The iOS Shortcut Pipeline

The Shortcut attached to my iPhone's action button is the glue between the physical microphone and my NixOS stack.

1. **Record audio:** The Shortcut opens a native recorder and stops when I tap the screen.
2. **Send to server:** It runs `ssh bas@nixos-builder agent-cli ingest --stdin` with the WAV payload.
3. **Transcribe:** `agent-cli` calls FasterWhisper, producing raw text plus timestamps.
4. **Polish:** The text flows into an Ollama prompt that applies my personal style guide (short sentences, no filler).
5. **Push to clipboard:** The server emits a WebSocket message to a tiny Blink companion script (`blink://clipboard?text=...`), so the completed text pops into the iOS clipboard.
6. **Notify:** I get a haptic tap on the phone and a confirmation toast inside Blink.

The whole loop finishes fast enough that I can dictate a git commit message, tap once, and paste it into `git commit` inside Zellij without re-typing anything.

{{% callout warning %}}
**Security tip:** Lock the Shortcut to run only when your WireGuard tunnel is active and require Face ID before pushing clipboard data. I also gate the `agent-cli ingest` command through a per-device SSH key with a forced command wrapper.
{{% /callout %}}

## 8. A Typical Coding Session From the Phone

Here's what a real session looks like today:

1. Flick the action button and dictate a summary of the feature I want to build.
2. Open Blink, auto-connects through WireGuard, resumes the last Mosh session, and re-attaches to `zellij`.
3. Paste the dictation into my `agent-cli chat` pane to seed context, run tests with one tap on the on-screen keyboard, and let the agent propose patches.
4. Jump into `nvim` for manual edits, using Zellij's copy-mode to yank snippets.
5. Review diffs, run `nix flake check`, and push from the phone.
6. When inspiration fades, I lock the phone. Hours later I unlock it, and everything is exactly where I left it.

When the draft looks good, I hand off the git plumbing to my `coder` agent running on the same host—it stages the changes, writes the commit, pushes the branch, and opens a pull request for me. Final review happens in the GitHub iOS app, which is perfect for quick proofreading while the plane starts its descent.

Because all the heavy lifting happens on the NixOS machine, my phone stays cool and battery usage is surprisingly mild.

## 9. Lessons Learned and Caveats

- **Network hiccups still matter.** Mosh hides most drops, but large git clones will stall on weak LTE. I queue those until I am on Wi-Fi.
- **Keep shortcuts debuggable.** I log every transcription to `/var/log/agent-cli/transcriptions.log` so I can replay failures from a laptop.
- **Voice accuracy improves with context.** Feeding previous snippets into the Ollama rewrite step keeps variable names consistent.
- **Beware of clipboard overwrites.** iOS allows only one clipboard at a time; I use Shortcuts automation to delay re-runs for five seconds so I have time to paste.
- **Documentation helps future me.** Everything lives in my dotfiles (`configs/shortcuts/`, `configs/agent-cli/`). When I swap phones, I just re-run `./install`.
- **NixOS keeps networking tidy.** Firewall rules (including the UDP range for Mosh and the agent server port) are codified in [`configs/nixos/hosts/pc/networking.nix`](https://github.com/basnijholt/dotfiles/blob/8f6bf0b7219195a46a3e010d3538e1e449634db7/configs/nixos/hosts/pc/networking.nix#L30-L49), so the setup survives rebuilds.

## 10. Where to Go Next

This workflow already let me hack on [`matty`](https://github.com/basnijholt/matty) and bug-fix [Adaptive](https://github.com/basnijholt/adaptive) while away from my desk, but there is room to expand:

- Integrate [`clip-files`]({{< ref "/post/advent-of-open-source/15-clip-files" >}}) so I can blast entire repos into the agent context instantly.
- Explore [LangGraph](https://langchain-ai.github.io/langgraph/) orchestration the way I teased in {{< ref "/post/local-ai-journey" >}} for multi-agent debugging.
- Add an `agent-cli deploy` command that runs `nixos-rebuild` for my homelab nodes without leaving the phone.

## 11. Conclusion and Further Reading

I wanted a workflow that matched the autonomy I described in [Agentic Coding]({{< ref "/post/agentic-coding" >}}) but that fit in my pocket.
WireGuard, Blink, Mosh, Zellij, and my `agent-cli` server gave me exactly that: agentic development from anywhere, with privacy intact.

If you're curious to dive deeper, here are a few related posts:

- [Dotfiles: A Practical, Cross-Platform Terminal Setup]({{< ref "/post/dotfiles" >}})
- [Local AI Journey: RTX 3090 Edition]({{< ref "/post/local-ai-journey" >}})
- [Terminal Ninja]({{< ref "/post/terminal-ninja" >}})
- [Using LLMs Effectively]({{< ref "/post/using-llms" >}})

I'd love to hear what self-hosted tricks you're using for mobile development—reach out if you adapt this stack or build something wild on top of it.
