---
title: "Friend-to-friend ZFS backups, version two"
subtitle: "Giving a friend a quota-capped corner of my pool, without a VM or a shell"
summary: "Two years ago, a friend and I backed each other up through a TrueNAS VM on an iSCSI zvol. Now that I run NixOS, I replaced that machinery with zfs-tenant: OpenZFS delegation and a quota keep him inside one dataset, and a small SSH forced command plus zfs zone make sure he sees nothing else of my pool. His keys never leave his house, and a VM test checks each of those claims."
date: 2026-09-26
draft: true
featured: false
authors:
  - admin
tags:
  - zfs
  - backups
  - homelab
  - nixos
  - syncoid
  - security
  - open-source
  - agentic-coding
categories:
  - technology
  - DevOps
  - level:intermediate
---

Two years ago I wrote about [friend-to-friend backups with TrueNAS]({{< ref "/post/truenas-remote-backups" >}}).
A friend and I store each other's ZFS snapshots, which is the cheapest off-site backup there is.
TrueNAS's replication tasks wanted root on the receiving system, and neither of us wanted to give the other root on the machine that holds our family photos.
So each of us ran a TrueNAS VM on a hypervisor, backed by an iSCSI zvol on the real NAS, and gave the other person root inside that VM instead.
Sounds complicated?
It was.
It worked, but it meant running ZFS on a zvol on ZFS, inside a VM that each of us had to keep updated.

Since then I [replaced TrueNAS with NixOS]({{< ref "/post/truenas-to-nixos" >}}), and my friend plans to move his machines to NixOS too.
This time we looked for the simplest solution, built from standard Linux and ZFS features wherever possible.
He wanted plain `zfs send` and `zfs receive`, with his data still encrypted and his keys never on my server.
I agreed, on one condition: neither of us should be able to destroy the other's datasets.

The result is [zfs-tenant](https://github.com/basnijholt/zfs-tenant), which is now [on PyPI](https://pypi.org/project/zfs-tenant/) and has [documentation](https://zfs-tenant.nijho.lt).

{{< figure src="logo.svg" alt="The zfs-tenant logo: a storage pool with two dim compartments for the host and one locked amber compartment for a friend, filled up to a dashed quota line" width="220" >}}

{{< toc >}}

## Why ZFS

[OpenZFS](https://openzfs.org/) is a filesystem and a volume manager in one.
You add disks to a pool, and it behaves like one large partition: every dataset you create draws from the same free space, and each can still have its own quota and encryption.
ZFS checksums every block it writes, so it notices when a disk hands back something else, and with a mirror or RAIDZ it repairs the block from a good copy.
That protection costs disk space: a mirror of two disks holds one disk's worth of data.

For me, snapshots are one of the coolest parts.
ZFS never overwrites data in place, so a snapshot only has to hold on to the blocks that existed at that moment.
Taking one is instant, and it costs no space until the data changes.
[`zfs send`](https://openzfs.github.io/openzfs-docs/man/master/8/zfs-send.8.html) turns a snapshot, or the difference between two snapshots, into a stream that `zfs receive` writes into a pool on another machine, usually piped through SSH.
It moves blocks, not files: an incremental send contains only the blocks that changed, and ZFS knows which ones those are without visiting a single file.
A bajillion one-kilobyte files do not slow it down, because nothing has to look at them one by one.
For comparison, restic on my PC needed [an hour and a half per run]({{< ref "/post/btrfs-to-zfs" >}}) just to check close to a hundred million files for changes.

Two tools from the same project automate this.
[sanoid](https://github.com/jimsalterjrs/sanoid) takes snapshots on a schedule and prunes them by policy, for example hourly ones for a day and daily ones for a month.
syncoid wraps `zfs send` and `zfs receive` over SSH: it finds the newest snapshot both sides share and sends everything after it.

## What we wanted

We wrote down the rules before anything else:

1. He cannot see any of my data, including metadata like dataset names and sizes.
2. He cannot change or destroy anything of mine.
3. I cannot read his data, because his keys stay at his house.
4. He gets one dataset where he can create and remove nested datasets as he likes.
5. That dataset has a size limit.
6. No new replication tool on either side: plain `zfs send` or syncoid.

Until then his NAS runs TrueNAS, so whatever I built also had to work on a machine without NixOS.

## ZFS already had most of it

OpenZFS has a permission system that most people never touch: [`zfs allow`](https://openzfs.github.io/openzfs-docs/man/master/8/zfs-allow.8.html).
It delegates individual operations like `receive`, `create`, and `destroy` on one dataset to an unprivileged user.
Put a root-owned `quota` on that dataset and the user cannot store more than you agreed.
Raw sends (`zfs send -w`) ship the encrypted blocks as they are, so the receiving side never needs the key.

On paper, that covers five of the six rules.
The gap is visibility.
Any local user can run `zfs list` and see every dataset on the machine, with names, sizes, and properties.
And an SSH account for replication is, by default, also a shell.

There are tools that would sidestep some of this.
[zrepl](https://zrepl.github.io/) has a sink mode with a subtree per client, but it replaces sanoid and syncoid on both sides and runs as root on the receiver.
restic or borg to a friend's box would also work, but everything else on my network is ZFS: my machines [replicate to the NAS with syncoid](https://github.com/basnijholt/dotfiles/blob/6526b50e9bae1449a915239491099ef71528f10c/configs/nixos/hosts/nas/replication.nix#L40-L49), and a restore is `zfs send` and `zfs receive`.
Adding another backup format means one more thing to understand when something breaks.
My current off-site copy goes to [Backblaze B2 with rclone](https://github.com/basnijholt/dotfiles/blob/6526b50e9bae1449a915239491099ef71528f10c/configs/nixos/hosts/docker-lxc/rclone-b2-backup.nix).
Ideally that would be ZFS as well, and some hosting services accept `zfs send`, but they cost far more than object storage.
A friend with a ZFS box costs nothing.

## Rehearsing the permissions in a VM

Before writing any code, I had an agent build a throwaway NixOS VM test with a real pool, a delegated user, and a list of probes.
Each probe tried one thing the friend should not be able to do and recorded what ZFS answered.

The first surprise came from the most obvious setup.
With a plain `zfs allow -u joe create,receive,destroy,... tank/friends/joe`, the delegated user could run `zfs destroy -r tank/friends/joe` and delete the dataset I had created for him, quota included.
Delegated rights apply to the dataset itself as well as everything below it, unless you say otherwise.
The fix is to split them: on the root itself only `create,mount,receive` with `zfs allow -l`, and the full set only for descendants with `zfs allow -d`.
After that change, destroying, snapshotting, re-delegating, or changing the quota of the root all failed with `permission denied`.

A send stream can carry properties, and a hostile one could carry `mountpoint=/etc`.
Receiving it as the delegated user gave `cannot receive mountpoint property on tank/friends/joe/evil: permission denied`, and the dataset kept the `mountpoint=none` it inherited from the root.
ZFS applies received properties with the receiving user's rights, so a property you never delegated cannot arrive through a stream.

The probes also confirmed the gap: the delegated user saw my `tank/host` dataset in `zfs list`, and `zfs get used tank/host` returned its size.

## A gate that speaks syncoid

The shell part has a standard answer.
An `authorized_keys` line with `restrict,command="..."` runs one fixed program for every login, and passes whatever the client asked for in `SSH_ORIGINAL_COMMAND`.
zfs-tenant's gate is that program.
It tokenizes the request, accepts only the handful of command shapes a backup needs, checks that every dataset name is inside the friend's dataset, and runs `zfs` with an argument list it builds itself.
It never starts a shell, so there is nothing to inject into.

The hard part was knowing exactly which commands syncoid sends, so an agent read [syncoid's Perl](https://github.com/jimsalterjrs/sanoid/blob/v2.3.0/syncoid) and logged every remote command it ran.
Most are the `zfs` commands you would expect.
One surprise: before each receive, syncoid runs `ps -Ao args=` on the receiving machine, which lists every running process with its full command line, to check that no other transfer is already writing to the same dataset.
That list would show my friend everything running on my NAS, so the gate answers with an empty one.

Reading syncoid that closely also turned up a bug in version 2.3.0, outside zfs-tenant itself.
In push mode, syncoid asks the receiving host for a ZFS resume token.
It passed that answer unescaped into shell commands for estimating and resuming the send, which run on the source machine.
A malicious or compromised backup host could therefore return shell syntax instead of a token and execute arbitrary commands on the sender with the privileges of the syncoid process.

I reproduced this in two isolated NixOS VMs using real ZFS and SSH: a harmless command embedded in the receiver's answer created a marker file on the sender.
I reported it to the maintainer and opened [sanoid PR #1114](https://github.com/jimsalterjrs/sanoid/pull/1114) with a small fix that shell-quotes the token at both uses.
Even with that fix, the sending side should run syncoid as an unprivileged user that may only `send` and `hold`.
nixpkgs' `services.syncoid` already works that way, so my friend needs nothing from zfs-tenant at all.

## Zones, and the setup that would have made things worse

At that point the gate was the only thing hiding my datasets.
Then my friend sent me a message: ZFS has a feature called zones, which restricts a dataset tree to a Linux user namespace.

[`zfs zone`](https://openzfs.github.io/openzfs-docs/man/master/8/zfs-zone.8.html) attaches a dataset to one user namespace, and inside that namespace the ZFS kernel module answers `dataset does not exist` for everything that is not attached.
Even if my gate had a bug that let arbitrary `zfs` commands through, `tank/host` would stay invisible.

The VM test also showed a problem with the usual setup.
Containers typically map the user to root inside the namespace.
ZFS treats root in the namespace as the zone's administrator, and that bypasses `zfs allow`.
In the test, the tenant could destroy the root dataset I had created for it.
Mapping the tenant to its own uid instead keeps it without capabilities inside the namespace, and then delegation applies exactly as before, while the kernel still hides everything else.

Root inside a user namespace also turned up in a real OpenZFS bug in August.
Before 2.4.4, 2.3.9, and 2.2.11, several pool operations, such as destroying a pool, accepted `CAP_SYS_ADMIN` inside a user namespace the caller had created as if it were host root ([CVE-2026-79619](https://github.com/openzfs/zfs/security/advisories/GHSA-mhf5-q8gw-qg9v)).
Any local user who can open `/dev/zfs` and create a user namespace could use it, and zfs-tenant needs both to be allowed.
Joe cannot reach it through the gate, but a host running zfs-tenant should load a patched module: `cat /sys/module/zfs/version` shows the loaded one, which only changes after a reboot.

A zone needs a running namespace to attach to, so zfs-tenant runs a small service per friend that holds one.
The gate joins that namespace before it looks at the command, and refuses to run if the service is down.
Two details only showed up while building it.
Joining a user namespace grants every capability inside it, so the gate drops them right away and checks `/proc/self/status` before it does anything else.
And with `zoned=on`, delegated writes from outside the namespace fail too: a process that escaped the zone could still not change anything.

OpenZFS master can attach datasets to a uid instead of a single namespace, which would make the holder service unnecessary.
Once that lands in a release and keeps `zfs allow` in charge, the holder can go; [issue #6](https://github.com/basnijholt/zfs-tenant/issues/6) tracks it.

## What it cannot hide

ZFS encryption protects file contents, not structure.
In the words of [`zfs-load-key(8)`](https://openzfs.github.io/openzfs-docs/man/master/8/zfs-load-key.8.html), ZFS "will not encrypt metadata related to the pool structure, including dataset and snapshot names, dataset hierarchy, properties, file size, file holes, and deduplication tables."
So I can see the names, sizes, and snapshot times of whatever my friend sends me.
Boring dataset names help, and sending without `-p` keeps properties out of the stream.

I can also always delete his copy, because I am root on my own machine.
What I can never do is read it.
My [monthly scrubs](https://github.com/basnijholt/dotfiles/blob/6526b50e9bae1449a915239491099ef71528f10c/configs/nixos/hosts/nas/storage.nix#L71-L81) still verify his data without his key, because ZFS checksums the encrypted blocks.

What we protect against is a dead machine: a failed pool, a fire, a flood.
His key may destroy anything below his root, which is what lets syncoid mirror his snapshot retention, so someone who steals that key can also delete his backups on my NAS.
We talked about that and left it out on purpose.
Covering it would take holds that I place as root and release on a schedule, and it was not a threat either of us wanted to design for.

## Setting it up

On a NixOS host, giving a friend space takes this:

```nix
services.zfs-tenant = {
  enable = true;
  tenants.joe = {
    dataset = "tank/friends/joe";
    quota = "2T";
    authorizedKeys = [ "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... joe-nas" ];
    allowedFrom = [ "100.64.0.12" ];  # his tailnet address
  };
};
```

That creates the user, pins the key to the gate, applies the dataset, properties, and delegation on every boot, and runs the zone service.
My own setup is in [`friend-backups.nix`](https://github.com/basnijholt/dotfiles/blob/6526b50e9bae1449a915239491099ef71528f10c/configs/nixos/hosts/nas/friend-backups.nix#L43-L50), with his real key and address.
If your sanoid snapshots the whole pool, [exclude the tenant tree](https://github.com/basnijholt/dotfiles/blob/6526b50e9bae1449a915239491099ef71528f10c/configs/nixos/hosts/nas/friend-backups.nix#L52-L59): your sanoid must neither snapshot nor prune it, or his next incremental push finds snapshots on the target that he never sent.
The network does its part as well: on our tailnet, only his router may reach port 22 on my NAS, and `from=` in `authorized_keys` only accepts his key from that address.
Once my friend is on NixOS, he can push with nixpkgs' own module:

```nix
programs.ssh.knownHosts.bas-nas.publicKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA...";

services.syncoid = {
  enable = true;
  sshKey = "/var/lib/syncoid/id_ed25519";
  localSourceAllow = [ "send" "hold" ];
  commonArgs = [
    "--no-sync-snap"
    "--compress=none"
    "--delete-target-snapshots"
    "--sshoption=StrictHostKeyChecking=yes"
  ];
  commands."tank/offsite" = {
    target = "zfs-tenant-joe@bas-nas:tank/friends/joe/offsite";
    recursive = true;
    sendOptions = "w";
  };
};
```

My NAS will push to his with the [same configuration](https://github.com/basnijholt/dotfiles/blob/6526b50e9bae1449a915239491099ef71528f10c/configs/nixos/hosts/nas/friend-backups.nix#L66-L91) once he hosts a root for me.

For his TrueNAS box there is a single `zfs-tenant.pyz` on every [release](https://github.com/basnijholt/zfs-tenant/releases), which runs with the Python that TrueNAS already ships, plus a `setup --dry-run` command that prints the exact `zfs` commands to run.
The [getting started guide](https://zfs-tenant.nijho.lt/getting-started/) walks through both.
Hosting on TrueNAS has only run in VMs so far; [issue #4](https://github.com/basnijholt/zfs-tenant/issues/4) is open for anyone who wants to try it on a real TrueNAS host.
Sending from TrueNAS is where its built-in tools stop working: replication tasks wrap every remote command in `sh -c`, which the gate refuses, so he pushes with `zfs send` or syncoid instead.

## Knowing when it stops working

The [last btrfs machine]({{< ref "/post/btrfs-to-zfs" >}}) taught me a fifth question for any backup: how do I find out when it stops working?
A failed push shows up in `systemctl status` on the sending side, which nobody reads.
The check belongs on the receiving side, and it has to look at every pushed dataset separately, because one healthy dataset can hide another that stopped replicating.
That is how I watch my own machines: the NAS [checks the newest snapshot of every dataset it replicates](https://github.com/basnijholt/dotfiles/blob/6526b50e9bae1449a915239491099ef71528f10c/configs/nixos/hosts/nas/replication.nix#L332-L352) every hour and alerts my phone when one is too old.
zfs-tenant does not alert yet; [issue #3](https://github.com/basnijholt/zfs-tenant/issues/3) tracks it.

## Restoring

The gate also allows `zfs send` of his own snapshots, so getting data back is one pipe, run at his house:

```bash
ssh zfs-tenant-joe@bas-nas zfs send -w tank/friends/joe/offsite/photos@autosnap_2026-09-25_00:00:01_daily \
  | zfs receive -u tank/photos
zfs load-key tank/photos
zfs mount tank/photos
```

That raised a question on my side.
My photos are a child dataset that inherits its key from an encryption root, and I only push the child.
If my NAS dies and I pull the child back, can I still unlock it without the root?
A throwaway VM says yes.
Every dataset has its own master key, stored wrapped by the key derived from the passphrase, and a raw send carries that wrapped key together with the salt and iteration count.
The child arrives as its own encryption root and opens with the same passphrase.
The one catch: after a `zfs change-key`, the next incremental carries the new wrapping, and in the VM the old passphrase no longer worked.
So the passphrase that matters is the one at the time of the last push, and it has to live somewhere other than the NAS.
Mine does: [zfs-unlock](https://github.com/basnijholt/zfs-unlock) keeps the passphrases on a separate device and [unlocks the NAS](https://github.com/basnijholt/dotfiles/blob/6526b50e9bae1449a915239491099ef71528f10c/configs/nixos/hosts/nas/zfs-unlock.nix) after every boot.

## The first real push

Once [my side was deployed](https://github.com/basnijholt/dotfiles/blob/6526b50e9bae1449a915239491099ef71528f10c/configs/nixos/hosts/nas/friend-backups.nix), Joe tried it from his TrueNAS box.
His first move was to see what else his key could do.
The gate logged every attempt on my NAS:

```
root=tank/friends/joe denied interactive session
root=tank/friends/joe denied 'ls': only zfs commands and syncoid's probes are allowed
root=tank/friends/joe denied '/usr/bin/bash': only zfs commands and syncoid's probes are allowed
root=tank/friends/joe denied '/bin/bash': only zfs commands and syncoid's probes are allowed
root=tank/friends/joe allowed 'zfs receive -s -u tank/friends/joe/zt-test'
```

The last line is a small encrypted test dataset, sent with `zfs send -w` piped into `ssh`, without syncoid.
It arrived with `keystatus` set to `unavailable`.
Then I tried to read it as root on my own machine.
`zfs mount` answered `cannot mount 'tank/friends/joe/zt-test': dataset is exported to a local zone`, and `zfs load-key` with a guessed passphrase gave `Key load error: Incorrect key provided`.
The only readable text in the raw stream was ZFS property names and the snapshot name, which is the metadata ZFS leaves unencrypted, as described above.

## Tested like everything else

Every security claim in this post is also checked by a VM test: two NixOS machines back each other up, the way my friend and I do, with real sanoid and syncoid 2.3.0, through real sshd and the gate, into real OpenZFS 2.4.4.
Its 34 subtests cover the zone hiding my datasets, the gate failing closed, and the delegation limits with and without the gate.
They also cover what happens over time: pruning, retention gaps, interrupted transfers and restores, the quota and dataset limits, and both machines rebooting.
It runs on every push in GitHub Actions, next to the unit tests.

While I was building this, the VM test found that incremental sends need `hold` on the sending side, and that syncoid only prunes after it has sent something new.
Later it caught two bugs that only show up once a setup has been running for a while.
After a reboot, setup failed on a tenant root that already held data, because OpenZFS rejects even a redundant `mountpoint` write once zoned children inherit it.
And syncoid stopped replicating after sanoid's retention had removed the newest snapshot both sides shared.
To continue from an older common snapshot, syncoid rolls the target back with `zfs receive -F`, and the gate used to drop that flag.
It now passes `-F` through, still only below the tenant root, and the test pins that libzfs refuses to replace an encrypted dataset that way.

The route to the syncoid finding was slightly absurd.
I built much of zfs-tenant through coding agents, often literally from the bathtub, and then asked several frontier models to review the security boundary independently.
One of them followed receiver-controlled data beyond my new code and into syncoid.
A model's suspicion is not evidence, so I turned it into the two-VM reproduction above: it failed on unpatched syncoid 2.3.0 and passed after the seven-line fix.
The most consequential result of reviewing my small new project was a command-injection bug in the mature tool next to it.

A second round of review found two gaps in my own code.
Setup reset my friend's own grants on his root but kept any others it found in his tree, so a leftover `zfs allow everyone destroy` on his root would have let him delete it.
It now refuses a tree with grants it did not make, and leaves removing them to me.
And the quota capped disk space, not the processes a push starts on my NAS; on NixOS, every SSH session now runs in a systemd slice limited to 512 MB of memory and one CPU core.

The whole thing is about 930 lines of Python, not counting comments and docstrings, with no dependencies.
The kernel does the actual enforcing: delegation, the quota, and the zone.
The gate only removes the shell, and it is small enough to read in one sitting.

## The feature nobody asked for

The first version had *grace holds*: every day, the host held the newest snapshot of each of my friend's datasets for 14 days.
It was on none of our lists, and when the agent later argued against the usual zone setup, its main reason was that namespace root could release those holds.
I asked whether it was defending the design with a reason I had never included in it, and it was.
It had made a scope decision without flagging it, and then reasoned from that decision as if it were mine.

## References

- [zfs-tenant on GitHub](https://github.com/basnijholt/zfs-tenant)
- [zfs-tenant documentation](https://zfs-tenant.nijho.lt)
- [Friend-to-friend TrueNAS backups without the cloud]({{< ref "/post/truenas-remote-backups" >}})
- [Migrating from TrueNAS to NixOS]({{< ref "/post/truenas-to-nixos" >}})
- [The last btrfs machine: migrating my PC to ZFS]({{< ref "/post/btrfs-to-zfs" >}})
- [`zfs-allow(8)`](https://openzfs.github.io/openzfs-docs/man/master/8/zfs-allow.8.html)
- [`zfs-zone(8)`](https://openzfs.github.io/openzfs-docs/man/master/8/zfs-zone.8.html)
- [Sanoid and syncoid](https://github.com/jimsalterjrs/sanoid)
