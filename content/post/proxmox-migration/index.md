---
title: "I've gone full Nix: Proxmox to NixOS + Incus"
date: 2025-11-29T13:00:00+01:00
draft: false
tags: ["nixos", "proxmox", "incus", "homelab", "migration", "agentic-ai"]
---

# I've gone full Nix: Proxmox to NixOS + Incus

I have officially decommissioned my Proxmox cluster.
After years of running my homelab on Proxmox, starting with a single NUC and expanding to a multi-node cluster, I have migrated everything to NixOS running Incus.

## From Skeptic to Believer

I wasn't always a Nix evangelist.
In fact, I initially despised the language and its syntax.
I couldn't figure out how it worked, and I already had my own specific way of setting up my dotfiles.
I used [Dotbot](/post/dotfiles/) for symlinking and a tool I wrote called [dotbins](/post/dotbins/) for managing binaries.
I didn't feel like I required Nix for most of my tools.
I used [nix-darwin](https://github.com/basnijholt/dotfiles/blob/4f534bf32fb4396dd86ce631dec00717eab7656d/configs/nix-darwin/configuration.nix) on my Mac for a long time, but only to specify Homebrew packages and application settings.

My true conversion happened when I bought my gaming PC, as described in my [local LLM post](/post/local-ai-journey/).
I initially installed Pop!_OS because I wanted to play games and absolutely wanted to avoid Windows.
I got some games to work, but I constantly ran into NVIDIA driver issues that required running random, imperative commands to fix.
I felt that was a bad solution because I could never reproduce those debugging steps later.
Then I did the dumb thing of updating my NVIDIA drivers, not realizing that imperatively managing driver versions and repositories is a recipe for disaster, and got stuck in a GRUB boot loop.
Frustrated, I installed NixOS, hoping its promise of atomic updates would solve this.
The result was glorious.
I never really believed that everything would be byte-for-byte equivalent until I migrated that system to a new disk.
I didn't clone the drive; I just applied my Nix configuration to a fresh install.
It booted, I copied my data, and everything was identical.
That was the moment it clicked.

## The Friction of Imperative Systems

Proxmox is fantastic software.
It lowered the barrier to entry for me and taught me almost everything I know about virtualization, LXC containers, and ZFS.
But fundamentally, Proxmox is built around **clicking buttons**.
It is a GUI-first paradigm.
While you *can* automate it with Terraform or Ansible, it often feels like fighting the tool.
State drift is real.
You change a setting in the UI to debug something, forget about it, and six months later your "infrastructure as code" is out of sync with reality.
For a human, this is annoying.
For an AI agent, it is a disaster.
An agent running in "YOLO mode" might execute hundreds of imperative commands to fix a problem.
It might succeed, but it leaves your system in an undefined, unreproducible state that no one—not even the agent—can fully understand or replicate later.

This friction manifests in hardware management too.
On my HP EliteDesk, the Intel I219-LM network card has a known bug where it hangs with hardware offloading enabled.
I vaguely remembered fixing this years ago on Proxmox, but I had forgotten the details.
When I set up NixOS, I ran into the same issue: the network would randomly drop.
This time, however, the fix isn't a forgotten command run in a root shell history.
It is a [documented systemd service](https://github.com/basnijholt/dotfiles/blob/4f534bf32fb4396dd86ce631dec00717eab7656d/configs/nixos/hosts/hp/networking.nix#L16-L31) in my configuration.
I added a comment explaining exactly *why* `tso off gso off` is needed, citing the forum threads.
If I ever reinstall this machine, the fix applies automatically.
On Proxmox, I would have had to rediscover this pain all over again.

Another example is my Intel NUC, which I wanted to use as a Home Theater PC (HTPC).
On Proxmox, this was a nightmare.
To get video output, I had to pass the GPU through to a VM.
But doing so meant the Proxmox host lost access to the GPU entirely, meaning no local console if things went wrong.
It was a strict trade-off: either I have a media player, or I have a debuggable hypervisor.
With NixOS, I don't have to choose.
The host OS runs [Kodi directly](https://github.com/basnijholt/dotfiles/blob/4f534bf32fb4396dd86ce631dec00717eab7656d/configs/nixos/hosts/nuc/kodi.nix), giving me native hardware acceleration and video output.
Simultaneously, `incus` runs in the background, hosting my containers.
I get my HTPC and my server on the same metal, without the virtualization tax or the "headless host" limitation.

## The Agentic Multiplier

I have written before about [my shift towards agentic coding](/post/agentic-coding/).
In a world where AI agents execute tasks, **CLI-first** and **declarative** systems are king.
An AI agent cannot reliably "click buttons" in a web interface to configure a VLAN tag or resize a disk.
It needs text.
It needs determinism.

By moving to NixOS, my entire infrastructure is defined in text files.
This means my AI agents can read, understand, and even safely modify my infrastructure.
Proxmox's opaque database and UI-driven workflow were a black box to my agents.
NixOS is an open book.
If I want my agent to "ensure the Home Assistant VM has 8GB of RAM", it doesn't need to navigate a menu.
It just changes one line in a `.nix` file and runs a command.
The agent can even verify the change was successful by checking the git diff or the active configuration.
This is the infrastructure counterpart to the "agentic coding" revolution I'm living in.

A friend recently complimented me on how nicely my configuration was structured, especially for managing 8 different machines.
The funny thing is, I haven't written almost a single line of my configuration myself.
I did all of it using agentic AI over many sessions.
I have restructured and refactored it quite a few times, going from a single machine to 2 machines, and eventually to 9.
The AI handles the heavy lifting of refactoring, ensuring that my [PC, NUC, and HP](https://github.com/basnijholt/dotfiles/blob/4f534bf32fb4396dd86ce631dec00717eab7656d/configs/nixos/flake.nix) all share common modules while keeping their unique personalities.
It feels like I have a team of junior developers maintaining my infrastructure.

## The Architecture: Incus & Simulation

I still wish there was a purely "Nix" way to manage persistent, stateful LXC containers and VMs.
There are projects like `nixos-containers` or `microvm.nix`, but they often lack the operational maturity or live-migration features of a robust hypervisor.
[Incus](https://linuxcontainers.org/incus/) (the community fork of LXD) fills this gap perfectly.
It gives me the "cattle" management of NixOS for the host, while allowing me to run "pet" legacy workloads (like my old Ubuntu containers or Home Assistant VM) in a stable, manageable environment.
Crucially, Incus is entirely controllable via a clean CLI, making it a perfect citizen in my agentic workflow.

One neat thing I did was create Incus VMs that replicate the exact same configuration as my physical machines.
Before I actually switched off my last Proxmox host, I was already confident that the full configuration worked because I had a virtual machine running the same setup.
I just have a small file with [overrides](https://github.com/basnijholt/dotfiles/blob/4f534bf32fb4396dd86ce631dec00717eab7656d/configs/nixos/hosts/hp/incus-overrides.nix).
Then I could validate that the virtual machine worked.
This removed the fear of "nuking and paving" my physical servers.

## The Migration

Migrating was surprisingly straightforward, thanks to `vzdump` and `qemu-img`.
Here is how I moved my 7+ years of digital history without losing data.

### 1. Migrating LXC Containers

For my LXC containers (running Docker, DNS, etc.), I essentially "teleported" them.
I dumped the running container on Proxmox to a standardized tarball, copied it over, and streamed it directly into a fresh Incus container.

On Proxmox:
```bash
# Dump container 101 to a compressed archive
vzdump 101 --dumpdir /var/lib/vz/dump --mode suspend --compress zstd
```

On NixOS (using my [`migrate-lxc.sh`](https://github.com/basnijholt/dotfiles/blob/4f534bf32fb4396dd86ce631dec00717eab7656d/configs/nixos/archive/migrate-lxc.sh) script):
```bash
# Stream the backup into a new Incus container
./migrate-lxc.sh vzdump-lxc-101-*.tar.zst ubuntu-container
```

This script creates a fresh container, mounts its root filesystem, and overwrites it with the Proxmox dump.
It handles the messy parts—like mapping UIDs and fixing `machine-id`—automatically.

### 2. Migrating Virtual Machines

For VMs (like Home Assistant OS), it was a matter of converting the disk format.
Proxmox uses LVM-thin or ZFS zvols; Incus is happy with QCOW2 or raw ZFS.

On Proxmox:
```bash
# Export the ZFS volume to a QCOW2 file
qemu-img convert -p -O qcow2 /dev/zvol/rpool/data/vm-100-disk-0 vm-100.qcow2
```

On NixOS (using [`migrate-vm.sh`](https://github.com/basnijholt/dotfiles/blob/4f534bf32fb4396dd86ce631dec00717eab7656d/configs/nixos/archive/migrate-vm.sh)):
```bash
# Import the disk and create the VM
./migrate-vm.sh vm-100.qcow2 home-assistant
```

## The Result

I now manage my entire fleet—Host OS, networking, storage, and hypervisor configuration—from a single git repository.
My "pets" live comfortably inside Incus, but their cage is defined declaratively.
I can wipe my host machine, reinstall NixOS, run a restore script, and be back online in minutes.
Best of all, I never have to remember which checkbox I clicked in a web UI three years ago.
It is all in the code.
And because it is code, my agents can help me manage it.