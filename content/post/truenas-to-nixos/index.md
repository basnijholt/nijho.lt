---
title: "Migrating from TrueNAS to NixOS without losing data after the build-system rug pull"
subtitle: "How I used an AI agent with root-capable SSH, strict no-change instructions, disko, and a VM rehearsal to replace my last appliance OS without letting it near my ZFS data pools"
summary: "TrueNAS was the last appliance OS in my homelab. The build-system change was the last straw, but the itch had been building for a while: too much UI state, unclear defaults, and virtualization churn around Incus. This is the story of how I gave an AI agent root-capable SSH access with strict instructions not to change anything, used it to inspect the live machine, recreated the config declaratively, and built a VM rehearsal to prove disko would only wipe the boot disk."
date: 2026-06-28
draft: true
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

Not because I loved having one appliance OS left, but because migrating something with ~100 TiB of data feels scary.
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

Then I saw Jeff Geerling mention TrueNAS's recent shady behavior in a video, and I started looking into what had actually changed.

The short version is that iXsystems made part of the TrueNAS ecosystem closed source.
Specifically, iXsystems moved the TrueNAS build scripts and related build infrastructure internal for the TrueNAS 27 line.
Their forum post, [Clearing the Air on Build Scripts](https://forums.truenas.com/t/clearing-the-air-on-build-scripts/64357), frames this as a practical build-system decision and says normal installation and updates remain unaffected.
The old [`truenas/scale-build`](https://github.com/truenas/scale-build) repository now says it is preserved historically and is no longer the maintained build system.
Community reactions, for example [this TechEnclave thread](https://techenclave.com/t/truenas-has-gone-closed-source/420208), understandably read this as a meaningful step away from fully open development.

Would I ever have built TrueNAS from source myself?
Almost certainly not.

But that is not the point.
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

At this point I did the most 2026 version of infrastructure work imaginable: I gave ChatGPT 5.5 in xhigh mode SSH access to the live TrueNAS box and told it, repeatedly and very explicitly, not to change anything.
To be clear, this was not technically sandboxed read-only access.
It had root power.
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
This was not one neat two-agent pass.
It was many independent rounds of review: build a scaffold, ask a model to attack it, compare that against the live TrueNAS state, refine the scaffold, and repeat.
ChatGPT 5.5 did most of the initial construction.
Claude Opus 4.8 on max effort did one of the later independent cross-checks against the live system.
By the end, the point was not that I had manually rederived every TrueNAS setting myself.
The point was that multiple independent reviews had converged on the same assumptions and the remaining differences were things I understood.

The goal was not to clone TrueNAS byte for byte.
The goal was to make every important behavior explicit: storage import, shares, snapshots, replication, Incus recovery, monitoring, and the few places where NixOS intentionally differs from the old appliance.
By the end, the NixOS config reproduced the parts of TrueNAS I actually depended on, and the remaining differences were deliberate.

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

But the job was not to blindly preserve everything.
The job was to convert the useful parts into code and make the dangerous parts explicit.

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
The migration stopped being a pile of screenshots and became a pull request.

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
This is also why the host is called `nas`, not `truenas`.
The goal is not to recreate TrueNAS on NixOS.
The goal is to make the NAS a NixOS machine that preserves the services and data I actually need.
{{% /callout %}}

## The disko problem

[`disko`](https://github.com/nix-community/disko) is a fantastic tool.
It lets you describe disks declaratively and then formats/partitions/mounts them.
For a fresh NixOS install, it is exactly what I want.

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

That does not prove the real cutover is risk-free.
Nothing can prove that from my desk, because the remaining risk is physical identity:

> Does the by-id path in the Nix config resolve to the current boot-pool disk on the real machine?

The VM test proves the generated Nix/disko logic only formats the configured boot target.
It does not prove that the real boot target is what I think it is.

That is why the cutover runbook also contains a remote-only installer preflight:

- Evaluate the disko target from the flake.
- Resolve it with `readlink -f`.
- Print `lsblk`.
- List importable ZFS pools.
- Run `zdb -l` on the target and its partitions.
- Abort if `tank` or `ssd` labels appear on the target.
- Abort if the target is data-disk-sized.
- Run `wipefs --no-act` before doing anything destructive.

This is the level of paranoia I want around storage migrations.

## The parts that are not just storage

Once the "do not wipe the pools" boundary was in place, the rest of the migration became more normal infrastructure work.
Still annoying, but normal.

SMB was not a byte-for-byte port.
TrueNAS ships private Samba VFS modules and has its own ACL/middleware behavior.
Stock NixOS Samba can get close with `fruit`, `streams_xattr`, `shadow_copy2`, and sensible share definitions, but it is not literally the same stack.
So the plan calls out what must be tested from real clients: Time Machine, guest access, photo/media access, and previous versions.

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
Again, the point is not to pretend there is no state.
The point is to make the state boundary explicit.

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
They were not running directly on the TrueNAS host, but virtualized in containers, which made it feel like a reasonable compromise for a long time.

The migration also became a chance to fix a real operational problem.
My worst TrueNAS incident was a long OOM death spiral: no swap, too many unbounded containers, and services repeatedly getting killed and restarted.
This was not the philosophical reason I decided to leave TrueNAS, but it was a very practical reminder that the NAS had become a general-purpose compute host.
In the NixOS version, container memory limits, zram, earlyoom, and an explicit ZFS ARC cap are part of the configuration instead of being tribal knowledge or post-incident notes.

## Secrets stay out of the repo

My dotfiles are public.
That makes the migration more interesting.

The Nix config necessarily contains some operational facts: hostnames, share names, service definitions, and so on.
But the plan deliberately keeps secrets and sensitive cutover material out of git.

For this migration, that means:

- ZFS dataset passphrases are recorded/backed up off-box before shutdown and stored outside the repo.
- Replication private keys are installed manually under `/etc/ssh`.
- Inbound authorized keys for backup senders are installed during cutover.
- Alerting secrets live in a runtime env file.
- A local `~/nas-cutover/` staging directory can exist, but it is explicitly not part of the repo and should not be casually read by agents.

One important discovery: the encrypted datasets use passphrase keys.
That is good.
It means the data is recoverable with the passphrases.
But TrueNAS's auto-unlock copy lives in TrueNAS state on the boot pool.
If I destroy the boot pool without having those passphrases recorded somewhere else, I can strand encrypted datasets even though the ZFS pools themselves survived.

That is exactly the kind of migration footgun I want written down before the cutover, not rediscovered afterward.

## What I like about this workflow

This migration is the clearest example yet of why I want infrastructure in text.

An AI agent inspected the live TrueNAS box.
It produced a NixOS scaffold.
Another review pass found missing replication behavior, SMB differences, Incus recovery gaps, and monitoring regressions.
The human-intent parts stayed explicit instead of being blindly copied from the live system.
Then we encoded the dangerous storage assumption as a VM test.

This is not "vibe sysadmin."

It is closer to code review:

1. Inspect the current system.
2. Convert the desired parts to code.
3. Review the diff.
4. Ask another model to review the diff.
5. Add tests for the scariest assumption.
6. Write the cutover runbook.
7. Keep the actual destructive step small and explicit.

The agent is useful because the system is textual.
It can read Nix files.
It can generate a patch.
It can run `nix build`.
It can run the VM test.
It can inspect the generated disko script.
It can update the PR body.

Try doing that with a web UI full of hidden state.

## Where this leaves TrueNAS

I do not hate TrueNAS.
It got me very far.
It made ZFS approachable.
It gave me a good NAS UI when I wanted a NAS UI.
And if you want an appliance that mostly owns storage for you, it is still a very compelling project.

But for my own infrastructure, the direction is clear.

I do not want the most important machine in my house to be an appliance I configure through a UI.
I do not want the build system for that appliance to move behind closed doors and have to decide whether I am still comfortable with the governance model.
I do not want AI agents poking at mutable state they cannot fully represent.

I want a git diff.

After the Proxmox migration, TrueNAS was the last major exception.
This migration removes that exception.

## The current state

{{% callout warning %}}
Draft status: this section should be updated after the actual cutover.
At the time of writing, the NixOS `nas` scaffold builds, the VM disko rehearsal passes, and the cutover plan is documented.
The real machine has not been declared "done" until the installer preflight and client validation have completed.
{{% /callout %}}

What is already validated locally:

- The `nas` NixOS system builds.
- The generated disko script targets only the configured boot disk.
- The VM disko rehearsal passes.
- The fake data pools survive the rehearsal and re-import with sentinel files intact.
- ZFS data pools are imported by name, not described in disko.
- Force import is disabled.
- Boot-time encryption prompts are disabled.
- SMB config parses with `testparm`.
- Replication scripts pass syntax checks.
- Incus preseed evaluates.
- The cutover docs explicitly call out the remote-only disk identity preflight.

What still must happen during the real cutover:

- Confirm encrypted dataset passphrases are recorded/backed up off-box.
- Cleanly shut down TrueNAS.
- Boot the NixOS installer.
- Run the remote-only disko preflight on the actual hardware.
- Confirm the disko target is the old boot-pool disk and has no data-pool labels.
- Run disko and `nixos-install`.
- Import pools.
- Unlock encrypted datasets.
- Validate SMB/NFS from real clients.
- Recover Incus state.
- Verify replication and monitoring.

That sounds like a lot, because it is.
But the important thing is that the risk has been decomposed.
The scary part is no longer "replace TrueNAS somehow."
It is a checklist of explicit assumptions, most of which are now encoded in Nix or tested in a VM.

## References

- [I've gone full Nix: Proxmox to NixOS + Incus]({{< ref "/post/proxmox-to-nixos" >}})
- [Why NixOS lets me sleep at night]({{< ref "/post/why-nixos-lets-me-sleep" >}})
- [My homelab: from a single Raspberry Pi to a Proxmox cluster and a dedicated NAS]({{< ref "/post/homelab" >}})
- [On agentic coding]({{< ref "/post/agentic-coding" >}})
- [TrueNAS forum: Clearing the Air on Build Scripts](https://forums.truenas.com/t/clearing-the-air-on-build-scripts/64357)
- [`truenas/scale-build` on GitHub](https://github.com/truenas/scale-build)
- [TechEnclave discussion: TrueNAS has gone closed source?](https://techenclave.com/t/truenas-has-gone-closed-source/420208)
- [TrueNAS 25.04 documentation](https://www.truenas.com/docs/scale/25.04/)
- [TrueNAS 25.04.1: Fangtooth Unification Gains Momentum](https://www.truenas.com/blog/truenas-fangtooth-25-04-1/)
- [TrueNAS Virtualization Plans for 25.04.2](https://forums.truenas.com/t/truenas-virtualization-plans-for-25-04-2/46236)
- [TrueNAS 25.04.2 release announcement](https://forums.truenas.com/t/truenas-25-04-2-is-now-available/49165)
- [Linux Jails with Incus forum thread](https://forums.truenas.com/t/linux-jails-containers-vms-with-incus/23599?page=21)
- [Jailmaker](https://github.com/Jip-Hop/jailmaker)
- [The NAS NixOS scaffold PR](https://github.com/basnijholt/dotfiles/pull/61)
