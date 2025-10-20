---
title: "📱 Agentic Phone Coding: WireGuard, Blink Shell, and My Self-Hosted AI Stack"
subtitle: "A reproducible voice-driven workflow using Mosh, Zellij, FasterWhisper, Ollama, and my agent-cli server to build software from an iPhone without sending code to SaaS."
summary: "My mostly self-hosted mobile development loop: WireGuard from an iPhone into my NixOS machine, persistent Blink/Mosh sessions, a systemd-managed agent-cli server, and an iOS Shortcut for FasterWhisper+Ollama dictation—paired with the best proprietary coding model available."
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
I am currently a little addicted to agentic coding: as soon as an idea pops into my head, I feel compelled to act on it immediately, even if that means hacking from a cramped seat in the sky.
This is the workflow I have been refining after the experiments I described in [my agentic coding write-up]({{< ref "/post/agentic-coding" >}}) and the self-hosted AI obsession in [my local AI journey]({{< ref "/post/local-ai-journey" >}}).
It's my contingency plan for those moments when a laptop simply isn't nearby—the rest of the time I'm still at a keyboard like any other developer.
It is a personal, mostly open stack: transcription, automation, and orchestration run on my own hardware, while the actual coding agent still calls into the best proprietary frontier model I can access.

Earlier this autumn I switched from `Claude Opus 4.1` to OpenAI's `gpt-5-codex-high` for the heavy lifting.
Anthropic's September 17 postmortem, [“A postmortem of three recent issues”](https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues), detailing three infrastructure bugs and weeks of degraded quality, was the final straw for trusting my mainline development flow to their stack.

Day to day, a CLI-first agent stack holds the workflow together: the [Code CLI](https://github.com/just-every/code) (a fast-moving fork of Codex) is a coding agent in the terminal; I run multiple instances in parallel via `zellij` (or separate SSH sessions), and `agent-cli` captures dictation and the prompts I’d otherwise type—right in the same terminal where I already work.
My agentic tooling changes almost monthly—whenever a better local option appears, I happily swap it in—but today this stack captures what actually gets work done when the phone is the only screen within reach.
For coding help I now lean on `gpt-5-codex-high` (and will happily swap again if something better appears); the local tooling in this post simply gives that model a private, flexible cockpit.

{{% callout note %}}
**TL;DR:** iPhone → WireGuard → Blink+Mosh → Zellij. I dictate via a Shortcut → FasterWhisper (transcribe) → Ollama (polish) → clipboard, then paste into the Code CLI using OpenAI’s `gpt-5-codex-high`. Everything is local except the model.
{{% /callout %}}

{{< toc >}}

## 1. Why Phone Coding Works Now

For years I used **iSH** with an SSH client on my phone to hop into servers.
Because coding on a phone keyboard is terrible, I kept it to tiny configuration tweaks or one-off fixes of a few characters.
Agentic tools changed that: with a CLI coding agent, I don’t need to type the code—I describe the change, review the patch, and run it.
That made meaningful work on the phone possible for the first time, for those moments when a laptop isn’t around.

I tried **VS Code in the browser**, bounced between **iSH** and **Terminus** for SSH, and even lived inside a handful of in-browser terminal clients.
I also spent time with mobile companions like [**Happy**](https://happy.engineering/) and [**Omnara**](https://www.ycombinator.com/companies/omnara), both designed to mirror Claude Code sessions on the phone, but they still felt like another relay layer between me and my shell.
That friction pushed me toward a phone‑ready, self‑hosted workflow that still gives me raw SSH access to my own machine when the laptop is out of reach.

This post is based on the way I develop software today.
Your mileage may vary, but if you also care about privacy, open tooling, and reproducible environments, I think there are useful pieces here.

## 2. Constraints and Trade-offs

I approached the project with a few hard requirements:

- **Single trust boundary:** Only the model provider (OpenAI) sees code context; audio and automation stay local, and I avoid any additional third‑party relays.
- **Resilient sessions:** Connections should survive sleep and spotty networks.
- **Voice-friendly:** Dictation should be accurate enough that I can trust it.
- **Reproducible config:** The entire stack must live in my [dotfiles]({{< ref "/post/dotfiles" >}}) and [NixOS configuration](https://github.com/basnijholt/dotfiles/tree/main/configs/nixos).

To give you a sense of what I tried, here is the short comparison that convinced me to roll my own:

| Approach | Pros | Why I moved on |
| --- | --- | --- |
| VS Code in the browser | Familiar editor UI | Needs a steady connection and still lives outside my dotfiles comfort zone |
| iSH / Terminus SSH | Works without extra infrastructure | Laggy, no Mosh, and awkward keybindings |
| In-browser terminals | Instant access from anywhere | Poor copy/paste ergonomics and flaky mobile keyboards |
| [Happy](https://apps.apple.com/us/app/happy-codex-claude-code-app/id6748571505) (Claude Code companion) | Push notifications, encrypted mobile UI for Claude Code | Requires wrapping every session with a separate CLI and still abstracts away my shell |
| [Omnara](https://omnara.com) (agent command center) | Centralizes Claude Code/Cursor sessions with terminal replay | Proxies via their servers; I already trust OpenAI for the model and don't want another third‑party handling my code |

The stack below gives me the resilience of Mosh, the ergonomics of Zellij, and full control over the AI layer.

## 3. Layer 1: WireGuard From the Router

I terminate WireGuard on my router so every device in the house (and on the road) can dial home with the same config.

- **Server:** ASUS XT8 router with WireGuard enabled via the router UI.
- **Client:** The WireGuard iOS app with `On-Demand` rules so the tunnel flips on whenever I am off trusted Wi-Fi.
- **DNS:** All mobile sessions resolve through my home DNS, so `git.nijho.lt` and internal services resolve instantly.

This gives Blink a local-LAN address for my desktop `nixos`, without hairpin NAT or double SSH jumps.

## 4. Layer 2: Blink Shell + Mosh for Durable Sessions

Blink Shell is my daily driver on iOS because it pairs beautifully with Mosh and has solid keyboard ergonomics (external keyboards, sane modifiers, and reliable shortcuts).

- I launch sessions using `mosh bas@nixos -- zellij attach -c phone`.
- Mosh smooths over spotty LTE and keeps my session alive when the phone sleeps.
 

If you have ever lost a long REPL session to a dropped train tunnel, Mosh feels like magic.

## 5. Layer 3: Zellij Layouts

I use **Zellij** as my terminal multiplexer for mobile work.

- I stick to the defaults and use a couple of predefined layouts (e.g., a "phone" layout with editor + shell panes).

Ergonomics matter even more on a glass keyboard, so I lean on a few shell helpers:

- **[`zoxide`](https://github.com/ajeetdsouza/zoxide)** means I can jump between repos with `z foo` instead of pecking long paths.
- **Single-character aliases** like `p` for `pytest` and `gs` for `git status` live in [`configs/shell/10_aliases.sh`](https://github.com/basnijholt/dotfiles/blob/8f6bf0b7219195a46a3e010d3538e1e449634db7/configs/shell/10_aliases.sh), keeping command entry to a minimum.
- **Autocompletion plugins**—[`zsh-autosuggestions`](https://github.com/zsh-users/zsh-autosuggestions) and `zsh-syntax-highlighting`—are wired up in [`configs/shell/70_zsh_plugins.sh`](https://github.com/basnijholt/dotfiles/blob/8f6bf0b7219195a46a3e010d3538e1e449634db7/configs/shell/70_zsh_plugins.sh), so I get inline hints and colour cues while typing.

I break these tricks down in more depth in [Terminal Ninja]({{< ref "/post/terminal-ninja" >}}), explain how I sync them with my [Dotfiles]({{< ref "/post/dotfiles" >}}), and even package binaries like `zoxide` with [Dotbins]({{< ref "/post/dotbins" >}}).



## 6. Layer 4: `agent-cli` Server

The workflow uses a long‑lived `agent-cli` server on my NixOS machine to handle transcription and prompt cleanup.
I run it as a systemd user service defined in my dotfiles—see the permalink to `configs/nixos/modules/user.nix` here:
[`user.nix` (agent-cli user service)](https://github.com/basnijholt/dotfiles/blob/8f6bf0b7219195a46a3e010d3538e1e449634db7/configs/nixos/modules/user.nix#L29-L40).

My Shortcut sends audio to the server; it returns cleaned text that I paste into the Code CLI.

The models run on the same box:

- **FasterWhisper** via [`faster-whisper-server`](https://github.com/guillaumekln/faster-whisper) for transcription.
- **Ollama** for local text cleanup/rephrasing before sending prompts to the coding agent.

FasterWhisper on my box is slower than Apple’s on‑device dictation. The accuracy makes it a clear win for me when coding from the phone.

For deep coding refactors, though, I still hand context to `gpt-5-codex-high` through Code's proprietary back end—open models continue to trail frontier systems here, so I happily mix the two.

## 7. Layer 5: The iOS Shortcut Pipeline

The Shortcut attached to my iPhone's action button—something I built myself in Shortcuts + `agent-cli`—bridges the physical microphone and my NixOS stack.

For a step‑by‑step setup, see the iOS Shortcut Guide in the repo: [agent-cli/iOS_Shortcut_Guide.md](https://github.com/basnijholt/agent-cli/blob/main/iOS_Shortcut_Guide.md).

1. **Record audio:** The Shortcut opens a native recorder and stops when I tap the screen.
2. **Send to server:** It runs `ssh bas@nixos agent-cli ingest --stdin` with the WAV payload.
3. **Transcribe:** `agent-cli` calls FasterWhisper, producing raw text plus timestamps.
4. **Polish:** The text flows into an Ollama prompt that applies my personal style guide (short sentences, no filler).
5. **Push to clipboard:** The Shortcut puts the cleaned text on the iOS clipboard so I can paste it into the Code CLI.
6. **Notify:** I get a haptic tap on the phone and a confirmation toast inside Blink.

The whole loop finishes fast enough that I can capture intent by voice and paste it into the Code CLI without re‑typing.

{{% callout note %}}
**Dictation quality:** In my experience, the built‑in iOS dictation is absolute garbage compared to Whisper/FasterWhisper. Accuracy and punctuation are much better with the FasterWhisper server running at home; it’s a bit slower, but that trade‑off is worth it for clean, usable text.
{{% /callout %}}

{{% callout warning %}}
**Security tip:** Lock the Shortcut to run only when your WireGuard tunnel is active and require Face ID before pushing clipboard data. I also gate the `agent-cli ingest` command through a per-device SSH key with a forced command wrapper.
{{% /callout %}}

## 8. Workflow in Practice

- Open Blink and Mosh into `nixos`; `zellij` reattaches with my existing panes.
- Ensure WireGuard is connected.
- Dictate the feature/change, paste into the Code CLI (using `gpt-5-codex-high`), and iterate.
- Review diffs either in another Mosh/Zellij pane or as a pull request.
- I handle commits and pushes myself from the terminal.

On the phone, I aim for the smallest practical edits and initial implementations.
For serious work, I usually finish on a laptop with a few careful changes.
For personal or semi‑trivial fixes, I sometimes accept the agent’s output as‑is; for open‑source with real users, I’m much more thorough.

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
