---
title: "Switching apps on macOS in under 30 ms ⚡"
subtitle: "How I found out what Keyboard Maestro does, and what actually makes it fast"
summary: "Keyboard Maestro was one of the last things on my Mac I couldn't configure from a text file in my dotfiles, and I only used it to switch apps with a hotkey. AppleScript was too slow, so I had an agent inspect which macOS call Keyboard Maestro makes and build a small Swift replacement. Then benchmarking alternatives turned up a surprise about what actually makes it fast."
date: 2026-11-20
draft: false
featured: false
authors:
  - admin
tags:
  - macos
  - productivity
  - nix
  - dotfiles
  - keyboards
  - agentic-coding
  - open-source
categories:
  - Software Development
  - Open Source
  - level:intermediate
---

I have an extreme obsession with productivity, and I address it on the micro level.
For example, I almost exclusively voice-dictate my interactions with AI (I [self-host the dictation]({{< ref "/post/diction-agent-cli-qwen" >}}) too).
When my hands are on the keyboard, they're on a [Glove80]({{< ref "/post/split-ergonomic-mechanical-keyboard-glove80" >}}), the nerdiest variant you can get, with all black keys.

I also have a deep obsession with declarative tools.
Whenever I set up a new VM, a computer at home, or a new MacBook, I want the entire process to be reproducible and fast.
That ties in with my love for [NixOS]({{< ref "/post/proxmox-to-nixos" >}}), and it's why my [dotfiles]({{< ref "/post/dotfiles" >}}) are public.
Keyboard Maestro didn't fit that, so I replaced it.

This post is about [`macos-hotkey-app-switcher`](https://github.com/basnijholt/macos-hotkey-app-switcher), which I believe to be one of the fastest and simplest hotkey app switchers for macOS.
I built it end to end in [MindRoom]({{< ref "/post/mindroom" >}}), my [open-source](https://github.com/mindroom-ai/mindroom) agent platform.
It reads its hotkeys from a plain text file, and on my M2 MacBook it brings an app to the front in a median of 29 ms.

{{% callout note %}}
**TL;DR:**
- I used Keyboard Maestro almost only for app hotkeys, and it was one of the last things on my Mac I couldn't configure from a text file.
- AppleScript was much slower, so I had an agent find which macOS call Keyboard Maestro makes and build a small Swift replacement installed by nix-darwin.
- AppKit's supported `activate` call turned out to be just as fast as Keyboard Maestro's deprecated Carbon call: the speed comes from not starting a new process on every key press.
{{% /callout %}}

{{< toc >}}

## Four commands to a new Mac

Whenever I set up a new laptop, I run about four commands in the terminal.
One installs my [dotfiles](https://github.com/basnijholt/dotfiles).
One loads my {{< tooltip text="A private key used to decrypt files. My SSH keys and other secrets live in a private repository encrypted with it." >}}GPG key{{< /tooltip >}}, to decrypt my secrets, like SSH keys and such.
One installs {{< tooltip text="Nix for macOS system configuration: the apps, settings and background services of the whole Mac are declared in one config file." >}}nix-darwin{{< /tooltip >}}.
And finally a Nix switch command, and everything is the way I want it to be.

However, there were a couple of holdouts.
One of them was [Keyboard Maestro](https://www.keyboardmaestro.com/), which is a fantastic application.
It's paid, and I paid for it.
But I almost exclusively used it to map keys on my keyboard to rapidly switch between apps.
Its macros are made in its own app, not in a text file I can keep in my dotfiles.

## How I switch apps

I'm a furious multitasker, so I have many things open at once.
I don't want to look like a [mad person clicking Command-Tab]({{< ref "/post/split-ergonomic-mechanical-keyboard-glove80" >}}) all the time to switch between apps.

So what I have is one key.
If I hold my `Home` key, which is under my pinky, plus another key like `B`, I go to the Brave browser.
`Home` + `T` is my terminal.
`Home` + `M` is the MindRoom app.
My Glove80 firmware turns holding `Home` into `Ctrl` + `Alt` + `Shift`, and I have 14 of these bindings.
The same ones live in my Hyprland config on Linux.

## Why not AppleScript

Typically people suggest using an {{< tooltip text="Apple's scripting language for controlling Mac apps. Running a script starts a new process, compiles it, and sends a message to the app." >}}AppleScript{{< /tooltip >}} like `tell application "Brave Browser" to activate`, or `open -b <bundle id>`.
I did not find those reliable, and they were quite slow compared to Keyboard Maestro.
Karabiner-Elements can bind app hotkeys from a file too, often via `open -b` or its `open_application` action, but I didn't want a verbose JSON config just for 14 bindings.

So what did I do?
I used a reverse engineering tool to figure out what mechanism Keyboard Maestro actually uses.

## What Keyboard Maestro actually does

I asked my agent in MindRoom to use [REA](https://github.com/morluto/rea), a tool that lets AI agents reverse engineer apps and binaries, on Keyboard Maestro.
The Claude Opus 5.5 subagent it handed this to declined straight away, because it was asked to disassemble a commercial binary.
So I switched to a more willing model.
I gave it a prompt that asked for static analysis only, for interoperability, without launching or patching anything and skipping all licensing and registration code[^license].
A quick check with `nm` and `strings` already turned up the candidate APIs.
To see which path actually runs, it ran REA with {{< tooltip text="A free reverse engineering suite from the NSA that turns machine code back into readable assembly and C-like code." >}}Ghidra{{< /tooltip >}} on a copy of the Keyboard Maestro Engine binary and wrote a report[^rea].

Keyboard Maestro registers its global hotkeys with Carbon's `RegisterEventHotKey`, which needs no Accessibility permission.
When a hotkey fires, it calls `SetFrontProcessWithOptions`, an old {{< tooltip text="Apple's older C interfaces for Mac apps, from the classic Mac OS era. Many are deprecated but still work." >}}Carbon{{< /tooltip >}} function that brings the app to the front with all its windows.
Apple deprecated `SetFrontProcessWithOptions` in 2013, but it still works.
There's no AppleScript involved, and the app doesn't have to answer anything.

## Building the replacement

From that report, my agent had Claude Opus 5.5 write a small Swift program that stays running in the background and does the same thing.
The first working version took just a couple of prompts, and my main instruction was one line:

> i want to have something that i can just configure with a text file. declaratively

Then GPT-6.2 Sol reviewed it and found bugs.
The worst one would have broken my MindRoom key: the tool read any value ending in `.app` as a file path, so the {{< tooltip text="The unique name macOS uses for an app, like com.brave.Browser. It stays the same when the app is renamed or moved." >}}bundle ID{{< /tooltip >}} `chat.mindroom.app` was never looked up as an app.

It took one afternoon to go from my first message to a public repo with CI, a Homebrew formula, and a nix-darwin module.

## Testing the alternatives

I had assumed the deprecated Carbon call was what made Keyboard Maestro fast.
Apple can remove a deprecated function in any macOS release, so I had an agent benchmark nine ways to bring an app to the front from a background process[^alt].

AppKit's supported {{< tooltip text="The Swift and Objective-C interface for a running app. Its activate method asks macOS to bring that app to the front." >}}`NSRunningApplication.activate`{{< /tooltip >}}, with the option to bring all windows, turned out to be just as fast.
In every run it came within about 3 ms of `SetFrontProcessWithOptions`, sometimes faster and sometimes slower.
The raw activation calls, timed without a hotkey press, had already hinted at it: 20.8 ms for `SetFrontProcessWithOptions` versus 23.1 ms for AppKit's `activate`.
Since macOS 14, the OS can refuse an activation request from a background app, for example right after you type into the frontmost window.
In 480 test switches across the benchmarked methods, with typing right before each switch, macOS never refused.
So the tool now uses AppKit's `activate` call instead.

That points to the real reason Keyboard Maestro feels instant: it stays resident and makes one in-process call, whichever activation API it uses.
`osascript` starts a new process for every key press, compiles the script, and sends an {{< tooltip text="The message system Mac apps use to talk to each other. The sender waits until the receiving app answers." >}}Apple Event{{< /tooltip >}} that the app has to answer.
`open -b` also starts a new process every time.

## How fast it is

These are the medians from synthetic key press to app in front, on my M2 MacBook[^bench]:

| Method | Median | Benchmark run |
|---|---:|---|
| `macos-hotkey-app-switcher` (AppKit, current) | 29.3 ms | Nov 20 head-to-head |
| `macos-hotkey-app-switcher` (Carbon, earlier) | 26.6 ms | Nov 20 head-to-head |
| `open -b <bundle id>` | 58 ms | Nov 19 baseline |
| `osascript -e 'tell application id "…" to activate'` | 112 ms | Nov 19 baseline |

That's about twice as fast as `open -b`, and nearly four times as fast as AppleScript.
I didn't time Keyboard Maestro's full hotkey path, or other resident launchers like Hammerspoon or Raycast.
They also avoid spawning a process per key press, so they should be in the same ballpark.
The difference here is scope: this tool is one Swift file of under 300 lines, with no dependencies, no Accessibility permission, and no UI.

## How it fits in my config

The config is one line per hotkey.
These are my bindings:

```ini
# Format: modifiers+key = bundle id (or an app path, which must contain a /). Saved changes apply at once.
# Taken from the Keyboard Maestro "Open Apps" group (all windows, reopen windows, leave it at the front).

ctrl+alt+shift+1 = com.1password.1password        # 1Password
ctrl+alt+shift+3 = com.t3tools.t3code             # T3 Code
ctrl+alt+shift+b = com.brave.Browser              # Brave Browser
ctrl+alt+shift+c = com.apple.iCal                 # Calendar
ctrl+alt+shift+e = com.apple.mail                 # Mail
ctrl+alt+shift+g = com.google.Chrome              # Google Chrome
ctrl+alt+shift+m = chat.mindroom.app              # MindRoom
ctrl+alt+shift+p = com.spotify.client             # Spotify
ctrl+alt+shift+s = com.tinyspeck.slackmacgap      # Slack
ctrl+alt+shift+t = com.googlecode.iterm2          # iTerm2
ctrl+alt+shift+u = com.todesktop.230313mzl4w4u92  # Cursor
ctrl+alt+shift+v = com.microsoft.VSCode           # Visual Studio Code
ctrl+alt+shift+x = com.openai.codex               # Codex
ctrl+alt+shift+z = us.zoom.xos                    # Zoom
```

The tool watches the file, so saving it applies the change right away.

My [hotkeys file](https://github.com/basnijholt/dotfiles/blob/main/configs/macos-hotkey-app-switcher/hotkeys.conf) lives in my dotfiles.
nix-darwin installs the tool and starts it as a {{< tooltip text="The macOS service manager. A launchd agent is a background program that starts when you log in." >}}launchd{{< /tooltip >}} agent:

```nix
inputs.macos-hotkey-app-switcher.url = "github:basnijholt/macos-hotkey-app-switcher";
# ...
services.macos-hotkey-app-switcher.enable = true;
```

If you don't use Nix, Homebrew works too:

```sh
brew install basnijholt/tap/macos-hotkey-app-switcher
brew services start macos-hotkey-app-switcher
```

Now my app hotkeys come with those four commands too.

## What it doesn't do

It only switches apps.
Keyboard Maestro does hundreds of other things, and it's still the tool I'd recommend for anything beyond this.
If you keep it, turn off its app hotkeys first, because macOS lets two apps hold the same key and then both fire.

## Conclusion

I reverse engineered Keyboard Maestro to copy its trick, and the tool ended up not needing it.
Staying running in the background and making one call is enough, and my app hotkeys now live in my dotfiles like everything else.

[^rea]: The analysis ran on Keyboard Maestro Engine 11.1.1, on the arm64 slice of a copied binary (`lipo -thin arm64`), with the REA CLI (`search`, `xrefs`, `function`) and Ghidra 12.2. Nothing was launched or patched. The report traced the action from `AActivateApplication::DoAction` through Keyboard Maestro's own `activateWithOptions:` wrapper to `GetProcessForPID` and `SetFrontProcessWithOptions`, and found that "all windows" maps to flag `0` and "one window" to flag `1` (`kSetFrontProcessFrontWindowOnly`).
[^license]: Before writing this post (checked on 2026-11-20), I looked for whether Keyboard Maestro's license forbids this kind of analysis and couldn't find an app license agreement at all. I bought Keyboard Maestro 11 directly from Stairways Software (through FastSpring), not from the Mac App Store. The 11.1.1 download, the store page, and the wiki state only that a license is per user, for up to five Macs, and for one major version. The app bundle's license folder holds only the licenses of open-source libraries it uses, and my tool contains no Keyboard Maestro code.
[^bench]: Measured on an M2 MacBook using two small test apps switched back and forth 30 times per method with synthetic key presses, timed until the app was in front with its window on top. On 2026-11-19 (the baseline run), the earlier Carbon build measured 26 to 28.3 ms across revisions against 57.5 ms for `open -b` and 112 ms for `osascript`. On 2026-11-20, the current AppKit build measured 29.3 ms against 26.6 ms for the Carbon build in the same head-to-head run, which is within the spread between runs.
[^alt]: Measured on 2026-11-20 on the M2, macOS 26.5.2, 30 rounds per method and condition, from a background launchd job, between two test apps and between TextEdit and Calculator. `NSWorkspace.openApplication` and `LSOpenCFURLRef` were 1 to 24 ms slower and raised only one window. Setting the app's "frontmost" attribute through the Accessibility API needs a permission grant. On macOS 13 the tool also sets the older `activateIgnoringOtherApps` option, which macOS 14 and later ignore. Private SkyLight functions were not considered.
