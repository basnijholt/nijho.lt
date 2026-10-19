---
title: "Why Docker isn't an AI-safe sandbox anymore, and how I fixed it in MindRoom 🔒"
subtitle: "What I learned about kernels, containers, and VMs while adding a stronger sandbox to MindRoom."
summary: "For years, a Docker container was a good enough box to run code in, because getting out of one usually needed a hard-to-find bug in the Linux kernel. Now AI models are good at finding those bugs, and AI agents write the code running inside the containers. This post explains what the kernel does, how containers use it to fake a separate computer, why that is a problem now, and how six lines of code let MindRoom give its agents a stronger wall."
date: 2026-10-18
draft: false
featured: false
authors:
  - admin
tags:
  - ai
  - mindroom
  - security
  - docker
  - agents
  - self-hosting
categories:
  - AI
  - Software Development
  - level:intermediate
---

For years, a Docker container was my default answer to "where do I run this?"
I never thought it was a perfect sandbox.
It was good enough, because getting out of one usually meant finding a specific kind of bug in the Linux kernel itself, and those were hard to find.[^runc]

AI models have become very good at finding security bugs, including in Linux.
Anthropic and OpenAI now keep their strongest security models, [Claude Mythos](https://www.anthropic.com/claude/mythos) and [Daybreak Blue](https://openai.com/the-defense-factory/), behind identity checks and vetting.
Open-weight models, which anyone can download and run, come with no such rules, and they trail the closed ones by only [six to seven months](https://epoch.ai/data-insights/open-closed-cyber-eci-gap).
Once there is an open model as good as Mythos, anyone can strip out its refusals with a tool like [Heretic](https://github.com/p-e-w/heretic) (people call this abliteration) and point it at the Linux kernel.
The security company DepthFirst used its own model to find a way out of a container and titled the write-up [Containers Are No Longer a Security Boundary](https://depthfirst.com/research/containers-are-no-longer-safe).

I care about this because running untrusted code in containers is exactly what [MindRoom]({{< ref "/post/mindroom" >}}), my open-source system for AI agents that live in Matrix chat rooms, does.
Every agent can get its own Docker worker, and its shell, file, Python, and browser tools run there.
It can install anything, start background processes, and drive a real browser.
And as I wrote in [my ZFS post]({{< ref "/post/btrfs-to-zfs" >}}), I run coding agents in {{< tooltip text="The agent runs every command without asking me for approval first." >}}YOLO mode{{< /tooltip >}}, exclusively.
I do not review the commands they run, I look at the results.

So both sides changed at once.
The code inside the container is now written by an AI, and the bugs that let it out are now found by an AI.
A [video from the Low Level channel](https://youtu.be/9-2CSJC114k) asking whether containers are still safe made me sit down and rethink my setup.

I am not an expert in any of this.
I have used containers, KVM, and hypervisors for years, including Proxmox before I [moved to NixOS]({{< ref "/post/proxmox-to-nixos" >}}), but I never deeply understood what happens underneath.
Building this forced me to learn it, and writing this post is my exercise in understanding it all.
All of this is very complicated (as is everything new), and I am still learning.
I am sure I skip over a lot and simplify the rest; what is here are the parts that helped me understand it.
I thought it would be nice to share.

{{% callout note %}}
**TL;DR:** A container is a process on your machine that the kernel dresses up as a separate computer.
Every container shares that one kernel with the host, so a single bug in it can be a way out.
MindRoom can now give each agent's worker its own kernel, with one setting and six lines of code.
{{% /callout %}}

{{< toc >}}

## What the kernel actually does

When people talk about Linux, they usually mean an operating system like Ubuntu, Fedora, or NixOS.
Those differ in almost everything you see: package managers, desktops, config files.
What they all have in common is the kernel, the part Linus Torvalds started in 1991 and still leads today.
Strictly speaking, that kernel is the only part called Linux.

The kernel is the one program on a Linux machine that talks to the hardware directly.
Everything else, your shell, Python, Chrome, Docker, runs on top of it and has to ask it for things.
Open this file.
Give me some memory.
Send this packet.
Start a new process.
Those requests are called system calls, or syscalls for short.

There is one kernel per machine, and it decides who is allowed to do what.
That makes it the most trusted code on the system.
Most kernel bugs only crash the machine or cause glitches.
But some let a normal program become root, the admin account, or even run its own code inside the kernel.
At that point it can do anything on the machine, including leaving any container it was in.

## A container is a process in a costume

When you `docker run -it ubuntu`, you get a root shell in what feels like a fresh computer.
Under the hood it is one ordinary process.
The kernel dresses it up using three features:

- **Namespaces** decide what the process can see. It gets its own list of processes (where it is process number 1), its own filesystem, and its own network. Root inside is still root on the host, with {{< tooltip text="Docker drops most of root's special powers, which Linux calls capabilities, and seccomp and AppArmor block more. Namespaces only change what root can see." >}}most of its powers taken away{{< /tooltip >}}.[^root]
- **cgroups** decide how much it can use: CPU, memory, number of processes.
- **seccomp** decides which syscalls it may make at all. It is a filter that blocks the ones a normal program never needs.

That also works in the other direction.
Whoever can tell Docker what to run can start a container as root and mount any folder from the host into it.
Because root inside is root outside, they can then read and change every file in that folder, including files their own account may not open.
Docker's own documentation says the `docker` group [grants root-level privileges](https://docs.docker.com/engine/install/linux-postinstall/).
I knew that in theory, but it only clicked when I watched an AI agent do it on a machine where I had no root, only Docker access.
It needed to change files it was not allowed to touch, so it started a small container, mounted their folder, and edited them from inside.
No kernel bug needed.

{{< figure src="container-kernel.svg" alt="Two containers and the host's own processes all make syscalls into one shared Linux kernel, which keeps the containers apart with namespaces, cgroups and seccomp. One bug in that kernel reaches every container and the host." >}}

There is no second kernel.
Every syscall from inside a container lands in the same kernel as every other container and the host itself.
The kernel enforces the isolation, and it is also what gets attacked.

For most uses that is fine.
Usually you put fixed software in a container: a database, a web app, some self-hosted service.
You know where that code comes from, you keep your kernel patched, and that is good enough.

An AI agent is different.
It writes new code on the spot and runs it, and nobody knows in advance what that code will do.

## Why kernel bugs matter more now

Kernel bugs that let a normal program take over the whole machine used to take skilled people weeks or months to find and exploit.
The famous ones, like [Dirty COW](https://dirtycow.ninja) in 2016, made the news every year or two, you patched, and that was it.

AI is speeding this up, and the DepthFirst write-up I mentioned is a good example.
Their model found a bug in the kernel code for Unix sockets, which programs on the same machine use to talk to each other.
The kernel freed a piece of memory and then kept using it, a so-called use-after-free, and from inside a container that was enough to get out.
Their conclusion is that you should assume attackers can escape containers at will.

Could I block more syscalls, or take more powers away from root?
A little, but that only narrows which parts of the shared kernel a container can reach.
This bug sat in Unix sockets, which almost every program uses, including the browser the agent drives, so blocking them would break the agent.

Now put an AI agent in that container.
It reads web pages and repositories written by strangers, and one of those could talk it into running an exploit.
On a MindRoom server, getting out of a worker means getting onto the machine that runs MindRoom itself.
That is where the API keys, Matrix logins, and stored credentials live, which the workers are built to never see.

## So I asked a model to break out

Before changing anything, I wanted to know how real this was for my own setup.
I gave a MindRoom agent [Daybreak Blue](https://openai.com/the-defense-factory/) and asked it to escape its worker container using known kernel vulnerabilities.
Daybreak Blue is OpenAI's security model for verified users, so it does the offensive security work that other models refuse.

It did not get out, which was reassuring.
But it only tried known bugs.
A kernel a few weeks behind on patches, or a bug nobody has published yet, would be a different story.
So the attempt tells me the easy path was closed that day, and not much more.

## Stronger walls: virtual machines

The classic answer is a virtual machine.
A container shares the host's kernel, but a VM brings its own, and this is where the hardware comes in.
Modern CPUs have a virtualization mode built in, called VT-x on Intel and AMD-V on AMD.
In that mode, a second kernel, the guest kernel, runs directly on the real CPU and believes it is in charge, while the CPU quietly limits it.
When the guest tries something it may not do on its own, like talking to a disk or a network card, the CPU pauses the guest and hands control to the host.
This is called a VM exit.
Despite the name, nothing escapes and nothing crashes.
The host handles the request, for example by pretending to be that disk, and then resumes the guest where it stopped.
From the guest's point of view, the instruction simply finished.

Memory is fenced off too.
The host gives the CPU a separate map of which real memory each guest may use, and the CPU checks every memory access against it.
So even a guest kernel with full privileges cannot touch the host's memory.

The CPU only provides the mechanism.
The software that sets the rules and handles the VM exits is called the hypervisor.
"Hypervisor" is a role, not one program, and on Linux it is two pieces:

- **KVM**, a module in the Linux kernel, uses the CPU's virtualization mode to run the guest, keeps that memory map, and catches its VM exits. It shows up as the device `/dev/kvm`.
- **A VMM** (virtual machine monitor), a normal program on top, sets up the VM and handles the exits that KVM passes up, for example by pretending to be the guest's disk and network card. [QEMU](https://www.qemu.org), [Firecracker](https://firecracker-microvm.github.io), and [Cloud Hypervisor](https://www.cloudhypervisor.org) are three VMMs you can pick from.

Proxmox, which I mentioned above, is KVM plus QEMU.
AWS Lambda is KVM plus Firecracker.

Code in a VM talks to its own guest kernel.
To reach the host, it usually has to break that kernel first and then the hypervisor.[^devices]
That is still possible.
Google Project Zero turned [a bug in how KVM runs VMs inside VMs on AMD](https://googleprojectzero.blogspot.com/2021/06/an-epyc-escape-case-study-of-kvm.html) into a full escape in 2021.
Google's [kvmCTF](https://security.googleblog.com/2024/06/virtual-escape-real-reward-introducing.html) pays up to {{< tooltip text="The top reward in the current kvmCTF rules, for a full escape from the guest VM to the host." >}}$250,000{{< /tooltip >}} for a new one.
And this year, one researcher, Hyunwoo Kim, published [three KVM escapes](https://github.com/V4bel/Zapscape), one of them hidden in KVM {{< tooltip text="Januscape, CVE-2026-53359: a use-after-free in the shadow page tables of x86 KVM, added in August 2010 and fixed in June 2026." >}}since 2010{{< /tooltip >}}.

The difference between a container and a VM is how much code an attacker can reach, and that gap is large.
On x86 (the Intel and AMD chips in most PCs and servers), Linux has {{< tooltip text="The x86_64 syscall table of Linux 7.3-rc7 has 386 entries for 64-bit programs, and 16 of them are empty slots that only return an error." >}}about 370 syscalls{{< /tooltip >}}, and Docker's [default seccomp filter](https://docs.docker.com/engine/security/seccomp/) blocks {{< tooltip text="Docker's documentation says its default profile disables around 44 system calls out of 300+. The current profile blocks a few more, like the io_uring calls." >}}a few dozen{{< /tooltip >}} of them.
Behind the rest sit the kernel's filesystems, networking, memory management, and core code: {{< tooltip text="The fs, net, mm and kernel folders of Linux 7.3-rc7, counted with tokei, comments and blank lines included. The whole tree is 43 million lines, 26.5 million of them drivers." >}}about 3.8 million lines{{< /tooltip >}}, even without counting drivers.
Not all of that is reachable from a container, but a lot of it is.
KVM on x86 is {{< tooltip text="arch/x86/kvm plus virt/kvm in the same Linux 7.3-rc7 tree, counted the same way: 113,720 lines." >}}about 114,000 lines{{< /tooltip >}}.
On top of KVM comes the VMM, but only the few devices it fakes for the guest.
Most QEMU escapes came from its many emulated devices, which is why Firecracker and Cloud Hypervisor keep that list short.

Google's bug bounties point the same way.
[kernelCTF](https://google.github.io/security-research/kernelctf/rules.html) pays {{< tooltip text="One fixed amount per accepted exploit, according to the current kernelCTF rules." >}}$71,337{{< /tooltip >}} for each new kernel exploit that turns a normal user into root, and Google's [public repository](https://github.com/google/security-research/tree/master/pocs/linux/kernelctf) holds exploits for {{< tooltip text="119 exploit folders in pocs/linux/kernelctf, covering 93 unique CVEs, at commit 79f049dc from October 16, 2026." >}}93 different kernel bugs{{< /tooltip >}}.
kvmCTF pays more than three times as much, and the same repository holds {{< tooltip text="The only folder in pocs/linux/kvmctf at the same commit: a NULL pointer dereference reached through nested virtualization. Januscape was also used in kvmCTF but is not in the repository yet." >}}one KVM exploit{{< /tooltip >}}, which crashes the host instead of escaping it.
kvmCTF started a year later, but the gap is still big.
Most of those kernel exploits would not work as written from a default container, because they {{< tooltip text="84 of the 119 exploit folders create a user namespace, which gives a normal process root's powers over its own set of namespaces and opens up kernel code it could not reach otherwise. Docker's default seccomp profile blocks that unless the container has the CAP_SYS_ADMIN capability." >}}first use a feature Docker blocks{{< /tooltip >}}.
Still, they show how many exploitable bugs sit behind the syscalls.

## Kata Containers and gVisor

Regular VMs are heavy.
They boot a full operating system and tend to use a lot of memory.
A microVM is a stripped-down VM meant to run one workload and start quickly.
That still leaves a practical problem.
MindRoom, like most tools, speaks Docker: it hands Docker an image and some folders to mount, and gets a running container back.
A VM does not take a Docker image.
Switching to VMs would normally mean building disk images, booting them, and wiring up files and networking myself.

Docker does not start containers by itself, though.
It takes care of images, networks, and volumes, and then hands the actual start to a small program called a runtime.
The default runtime, `runc`, does what I described earlier: it starts a process on the host kernel with namespaces, cgroups, and seccomp.
But you can tell Docker to use a different runtime.

[Kata Containers](https://katacontainers.io) is such a runtime, and it starts a microVM instead.
It picks one of the VMMs above (my test used QEMU), boots a small guest kernel, and starts the container inside it.[^kata]
Docker, and MindRoom, still see an ordinary container.

[gVisor](https://gvisor.dev), from Google, takes a different route, and it is not a VM.
It is a reimplementation of the Linux kernel, written in Go, that runs as a normal program on the host.
Go manages memory for the programmer, so the use-after-free mistake behind the DepthFirst escape is much harder to make in gVisor.
The worker's syscalls go to gVisor instead of the host kernel, and gVisor itself only makes a small, filtered set of host syscalls.
That is the hardening idea taken all the way: gVisor answers the agent's syscalls itself, so the filter on the host can be much stricter than Docker's.
It needs no `/dev/kvm`, so it also runs inside cloud VMs that cannot start VMs of their own.
My test machine, an ARM server (with the kind of chip phones use) running NixOS, had no `/dev/kvm`, which is why I tried gVisor first.
Its runtime is called `runsc`, and it plugs into Docker the same way.

{{< figure src="isolation-stacks.svg" caption="The three options side by side." alt="Three stacks side by side. Plain Docker: the agent's code makes syscalls straight into the host kernel, so the usual way out is a host kernel bug, reached through any syscall seccomp allows. gVisor: the agent's code makes syscalls into gVisor's own kernel, written in Go, which makes a small set of syscalls to the host kernel, so the usual way out is a gVisor bug and then a host kernel bug. Kata Containers: the agent's code runs on a guest kernel inside a microVM, and the CPU runs that guest kernel directly, next to the host kernel instead of on top of it. When the guest needs a device, a VM exit hands control to the KVM module in the host kernel, which passes the request up to the VMM, a normal program on the host that fakes the device. The VMM and KVM together are the hypervisor, so the usual way out is a guest kernel bug and then a hypervisor bug." >}}

Or as a table:

| Isolation | What worker code talks to | Needs KVM | Usual escape route |
|---|---|---|---|
| Plain Docker (`runc`) | The host kernel, filtered by seccomp | No | A host kernel bug |
| gVisor (`runsc`) | gVisor's own kernel, written in Go | No | A gVisor bug, then a host kernel bug through its small filtered surface |
| Kata Containers | Its own guest kernel in a microVM | Yes | A guest kernel bug, then a hypervisor bug |

Each option also changes how much code on the host an escape can pick its bug from.

{{< plot name="attackSurface" caption="Lines of code on the host that deal with what the agent's code asks for, counted with tokei, comments and blank lines included. For Docker, the core of Linux without drivers; for gVisor, its kernel and network stack without tests; for Kata, KVM alone, without the VMM and Kata's other helpers. Not all of it is reachable. Hover for exact numbers." >}}

## The PR: six lines

The change is [PR #2886](https://github.com/mindroom-ai/mindroom/pull/2886), which is now merged.
It adds one setting, `MINDROOM_DOCKER_WORKER_RUNTIME`, and MindRoom passes its value to Docker as the runtime whenever it starts a worker.
That is {{< tooltip text="Three lines in docker.py and three in docker_config.py. The merged PR adds 98 lines: these 6, 62 lines of tests, and 30 lines of docs." >}}six lines of source code{{< /tooltip >}}, plus 62 lines of tests and some docs.
Changing the setting recreates each worker the next time it is used, and leaving it unset keeps everything as it was.

For gVisor, setting it up is two steps: register the runtime in Docker's `/etc/docker/daemon.json` and restart Docker, then point MindRoom at it.

```json
{
  "runtimes": {
    "runsc": { "path": "/usr/local/bin/runsc" }
  }
}
```

```bash
MINDROOM_DOCKER_WORKER_RUNTIME=runsc
```

Kata needs no entry in that file: once it is installed, `MINDROOM_DOCKER_WORKER_RUNTIME=io.containerd.kata.v2` is enough.
The full setup, and a few catches for each runtime, are in the [MindRoom docs](https://docs.mindroom.chat/deployment/sandbox-proxy/#security-considerations).

The six lines are short because everything else already existed.
gVisor and Kata do the isolating.
Docker already gives each worker its folders, its credentials, and its network, and it already knows how to hand a container to a different runtime.
On the MindRoom side, the hard part happened months earlier, when agent tools moved out of the main process into dedicated workers with explicit mounts and credentials.
Once every worker is a single call to Docker's `containers.run`, swapping what runs underneath it is one argument.
For comparison, Claude Opus estimated that building a microVM backend into MindRoom itself would take {{< tooltip text="For a native Cloud Hypervisor backend that rebuilds image conversion, guest init, folder sharing, networking, and VM supervision. The estimate is in the PR description." >}}2,500 to 4,000 lines{{< /tooltip >}}.

## What it costs

I tested both runtimes with a real agent in a Matrix room: gVisor on that ARM server, and Kata {{< tooltip text="Kata 4.2 with QEMU and Docker 29.9, inside an Incus VM with nested KVM on my desktop's Ryzen 9 3900X." >}}in a throwaway VM on my desktop{{< /tooltip >}}.
Shell, Python, git, background processes, and the browser all worked, without any MindRoom code change.
My Kata numbers below come from a VM inside a VM, so bare-metal numbers will differ.

Configuration is the cheap part: one environment variable, plus one entry in Docker's config for gVisor.
The other costs are the usual trade-offs between containers and VMs:

- **Computation.** Code that only calculates, without asking the kernel for anything, runs at full speed with both. gVisor lets those instructions run directly on the CPU, according to its [performance guide](https://gvisor.dev/docs/architecture_guide/performance/). A Kata guest runs on the CPU in its virtualization mode, and in [AWS's paper on Firecracker](https://www.usenix.org/conference/nsdi20/presentation/agache), the CPU overhead was {{< tooltip text="The paper reports memory overhead as low as 3% and negligible CPU overhead." >}}negligible{{< /tooltip >}}.
- **Syscalls, disk, and network.** The cost starts when a program does ask the kernel for something. Under gVisor, every syscall takes a detour through gVisor's kernel, so programs that make many small syscalls, like ones that open thousands of small files, slow down the most. Under Kata, disk and network go through the VMM's fake devices. In that same paper from 2020, a Firecracker guest reached {{< tooltip text="iperf3 over a tap device on an EC2 m5d.metal host, one stream: 44.1 Gbit/s for the host, 15.6 for Firecracker, and 23.8 for QEMU." >}}15 Gbit/s of network traffic where the host reached 44{{< /tooltip >}}.
- **Startup.** gVisor only has to start a program, so it starts quickly. Kata has to boot a kernel first, and my worker took {{< tooltip text="From creating the container until the worker answered its health check, three runs each: 10.1 to 10.9 seconds with Kata, 2.4 to 3.3 with runc." >}}about 10 seconds to start instead of about 3{{< /tooltip >}}. Booting a VM can be much faster than that: [Firecracker](https://firecracker-microvm.github.io) boots a minimal one in about 125 ms.
- **Memory.** gVisor adds a {{< tooltip text="gVisor's performance guide: the sandbox itself is responsible for a small, mostly fixed amount of memory overhead." >}}small, mostly fixed amount{{< /tooltip >}} per sandbox. Each Kata VM runs a second kernel plus the VMM, which alone takes {{< tooltip text="Figure 7 of the Firecracker paper: memory used by the VMM process on top of the guest's own memory, about 3 MB for Firecracker, 13 MB for Cloud Hypervisor, and 131 MB for QEMU." >}}about 3 MB with Firecracker and 131 MB with QEMU{{< /tooltip >}}. Kata gives each worker VM {{< tooltip text="Kata's default VM has 1 vCPU and 2 GiB, set by default_vcpus and default_memory in its configuration file. Kata adds a container's memory limit on top, but MindRoom sets none for its workers. The worker's 1 GiB /tmp counts against it." >}}2 GiB by default{{< /tooltip >}}, and `/tmp` lives in that RAM. The host only hands out memory the guest actually touches, so my idle worker used {{< tooltip text="QEMU used 530 to 616 MiB and virtiofsd, which shares the folders, about 160 MiB for one idle worker VM. Both map the guest's memory, so some pages count twice and the real total is lower." >}}under 0.8 GiB{{< /tooltip >}} of host memory. Raising the VM size {{< tooltip text="The guest kernel keeps 64 bytes of bookkeeping for every 4 KiB page, about 1.6% of the VM's size, so an 8 GiB VM costs about 128 MiB up front." >}}costs little{{< /tooltip >}} until a worker needs it. But a VM cannot grow past its size the way a container can, and memory the guest has used, for example to keep recently read files in its cache, {{< tooltip text="Kata's reclaim_guest_freed_memory option, off by default, returns pages the guest frees. File cache does not count as free, so it stays." >}}mostly stays with the VM{{< /tooltip >}}.
- **Compatibility.** gVisor reimplements Linux, and its [docs](https://gvisor.dev/docs/user_guide/compatibility/) say there will always be unimplemented features and bugs, so now and then a program will not work. Kata runs a real Linux kernel, so programs behave as usual, with a few catches. For example, a file lock held on the host does not block the worker, because the lock lives in the guest kernel.

## What this does not fix

A stronger sandbox protects the host.
It does nothing about the tokens and network access you give the worker.
An agent needs no kernel exploit to misuse a token that can push to your repositories, or to poke at every device on your home network.
Scoped credentials and a firewall allowlist matter at least as much, and MindRoom handles both separately: [Agent Keys](https://docs.mindroom.chat/deployment/egress-broker/) let agents use API keys without ever seeing them, and [Approved Egress](https://docs.mindroom.chat/deployment/approved-egress/) limits which servers a worker on Kubernetes can reach.

gVisor has had its own bugs, and it still talks to the host kernel, just through a much smaller door.
KVM has bugs too, as this year's escapes show.
Both walls make an escape far harder, and neither makes it impossible.

## Conclusion

Once I started reading about this, I kept running into people saying containers were never a security boundary.
That is true, and for years it did not matter much to me.
With AI finding kernel bugs faster and agents running code nobody reads, it matters now.
MindRoom can now move its agents off the shared kernel with one environment variable.
I do not use it myself yet, but if you are more paranoid than I am, it is there.

[^runc]: The other way out is a bug in the program that starts the container. In 2024, [CVE-2024-21626](https://github.com/opencontainers/runc/security/advisories/GHSA-xr7r-f8xq-vfvv) in runc, the program Docker uses for that, leaked a handle to a host folder into new containers, so a malicious image could reach the host's files without any kernel bug.

[^root]: Docker can map the container's root to an ordinary user on the host with [user namespace remapping](https://docs.docker.com/engine/security/userns-remap/), or run without root altogether in [rootless mode](https://docs.docker.com/engine/security/rootless/), but neither is the default. Rootless mode would have stopped the agent in my Docker story, because Docker then has only my own rights. Remapping would not, because anyone who can use Docker can turn it off for a single container. Neither helps against a kernel bug, because code running inside the kernel is above every user.

[^kata]: Like runc for Docker, Kata's own programs on the host are a way out too. In 2020, one bug ([CVE-2020-2023](https://nvd.nist.gov/vuln/detail/CVE-2020-2023)) let a container take over the guest without a kernel bug, and a second ([CVE-2020-2026](https://nvd.nist.gov/vuln/detail/CVE-2020-2026)) then let the guest trick the Kata runtime on the host into mounting files over any host path. Neither needed a KVM bug. virtiofsd, the program that shares folders with the guest, also runs on the host and handles the guest's file requests.

[^devices]: A bug in the VMM's fake devices, or in other VMM code that handles the guest's traffic, can skip the first step, because a normal program in the guest can feed that code data through the network or a shared folder. [CVE-2020-8608](https://access.redhat.com/security/cve/cve-2020-8608), a buffer overflow in QEMU's user-mode networking, could be triggered that way with crafted network traffic.
