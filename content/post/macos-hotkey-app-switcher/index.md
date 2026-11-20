---
title: "Switching apps on macOS in 27 ms ⚡"
subtitle: "How I found out what Keyboard Maestro does, and turned it into a one-file tool I configure with a text file"
summary: "Keyboard Maestro was one of the last things on my Mac I couldn't set up from a text file in my dotfiles, and I only used it to switch apps with a hotkey. AppleScript was too slow, so I had an agent run a static analysis on Keyboard Maestro to find the macOS call it makes. A few hours and a couple of prompts later, I had a 267-line Swift tool that reads a plain text file, needs no permissions, and installs with Homebrew or nix-darwin."
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
I almost exclusively voice-dictate my interactions with AI (I [self-host the dictation]({{< ref "/post/diction-agent-cli-qwen" >}}) too).
When my hands are on the keyboard, they're on a [Glove80]({{< ref "/post/split-ergonomic-mechanical-keyboard-glove80" >}}), the nerdiest variant you can get, with all black keys.

I also have a deep obsession with declarative tools.
Whenever I set up a new VM, a computer at home, or a new MacBook, I want the entire process to be reproducible and fast.
That's what pulled me into [NixOS]({{< ref "/post/proxmox-to-nixos" >}}) and why my [dotfiles]({{< ref "/post/dotfiles" >}}) are public.

There was one holdout on my Mac: Keyboard Maestro, which I only used to switch between apps with a hotkey.
This week I replaced it with [`macos-hotkey-app-switcher`](https://github.com/basnijholt/macos-hotkey-app-switcher), a small tool I built end to end with AI agents from a couple of prompts.
It reads its hotkeys from a plain text file, and it brings an app to the front in about 27 ms.

{{% callout note %}}
**TL;DR:**
- I used Keyboard Maestro only for app hotkeys, and it was one of the last things on my Mac I couldn't configure from a text file.
- AppleScript and `open -b` were two to four times slower, so I had an agent run a static analysis on Keyboard Maestro to see which macOS call it makes.
- It's one deprecated Apple function, `SetFrontProcessWithOptions`, and it needs no special permissions.
- An agent built a Swift tool around it, with a plain text config, CI, a Homebrew formula and a nix-darwin module, in about four hours.
- A public, non-deprecated AppKit call turned out to be just as fast, so the tool now uses that instead, in 267 lines.
{{% /callout %}}

{{< toc >}}

## Four commands to a new Mac

When I set up a new laptop recently, I ran about four commands in the terminal.
One installs my [dotfiles](https://github.com/basnijholt/dotfiles).
One loads my {{< tooltip text="A private key used to decrypt files. My SSH keys and other secrets live in a private repository encrypted with it." >}}GPG key{{< /tooltip >}}, which decrypts my secrets, like my SSH keys.
One installs {{< tooltip text="Nix for macOS system configuration: the apps, settings and background services of the whole Mac are declared in one config file." >}}nix-darwin{{< /tooltip >}}.
And the last one is a Nix switch command, after which everything is the way I want it to be.

There were a couple of holdouts.
One of them was [Keyboard Maestro](https://www.keyboardmaestro.com/), which is a fantastic application.
It's paid, and I paid for it.
But I used it almost exclusively for one thing: hotkeys that switch to an app.
Its macros are made in its own app, not in a text file I can keep in my dotfiles.

## How I switch apps

I'm a furious multitasker, so I have many things open at once.
I don't want to be [tapping Command+Tab like a mad person]({{< ref "/post/split-ergonomic-mechanical-keyboard-glove80" >}}) to get to the one I want.

Instead, I hold my `Home` key, which sits under my pinky on the Glove80, and press a letter.
`Home` + `B` brings up the Brave browser.
`Home` + `T` is my terminal.
`Home` + `M` is the MindRoom app.
On macOS, holding `Home` sends `Ctrl` + `Alt` + `Shift`, so `Home` + `B` is really `Ctrl` + `Alt` + `Shift` + `B`.
I had 14 of these in Keyboard Maestro, and the same bindings already lived in my Hyprland config on Linux.

## Why not AppleScript

The usual advice is to bind the hotkey to an {{< tooltip text="Apple's scripting language for controlling Mac apps. Running a script starts a new process, compiles it, and sends a message to the app." >}}AppleScript{{< /tooltip >}} like `tell application "Brave Browser" to activate`, or to `open -b <bundle id>`.
I'd tried that before.
I didn't find it reliable, and it was much slower than Keyboard Maestro.

The other common tools have their own catch.
Karabiner-Elements is configured with a JSON file, but it runs a shell command like `open -b` for every key press.
`skhd` can be configured from nix-darwin, but it needs the {{< tooltip text="The macOS privacy setting that lets an app watch or control other apps. It is granted by hand in System Settings, per app binary." >}}Accessibility permission{{< /tooltip >}}, and macOS forgets it every time Nix rebuilds the binary to a new path.

So I wanted to know what Keyboard Maestro does differently.

## Finding out what Keyboard Maestro does

I asked my agent in [MindRoom]({{< ref "/post/mindroom" >}}) to use [REA](https://github.com/morluto/rea), a tool that lets AI agents reverse engineer apps and binaries, on Keyboard Maestro.
The Claude Opus 5.5 subagent it handed this to declined straight away, because it was asked to disassemble a commercial binary.
The agent then listed the functions Keyboard Maestro imports with `nm` and `strings`, which already pointed at two old {{< tooltip text="Apple's older C interfaces for Mac apps, from the classic Mac OS era. Many are deprecated but still work." >}}Carbon{{< /tooltip >}} functions.

To confirm it, I switched to a more willing model.
Its prompt asked for static analysis only, for interoperability, without launching or patching anything and skipping all licensing and registration code.
It ran REA with {{< tooltip text="A free reverse engineering suite from the NSA that turns machine code back into readable assembly and C-like code." >}}Ghidra{{< /tooltip >}} on a copy of the Keyboard Maestro Engine binary and wrote a report[^rea].

The answer turned out to be simple.
Keyboard Maestro catches the key with `RegisterEventHotKey`, which needs no permission.
Then it looks up the app's process and calls `SetFrontProcessWithOptions` with flag `0`, which brings the app to the front with all its windows.
If the app isn't running, it launches it and then makes the same call.
There's no AppleScript and no message to the app that it has to answer.

`SetFrontProcessWithOptions` is a public Apple function, still declared in the macOS SDK headers, but marked deprecated since macOS 10.9.
AppleScript is slower because every `osascript` call starts a new process, compiles the script, and sends an {{< tooltip text="The message system Mac apps use to talk to each other. The sender waits until the receiving app answers." >}}Apple Event{{< /tooltip >}} to the app, which a busy app can take a while to answer.

Before writing this post, I checked whether Keyboard Maestro's license forbids this kind of analysis[^license].
I couldn't find a license agreement for the app at all.
The tool I built contains no Keyboard Maestro code.
At first it only called the same Apple function, and now it doesn't even do that (more below).

## Building it from a couple of prompts

With the report in hand, my agent had Claude Opus 5.5 write a small Swift program that stays running in the background and does the same thing.
I said what I wanted, and the agents did the rest:

> i want to have something that i can just configure with a text file. declaratively

Then GPT-6.2 Sol reviewed it and found real bugs.
The worst one would have broken my MindRoom key: the tool read any value ending in `.app` as a file path, so the {{< tooltip text="The unique name macOS uses for an app, like com.brave.Browser. It stays the same when the app is renamed or moved." >}}bundle ID{{< /tooltip >}} `chat.mindroom.app` was never looked up as an app.
A last review of the code against the report found two places where it still behaved differently from Keyboard Maestro.
For example, it skipped the call when the app was already in front, so a window buried under another app's window stayed buried.

After that I asked for a separate repository, CI, a Homebrew formula, an animated SVG logo and a nicer README.
Along the way, the agent noticed that the daily updater in my Homebrew tap had been failing for days, and fixed it.
I also asked for a more descriptive name, which is how `app-hotkeys` became `macos-hotkey-app-switcher`.

From my first screenshot to the renamed v0.2.0 took about four hours.
Most of my messages were one line[^messages].

## Dropping the deprecated call

While writing this post, I asked whether there's a call that isn't deprecated and is just as fast.
An agent compared nine ways to bring an app to the front, on my M2, from a background process like the tool[^alt].
AppKit's {{< tooltip text="The public Swift and Objective-C interface for a running app. Its activate method asks macOS to bring that app to the front." >}}`NSRunningApplication.activate`{{< /tooltip >}} with the "all windows" option came within about 3 ms of `SetFrontProcessWithOptions` in every run, either way, which is noise.
Since macOS 14, an app can turn down such a request, for example when you just typed into the app in front.
It never happened: in 480 switches with typing right before each one, across all the methods, macOS turned down none.
It also passed every check: buried windows raised, hidden apps shown, minimized windows back, and apps that weren't running launched.

So v0.3.0 uses the public call, and the code got 13 lines shorter.

## How fast it is

I believe this is the fastest and simplest way to switch apps with a hotkey on macOS.
To be fair, Keyboard Maestro is about as fast: its deprecated call and my public one measured the same.

These are the medians from key press to app in front, on my M2 MacBook[^bench]:

| Method | Median |
|---|---:|
| `macos-hotkey-app-switcher` | 27 ms |
| `open -b <bundle id>` (what Karabiner runs) | 58 ms |
| `osascript -e 'tell application id "…" to activate'` | 112 ms |

That's about twice as fast as `open -b`, and four times as fast as AppleScript.
The tool is one Swift file of 267 lines, with no dependencies, no menu bar icon and no UI.

## How it fits in my config

The config is one line per hotkey:

```ini
ctrl+alt+shift+b = com.brave.Browser
ctrl+alt+shift+t = com.googlecode.iterm2
ctrl+alt+shift+m = chat.mindroom.app
```

A value with a `/` is treated as a path to an app, anything else as a bundle ID.
The tool watches the file, so saving it applies the change right away, and a broken edit keeps the old bindings and logs the line number.
`--check` validates the file without running anything.

My [hotkeys file](https://github.com/basnijholt/dotfiles/blob/main/configs/macos-hotkey-app-switcher/hotkeys.conf) lives in my dotfiles, next to the Hyprland bindings for Linux.
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

## What it costs

- **macOS decides.** Since macOS 14, an app can be refused the front. In my tests it never was, but a future macOS could be stricter.
- **Two apps can hold the same key.** macOS lets a second app register the same combination, and then both fire. I had to turn off the Keyboard Maestro group before switching.
- **It does one thing.** Keyboard Maestro does hundreds of other things, and it's still the tool I'd recommend for anything beyond switching apps.

## Conclusion

My app hotkeys are now a text file in my dotfiles instead of macros in an app.
I could have kept a paid app running for one feature, or put up with AppleScript being four times slower.
Instead, an agent found out which call the fast app makes, another agent built a tool around that call in an afternoon, and a third found a public call that is just as fast.

[^rea]: The analysis ran on Keyboard Maestro Engine 11.1.1, on the arm64 slice of a copied binary (`lipo -thin arm64`), with the REA CLI (`search`, `xrefs`, `function`) and Ghidra 12.2. Nothing was launched or patched. Setup took about 2 minutes and the first Ghidra analysis 208 seconds. The report traced the action from `AActivateApplication::DoAction` through Keyboard Maestro's own `activateWithOptions:` wrapper to `GetProcessForPID` and `SetFrontProcessWithOptions`, and found that "all windows" maps to flag `0` and "one window" to flag `1` (`kSetFrontProcessFrontWindowOnly`).
[^license]: Checked on 2026-11-20. I bought Keyboard Maestro 11 directly from Stairways Software (through FastSpring), not from the Mac App Store. The 11.1.1 download, the store page and the wiki state only that a license is per user, for up to five Macs, and for one major version. The app bundle's license folder holds only the licenses of open-source libraries it uses.
[^messages]: Counted from the chat thread on 2026-11-19: from 11:54 to 15:57, I sent 26 messages, including two screenshots and two pasted reports. Opus 5.5 wrote most of the code and Sol reviewed it over three rounds.
[^bench]: Measured by the building agent on 2026-11-19 on an M2 MacBook: two small test apps, switched back and forth 30 times per method with synthetic key presses, timed until the app was in front with its window on top. The tool's medians were 26 ms (v0.1.0), 27.3 ms (after review fixes) and 28.3 ms (v0.1.1). Keyboard Maestro's call on its own, timed the same way without a hotkey, took 20.8 ms. I didn't time Keyboard Maestro's whole hotkey path, or other launchers. On 2026-11-20, v0.3.0 with the public call took 29.3 ms against 26.6 ms for v0.2.0 in the same run, which is within the spread between runs.
[^alt]: Measured on 2026-11-20 on the M2, macOS 26.5.2, 30 rounds per method and condition, from a background launchd job, between two test apps and between TextEdit and Calculator. `NSWorkspace.openApplication` and `LSOpenCFURLRef` were 1 to 24 ms slower and raised only one window. Setting the app's "frontmost" attribute through the Accessibility API needs a permission grant. The `activateIgnoringOtherApps` option is deprecated since macOS 14 and does nothing. Private SkyLight functions were not considered.
