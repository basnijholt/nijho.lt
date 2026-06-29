---
title: "Migrating from TrueNAS to NixOS without losing data after the build-system rug pull"
subtitle: "How I used an AI agent with root-capable SSH, strict no-change instructions, disko, and a VM rehearsal to replace my last appliance OS without letting it near my ZFS data pools"
summary: "TrueNAS was the last appliance OS in my homelab. The build-system change was the last straw, but the itch had been building for a while: too much UI state, unclear defaults, and virtualization churn around Incus. This is the story of how I gave an AI agent root-capable SSH access with strict instructions not to change anything, used it to inspect the live machine, recreated the config declaratively, and built a VM rehearsal to prove disko would only wipe the boot disk."
date: 2026-06-28
draft: false
featured: false
authors:
  - admin
tags:
  - nixos
  - truenas
  - zfs
  - disko
  - homelab
  - agentic-coding
  - open-source
  - infrastructure
categories:
  - technology
  - DevOps
  - level:intermediate
---

TrueNAS was the last non-NixOS machine in my home lab.

I kept postponing it for a simpler reason: moving something with ~100 TiB of data feels scary.
My NAS holds the big ZFS pools.
It has the SMB shares, NFS exports, snapshots, replication tasks, encrypted datasets, Incus state, Docker workloads, and all the boring-but-important health checks that are easy to take for granted until something fails.

I had already migrated most of my machines from Proxmox to NixOS with Incus, as I wrote about in [I've gone full Nix: Proxmox to NixOS + Incus]({{< ref "/post/proxmox-to-nixos" >}}).
That migration made me increasingly intolerant of appliance-style infrastructure.
If the important state lives in a database behind a web UI, I cannot review it in a pull request.
If I change something while debugging, I cannot guarantee the change made it back into the source of truth.
And if I let an AI agent help me, imperative systems become even more uncomfortable: an agent can run a hundred commands, succeed, and leave behind a system that nobody can reproduce.
For the NAS specifically, that basically meant I did not dare touch the machine with an AI agent at all.

NixOS is different.
The diff is the state.
If an agent changes my infrastructure, I can review the patch.
If the change is wrong, I can reject it.
If it works, I can commit it.

TrueNAS was the last holdout.
It had been itching for a while.
Then the [build-system rug pull](https://forums.truenas.com/t/clearing-the-air-on-build-scripts/64357) made the decision easy.

{{< toc >}}

## The itch before the last straw

The build-system change was not the first thing that bothered me.
It was just the last straw.

The deeper problem was that my TrueNAS setup had slowly become complicated in exactly the way I dislike.
I had clicked many buttons in the UI over time:

- SMB shares
- NFS exports
- snapshot tasks
- replication tasks
- users and groups
- encrypted datasets
- apps and containers
- Incus storage
- old Jailmaker/systemd-nspawn state
- alerting
- UPS settings

TrueNAS can export and import its configuration.
That is genuinely useful.
But a database export is not the same thing as a configuration I can comfortably review.
When I look at a TrueNAS backup, it is not obvious to me which settings I intentionally changed, which settings are defaults, which settings are historical leftovers, and which settings only exist because I clicked something while debugging two years ago.

One concrete example was NFS.
I needed the `crossmnt` export option so child datasets would show up correctly inside the Docker container host, but TrueNAS did not expose that option in the UI.
So I had a periodic root cron job patching `/etc/exports` after TrueNAS generated it.
It worked, but it was exactly the kind of small appliance hack that made me uneasy: partly outside the UI, partly outside the exported configuration, and very easy to forget during a migration.
In NixOS, that behavior is just part of the export line.

That is the exact discomfort that pushed me away from Proxmox.
I do not want to remember what I clicked.
I want the system to remember it as code.

The second itch was virtualization.
My TrueNAS container story had already gone through one migration.
For a while I used [Jailmaker](https://github.com/Jip-Hop/jailmaker), which is a clever script around `systemd-nspawn` for running Linux "jails" on TrueNAS SCALE.
It worked well enough for what I needed at the time: a Debian environment where I could run Docker workloads close to the data.
But it also reinforced the feeling that I was building a fairly custom server on top of an appliance OS.

[TrueNAS 25.04 "Fangtooth"](https://www.truenas.com/docs/scale/25.04/) introduced experimental Containers, named Instances in the early 25.04 releases, and the [25.04.1 announcement](https://www.truenas.com/blog/truenas-fangtooth-25-04-1/) explicitly described Instances as being based on Incus, supporting both VMs and LXCs.
That was interesting to me because the older TrueNAS VM system was libvirt-based, while Incus felt like a more coherent container/VM story.
Then the [TrueNAS virtualization plan for 25.04.2](https://forums.truenas.com/t/truenas-virtualization-plans-for-25-04-2/46236) explained that Fangtooth's Instances feature caused challenges for some users and that 25.04.2 would re-enable the older Virtualization VM path alongside Instances.
The [25.04.2 release announcement](https://forums.truenas.com/t/truenas-25-04-2-is-now-available/49165) made that split official: Virtual Machines came back, while VMs created through the earlier Instances feature continued to appear under Containers.

For many people that churn was probably annoying.
For me it was especially ironic.
I had migrated from Jailmaker's `systemd-nspawn` setup to Incus, read up on [Incus](https://linuxcontainers.org/incus/), got excited about it, started using it, and then became genuinely happy with it when I migrated from Proxmox to NixOS with Incus.
Incus fit my mental model perfectly: a clean CLI, containers and VMs in one place, easy scripting, and a workflow that agents can inspect.

Then TrueNAS started moving away from that direction again.
Forum discussion around the 25.04.2 and later virtualization plans made it clear that Incus was not the stable long-term abstraction I hoped it would be inside TrueNAS.
In the long-running [Linux Jails with Incus thread](https://forums.truenas.com/t/linux-jails-containers-vms-with-incus/23599?page=21), Kris Moore is quoted saying that Incus is being removed from the base system and that libvirt will handle the backend for VMs and LXC.
That probably makes sense for TrueNAS.
They have enterprise users, compatibility concerns, and a support matrix that is very different from mine.

But for me it meant the NAS was again becoming an appliance whose internal direction I had to follow.
I had just escaped that with Proxmox.
I did not want to do it again for the most important machine in my house.

## The last straw

Then I saw Jeff Geerling mention TrueNAS's recent "shady behavior" in a video, and I started looking into what had actually changed.

The short version is that iXsystems made part of the TrueNAS ecosystem closed source.
Specifically, iXsystems moved the TrueNAS build scripts and related build infrastructure internal for the TrueNAS 27 line.
Their forum post, [Clearing the Air on Build Scripts](https://forums.truenas.com/t/clearing-the-air-on-build-scripts/64357), frames this as a practical build-system decision and says normal installation and updates remain unaffected.
The old [`truenas/scale-build`](https://github.com/truenas/scale-build) repository now says it is preserved historically and is no longer the maintained build system.
Community reactions, for example [this TrueNAS forum thread](https://forums.truenas.com/t/truenas-closing-its-build-system-has-sparked-a-significant-trust-crisis-in-the-self-hosted-and-engineering-communities/64549), understandably read this as a meaningful step away from fully open development.

Would I ever have built TrueNAS from source myself?
Almost certainly not.

That misses the point.
I also rarely compile my Linux kernel manually, yet I care deeply that the ecosystem is open enough that I *could* understand, rebuild, inspect, and fork the pieces if necessary.
For a storage appliance, trust matters more than convenience.
The NAS is not a toy VM.
It is the machine that owns my data.

That was the final push.
The UI state bothered me.
The virtualization churn bothered me.
The build-system change made the decision obvious.

## Why this was scarier than Proxmox

Migrating Proxmox to NixOS was scary in the normal infrastructure sense.
I had containers and VMs to move, but the blast radius was understandable.
I could export with `vzdump`, import into Incus, and test a lot of it in virtual machines.

Migrating TrueNAS is a different kind of scary.
The data is not a VM disk that I can casually copy around.
The important thing is *not* to recreate the data pools.
The important thing is to **not touch them**.

The target architecture is simple in principle:

```nix
# Conceptually:
# - disko owns only the boot disk
# - existing data pools are imported by name
boot.zfs.extraPools = [
  "ssd"
  "tank"
];
```

The NixOS boot disk can be destroyed and recreated.
The existing `tank` and `ssd` pools cannot.

This is the part where many migration guides become hand-wavy:

1. Install the new OS.
2. Import your ZFS pools.
3. Good luck.

That is not enough for me.
I could physically access the machine, but unplugging the relevant NVMe hardware would mean taking apart more of the box than I wanted to touch.
So I treated the cutover as if the disks had to stay connected.
And I absolutely did not want one typo in a disk path to become yet another meme in AI agent failures.

## Giving an agent the keys, carefully

Without AI this would probably have become a week-long project that I would forever postpone.
With AI, it felt plausible to get the first serious version done in a single sitting.
My approach was to give GPT 5.5 in xhigh mode SSH access to the live TrueNAS box and tell it, repeatedly and very explicitly, not to change anything.
To be clear, it had root access.
At this point these models have become powerful enough that I trust them to follow explicit instructions.
The safety boundary was instruction-following, narrow scope, and review.

Not "please be careful."
More like:

```text
You can inspect.
You cannot change anything.
Do not start or stop services.
Do not import or export pools.
Do not load keys.
Do not mount datasets.
Read only.
```

This is the part where people either nod along or think I have completely lost my mind.
I think the distinction matters.
I did not ask an agent to "migrate my NAS."
I asked it to inspect the current system, summarize the live state, compare that against my NixOS repository, and propose declarative config.

Then I reviewed the diffs.
Then I asked for another review.
Then another.
The process was messier than one neat two-agent pass: build a scaffold, ask a model to attack it, compare that against the live TrueNAS state, refine the scaffold, and repeat.
GPT 5.5 did most of the initial construction.
Claude Opus 4.8 on max effort did one of the later independent cross-checks against the live system.
By the end, I trusted the result because multiple independent reviews had converged on the same assumptions, and I understood the remaining differences.
The loop felt like code review: inspect live state, turn the desired parts into Nix, review the diff, and ask another model to attack it.
The scariest assumption got a VM test, and the destructive step stayed small.

Byte-for-byte TrueNAS cloning was never the target.
I wanted every important behavior explicit: storage import, shares, snapshots, replication, Incus recovery, monitoring, and the few places where NixOS intentionally differs from the old appliance.
At that point, the NixOS config reproduced the parts of TrueNAS I actually depended on, and the remaining differences were deliberate.

The agent was excellent at inventory:

- Which pools exist
- Which datasets are encrypted
- Which NFS exports are live
- Which SMB shares exist
- Which users and numeric IDs matter
- What Incus storage pool is in use
- What replication tasks exist
- What SMART/NUT/health monitoring exists
- What host ID ZFS expects
- Which disk is the current boot pool

Preserving everything blindly would have been wrong.
The useful parts became code, and the dangerous parts became explicit.

## The NixOS scaffold

The resulting NixOS host is split into small files:

```text
hosts/nas/
├── default.nix
├── disko.nix
├── hardware-configuration.nix
├── health.nix
├── identity.nix
├── networking.nix
├── nfs.nix
├── replication.nix
├── samba.nix
├── storage.nix
├── virtualization.nix
├── CUTOVER.md
└── PLANNING.md
```

This is exactly why I like NixOS.
The migration stopped being a list of steps I needed to follow and became a [pull request](https://github.com/basnijholt/dotfiles/pull/61/).

The important storage boundary is:

- `disko.nix` describes only the boot disk.
- The data pools are imported by name.
- ZFS force-import is disabled.
- Boot-time encrypted credential prompts are disabled.
- Encrypted datasets are unlocked manually after boot.
- Sanoid/Syncoid replace TrueNAS snapshot and replication tasks.
- SMB, NFS, Docker, Incus, SMART, ZED, NUT, Netdata, and exporters are all declared in code.

The data pools are intentionally *not* in disko.
That is the entire point.

{{% callout note %}}
The host is called `nas` because that is the role I want to keep.
TrueNAS was the old implementation.
NixOS becomes the new one, while preserving the services and data I actually need.
{{% /callout %}}

## The disko problem

[`disko`](https://github.com/nix-community/disko) is a fantastic tool.
It lets you describe disks declaratively and then formats/partitions/mounts them.
For a fresh NixOS install, it is exactly what I want.

This also fits how I install NixOS machines.
I build a custom [installer ISO](https://github.com/basnijholt/dotfiles/blob/main/configs/nixos/installers/iso.nix), put it on a USB stick, and boot from it.
The image already has SSH enabled with my keys, flakes enabled, and the tooling needed to run the repo-defined `disko` and `nixos-install` flow.
That turns the installer environment into part of the reviewed configuration, instead of another place where I have to remember which choices to make.

It is also exactly the tool that can ruin your day if pointed at the wrong disk.

My requirement was:

> Use disko to destroy and recreate the boot disk, but prove it cannot touch the existing ZFS data pools.

The static config already looked right.
The generated disko script only referenced the boot device and generated partition labels.
The data pools were only present under `boot.zfs.extraPools`.

But "looks right" is not enough when the downside is wiping a NAS.

So we built a VM rehearsal.

## Rehearsing the dangerous part in a VM

The VM test creates a miniature version of the dangerous situation:

1. Attach several throwaway disks to a disposable NixOS VM.
2. Create a fake `boot-pool` on one disk.
3. Create fake `tank` and `ssd` ZFS pools on other disks.
4. Write sentinel files into the fake data pools.
5. Export the fake data pools.
6. Run the generated `nas` disko script against the fake boot disk.
7. Confirm the boot disk now contains the new `zroot`.
8. Confirm fake `tank` and `ssd` still have their ZFS labels.
9. Re-import fake `tank` and `ssd`.
10. Read the sentinel files.

The check lives in the flake now:

```bash
cd configs/nixos
nix build .#checks.x86_64-linux.nas-disko-safety
```

It passed.

Passing that VM test gives me confidence in the generated Nix/disko logic.
The read-only check on the live TrueNAS box gives me confidence in the configured disk target: the by-id path resolves to the 500 GB `boot-pool` disk, and `tank` and `ssd` live on different devices.
The installer preflight repeats that same check immediately before the destructive step.

This is the level of paranoia I want around storage migrations.

## The parts that are not just storage

Once the "do not wipe the pools" boundary was in place, the rest of the migration became more normal infrastructure work.
Still annoying, but normal.

SMB was not a byte-for-byte port.
TrueNAS ships private Samba VFS modules and has its own ACL/middleware behavior.
Stock NixOS Samba covers the parts I need with `fruit`, `streams_xattr`, and sensible share definitions, but it is not literally the same stack.
So the plan calls out what must be tested from real clients: Time Machine, guest access, and photo/media access.

Snapshots and replication also changed.
TrueNAS snapshot tasks become Sanoid policy.
TrueNAS replication tasks become Syncoid systemd timers.
Existing snapshots are preserved, but Sanoid will not magically prune old TrueNAS-named snapshots.
That is a feature, not a bug.
I would rather manually decide when old snapshots age out than have a new tool silently "clean up" history.

Incus is another subtle one.
The storage pool lives on a data pool, so disko will not touch it.
But a fresh NixOS install has a fresh Incus database.
The plan is to run `incus admin recover`, then apply a small declarative reconciler for the known instances.
The state boundary has to be clear: preserve the storage dataset, recover the Incus database, then reconcile the instance config.

Health monitoring is also declared:

- SMARTD
- ZFS Event Daemon
- NUT/UPS client
- Netdata bound locally
- Prometheus exporters
- A shared alert hook that can log, wall, and optionally send ntfy alerts

TrueNAS gives you many of these things in the UI.
NixOS gives them to me as code.

I know using your NAS for other services is a bit of an anti-pattern.
In an ideal world, the storage box just stores data and stays boring.
But when I originally bought and configured this machine, it became the most powerful machine in my home lab.
So it naturally started attracting the Docker workloads too.
Most of those workloads are not resource intensive, and keeping them close to the data is genuinely convenient.
At one point I was running more than a hundred containers on that machine and it barely made a dent.
They ran inside LXC containers on Incus rather than directly on the TrueNAS host, which made it feel like a reasonable compromise for a long time.

The migration also became a chance to fix a real operational problem.
My worst TrueNAS incident was a long OOM death spiral: no swap, too many unbounded containers, and services repeatedly getting killed and restarted.
The philosophy came from Nix and open infrastructure.
The OOM incident was the practical reminder that the NAS had become a general-purpose compute host.
In the NixOS version, container memory limits, zram, earlyoom, and an explicit ZFS ARC cap are part of the configuration instead of being tribal knowledge or post-incident notes.

## Secrets stay out of the repo

My dotfiles are public.
That makes the migration more interesting.

The Nix config necessarily contains some operational facts: hostnames, share names, service definitions, and so on.
But the plan deliberately keeps secrets and sensitive cutover material out of git.

For this migration, that means:

- ZFS dataset passphrases and unlock material stay off-box and outside the repo.
- Replication private keys are installed manually under `/etc/ssh`.
- Inbound authorized keys for backup senders are installed during cutover.
- Alerting secrets live in a runtime env file.
- A local `~/nas-cutover/` staging directory can exist, but it is explicitly not part of the repo and should not be casually read by agents.

One important detail: the encrypted datasets use passphrase keys.
In the TrueNAS setup I handled that with [truenas-unlock](https://github.com/basnijholt/truenas-unlock), a small tool I wrote for this exact problem.
The unlock material lives on another device; when that device is on the same network, it can unlock the datasets through the TrueNAS API.
That gave me a lightweight hardware/network-presence factor: the NAS could boot, and the encrypted datasets only unlocked when the separate unlock device was present too.

That changes the migration footgun.
The TrueNAS API path does not survive the cutover as-is, so I split the same idea out into [zfs-unlock](https://github.com/basnijholt/zfs-unlock): the NixOS/OpenZFS version that talks to a restricted SSH receiver instead.
During the migration I still kept an independent manual passphrase recovery path, because I do not want the automatic unlock mechanism to be the only way back into my data.

## Where this leaves TrueNAS

I still like TrueNAS.
It got me very far.
It made ZFS approachable.
It gave me a good NAS UI when I wanted a NAS UI.
And if you want an appliance that mostly owns storage for you, it is still a very compelling project.

I like NixOS more for my own infrastructure.
The most important machine in my house should live in reviewable code instead of mutable appliance state spread across a UI, a database, and old debugging decisions.
NixOS and AI are a particularly good match for that.
I can describe messy infrastructure intent in imprecise English, let the agent turn that into exact Nix code, and review the diff before it becomes system state.
The prompt stays fuzzy.
The machine state does not.

After the Proxmox migration, TrueNAS was the last major exception.
This migration removes that exception.

## The cutover

I ended up using a phased [`nixos-anywhere`](https://github.com/nix-community/nixos-anywhere) cutover instead of the USB installer path.
The important safety property stayed the same: first kexec into a temporary NixOS installer, stop there, run the disk preflight from inside that installer, and only then run the destructive `disko,install,reboot` phase.
Before the destructive phase, the box was running the installer in RAM and the disks had not been intentionally modified yet.
That gave me a real checkpoint where aborting was still cheap.

I kept my hands on the few commands that actually changed the machine.
I ran the `nixos-anywhere` phases and the later `nixos-rebuild` commands myself.
The agent stayed next to it, reading the outputs, checking the assumptions, SSHing in to verify pool health, services, mounts, Incus state, NFS clients, and then turning any findings back into code or documentation.
That split felt right to me: I pressed enter on the small number of irreversible commands, and the AI did the tedious verification work that I would otherwise be tempted to rush.

The actual migration was almost anticlimactic compared to the preparation.
From the moment TrueNAS stopped being the running OS to having the Incus containers back with my hundred-plus services running again took less than 20 minutes.
The slow work was not the cutover.
The slow work was making the cutover boring.

<details>
<summary>The small things that still needed fixing during cutover</summary>

<p>There were a few small first-boot reconciliations. I am writing them down mostly for future readers who want to follow a similar path:</p>

<ul>
  <li>imported data-pool mountpoints needed to be reconciled to the <code>/mnt/...</code> paths my clients and services already used;</li>
  <li>encrypted datasets needed a better manual post-boot unlock helper, and the old TrueNAS API unlock flow needed a NixOS/OpenZFS successor;</li>
  <li>Incus needed <code>incus admin recover</code> because the storage pool survived but the new OS had a fresh Incus database;</li>
  <li>one unprivileged recovered container needed the matching subordinate UID/GID ranges declared for its passthrough idmap;</li>
  <li><code>nas.local</code> needed an explicit DNS record so my wildcard did not send it to a workload container;</li>
  <li>the old PC job that backed up the TrueNAS API config needed to be removed;</li>
  <li>the PC NFS mounts, Nix cache endpoints, and recovered Docker workload container all needed client-side validation.</li>
</ul>

<p>Those findings went back into the cutover runbooks and the Nix config, so the notes are available for anyone who might benefit from them later.</p>

</details>

At the end of the cutover, the machine was `nas`, the ZFS pools were healthy, the NFS mounts worked from my PC, the Incus containers were recovered, and the Docker workloads were running again.
SMB authentication, guest access, and Time Machine worked after one final share-root permission fix.
Normal authenticated media access still deserves the usual client check, but the scary storage part is done.

## References

- [I've gone full Nix: Proxmox to NixOS + Incus]({{< ref "/post/proxmox-to-nixos" >}})
- [My homelab: from a single Raspberry Pi to a Proxmox cluster and a dedicated NAS]({{< ref "/post/homelab" >}})
- [On agentic coding]({{< ref "/post/agentic-coding" >}})
- [TrueNAS forum: Clearing the Air on Build Scripts](https://forums.truenas.com/t/clearing-the-air-on-build-scripts/64357)
- [`truenas/scale-build` on GitHub](https://github.com/truenas/scale-build)
- [TrueNAS forum: build-system trust crisis discussion](https://forums.truenas.com/t/truenas-closing-its-build-system-has-sparked-a-significant-trust-crisis-in-the-self-hosted-and-engineering-communities/64549)
- [TrueNAS 25.04 documentation](https://www.truenas.com/docs/scale/25.04/)
- [TrueNAS 25.04.1: Fangtooth Unification Gains Momentum](https://www.truenas.com/blog/truenas-fangtooth-25-04-1/)
- [TrueNAS Virtualization Plans for 25.04.2](https://forums.truenas.com/t/truenas-virtualization-plans-for-25-04-2/46236)
- [TrueNAS 25.04.2 release announcement](https://forums.truenas.com/t/truenas-25-04-2-is-now-available/49165)
- [Linux Jails with Incus forum thread](https://forums.truenas.com/t/linux-jails-containers-vms-with-incus/23599?page=21)
- [Jailmaker](https://github.com/Jip-Hop/jailmaker)
- [truenas-unlock](https://github.com/basnijholt/truenas-unlock)
- [zfs-unlock](https://github.com/basnijholt/zfs-unlock)
- [The NAS NixOS scaffold PR](https://github.com/basnijholt/dotfiles/pull/61)
