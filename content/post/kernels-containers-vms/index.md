---
title: "It took me 6 lines to make MindRoom robust against agents escaping via kernel bugs 🔒"
subtitle: "What I learned about kernels, containers, and VMs while adding a stronger sandbox to MindRoom."
summary: "For years, a Docker container was a good enough box to run code in, because getting out of one needed a rare bug in the Linux kernel. Now AI models are good at finding those bugs, and AI agents write the code running inside the containers. This post explains what the kernel does, how containers use it to fake a separate computer, why that is a problem now, and how six lines of code let MindRoom give its agents a stronger wall."
date: 2026-10-18
draft: true
featured: false
authors:
  - admin
tags:
  - ai
  - mindroom
  - security
  - docker
  - gvisor
  - agents
  - self-hosting
categories:
  - AI
  - Software Development
  - level:intermediate
---

For years, a Docker container was my default answer to "where do I run this?"
I never thought it was a perfect sandbox.
It was good enough, because getting out of one meant finding a specific kind of bug in the Linux kernel itself, and those were rare.

That is changing.
AI models have become very good at finding security bugs, including in Linux.
Anthropic and OpenAI now keep their strongest security models, [Claude Mythos](https://www.anthropic.com/claude/mythos) and [Daybreak](https://openai.com/the-defense-factory/), behind identity checks and vetting.
That restriction will not last long.
Open-weight models trail the closed ones [by months, not years](https://epoch.ai/data-insights/open-closed-cyber-eci-gap), and they come with no such rules.
Once there is an open model as good as Mythos, anyone can strip out its refusals (people call this abliteration) and point it at the Linux kernel.
One security company used their own model to find a way out of a container and titled the write-up [Containers Are No Longer a Security Boundary](https://depthfirst.com/research/containers-are-no-longer-safe).

I care about this because running untrusted code in containers is exactly what [MindRoom]({{< ref "/post/mindroom" >}}) does.
Every agent can get its own Docker worker, and its shell, file, Python, and browser tools run there.
It can install anything, start background processes, and drive a real browser.
And as I wrote in [my ZFS post]({{< ref "/post/btrfs-to-zfs" >}}), I run coding agents in {{< tooltip text="The agent runs every command without asking me for approval first." >}}YOLO mode{{< /tooltip >}}, exclusively.
I do not review the commands they run, I look at the results.

So both sides changed at once.
The code inside the container is now written by an AI, and the bugs that let it out are now found by an AI.
A [Low Level Learning video](https://youtu.be/9-2CSJC114k) asking whether containers are still safe made me sit down and rethink my setup.

I am not an expert in any of this.
I have used containers, KVM, and hypervisors for years, including Proxmox before I [moved to NixOS]({{< ref "/post/proxmox-to-nixos" >}}), but I never really understood what happens underneath.
Building this forced me to learn it, and writing this post is my exercise in understanding it all.
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
Most kernel bugs are harmless crashes or glitches.
But some let a normal program become root, or even run its own code inside the kernel.
At that point it can do anything on the machine, including leaving any container it was in.

## A container is a process in a costume

When you `docker run ubuntu`, you get a root shell in what feels like a fresh computer.
Under the hood it is one ordinary process.
The kernel dresses it up using three features:

- **Namespaces** decide what the process can see. It gets its own list of processes (where it is PID 1), its own filesystem, its own network, and its own idea of who root is.
- **cgroups** decide how much it can use: CPU, memory, number of processes.
- **seccomp** decides which syscalls it may make at all. It is a filter that blocks the ones a normal program never needs.

{{< figure src="container-kernel.svg" alt="Containers are processes that all make syscalls into one shared Linux kernel, which enforces namespaces, cgroups and seccomp" >}}

There is no second kernel.
Every syscall from inside a container lands in the same kernel as every other container and the host itself.
The kernel enforces the isolation, and it is also what gets attacked.

For most uses that is fine.
Usually you put fixed software in a container: a database, a web app, some self-hosted service.
You know where that code comes from, you keep your kernel patched, and that is good enough.

An AI agent is different.
It writes new code on the spot and runs it, and nobody knows in advance what that code will do.

## Why kernel bugs matter more now

Kernel bugs that let a normal program take over the whole machine used to be rare.
[Dirty COW](https://dirtycow.ninja) in 2016 was big news.
Something like it came out every year or two, you patched, and that was it.

AI is changing that pace.
The DepthFirst write-up I mentioned is a good example.
Their model found a bug in the kernel code for Unix sockets, which programs on the same machine use to talk to each other.
The kernel freed a piece of memory and then kept using it, a so-called use-after-free, and from inside a container that was enough to get out.
Their conclusion is that you should assume attackers can escape containers at will.

Now put an AI agent in that container.
It writes and runs code all day.
It reads web pages and repositories written by strangers.
One of those could talk it into running an exploit.

## So I asked a model to break out

Before changing anything, I wanted to know how real this was for my own setup.
I gave a MindRoom agent [Daybreak Blue](https://openai.com/the-defense-factory/) and asked it to escape its worker container using known kernel vulnerabilities.
Daybreak Blue is OpenAI's security model for verified users, so it does the offensive security work that other models refuse.

It did not get out, which was reassuring.
But it only tried known bugs.
A kernel a few weeks behind on patches, or a bug nobody has published yet, would be a different story.
So the attempt tells me the easy path was closed that day, and not much more.

## Stronger walls: virtual machines and gVisor

The classic answer is a virtual machine, and this is where the hardware comes in.
Modern CPUs have a virtualization mode built in, called VT-x on Intel and AMD-V on AMD.
In that mode, a second kernel, the guest kernel, runs directly on the real CPU and believes it is in charge, while the CPU quietly limits it.
When the guest tries something it may not do on its own, like talking to a disk or a network card, the CPU pauses the guest and hands control to the host.
This is called a VM exit.
Despite the name, nothing escapes and nothing crashes.
The host handles the request, for example by pretending to be that disk, and then resumes the guest where it stopped.
From the guest's point of view, the instruction simply finished.
Memory is fenced off too.
A second set of page tables in the CPU decides which real memory the guest can reach, so even a fully privileged guest kernel cannot touch host memory.

The CPU only provides the mechanism.
The software that sets the rules and handles the VM exits is called the hypervisor.
"Hypervisor" is a role, not one program, and on Linux it is two pieces:

- **KVM**, a module in the Linux kernel, uses the CPU's virtualization mode to run the guest and catches its VM exits. It shows up as the device `/dev/kvm`.
- **A VMM** (virtual machine monitor), a normal program on top, sets up the VM and handles the exits that KVM passes up, for example by pretending to be the guest's disk and network card. [QEMU](https://www.qemu.org), [Firecracker](https://firecracker-microvm.github.io), and [Cloud Hypervisor](https://www.cloudhypervisor.org) are three VMMs you can pick from.

Proxmox, which I mentioned above, is KVM plus QEMU.
AWS Lambda is KVM plus Firecracker.
Without KVM, QEMU can still emulate the whole CPU in software, but that is very slow.
This also finally explained Proxmox's passthrough option to me: when you pass a real GPU or network card to a VM, the VMM stops faking that device, and a chip called the IOMMU makes sure the device can only reach the guest's memory.

Code in a VM talks to its own guest kernel.
To reach the host, it has to break that kernel first and then the hypervisor.
That is still possible.
Google Project Zero turned [a bug in KVM's nested virtualization on AMD](https://googleprojectzero.blogspot.com/2021/06/an-epyc-escape-case-study-of-kvm.html) into a full escape in 2021.
Google's [kvmCTF](https://security.googleblog.com/2024/06/virtual-escape-real-reward-introducing.html) pays up to {{< tooltip text="The top reward in the current kvmCTF rules, for a full escape from the guest VM to the host." >}}$250,000{{< /tooltip >}} for a new one.
And this year, one researcher, Hyunwoo Kim, published [three KVM escapes](https://github.com/V4bel/Zapscape), one of them hidden in KVM {{< tooltip text="Januscape, CVE-2026-53359: a use-after-free in the shadow page tables of x86 KVM, added in August 2010 and fixed in June 2026." >}}since 2010{{< /tooltip >}}.

The difference is how much code the attacker can reach, and that gap is large.
On x86, Linux has {{< tooltip text="386 to be exact: the entries that 64-bit programs can use in the x86_64 syscall table of Linux 7.3-rc7." >}}about 390 syscalls{{< /tooltip >}}, and Docker's [default seccomp filter](https://docs.docker.com/engine/security/seccomp/) blocks {{< tooltip text="Docker's documentation says its default profile disables around 44 system calls out of 300+." >}}around 44{{< /tooltip >}} of them.
Behind the rest sit the kernel's filesystems, networking, memory management, and core code: {{< tooltip text="The fs, net, mm and kernel folders of Linux 7.3-rc7, counted with tokei, comments and blank lines included. The whole tree is 43 million lines, 26.5 million of them drivers." >}}about 3.8 million lines{{< /tooltip >}}, even without counting drivers.
Not all of that is reachable from a container, but a lot of it is.
KVM on x86 is {{< tooltip text="arch/x86/kvm plus virt/kvm in the same Linux 7.3-rc7 tree, counted the same way: 113,720 lines." >}}about 114,000 lines{{< /tooltip >}}.
I counted both with [tokei](https://github.com/XAMPPRocky/tokei) on Linux 7.3-rc7, so treat them as ballpark numbers.
On top of KVM comes the VMM, but only the few devices it fakes for the guest.
Most QEMU escapes came from its many emulated devices, which is why Firecracker and Cloud Hypervisor keep that list short.

Google's bug bounties point the same way.
[kernelCTF](https://google.github.io/security-research/kernelctf/rules.html) pays {{< tooltip text="One fixed amount per accepted exploit, according to the current kernelCTF rules." >}}$71,337{{< /tooltip >}} for each new kernel exploit that turns a normal user into root, and Google's [public repository](https://github.com/google/security-research/tree/master/pocs/linux/kernelctf) holds exploits for {{< tooltip text="119 exploit folders in pocs/linux/kernelctf, covering 93 unique CVEs, at commit 79f049dc from October 16, 2026." >}}93 different kernel bugs{{< /tooltip >}}.
kvmCTF pays more than three times as much, and the same repository holds {{< tooltip text="The only folder in pocs/linux/kvmctf at the same commit: a NULL pointer dereference reached through nested virtualization." >}}one KVM exploit{{< /tooltip >}}, which crashes the host instead of escaping it.
The programs started a year apart, and publishing takes time (Januscape, one of Kim's escapes, was used in kvmCTF but is not in the repository yet), but the gap is still big.

Regular VMs are heavy.
They boot slowly and reserve a lot of memory.
A microVM is a stripped-down VM meant to run one workload and start quickly.
That still leaves a practical problem.
MindRoom, like most tools, speaks Docker: it hands Docker an image and some folders to mount, and gets a running container back.
A VM does not take a Docker image.
Switching to VMs would normally mean building disk images, booting them, and wiring up files and networking myself.

This is where it helps to know that Docker does not start containers by itself.
Docker takes care of images, networks, and volumes, and then hands the actual start to a small program called a runtime.
The default runtime, `runc`, does what I described earlier: it starts a process on the host kernel with namespaces, cgroups, and seccomp.
But you can tell Docker to use a different runtime.

[Kata Containers](https://katacontainers.io) is such a runtime, and it starts a microVM instead.
It picks one of the VMMs above (my test used QEMU), boots a small guest kernel, and starts the container inside it.
Docker, and MindRoom, still see an ordinary container.

[gVisor](https://gvisor.dev), from Google, takes a different route, and it is not a VM.
It is a reimplementation of the Linux kernel, written in Go, that runs as a normal program on the host.
The worker's syscalls go to gVisor instead of the host kernel, and gVisor itself only makes a small, filtered set of host syscalls.
It needs no `/dev/kvm`, so it also runs inside cloud VMs that do not offer nested virtualization.
My test machine, an ARM server running NixOS, had no `/dev/kvm`, which is why I tried gVisor first.
Its runtime is called `runsc`, and it plugs into Docker the same way.

{{< figure src="isolation-stacks.svg" caption="The three options side by side. The red dashed parts are what the agent has to break to reach the host." alt="Three stacks side by side. Plain Docker: the agent's code talks to the host kernel directly. gVisor: the agent's code talks to the Sentry, a kernel written in Go, which makes a few filtered calls to the host kernel. Kata: the agent's code runs on a guest kernel inside a microVM, run by a VMM such as QEMU, Firecracker or Cloud Hypervisor, on top of the KVM module in the host kernel. The VMM plus KVM together are the hypervisor." >}}

Or as a table:

| Isolation | What worker code talks to | Needs KVM | Escape requires |
|---|---|---|---|
| Plain Docker (`runc`) | The host kernel, filtered by seccomp | No | A host kernel bug |
| gVisor (`runsc`) | gVisor's own kernel, written in Go | No | A gVisor bug, then a host kernel bug through its small filtered surface |
| Kata Containers | Its own guest kernel in a microVM | Yes | A guest kernel bug, then a hypervisor bug |

## The PR: six lines

The change is [PR #2886](https://github.com/mindroom-ai/mindroom/pull/2886), which is now merged.
It adds one setting, `MINDROOM_DOCKER_WORKER_RUNTIME`, and MindRoom passes its value to Docker as the runtime whenever it starts a worker.
That is {{< tooltip text="Three lines in docker.py and three in docker_config.py. The merged PR adds 98 lines: these 6, 62 lines of tests, and 30 lines of docs." >}}six lines of source code{{< /tooltip >}}, plus 62 lines of tests and some docs.
Changing the setting recreates each worker the next time it is used, and leaving it unset keeps everything as it was.

Setting it up is two steps: register the runtime with the Docker daemon, then point MindRoom at it.

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

On NixOS that first part is `virtualisation.docker.daemon.settings.runtimes`.
On Kubernetes, MindRoom already had `workers.kubernetes.runtimeClassName`; this is the Docker counterpart.

The six lines are short because everything else already existed.
gVisor and Kata do the isolating.
Docker already gives each worker what it needs: a root directory on the host, read-only credentials and config, workspaces shared live with MindRoom and with other workers, a published port, and a route back to the primary.
And Docker already knows how to hand a container to a different runtime.
On the MindRoom side, the hard part happened months earlier, when agent tools moved out of the main process into dedicated workers with explicit mounts and credentials.
Once every worker is one `containers.run` call, swapping what runs underneath it is one argument.
For comparison, Claude Opus estimated that building a microVM backend into MindRoom itself would take {{< tooltip text="For a native Cloud Hypervisor backend that rebuilds image conversion, guest init, folder sharing, networking, and VM supervision. The estimate is in the PR description." >}}2,500 to 4,000 lines{{< /tooltip >}}.

## What it costs

I tested both runtimes with a real agent in a Matrix room: gVisor on that ARM server, and Kata in a throwaway VM on my desktop.
Shell, Python, git, background processes, and the Worker Computer browser all worked, without any MindRoom code change.

gVisor has two version caveats, both in the [MindRoom docs](https://docs.mindroom.chat/deployment/sandbox-proxy/):

- Use release 20261005 or newer. Release 20260406 crashed Chromium after the first page.
- With 20261005 or older, register `runsc` without `--oci-seccomp`, or workers cannot start threads ([google/gvisor#14688](https://github.com/google/gvisor/issues/14688)).

Kata costs more:

- **Startup.** A worker takes {{< tooltip text="From creating the container until the worker answered its health check, three runs each: 10.1 to 10.9 seconds with Kata, 2.4 to 3.3 with runc." >}}about 10 seconds to start instead of about 3{{< /tooltip >}}.
- **Memory.** Each worker VM gets {{< tooltip text="Kata's default VM has 1 vCPU and 2 GiB, set by default_vcpus and default_memory in its configuration file. The worker's 1 GiB /tmp counts against it." >}}2 GiB by default{{< /tooltip >}}, and `/tmp` lives in that RAM. An idle worker already used {{< tooltip text="QEMU used 530 to 616 MiB and virtiofsd, which shares the folders, about 160 MiB for one idle worker VM." >}}about 0.7 GiB{{< /tooltip >}} of host memory.
- **File locks.** A lock held on the host does not block the worker, because the lock lives in the guest kernel.

I measured Kata {{< tooltip text="Kata 4.2 with QEMU and Docker 29.9, inside an Incus VM with nested KVM on my desktop's Ryzen 9 3900X." >}}nested inside a VM{{< /tooltip >}}, so bare-metal numbers will differ.

## What this does not fix

A stronger sandbox protects the host.
It does nothing about the tokens and network access you give the worker.
An agent needs no kernel exploit to misuse a token that can push to your repositories, or to poke at every device on your home network.
Scoped credentials and a firewall allowlist matter at least as much, and MindRoom handles both separately.

gVisor has had its own bugs, and it still talks to the host kernel, just through a much smaller door.
KVM has bugs too, as this year's escapes show.
Both walls make an escape far harder, and neither makes it impossible.

## Conclusion

Once I started reading about this, I kept running into people saying containers were never a security boundary.
That is true, and for years it did not matter much to me.
With AI finding kernel bugs faster and agents running code nobody reads, it matters now.
MindRoom can now move its agents off the shared kernel with one environment variable.
I do not use it myself yet, but if you are more paranoid than I am, it is there.
