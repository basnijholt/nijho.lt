---
title: "NixOS on Raspberry Pi: The Headless, Wireless, ZFS Way"
subtitle: "Bootstrapping a server without a monitor, keyboard, or patience"
summary: "Installing NixOS on a Raspberry Pi 4 is easy. Installing it on a ZFS-formatted USB SSD, completely headless, over WiFi, from a Mac, without ever connecting a monitor? That requires some engineering. Here is how I solved the 'Chicken and Egg' problem of bootstrapping embedded servers."
date: 2025-12-06T12:00:00+01:00
draft: false
authors:
  - admin
categories:
  - HomeLab
  - NixOS
  - Raspberry Pi
tags: ["nixos", "raspberry-pi", "zfs", "headless", "automation"]
---

# NixOS on Raspberry Pi: The Headless, Wireless, ZFS Way

## Why Am I Doing This?

Let me be honest: my Raspberry Pis were working perfectly fine.
They had been running DietPi for years without a single issue.
There was absolutely no practical reason to change anything.

But I have become a Nix evangelist.
A true believer.
Once you experience the peace of knowing your entire system is defined in code—reproducible, version-controlled, and recoverable—going back to imperative configuration feels like writing code without git.

I wrote about [my conversion from Proxmox to NixOS](/post/proxmox-to-nixos/) and how I set up a [local nix cache server](/post/nixos-cache/) to avoid compilation nightmares.
Now my entire homelab—PC, NUC, HP EliteDesk—is managed declaratively.
The Raspberry Pis were the last holdouts.
They had to be assimilated.

There is also a practical benefit beyond ideology: ZFS.
With ZFS on the Pi 4's external SSD, I can use [Syncoid](https://github.com/jimsalterjrs/sanoid) to automatically replicate snapshots to my TrueNAS server.
The Pi joins my backup rotation alongside every other machine in my fleet.
If the SSD fails, I can restore from a snapshot instead of rebuilding from scratch.

(My Pi 3, by contrast, just runs from an SD card with ext4—ZFS on an SD card is not a good idea due to the write amplification and limited lifespan of flash storage. But at least the *configuration* is still declarative and reproducible. One caveat: the Pi 3's 1GB of RAM is not enough to run `nixos-rebuild` locally—the Nix evaluator gets OOM-killed. I build on my PC and deploy remotely with a [simple script](https://github.com/basnijholt/dotfiles/blob/main/configs/nixos/hosts/pi3/deploy.sh).)

So here I am, spending days solving a problem I did not have, for a machine that was already working.
This is the NixOS way.

## The Setup

I have a Raspberry Pi 4 glued to the bottom of a standing lamp.
This is not a joke.
The lamp sits in the corner of my living room, and the Pi serves as a lightweight always-on server.
It is physically impossible to connect it to HDMI or Ethernet without dismounting it and rearranging furniture.

I also have an external Samsung T5 SSD that I want to use as the root filesystem.
SD cards are slow and unreliable; I have had them corrupt on me before.
I want ZFS for snapshots and compression.

So my constraints are:
1. **No monitor.** The Pi cannot be connected to HDMI.
2. **No Ethernet.** It must connect over WiFi immediately on first boot.
3. **ZFS on SSD.** Not the SD card.
4. **Fully declarative.** The entire setup should be reproducible from code.

This turned out to be one of the most frustrating NixOS projects I have undertaken.
It took me nearly 70 commits and countless hours of debugging.
Here is what I tried, what failed, and what finally worked.

## The Core Problem

The fundamental issue is a chicken-and-egg problem: to install NixOS on the SSD, I need to boot *something* first.
That something needs WiFi credentials baked in (so I can SSH to it), and it needs ZFS tools (so it can partition the SSD).
But I cannot interactively configure WiFi because there is no monitor.

## Attempt 1: Hijacking DietPi with nixos-anywhere

The Pi was already running DietPi.
I thought I could use [nixos-anywhere](https://github.com/nix-community/nixos-anywhere) to "hijack" it—SSH in and have it replace the running OS with NixOS.

`nixos-anywhere` uses `kexec` to load a NixOS installer into RAM, then wipes the disk and installs.
I ran:

```bash
nix run github:nix-community/nixos-anywhere -- root@192.168.1.x --flake .#pi4
```

It failed immediately:
```
kexec_load failed: Function not implemented
```

DietPi's minimal kernel compiles out `kexec` support to save memory.
Without `kexec`, `nixos-anywhere` cannot work.
I could have recompiled the kernel, but that defeats the purpose of a quick install.

## Attempt 2: A NixOS Bootstrap SD Card

Since I could not hijack the existing OS, I needed to build a custom NixOS SD card image with:
- SSH enabled with my public keys
- WiFi credentials baked in
- ZFS tools for partitioning the SSD

This is where I spent most of my time.

### The Disappearing WiFi Driver

My first builds booted, but the Pi had no network.
I eventually discovered that the Broadcom WiFi driver (`brcmfmac`) was missing.
The SD image builder aggressively strips kernel modules to keep the image small.
Since WiFi is not strictly required to *boot*, it got removed.

I forced the module to load:
```nix
boot.kernelModules = [ "brcmfmac" ];
```

### ZFS vs. Bleeding Edge Kernels

I initially used `pkgs.linuxPackages_latest`.
The build failed because OpenZFS had not caught up to that kernel version yet.
I switched to the LTS kernel, which is stable and fully supported by ZFS.

### The Kexec Dead End (Again)

Even with a working NixOS bootstrap image, `nixos-anywhere` failed at the `kexec` step with `Resource busy`.
The Pi 4 hardware locks up during kexec transitions.
I tried `--phases disko,install` to skip kexec, but the complexity of nixos-anywhere's remote building made it unreliable on the Pi's limited resources.

### WiFi Credentials and Git

Here is a subtle problem: WiFi credentials should not be committed to git.
But Nix flakes only see git-tracked files by default.
I needed a way to include a gitignored `wifi.nix` file in the build.

I learned this the hard way when an AI assistant I was using accidentally ran `git add -f wifi.nix` and pushed my credentials to GitHub.
I had to change my WiFi password and SSID, which took hours because every device in my house needed to be reconfigured.

The solution is to use `path:.` instead of `.` when building:
```bash
nix build 'path:.#nixosConfigurations.pi4-bootstrap.config.system.build.sdImage' --impure
```

The `path:.` prefix tells Nix to include all files in the directory, not just git-tracked ones.
The `--impure` flag allows reading files outside the pure evaluation sandbox.

## Attempt 3: Flash the SSD Directly from x86

After getting the SD card approach working (barely), I had what I thought was a better idea.

Why bother with an SD card at all?
I have a Linux PC with ZFS support.
I could just connect the SSD directly, partition it, install NixOS, and then move it to the Pi.
The Pi 4 can boot directly from USB; it does not strictly need an SD card.

This seemed elegant.
No SD card shuffling.
No waiting for WiFi to connect.
Just plug in a fully-configured SSD and boot.

### The binfmt Nightmare

The problem is that my PC is x86_64 and the Pi is aarch64.
NixOS can cross-compile, but many packages need to run native code during the build (like running `ldconfig` or activation scripts).
Linux has a feature called `binfmt_misc` that can transparently run ARM binaries through QEMU emulation.

I enabled it:
```nix
boot.binfmt.emulatedSystems = [ "aarch64-linux" ];
```

Then I tried to build the Pi's system and run `nixos-install` with `--root /mnt` pointing to the mounted SSD.

It was painfully slow.
My 24-core Ryzen 3900X ran at 100% on all cores for over two hours, building the Raspberry Pi Linux kernel under emulation.
It still was not done when I gave up.

The emulation overhead is brutal.
Every ARM instruction gets translated to x86 at runtime.
For a kernel build with millions of instructions, this adds up to hours of wall-clock time.

### It Worked... Almost

After working around the binfmt issues and configuring the Nix sandbox to expose the emulator:
```nix
boot.binfmt.registrations.aarch64-linux.fixBinary = true;
nix.settings.extra-sandbox-paths = [ "/run/binfmt" ];
```

I eventually got the SSD to boot on the Pi.
The system came up.
But it did not connect to WiFi.

The problem is that `nixos-install` does not run activation scripts.
NetworkManager's `ensureProfiles` option generates the WiFi profile during activation, which never happened.
So the system booted, but `/etc/NetworkManager/system-connections/` was empty.
No WiFi profile, no connection, no SSH access.

I was back to square one.

## The Working Solution: Keep It Simple

After all this complexity, I went back to the SD card approach.

The final workflow:

1. **Build a minimal NixOS SD image** on my Mac (using Docker, which is fast because Docker on Apple Silicon runs ARM natively—no emulation).
2. **Flash the SD card** and boot the Pi.
3. **SSH in** once WiFi connects.
4. **Run three commands** to partition the SSD with [disko](https://github.com/nix-community/disko) and install NixOS:

```bash
sudo nix run github:nix-community/disko -- --mode disko ./disko.nix
nix build .#nixosConfigurations.pi4.config.system.build.toplevel --print-out-paths
sudo nixos-install --system "$SYSTEM" --root /mnt --no-root-passwd
```

No binfmt emulation.
Just native ARM code running on ARM hardware.

### Why Docker on Mac is Fast

Building on my Mac via Docker finished in minutes, not hours.
This surprised me at first—my Mac has fewer cores than my Ryzen.
But Docker on Apple Silicon uses native ARM virtualization, not emulation.
The Linux kernel running inside Docker is actual ARM code running on actual ARM silicon.
There is no instruction translation overhead.

Meanwhile, my x86 PC was trying to emulate every ARM instruction through software.
Even with 24 cores, software emulation cannot compete with native execution.

## What I Learned

Here is a summary of the approaches I tried:

| Approach | Result |
|----------|--------|
| nixos-anywhere on DietPi | Failed: no kexec support |
| nixos-anywhere on NixOS SD | Failed: kexec locks up Pi 4 |
| Direct SSD flash via binfmt on x86 | Too slow (2+ hours on 24 cores) |
| Direct SSD flash (completed) | Booted, but no WiFi (activation scripts) |
| SD card bootstrap + install on Pi | Works reliably |

The lesson: do not fight the hardware.
Running ARM code on ARM silicon is fast.
Emulating ARM on x86 is slow.
The "clever" approach of pre-building everything on my PC was actually the worst approach.

## The Final Configuration

The [bootstrap image](https://github.com/basnijholt/dotfiles/blob/main/configs/nixos/installers/pi-bootstrap.nix) is minimal:
- SSH with my public keys
- WiFi via NetworkManager
- ZFS support
- Binary caches for faster builds

One optimization: I removed NetworkManager's VPN plugins (`plugins = lib.mkForce []`).
Without this, the build pulls in ffmpeg and webkit as dependencies, adding gigabytes to the image for features I do not need.

The [disko configuration](https://github.com/basnijholt/dotfiles/blob/main/configs/nixos/hosts/pi4/disko.nix) sets up a 512MB ESP partition and uses the rest for a ZFS pool with separate datasets for `/`, `/nix`, `/var`, and `/home`.

One important detail: the install script copies `wifi.nix` (which is gitignored) and builds with `path:.` and `--impure` to include it.
NetworkManager's `ensureProfiles` option is actually a systemd service that runs *after* boot, not during installation.
So the WiFi profile gets created on first boot, and the system connects automatically.

## The Result

I now have a Raspberry Pi 4 that boots from an external SSD with ZFS, managed entirely by code.
The Pi lives on its lamp, connecting over WiFi, and I never had to attach a monitor.

Best of all, it is now part of my backup rotation.
Syncoid runs nightly, replicating ZFS snapshots to my TrueNAS server.
If the SSD fails, I can restore from a snapshot.
If I want to migrate to new hardware, I just apply the same Nix configuration.
The Pi is no longer a snowflake—it is cattle, just like the rest of my fleet.

If I need to reinstall, I flash the bootstrap SD card, SSH in, and run three commands.
The entire configuration is in [my dotfiles](https://github.com/basnijholt/dotfiles/tree/main/configs/nixos/hosts/pi4).

It took nearly 70 commits to get here.
Most of those commits were failed experiments.
But now that it works, it is completely reproducible.
That is the NixOS promise: the pain is front-loaded, but you only pay it once.

Was it necessary? Absolutely not.
Would I do it again? Without hesitation.
This is what being a Nix evangelist means.
