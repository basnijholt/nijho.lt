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

It worked, but it meant running ZFS on a zvol on ZFS, inside a VM that each of us had to keep updated.
Since then I [replaced TrueNAS with NixOS]({{< ref "/post/truenas-to-nixos" >}}), and my friend moved his machines to NixOS too.
When we talked about setting the backups up again, his first message was that he had found our old setup complicated.
He wanted plain `zfs send` and `zfs receive`, with his data still encrypted and his keys never on my server.
I agreed, on one condition: neither of us should be able to destroy the other's datasets.

The result is [zfs-tenant](https://github.com/basnijholt/zfs-tenant), which is now [on PyPI](https://pypi.org/project/zfs-tenant/) and has [documentation](https://zfs-tenant.nijho.lt).

{{< toc >}}

## What we wanted

We wrote down the rules before anything else:

1. He cannot see any of my data, including metadata like dataset names and sizes.
2. He cannot change or destroy anything of mine.
3. I cannot read his data, because his keys stay at his house.
4. He gets one dataset where he can create and remove nested datasets as he likes.
5. That dataset has a size limit.
6. Both of us keep using sanoid and syncoid.

He is trying TrueNAS on his NAS again, so whatever I built also had to work on a machine without NixOS.

## ZFS already had most of it

OpenZFS has a permission system that most people never touch: [`zfs allow`](https://openzfs.github.io/openzfs-docs/man/master/8/zfs-allow.8.html).
It delegates individual operations like `receive`, `create`, and `destroy` on one dataset to an unprivileged user.
Put a root-owned `quota` on that dataset and the user cannot store more than you agreed.
Raw sends (`zfs send -w`) ship the encrypted blocks as they are, so the receiving side never needs the key.

On paper, that covers five of the six rules.
The gap is visibility.
Any local user can run `zfs list` and see every dataset on the machine, with names, sizes, and properties.
And an SSH account for replication is, by default, also a shell.

## Rehearsing the permissions in a VM

Before writing any code, I had an agent build a throwaway NixOS VM test with a real pool, a delegated user, and a list of probes.
Each probe tried one thing the friend should not be able to do and recorded what ZFS answered.

The first surprise came from the most obvious setup.
With a plain `zfs allow -u joe create,receive,destroy,... tank/friends/joe`, the delegated user could run `zfs destroy -r tank/friends/joe` and delete the dataset I had created for him, quota included.
Delegated rights apply to the dataset itself as well as everything below it, unless you say otherwise.
The fix is to split them: on the root itself only `create,mount,receive` with `zfs allow -l`, and the full set only for descendants with `zfs allow -d`.
After that change, destroying, snapshotting, re-delegating, or changing the quota of the root all failed with `permission denied`.

The second finding was a pleasant one.
A send stream can carry properties, and a hostile one could carry `mountpoint=/etc`.
Receiving it as the delegated user gave `cannot receive mountpoint property on tank/friends/joe/evil: permission denied`, and the dataset kept the `mountpoint=none` it inherited from the root.
ZFS applies received properties with the receiving user's rights, so a property you never delegated cannot arrive through a stream.

The probes also confirmed the gap: the delegated user saw my `tank/host` dataset in `zfs list`, and `zfs get used tank/host` answered happily.

## A gate that speaks syncoid

The shell part has a standard answer.
An `authorized_keys` line with `restrict,command="..."` runs one fixed program for every login, and passes whatever the client asked for in `SSH_ORIGINAL_COMMAND`.
zfs-tenant's gate is that program.
It tokenizes the request, accepts only the handful of command shapes a backup needs, checks that every dataset name is inside the friend's dataset, and runs `zfs` with an argument list it builds itself.
It never starts a shell, so there is nothing to inject into.

The hard part was knowing exactly which commands syncoid sends.
An agent read all 2,444 lines of syncoid's Perl and ran about twenty scenarios against a fake `ssh` that logged every remote command.
The list is short: a few probes, five forms of `zfs get`, the receive itself, and snapshot pruning.
Two of the probes deserve an answer of nothing.
`command -v mbuffer` gets the answer that means it is not installed, so syncoid skips mbuffer and compression on my side, which raw encrypted data does not benefit from anyway.
`ps -Ao args=` gets an empty process list, because the real one would show my friend everything running on my NAS.

Reading syncoid that closely also turned up two bugs in version 2.3.0.
`--no-command-checks` does nothing, because the option is stored under a different key than the one the code checks.
The more serious one: syncoid pastes the resume token it gets from the receiving host unescaped into a shell on the sending machine, so a malicious receiver can run commands on the sender.
<!-- TODO: link the upstream syncoid issue once it is filed, before publishing -->
That is why the sending side should run syncoid as an unprivileged user that may only `send` and `hold`.
nixpkgs' `services.syncoid` already works that way, so my friend needs nothing from zfs-tenant at all.

## Zones, and the setup that would have made things worse

At that point the gate was the only thing hiding my datasets.
Then my friend sent me a message: ZFS has a feature called zones, which restricts a dataset tree to a Linux user namespace.

[`zfs zone`](https://openzfs.github.io/openzfs-docs/man/master/8/zfs-zone.8.html) attaches a dataset to one user namespace, and inside that namespace the ZFS kernel module answers `dataset does not exist` for everything that is not attached.
Even if my gate had a bug that let arbitrary `zfs` commands through, `tank/host` would stay invisible.

The VM test showed a catch that the usual setup walks right into.
Containers typically map the user to root inside the namespace.
ZFS treats root in the namespace as the zone's administrator, and that bypasses `zfs allow`.
In the test, the tenant could destroy the root dataset I had created for it.
Mapping the tenant to its own uid instead keeps it without capabilities inside the namespace, and then delegation applies exactly as before, while the kernel still hides everything else.

A zone needs a running namespace to attach to, so zfs-tenant runs a small service per friend that holds one.
The gate joins that namespace before it looks at the command, and refuses to run if the service is down.
Two details only showed up while building it.
Joining a user namespace grants every capability inside it, so the gate drops them right away and checks `/proc/self/status` before it does anything else.
And with `zoned=on`, delegated writes from outside the namespace fail too: a process that escaped the zone could still not change anything.

OpenZFS master can attach datasets to a uid instead of a single namespace, which would make the holder service unnecessary.
Once that lands in a release, it can go.

## The feature nobody asked for

One part of this project I did not see coming was a feature I never requested.
The first version also had *grace holds*: every day, the host put a hold on the newest snapshot of each of my friend's datasets and released it 14 days later, so a compromised machine on his side could not wipe his recent backups on mine.
It is not a bad idea, but it was on none of our lists.
When the agent compared the zone setups, its main argument against the usual one was that namespace root could release those holds.

I asked whether it was defending the design with a reason I had never included in it.
It was.
We removed the holds, judged the zones against the six rules above, and the argument changed completely.
The agent had not hidden anything; it had just made a scope decision without flagging it, and then reasoned from its own decision as if it were mine.

## What it cannot hide

ZFS encryption protects file contents, not structure.
In the words of [`zfs-load-key(8)`](https://openzfs.github.io/openzfs-docs/man/master/8/zfs-load-key.8.html), ZFS "will not encrypt metadata related to the pool structure, including dataset and snapshot names, dataset hierarchy, properties, file size, file holes, and deduplication tables."
So I can see the names, sizes, and snapshot times of whatever my friend sends me.
Boring dataset names help, and sending without `-p` keeps properties out of the stream.

I can also always delete his copy, because I am root on my own machine.
What I can never do is read it.

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
My friend pushes with nixpkgs' own module:

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

For his TrueNAS box there is a single `zfs-tenant.pyz` on every [release](https://github.com/basnijholt/zfs-tenant/releases), which runs with the Python that TrueNAS already ships, plus a `setup --dry-run` command that prints the exact `zfs` commands to run.
The [getting started guide](https://zfs-tenant.nijho.lt/getting-started/) walks through both.
Sending from TrueNAS is where its built-in tools stop working: replication tasks wrap every remote command in `sh -c`, which the gate refuses, so he pushes with `zfs send` or syncoid instead.

## The first real push

Once my side was deployed, Joe tried it from his TrueNAS box.
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

One thing confused him.
A bare `zfs list` through the gate shows only his root, because the gate fills in the root as the dataset and ZFS does not recurse without `-r`.
He thought the send had failed until he ran `zfs list -r`.

## Tested like everything else

Every security claim in this post is also checked by a two-node NixOS VM test: one machine pushes with real syncoid 2.3.0, through real sshd and the gate, into real OpenZFS 2.4.4 on the other.
Its 17 subtests cover the pushes and pruning, the zone hiding my datasets, the gate failing closed, the delegation limits with and without the gate, a plaintext stream being refused, interrupted receives and restores resuming, and the quota.
It runs on every push in GitHub Actions, next to 193 unit tests.

The VM test earned its keep while I was building this.
It found that incremental sends need `hold` on the sending side, that syncoid only prunes after it has sent something new, and that `sharenfs` cannot be set once a dataset is zoned.

The whole thing is about 770 lines of Python, not counting comments and docstrings, with no dependencies.
The kernel does the actual enforcing: delegation, the quota, and the zone.
The gate only removes the shell, and it is small enough to read in one sitting.

## References

- [zfs-tenant on GitHub](https://github.com/basnijholt/zfs-tenant)
- [zfs-tenant documentation](https://zfs-tenant.nijho.lt)
- [Friend-to-friend TrueNAS backups without the cloud]({{< ref "/post/truenas-remote-backups" >}})
- [Migrating from TrueNAS to NixOS]({{< ref "/post/truenas-to-nixos" >}})
- [The last btrfs machine: migrating my PC to ZFS]({{< ref "/post/btrfs-to-zfs" >}})
- [`zfs-allow(8)`](https://openzfs.github.io/openzfs-docs/man/master/8/zfs-allow.8.html)
- [`zfs-zone(8)`](https://openzfs.github.io/openzfs-docs/man/master/8/zfs-zone.8.html)
- [Sanoid and syncoid](https://github.com/jimsalterjrs/sanoid)
