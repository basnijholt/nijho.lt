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

I have a Raspberry Pi 4. I have an external Samsung T5 SSD. I want to turn them into a rock-solid, declarative server running [NixOS](https://nixos.org/).

Sounds simple, right?

But I have a few constraints that make this surprisingly difficult:
1.  **I refuse to use the SD card for the OS.** SD cards are slow and unreliable. I want the root filesystem on the SSD, and I want it to be **ZFS** for snapshots and compression.
2.  **I refuse to attach a monitor.** The Pi lives in a cupboard. I want to plug it in, walk away, and SSH into it.
3.  **I am doing this from a Mac.** This complicates building Linux artifacts.
4.  **I want it to be fully declarative.** No "flash an image, then SSH in and run `apt update`". The entire install process should be code.

Here is the journey of how I solved the "Chicken and Egg" problem of headless bootstrapping.

## The Problem with "Standard" Installs

If you download a standard Raspberry Pi OS or Ubuntu image, the workflow is usually:
1.  Flash SD card.
2.  Edit a `wpa_supplicant.conf` or `user-data` file in the boot partition to enable WiFi/SSH.
3.  Boot.
4.  Manually run commands to move the OS to the SSD.

This is imperative. It's fragile. And if I mess up the SSD migration, I have to start over.

With NixOS, we have tools like [**nixos-anywhere**](https://github.com/nix-community/nixos-anywhere), which can take a running Linux machine, wipe it, and install a perfect NixOS configuration in its place via SSH. This sounded perfect.

## Attempt 1: The "Hijack" Method (Failure)

My first thought was: "The Pi is already running DietPi (Debian). I can just use `nixos-anywhere` to hijack it!"

`nixos-anywhere` works by using `kexec`—a Linux kernel feature that allows a running kernel to load *another* kernel into RAM and execute it, effectively soft-rebooting into a new OS without a BIOS reset. It uploads a NixOS installer into RAM, switches to it, wipes the disk, and installs.

I ran the command:
```bash
nix run github:nix-community/nixos-anywhere -- root@192.168.1.x ...
```

It failed immediately:
```
kexec_load failed: Function not implemented
```

It turns out minimal kernels (like those in DietPi or some default Pi images) often compile *out* `kexec` support to save a few kilobytes of RAM. Without `kexec`, `nixos-anywhere` cannot launch its installer. This path was a dead end unless I recompiled the Debian kernel first, which defeats the point.

## The Solution: A Custom Bootstrap Image



Since I couldn't hijack the existing OS, I had to replace it. I needed a bootable SD card image that:

1.  Is a valid NixOS system.

2.  Has **SSH enabled** with my public keys pre-authorized (no passwords).

3.  Has **WiFi credentials** baked in (so it gets online immediately).

4.  Contains the necessary proprietary firmware for the Pi 4.

5.  **Has ZFS tools** (so `nixos-anywhere` can run the installation from this environment).



### The Hurdles (and Fixes)



Building this image wasn't straightforward. I hit three major roadblocks:



#### 1. The Disappearing WiFi Driver

My first builds booted but had no network. Debugging showed that the Broadcom WiFi driver (`brcmfmac`) was missing.

It turns out the `sd-image` builder aggressively shrinks the kernel modules to keep the image small. Since WiFi isn't needed to *boot* (strictly speaking), it stripped the driver.



**The Fix:** I forced the module into the `initrd`, which protects it from being stripped. I also had to explicitly include the proprietary firmware package.



```nix

# installers/pi4-sd.nix

{

  # ...

  # Force WiFi module into initrd to prevent shrinking

  boot.initrd.availableKernelModules = [ "brcmfmac" ];

  

  # Essential for WiFi on Pi 4 (Proprietary blobs)

  hardware.enableRedistributableFirmware = true;

  hardware.firmware = [ pkgs.raspberrypiWirelessFirmware ];

}

```



#### 2. ZFS vs. Bleeding Edge Kernels

I initially used `pkgs.linuxPackages_latest` (Kernel 6.18+). The build failed immediately because OpenZFS hadn't caught up to that kernel version yet, marking the ZFS module as "broken."

**The Fix:** I switched to the LTS kernel (`pkgs.linuxPackages`), which is stable and fully supported by ZFS.



#### 3. The Kexec Dead End

Even with a working bootstrap image, `nixos-anywhere` failed at the `kexec` step with `Resource busy`. The Pi 4 hardware/kernel combination often locks up during kexec transitions.

**The Fix:** Since my bootstrap image was already running NixOS (and I added ZFS support to it), I realized **I didn't need to kexec**. I just needed to skip that phase.



### Defining the Installer



I added a special `pi4-bootstrap` configuration to my [flake.nix](https://github.com/basnijholt/dotfiles/blob/main/configs/nixos/flake.nix).



```nix

# installers/pi4-sd.nix

{ lib, pkgs, modulesPath, ... }:

{

  imports = [

    (modulesPath + "/installer/sd-card/sd-image-aarch64.nix")

    ../hosts/pi4/networking.nix # Contains WiFi config

  ];



  # Bake in WiFi credentials (from a secret file)

  imports = lib.optional (builtins.pathExists ../hosts/pi4/wifi.nix) ../hosts/pi4/wifi.nix;



  networking.hostName = lib.mkForce "pi4-bootstrap";

  

  # Enable ZFS (so we can format the target drive)

  boot.supportedFilesystems = lib.mkForce [ "ext4" "vfat" "zfs" ];

  networking.hostId = "8425e349"; # Required for ZFS

  

  # Use LTS kernel for ZFS compatibility

  boot.kernelPackages = pkgs.linuxPackages;

  

  # Essential tools

  environment.systemPackages = with pkgs; [ git vim htop kexec-tools ];

}

```



### The macOS Cross-Compilation Hurdle

Here was the next problem: I am on an Apple Silicon Mac (`aarch64-darwin`). The Raspberry Pi is `aarch64-linux`. 
While the architecture is the same (ARM64), the OS is not. Nix on macOS cannot natively build Linux kernel modules or disk images (it lacks the Linux filesystem tools).

Usually, you set up a remote builder or a Linux VM. But I didn't want to maintain a permanent builder just for this.

**The Fix: Docker as an Ephemeral Builder**

I realized I could use Docker to spin up a Linux environment *just* to build this image. By mounting my local directory into the container, I could build the artifact and spit it back out to my Mac.

I documented the exact command in my [README](https://github.com/basnijholt/dotfiles/blob/main/configs/nixos/hosts/pi4/README.md), but it looks roughly like this:

```bash
docker run --rm -it \
  --platform linux/arm64 \
  -v $(pwd):/work \
  nixos/nix \
  nix build .#nixosConfigurations.pi4-bootstrap.config.system.build.sdImage
```

This effectively gives me an on-demand Linux build farm.

## The Installation Dance

With my custom `pi4-bootstrap.img` generated, the process became beautifully reproducible:

1.  **Flash:** Write the image to an SD card.
2.  **Boot:** Plug the SD card and the empty SSD into the Pi and power it on.
3.  **Wait:** The Pi boots, loads the firmware, brings up `wlan0` with my credentials, and starts `sshd`.
4.  **Install:** I run `nixos-anywhere` from my Mac.

Because `kexec` fails on this hardware, I explicitly tell `nixos-anywhere` to skip the reboot-into-ram phase and just run the partitioning and installation directly from my running bootstrap OS.

```bash
nix run github:nix-community/nixos-anywhere -- \
  --flake .#pi4 \
  --build-on remote \
  --phases disko,install \
  root@<PI_IP_ADDRESS>
```

`nixos-anywhere` connects to the bootstrap OS (running on the SD card), detects the SSD, and uses my [Disko configuration](https://github.com/basnijholt/dotfiles/blob/main/configs/nixos/hosts/pi4/disko.nix) to partition it with ZFS. It then installs the *final* system configuration—which includes ZFS support, heavy virtualization tools, and my home server apps—onto the SSD.

## The Result

I now have a Raspberry Pi 4 that boots from an external SSD with enterprise-grade storage features (compression, snapshots), managed entirely by code.

If I ever want to repurpose this Pi, I don't need to hook up a monitor. I just flash the bootstrap card, boot it, and push a new config.

The combination of **NixOS**, **Disko**, and **nixos-anywhere** feels like a superpower for homelabs. It turns hardware into software.
