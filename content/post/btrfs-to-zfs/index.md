---
title: "The last btrfs machine: migrating my PC to ZFS"
subtitle: "Why uniformity in my backup situation was worth wiping my daily driver, and how I made the restore boring before touching the disk"
summary: "After replacing Proxmox and TrueNAS with NixOS, my GPU machine was the last one still on btrfs, picked years ago because forum threads had me convinced that ZFS and NixOS were a bad combination. What finally pushed me to fix it: I run AI agents in YOLO mode all day, the stories about frontier models wiping home directories kept coming, and my restic backups needed an hour and a half just to scan a hundred million files. The audit's first finding: the backups had been silently dead for four months. This is the story of auditing my backups, verifying the restore path end-to-end, and wiping my daily driver so that nine machines share the exact same ZFS setup."
date: 2026-07-23
draft: true
featured: false
authors:
  - admin
tags:
  - nixos
  - zfs
  - btrfs
  - disko
  - restic
  - backups
  - homelab
  - infrastructure
  - agentic-coding
categories:
  - technology
  - DevOps
  - level:intermediate
---

My GPU machine was the last machine in my fleet still running btrfs.
I [bought it for gaming]({{< ref "/post/local-ai-journey" >}}) (which never happened), and these days its dual RTX 3090s almost exclusively run [local AI models]({{< ref "/post/llama-nixos" >}}).

btrfs itself never failed me.
When I set up NixOS on this machine for the first time, I had read enough forum threads to become convinced that ZFS and NixOS were a troublesome combination, so I picked btrfs to be safe.
That belief was simply wrong.
As I [went full Nix]({{< ref "/post/proxmox-to-nixos" >}}) and eventually [moved even my TrueNAS to NixOS]({{< ref "/post/truenas-to-nixos" >}}), I learned there was no issue at all.
I just had to figure out the right incantation to make ZFS work with boot drives, [disko](https://github.com/nix-community/disko), and [nixos-anywhere](https://github.com/nix-community/nixos-anywhere).
My HP got ZFS first, that config grew into a shared disko module, and soon the whole fleet ran one pattern: NixOS on ZFS, snapshots and replication declared in code, and backups I can reason about.

Only the machine I sit at every day kept running on my old misconception, because a daily driver is exactly the one you do not casually reinstall.

{{< toc >}}

## Why touch a working machine

The operating system was already uniform.
The filesystem was not, and that turned out to matter more than I expected.

The real trigger was that I got increasingly paranoid about an AI agent messing up my system.
I run agentic AI in YOLO mode, exclusively.
All day, every day, agents execute commands on this machine without asking me first.
YOLO does not mean root, though: the agents run as my regular user, and the backup credentials live where only root can read them.
An agent that could destroy the backup itself would make everything else in this post pointless.
Meanwhile the stories keep coming in about even the most frontier models wiping someone's home directory:

> GPT-5.6-Sol just accidentally deleted almost ALL of my Mac's files. And this is why I trust Fable 1000x more.
>
> — [@mattshumer_](https://x.com/mattshumer_/status/2075657271401390161)

The reaction is always about which model deserves more trust.
I read these tweets differently.
Give any agent enough sessions and it will eventually delete something important, the same way I do every few years with a tired `rm -rf`.
Whether that moment becomes a catastrophe or an inconvenience depends entirely on the restore path.

So I felt I needed to properly audit the way my backups were done.
I want to be able to answer four questions about any machine I own:

1. What exactly is in the backup?
2. What is *not* in the backup, and did I choose that deliberately?
3. How big is a restore?
4. How long will it take?

## The backup that wasn't

Asking {{< tooltip text="What exactly is in the backup?" >}}question 1{{< /tooltip >}} delivered an unpleasant answer within the hour: the backups had quietly stopped four months earlier.
Two boring causes had stacked up: an interrupted prune left a stale repository lock, which the job could never clear because its own unlock step only ran *after* a successful backup, and the repository URL still pointed at `truenas.local`, a name that had stopped resolving [along the way]({{< ref "/post/truenas-to-nixos" >}}).
The last successful backup ran at 07:00 on March 22; the next one at 07:16 on July 22, after [the fix](https://github.com/basnijholt/dotfiles/commit/4d2a75efcb503b9ca2aabcbe8339be3e5a62d0ce).
Four months, almost to the minute.
systemd logged the failure on every single run, nobody read it, and nothing escalated.
I found out because I asked the question, not because anything told me.

## What the audit found

On the btrfs box, {{< tooltip text="How big is a restore?" >}}question 3{{< /tooltip >}} alone had three different answers depending on which tool I asked.
`du` counted reflinked copies at full size, so directories reported terabytes that physically did not exist.
`df` counted physical extents, which is honest about disk usage but tells you nothing about what a file-based restore will write.
And restic reported the *apparent* size of sparse VM images, which inflated the restore estimate to several times the disk.

When your storage layer gives you three sizes for the same data, you do not really understand your backup.
You have a backup, and you have hope.

{{< tooltip text="How long will it take?" >}}Question 4{{< /tooltip >}} was no better.
Because the PC was my only btrfs machine, it could not join [the ZFS snapshot replication the rest of the fleet uses](https://github.com/basnijholt/dotfiles/blob/0d6101c8e3f91a0845cb41adb3cda216f50917c8/configs/nixos/hosts/nas/replication.nix), so its backups relied entirely on restic pushing to the NAS.
Off-machine, note, but not off-site; {{< tooltip text="What is not in the backup, and did I choose that deliberately?" >}}question 2{{< /tooltip >}} turned out to apply to locations too, and closing that gap is its own project.
restic is file-based: every run visits the metadata of every single file to find what changed.
On this machine that meant close to a hundred million files per scan, which turned out to include some 600 GB of git worktrees stuffed with virtual environments and `node_modules`.
Each run took about an hour and a half, even when almost nothing had changed.

That scan time dictated my backup cadence.
The timer ran hourly, which in practice meant back-to-back scanning all day to move a couple hundred megabytes of real changes, and I recently [dropped it to every six hours](https://github.com/basnijholt/dotfiles/commit/4f2401de725d5201d4daca0e67505ad2e6f6691a) to stop the madness.
Either way, my most recent work existed only on the machine an agent was busy poking at.

The scanning is also not free for the hardware.
Reads are gentle on an SSD compared to writes, but hourly scans of an hour and a half each kept the drive at full duty cycle and elevated temperature for most of every day.
And drives stopped being cheap: I paid $227 for [a 4 TB NVMe drive]({{< ref "/post/homelab" >}}) in 2024, and the same drive lists for around $800 today.
I would rather not run the experiment of what years of continuous scanning do to a drive I can no longer afford to replace.

btrfs has perfectly good snapshots of its own, but sending them off-site was never an option for me: snapshot replication needs the same filesystem on the receiving end, and my NAS speaks ZFS.
With ZFS I can snapshot every few minutes and `zfs send` the actual block storage: an incremental send streams exactly the blocks that changed since the last snapshot, without walking a single file.
A hundred million files cost nothing when nobody has to visit them.

ZFS does not magically collapse those numbers into one.
But it gives me the same semantics everywhere, including on the NAS pools that hold the backups themselves.
Eight of my machines already share a single ZFS disk layout, defined in [one shared disko module](https://github.com/basnijholt/dotfiles/blob/0d6101c8e3f91a0845cb41adb3cda216f50917c8/configs/nixos/common/disko-zfs.nix).
The PC was the odd one out.
This migration makes it nine machines with the exact same strategy, and one backup story to audit instead of one per machine.

## The plan: one shared disko module

The Nix side was the easy part.
The PC now imports the same shared disko module as the other eight machines, with one addition: a `swapSize` parameter, because ZFS has no reliable swapfile story and the PC actually needs its 96 GB of swap.

The disk is [pinned by ID](https://github.com/basnijholt/dotfiles/blob/8c0bc5faded40362ac01347682aaf2089562047d/configs/nixos/hosts/pc/disko.nix), not by device name:

```nix
device = "/dev/disk/by-id/nvme-Samsung_SSD_990_EVO_Plus_4TB_...";
```

This matters more than usual here.
The PC dual-boots Windows from a second NVMe drive, and I want zero ambiguity about which of the two disks disko is allowed to erase.

The scary property of this migration is different from the NAS one.
For the NAS, the whole point was that disko must *not* touch the data pools.
For the PC, the new ZFS pool goes on the **same disk the data currently lives on**.
No second disk, no local rollback, no btrfs to boot back into.
From the moment disko runs, the restic repository on the NAS is the only road back.

That sentence is the reason most of this post is about verification.

The road back also has to survive the same agents that motivated all of this.
The PC pushes its backups over sftp as a user that owns every file in the repository, which means a compromised PC could delete or encrypt its own safety net.
So the NAS [snapshots the repository dataset on its own side](https://github.com/basnijholt/dotfiles/blob/0d6101c8e3f91a0845cb41adb3cda216f50917c8/configs/nixos/hosts/nas/storage.nix#L128-L143), where the PC's credentials cannot reach: two days of hourly ZFS snapshots and two weeks of dailies that only root on the NAS can destroy.

## Rehearsing in a VM, again

The [NAS migration]({{< ref "/post/truenas-to-nixos" >}}) taught me to rehearse the destructive step in a VM, so the flake grew a [`pc-vmtest` target](https://github.com/basnijholt/dotfiles/blob/8c0bc5faded40362ac01347682aaf2089562047d/configs/nixos/flake.nix#L110) and I ran the whole install through `nixos-anywhere --vm-test`.
Disko formatted a virtual disk, created the pool, installed the system, and booted it with swap active.

Passing that test proves the generated logic.
It does not prove the backup, which is where the real risk lives.

## The recovery kit

A restore that starts with "first, log in to the dead machine and fetch the credentials" is not a restore plan.
So everything a bare reinstall needs lives in a small recovery kit on two other machines in the house, permissions locked down: the restic password and SSH key that reach the repository, the staged restore script, a couple of verification scripts, and the PC's SSH host keys.
The host keys matter more than they look: the reinstalled machine comes back with its old identity, so no client complains and nothing in the fleet needs to be taught to trust a new machine.
A munge key and a README round it out.

## Trusting the backup enough to wipe the disk

My recovery story has two layers.
NixOS makes the *system* disposable: every service, driver fix, and firewall rule is in git, so no agent can leave the machine in a state I cannot rebuild.
Verified backups make the *data* recoverable.
This migration is the voluntary version of the tweets above: I am about to delete all of my PC's files on purpose.

I did three verifications, each one converting an assumption into a fact.
An AI agent did the tedious sweeps; I reviewed the evidence.

The first check was completeness.
We walked everything on the machine *outside* the backup paths, until every byte was accounted for.
It was all re-downloadable caches, and the largest unexplained thing turned out to be restic's own local cache.
Everything outside the backup set is now *known* disposable instead of *assumed* disposable.

The second check was the restore path.
A backup you have never restored from is a hypothesis.
On a different machine, using only the recovery kit and no access to the PC at all, we restored a sample from the latest snapshot and compared hashes against the live system.
The hashes matched byte for byte, and even the symlinks came back pointing at the right targets.
A sample proves the path works, from credentials to symlink handling; reading back every byte is the third check's job.
The machine running the rehearsal had the kit and nothing else, so recovery provably does not depend on the machine being recovered.

The third check is the data itself.
`restic check` validates the repository structure without reading back the actual data blobs.
Before the wipe, a `--read-data` pass ran on the NAS, where the repository sits on local disk instead of behind the network.
When the backup is the only rollback, I want its bits read back at least once.

## The fifth question

The outage taught me a {{< tooltip text="How do I find out when any of this stops working?" >}}fifth question{{< /tooltip >}}: how do I find out when any of this stops working?
All three checks above are point-in-time, and verification rots.
So the NAS now [re-verifies every hour](https://github.com/basnijholt/dotfiles/blob/0d6101c8e3f91a0845cb41adb3cda216f50917c8/configs/nixos/hosts/nas/replication.nix#L263-L285), from its own side of the sftp connection, that the newest snapshot in the repository is less than a day old, and pushes an alert to my phone when it is not.
That catches every failure mode on the PC side, including "the timer is simply disabled."
The watcher itself is watched: the NAS pings an [external dead-man's switch](https://github.com/basnijholt/dotfiles/blob/0d6101c8e3f91a0845cb41adb3cda216f50917c8/configs/nixos/hosts/nas/health.nix#L252-L280) every five minutes, so if the machine holding my only road back goes dark, the alert comes from outside the house.

While wiring this up we discovered that months of earlier NAS alerts had never arrived, because [ntfy silently rejects message bodies over 4 KB](https://github.com/basnijholt/dotfiles/blob/0d6101c8e3f91a0845cb41adb3cda216f50917c8/configs/nixos/hosts/nas/health.nix#L60-L67).
A notification you have never received is also a hypothesis.

## Restoring in stages

The measured restore set came out to roughly 1 TB, and 99.9% of it is `/home`.
But two directories are 64% of that terabyte: Steam (430 GB of re-downloadable games) and my local-AI model collection (217 GB of GGUF files).

I do not need either of those to have a working machine.
So the restore script now runs in stages:

```bash
sudo ./restore_from_backup.sh stage1   # everything else → a fully working machine
sudo ./restore_from_backup.sh stage2   # Steam + models, whenever
```

Stage 1 restores everything except the deferred paths, plus the system identity (host keys).
Stage 2 can run days later, from the rebooted system, while I am already using the machine.

One detail I care about: stage 1 resolves `latest` to a concrete snapshot ID and pins it to a file.
Stage 2 reads the pin.
My backups run every six hours, so without this, a timer firing between the stages would silently split the restore across two different snapshots.

The backup itself is untouched: Steam and the models are still in every snapshot.
Only the restore order changed.

## Slimming down first

The PC had also quietly become an Incus host for three LXC containers, including the [MindRoom bots]({{< ref "/post/mindroom" >}}) my family talks to every day.
Before the migration, those containers moved to the NAS.
That shrinks both the backup and the restore, and the family bots keep running while their old host is being wiped.

{{% callout note %}}
Moving the containers produced its own lesson in btrfs size confusion.
One container that measured "about 250 GB" shipped over 590 GB across the network overnight, because a directory that every disk-usage probe had failed to measure turned out to hold 2.5 TB of reflink-inflated build dependencies.
The rule I took away: a directory that has *never been successfully measured* is a red alert, not a rounding error.
That kind of confusion is part of why this migration exists.
{{% /callout %}}

## The cutover

The install followed the same phased `nixos-anywhere` pattern as the NAS cutover, driven from another machine on the LAN: kexec into an installer running in RAM, stop, re-verify the target disk from inside the installer, and only then run the destructive disko/install phase.
That checkpoint is the whole point: right up to the destructive phase, aborting was still cheap.
The destructive part turned out to be the trivial part: from wiping the disk to booting the new system took less than twenty minutes.

The one surprise of the day was in the restore, and it was exactly the kind rehearsal is supposed to catch.
Stage 1 would not start: the restore script runs restic as root, and a freshly installed root has no SSH identity and no known_hosts.
The key it needed sat in the recovery kit inside my home directory.
The rehearsal never hit this, because the rehearsal machine's root had already talked to the NAS.
A verified restore path can still depend on state you forgot you had.

Stage 1 restored 534 GiB across 4.5 million files in just over an hour and a half, at wire speed.
The machine rebooted with its old host keys and its old `/home`, and stage 2 started immediately.
The plan said stage 2 could wait for days; it started the minute the machine was back, because once the machine works there is no reason left to wait.
The deferred 648 GiB of games and models took six more hours in the background.

With that, the PC finally joins the fleet pattern it was locked out of: sanoid snapshots the pool every hour, so a tired `rm -rf`, mine or an agent's, now costs at most an hour of work and a rollback, and a daily syncoid run sends the changed blocks to the NAS.
restic is on borrowed time.
Its six-hour timer keeps running until I trust the new path, and then it stops: the repository stays on the NAS as the last file-level snapshots of the machine, but nothing will be added to it.

Aftercare was the same short list, written down instead of remembered: revert the temporary root-SSH commit the installer needed, and put the restic password back where the backup service expects it.

The slow work, as always, was not the cutover.
The slow work was making the cutover boring.

## References

- [I've gone full Nix: Proxmox to NixOS + Incus]({{< ref "/post/proxmox-to-nixos" >}})
- [Migrating from TrueNAS to NixOS]({{< ref "/post/truenas-to-nixos" >}})
- [My homelab]({{< ref "/post/homelab" >}})
- [The btrfs→ZFS migration PR](https://github.com/basnijholt/dotfiles/pull/16)
- [The PR that closed the silent backup-monitoring failure modes](https://github.com/basnijholt/dotfiles/pull/67)
- [disko](https://github.com/nix-community/disko)
- [nixos-anywhere](https://github.com/nix-community/nixos-anywhere)
- [restic](https://restic.net/)
- [Sanoid](https://github.com/jimsalterjrs/sanoid)
