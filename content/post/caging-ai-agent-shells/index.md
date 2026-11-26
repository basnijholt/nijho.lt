---
title: "My AI agents froze my PC, so I put their shells in a cage 🧊"
subtitle: "Why my CPU and out-of-memory safety nets missed a desktop freeze, and how one shared Linux memory cap fixed the setup"
summary: "On November 25, around forty coding agents (plus their subagents) running in parallel froze my 62 GiB Linux desktop so hard the motherboard rebooted it. Here's why lowering CPU priority and running a memory killer didn't save the box, and how I put all agent shell commands behind one shared memory, swap, and CPU cap."
date: 2026-11-25
draft: false
featured: false
authors:
  - admin
tags:
  - agents
  - agentic-coding
  - mindroom
  - nixos
  - homelab
  - self-hosting
categories:
  - AI
  - Homelab
  - Software Development
  - level:intermediate
---

On November 25, at 11:29 AM, my desktop PC froze solid.
Five minutes later the motherboard's {{< tooltip text="The AMD sp5100_tco hardware watchdog timer, configured with a 300-second timeout. If Linux stops responding for five minutes, the board forces a hard reset." >}}hardware watchdog{{< /tooltip >}} gave up and hard-reset the whole box.

That machine isn't just my workstation.
It also hosts the Linux container for my [MindRoom]({{< ref "/post/mindroom" >}}) setup, including the chat bots my family talks to every day and around forty coding agents running in parallel, many of them spawning subagents of their own.
When the reboot hit, every active agent thread and every family bot went down at once.
Host logs from just before the freeze showed swap usage passing 40.7 GiB while TypeScript hit its 4 GiB heap limit and parallel `pytest`, `vitest`, and `eslint` runs filled the rest of my 62 GiB of RAM[^crash-logs].

I thought I'd already prevented this twice.
A week earlier I'd lowered the agents' CPU priority, and months before that I'd installed a memory killer after earlier NixOS build lockups.
Neither one saved the machine.

{{% callout note %}}
**TL;DR:** Lowering CPU priority stops agent builds from lagging your chat server, not from filling RAM and thrashing swap until the desktop locks up.
And an out-of-memory killer with a 10% free-swap default waits way too long when your machine has 111 GiB of swap.
The fix was moving all agent shell commands into one shared Linux resource cap with hard RAM, swap, and CPU limits, leaving the MindRoom server and my desktop outside that cap.
{{% /callout %}}

{{< toc >}}

## Why my safety nets missed it

My desktop runs a 24-thread {{< tooltip text="AMD Ryzen 9 3900X (12 cores, 24 threads) with 62 GiB of usable RAM running NixOS." >}}Ryzen CPU with 62 GiB of RAM{{< /tooltip >}} and {{< tooltip text="A 96 GiB NVMe swap partition plus a 15.7 GiB compressed zram swap device in RAM." >}}111 GiB of swap{{< /tooltip >}}.
Once dozens of agents and subagents kick off test suites and type checks at the same time, they fill RAM and spill into swap on the same NVMe drive that holds the root filesystem.
Past about 40 GiB of swap, disk thrashing locks up the whole PC.

A week earlier, heavy builds had been slowing down MindRoom's chat server, so I updated MindRoom to run agent shells at {{< tooltip text="Linux SCHED_IDLE via chrt -i 0 (mindroom#4092). Tasks in this class only use CPU cycles that normal programs don't want." >}}idle CPU priority{{< /tooltip >}}.
That worked great when builds pegged all 24 threads, and did nothing once memory ran out.
Every shell command still lived in the exact same memory pool as the MindRoom server, and the container running MindRoom had no memory cap at all.

My second safety net was {{< tooltip text="earlyoom is a small Linux daemon that watches free RAM and swap and kills a memory-hungry process before the kernel freezes." >}}`earlyoom`{{< /tooltip >}}, which I installed back when [nightly NixOS builds]({{< ref "/post/nixos-cache" >}}) used to freeze this PC.
The funny thing is that `earlyoom` was working exactly as configured.
It only fires when both free RAM and free swap drop below their thresholds, and its default swap setting is 10% free.
On a laptop with 8 GiB of swap, 10% free fires at 7.2 GiB used.
On my desktop with 111 GiB of swap, 10% free waits until more than 100 GiB of swap is full.
The machine was already frozen at 41 GiB, so `earlyoom` sat there doing nothing while the hardware watchdog counted down to a reboot.

## One shared cage for every shell

Linux {{< tooltip text="Control groups (cgroups v2) organize processes into a tree and enforce hard RAM, swap, CPU, and I/O limits on each branch." >}}cgroups{{< /tooltip >}} let you split processes into separate resource budgets without running a VM for every command.
Because my MindRoom container already runs `systemd`, I moved every agent shell command into its own temporary scope inside one shared slice, leaving the MindRoom server in its own protected service group[^dotfiles-pr].

{{< figure src="isolation-layers.svg" alt="Before and after architecture diagram comparing one shared memory pool against four layered Linux resource limits" caption="Before, agent shells shared memory and swap with the MindRoom server and desktop. After, all shells share one capped slice while the server and host sit outside it." >}}

I sized the limits from the outside in, starting from my 62 GiB of RAM.
First, I capped the whole MindRoom container at 44 GiB of RAM and 8 GiB of swap, which always leaves at least 18 GiB of physical RAM for my desktop and ZFS cache.
Inside the container, the MindRoom server gets a 4 GiB guaranteed memory floor (6 GiB soft floor) and access to all 24 CPU threads.

Everything spawned by an agent's shell tool shares one cage: memory throttling kicks in at 28 GiB, a hard out-of-memory cap sits at 34 GiB, and swap is capped at 4 GiB so runaway jobs can't thrash the NVMe drive.
The shell slice is also restricted to 20 of the 24 threads, leaving four threads free of agent shells for MindRoom and desktop work.
On the host, I raised `earlyoom`'s free-swap threshold from 10% to 70% so it fires around 33 GiB of swap, and told it to prefer killing build tools (`pytest`, `tsc`, `vitest`, `cargo`) over the desktop or MindRoom.

On the MindRoom side, [mindroom#4379](https://github.com/mindroom-ai/mindroom/pull/4379) turns this on with one environment variable, `MINDROOM_SHELL_SYSTEMD_SLICE`[^mindroom-pr].
When it's set, MindRoom probes `systemd-run` once at startup and wraps each shell command in a scope inside that slice (plus idle disk priority via `ionice`, which helps on ext4 or btrfs even though ZFS ignores it).
On the live container, the wrapper adds about {{< tooltip text="Timed on the live container after reboot: wrapping /bin/true averaged ~7.5 ms per command." >}}7.5 milliseconds{{< /tooltip >}} per command.
On macOS or in minimal containers without `systemd`, it falls back and runs commands normally.

## Three things that tripped me up

- **Memory floors only work if every parent reserves them too.**
  Setting a 4 GiB `MemoryMin` floor on the MindRoom service does nothing unless `system.slice` and the Incus container cgroup above it also reserve at least 4 GiB.
- **Capping an Incus container's RAM zeroes out its swap.**
  My first try was `limits.memory=44GiB`, which on Incus 7.0.2 writes `0` to `memory.swap.max` and breaks any swap budget inside the container.
  Setting `lxc.cgroup2.memory.max` and `lxc.cgroup2.memory.swap.max` directly in `raw.lxc` kept an explicit 8 GiB swap cap.
- **Stopping the service won't stop caged shells.**
  Once shell jobs move into a separate slice, restarting MindRoom leaves orphaned `pytest` runs going unless the service also stops that slice on shutdown.

## Where things stand

After deploying the config and rebooting the container, every fresh agent shell lands inside the shared slice with idle CPU priority and 20 visible threads[^live-snapshot].
Even `nproc` inside a shell now reports `20` instead of `24`, so test runners that auto-scale to core count naturally leave four threads clear.

Since the reboot, 139 active tasks in the shell slice have peaked at 15.8 GiB of RAM (8.3 GiB current) and 42 MiB of swap.
That proves placement and overhead, not yet that the 34 GiB ceiling survives a real freeze-level spike, because normal work hasn't even hit the 28 GiB throttle yet.
I still want to see it ride out another heavy forty-agent pileup, or hit it with a deliberate stress test, before calling it battle-tested.

One thing cgroups don't do is keep untrusted code from escaping.
For that you still need a real sandbox, like the microVMs and container runtimes I wrote about in [Why Docker isn't an AI-safe sandbox anymore]({{< ref "/post/kernels-containers-vms" >}}).
Here the problem is much simpler: my own coding agents running too many test suites at once on the desktop I'm sitting in front of.
Instead of throttling agents to two commands at a time or spinning up a VM for every `git status`, one shared slice lets them run at full speed when the box is quiet and gives them a hard ceiling when forty agents wake up together.
The feature is built into MindRoom now, and documented in the [execution and coding docs](https://docs.mindroom.chat/tools/execution-and-coding/) if you self-host agents on a shared Linux box.

[^crash-logs]: Host `journalctl` on `pc` recorded 40.7 GiB of swap used at 11:29:33 PST on 2026-11-25 while `tsc` hit V8's 4 GiB heap limit and `systemd-journald` stalled on memory. The AMD `sp5100_tco` watchdog reset the machine at 11:34:48 PST (reset reason `0x02000800`).
[^dotfiles-pr]: Full NixOS configuration for both `mindroom` (delegated `user@1000.service` controllers, `mindroom-shells.slice`, `MemoryMin`/`MemoryLow` propagation, and `ExecStopPost` teardown) and `pc` (`earlyoom` `-s70` with `--prefer`/`--avoid`, plus Incus `raw.lxc` cgroup caps) is in [basnijholt/dotfiles#194](https://github.com/basnijholt/dotfiles/pull/194).
[^mindroom-pr]: Implemented in [mindroom-ai/mindroom#4379](https://github.com/mindroom-ai/mindroom/pull/4379) and documented in [mindroom-ai/mindroom#4381](https://github.com/mindroom-ai/mindroom/pull/4381). The wrapper also hides raw command arguments from `journalctl` (`--description=MindRoom shell`), disables `$$` expansion (`--expand-environment=no`), and separates the backend's user-bus env vars from the shell payload.
[^live-snapshot]: Captured on `mindroom` on 2026-11-25 via `systemctl --user show mindroom-shells.slice` (`MemoryCurrent=8912613376`, `MemoryPeak=16983384064`, `MemorySwapCurrent=44244992`, `TasksCurrent=139`).
