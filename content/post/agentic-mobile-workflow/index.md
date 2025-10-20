---
title: "📱 Agentic Phone Coding: WireGuard, Blink Shell, and My Self-Hosted AI Stack"
subtitle: "A reproducible voice-driven workflow using Mosh, Zellij, FasterWhisper, Ollama, and my agent-cli server to build software from an iPhone"
summary: "My mostly self-hosted mobile development loop: WireGuard from an iPhone into my NixOS machine, persistent Blink/Mosh sessions, a systemd-managed agent-cli server, and an iOS Shortcut for FasterWhisper+Ollama dictation—paired with the best proprietary coding model available."
date: 2025-10-20
draft: false
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

I am dictating this post at ten kilometers altitude on a flight home from Mexico, Blink Shell open on my iPhone, while an agentic assistant on my [NixOS](https://nixos.org/) machine writes an initial draft for this post.
Admittedly, I’m a little addicted to agentic coding: when an idea pops up, I want to jump on it right away—even if that means doing it from a cramped seat in the sky.
This is the workflow I’ve arrived at after trying many alternatives, it extends [my agentic coding write-up]({{< ref "/post/agentic-coding" >}}) and the self-hosted AI obsession in [my local AI journey]({{< ref "/post/local-ai-journey" >}}).
It's my backup plan for those moments when a computer simply isn't nearby—the rest of the time I'm still at a keyboard like any other developer.
This is in no way a replacement for a proper computer/laptop workflow but gets the job done when needed.
It's a personal, mostly open-source stack built around [`agent-cli`](https://github.com/basnijholt/agent-cli)—my local-first voice layer.
Here's how it works: I speak into my phone, the audio goes to [FasterWhisper](https://github.com/SYSTRAN/faster-whisper-server) for transcription, [Ollama](https://ollama.com/) cleans up the text, and it lands on my clipboard ready to paste.
My iOS Shortcut handles this through a small HTTP interface that agent-cli exposes.
The coding agent itself still uses the best proprietary model I can access.

{{% callout note %}}
Meta: I'm writing about agentic coding on mobile from my actual phone.
It's not the most efficient way to write, but it gets the job done — during a 6.5‑hour flight I dictated and iterated this entire post.
Each iteration was a commit: dictate changes, review the diff, refine, commit, repeat.
See all [50+ commits in PR #40](https://github.com/basnijholt/nijho.lt/pull/40) for the full iteration trail.
{{% /callout %}}

{{% callout note %}}
**TL;DR:** iPhone → WireGuard → Blink+Mosh → Zellij.
I dictate via a Shortcut → FasterWhisper (transcribe) → Ollama (polish) → clipboard, then paste into Codex CLI using OpenAI’s `gpt-5-codex-high`.
Everything is local except the model.
{{% /callout %}}

{{< toc >}}

## 1. Why Phone Coding Works Now

For years I used [**iSH**](https://ish.app/) (a full Alpine Linux emulator) with SSH to hop into servers from my phone, but dropped connections were a constant frustration (Mosh fixes this, more on that later).
Because coding on a phone keyboard is terrible, I kept it to tiny configuration tweaks or one-off fixes of a few characters.
Agentic tools changed that: with a CLI coding agent, I don’t need to type the code—I describe the change, review the patch, and run it.
That made meaningful work on the phone possible for the first time, for those moments when a computer isn’t around.

I tried **VS Code in the browser**, bounced between **iSH** and **Terminus** for SSH, and even lived inside a handful of in-browser terminal clients.
I also spent time with mobile companions like [**Happy**](https://happy.engineering/) and [**Omnara**](https://www.ycombinator.com/companies/omnara), both designed to mirror Claude Code sessions on the phone, but they still felt like extra steps between me and my actual terminal.
That friction pushed me toward a phone‑ready, self‑hosted workflow that still gives me raw SSH access to my own machine when the computer is out of reach.

This post is based on the way I develop software today.
Your mileage may vary, but if you also care about privacy, open tooling, and reproducible environments, I think there are useful pieces here.

## 2. Constraints and Trade-offs

This setup grew organically over time. What emerged are less strict requirements and more happy accidents that turned into core benefits:

- **Single trust boundary:** Only the model provider (OpenAI) sees code context; audio and automation stay local, and I avoid any additional third‑party relays.
- **Resilient sessions:** Connections should survive sleep and spotty networks.
- **Voice-friendly:** Dictation should be accurate enough that I can trust it.
- **Reproducible config:** The entire stack must live in my [dotfiles]({{< ref "/post/dotfiles" >}}) and [NixOS configuration](https://github.com/basnijholt/dotfiles/tree/8f6bf0b7219195a46a3e010d3538e1e449634db7/configs/nixos).

To give you a sense of what I tried, here is the short comparison that convinced me to roll my own:

| Approach                                                                                                | Pros                                                        | Why I moved on                                                                                                      |
| ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| VS Code in the browser                                                                                  | Familiar editor UI                                          | Needs a steady connection and still lives outside my dotfiles comfort zone                                          |
| iSH / Terminus SSH                                                                                      | Works without extra infrastructure                          | Laggy, no Mosh, and awkward keybindings                                                                             |
| In-browser terminals                                                                                    | Instant access from anywhere                                | Poor copy/paste ergonomics and flaky mobile keyboards                                                               |
| [Happy](https://apps.apple.com/us/app/happy-codex-claude-code-app/id6748571505) (Claude Code companion) | Push notifications, encrypted mobile UI for Claude Code     | Requires wrapping every session with a separate CLI and still abstracts away my shell, and was quite buggy for me   |
| [Omnara](https://omnara.com) (agent command center)                                                     | Centralizes Claude Code/Codex sessions with terminal replay | Proxies via their servers; I already trust OpenAI for the model and don't want another third‑party handling my code |

The stack below gives me the resilience of Mosh, the ergonomics of Zellij, and full control over the AI layer.

## 3. Layer 1: WireGuard From the Router

[WireGuard](https://www.wireguard.com/) is a modern VPN that lets me securely access my home network from anywhere.
I terminate WireGuard on my router so every device in the house (and on the road) can dial home with the same config.
(If you want something easier to set up without opening ports, [Tailscale](https://tailscale.com/) is a more user-friendly option.)

- **Server:** ASUS XT8 router with WireGuard enabled via the router UI.
- **Client:** The WireGuard iOS app with `On-Demand` rules so the tunnel flips on whenever I am off trusted Wi-Fi.
- **DNS:** All mobile sessions resolve through my home DNS, so `git.nijho.lt` and internal services resolve instantly.

This gives Blink a local-LAN address for my desktop `nixos`.

## 4. Layer 2: Blink Shell + Mosh for Durable Sessions

What is [Mosh](https://mosh.org/)?
It's like SSH, but it stays connected when the network changes or the phone sleeps, and it feels faster on bad connections.

[Blink Shell](https://blink.sh/) is my daily driver on iOS because it pairs beautifully with Mosh and has great keyboard ergonomics.

- I launch sessions using `mosh bas@nixos -- zellij attach --create phone` ([Zellij](https://zellij.dev/) is my terminal multiplexer—more on that in the next section).
- Mosh smooths over spotty LTE and keeps my session alive when the phone sleeps.

Mosh keeps the session responsive across flaky networks and sleep.

## 5. Layer 3: Zellij Layouts

I use **Zellij** as my terminal multiplexer for mobile work.

- I stick to the defaults and use a couple of predefined layouts (e.g., a "phone" layout with editor + shell panes).

Ergonomics matter even more on a glass keyboard, so I lean on a few shell helpers:

- **[`zoxide`](https://github.com/ajeetdsouza/zoxide)** means I can jump between repos with `z foo` instead of pecking long paths.
- **Single-character aliases** like `p` for `pytest` and `gs` for `git status` live in [`configs/shell/10_aliases.sh`](https://github.com/basnijholt/dotfiles/blob/8f6bf0b7219195a46a3e010d3538e1e449634db7/configs/shell/10_aliases.sh), keeping command entry to a minimum.
- **Autocompletion plugins**—[`zsh-autosuggestions`](https://github.com/zsh-users/zsh-autosuggestions) and `zsh-syntax-highlighting`—are wired up in [`configs/shell/70_zsh_plugins.sh`](https://github.com/basnijholt/dotfiles/blob/8f6bf0b7219195a46a3e010d3538e1e449634db7/configs/shell/70_zsh_plugins.sh), so I get inline hints and colour cues while typing.

I break these tricks down in more depth in [Terminal Ninja]({{< ref "/post/terminal-ninja" >}}), explain how I sync them with my [Dotfiles]({{< ref "/post/dotfiles" >}}), and even package binaries like `zoxide` with [Dotbins]({{< ref "/post/dotbins" >}}).

## 6. Layer 4: `agent-cli` Server

[`agent-cli`](https://github.com/basnijholt/agent-cli) runs as a small server on my NixOS machine.
In this workflow I only use `transcribe` from iOS Shortcuts: the phone records audio, the server transcribes and cleans it up, and I paste the text.
(Agent-CLI has other features like `autocorrect` and `chat`, but I don't use them for this workflow.)
On this machine I run a long‑lived `agent-cli` user service (systemd) so Shortcuts can POST audio to it and get cleaned text back—ready to paste into Codex CLI.
The service is defined in my dotfiles—see: [`configs/nixos/modules/user.nix` (agent-cli service)](https://github.com/basnijholt/dotfiles/blob/8f6bf0b7219195a46a3e010d3538e1e449634db7/configs/nixos/modules/user.nix#L29-L40).

For more background on why I built it and how I use it in practice, see [Local AI Journey]({{< ref "/post/local-ai-journey" >}}) (§3) and [Agentic Coding]({{< ref "/post/agentic-coding" >}}).

The models and services run on the same box:

- **FasterWhisper** via [`faster-whisper-server`](https://github.com/SYSTRAN/faster-whisper) for high‑accuracy streaming transcription.
- **Ollama** for on‑device rewrite/cleanup before sending prompts to the coding agent.

My iOS Shortcut dictation workflow is slower than Apple's built-in dictation, but the accuracy is much better—and that matters more.

For the actual coding agent, I use a [fork](https://github.com/just-every/code) of Codex CLI with OpenAI’s `gpt-5-codex-high` model (here no open-source solution matches the frontier).

## 7. Layer 5: The iOS Shortcut Pipeline

My iPhone's Action Button runs a Shortcut that records audio and sends my voice to agent-cli on my NixOS machine for transcription and cleanup.

For the full recipe, see the iOS Shortcut Guide: [agent-cli/iOS_Shortcut_Guide.md](https://github.com/basnijholt/agent-cli/blob/main/iOS_Shortcut_Guide.md).

In short: I press the Action Button, the Shortcut records a snippet, sends it to `agent-cli`, and copies the cleaned text to my clipboard so I can paste it into Codex CLI.

The whole loop finishes fast enough that I can capture intent by voice and paste it into Codex CLI without typing.

{{% callout note %}}
**Dictation quality:** In my experience, the built‑in iOS dictation is absolute garbage compared to Whisper/FasterWhisper.
Accuracy and punctuation are much better with the FasterWhisper server running at home; it’s a bit slower, but that trade‑off is worth it for clean, usable text.
{{% /callout %}}

## 8. Workflow in Practice

Here's the typical flow:

- WireGuard auto-connects when I'm off home WiFi
- Open Blink—my Mosh session is still alive from last time, Zellij panes intact
- Dictate the change, paste into Codex CLI, review the agent's response
- Check diffs in an adjacent Zellij pane or different Blink tab with separate Mosh session
- The agent commits and pushes to a branch, then opens a PR via `gh` for me to review and merge

On the phone, I aim for the smallest practical edits and initial implementations.
Even on personal repos, I still open a PR—sometimes prompting alone gets me to a merge‑ready result.
For open‑source with real users, I finish on the computer with a careful review and any final edits.

## 9. Conclusion and Further Reading

This phone setup extends my [Agentic Coding]({{< ref "/post/agentic-coding" >}}) workflow to mobile.
I connect to the same Zellij session on `nixos`, so when an idea hits, I pick up exactly where I left off—same environment, same context, no setup.
Everything runs on my hardware (voice processing and automation) except the coding model itself.
It’s the most effective mobile workflow I’ve had so far.
It’s mostly open‑source not out of dogma, but because those tools are the best options for my needs.
The one exception is the coding model: there’s no true open equivalent right now, and it makes no sense to buy 20× H100s just to self‑host a frontier model even if such a high quality model would be available open-source.

If you're curious to dive deeper, here are a few related posts:

- [Agentic Coding]({{< ref "/post/agentic-coding" >}})
- [Dotfiles: A Practical, Cross-Platform Terminal Setup]({{< ref "/post/dotfiles" >}})
- [Local AI Journey: RTX 3090 Edition]({{< ref "/post/local-ai-journey" >}})
- [Terminal Ninja]({{< ref "/post/terminal-ninja" >}})
- [Using LLMs Effectively]({{< ref "/post/using-llms" >}}) (already outdated at this point!)

I'd love to hear what self-hosted tricks you're using for mobile development—reach out if you adapt this stack or build something wild on top of it.
