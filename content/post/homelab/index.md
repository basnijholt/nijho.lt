---
title: "🔧 My Homelab: from a single Raspberry Pi to a Proxmox cluster and a dedicated NAS"
subtitle: Exploring the evolution of my homelab setup, from Home Assistant on a Raspberry Pi to a Proxmox cluster and dedicated NAS
summary: An overview of my journey from using a Raspberry Pi for Home Assistant to creating a Proxmox cluster and dedicated NAS for running various services efficiently.
projects: []
date: '2024-07-06T00:00:00Z'
draft: false
featured: false

authors:
  - admin

tags:
  - homelab
  - proxmox
  - nas
  - docker
  - home-assistant
  - zfs

categories:
  - technology
  - tutorial
  - level:intermediate
---

In 2020, I began my homelab journey with a simple yet powerful setup: Home Assistant running on Proxmox on a NUC8i3BEH.
My Home Assistant instance, with over 100 automations and about 20 addons (docker containers), had outgrown the capabilities of my Raspberry Pi 4, leading me to upgrade to the NUC8i3BEH.
You can check out my [Home Assistant configuration](https://github.com/basnijholt/home-assistant-config/).

This system was more than sufficient for running Home Assistant—arguably overkill.
However, because I passionately develop addons and custom components, I needed the ability to quickly restart and reload everything while debugging.
For a long time, I ran Proxmox, mainly because the Home Assistant community recommended it, but I only used it to host one extra Ubuntu VM and Home Assistant OS.

In 2022, I stumbled upon the [Proxmox VE Helper-Scripts](https://github.com/tteck/Proxmox) by tteck, which got me interested in the whole homelabber/self-hosting community.
These scripts opened a new world of possibilities.
With them, I expanded my Proxmox environment to run 25 different VMs and LXC containers, each performing a variety of tasks, from DNS servers and reverse proxies to local dashboards and backup software.

Initially, I used an external 2 TB drive for storage, but it quickly became insufficient as my data needs grew.
After some research, I found the [HP EliteDesk 800 G4 SFF](https://support.hp.com/id-en/document/c06047207), a renewed enterprise-grade desktop with slots for two 3.5-inch drives.
At approximately $160, it offered excellent specs for a budget-friendly price.
I decided to create a TrueNAS VM on this machine and passed through two 16TB renewed enterprise-level HDDs, which I had purchased from serverpartdeals.com.
I chose these drives based on their reliability as reported in the [BackBlaze drive stats](https://www.backblaze.com/blog/backblaze-drive-stats-for-2023/).

When I got the HP, I created a Proxmox cluster and was very excited about how easy it was to migrate containers and VMs from one machine to the other.
However, I soon encountered a significant drawback: enterprise drives are notably loud.
Since I had my Proxmox "cluster" (just the two machines) running behind the TV, the loudness was noticeable and disruptive.
This noise was just the beginning of my troubles.
The NFS server on the TrueNAS VM often crashed, causing the entire Proxmox system to lock up.
Initially, I mounted the NFS drives directly on the Proxmox host and used bind-mounts to pass through the drives.
Due to the locking behavior of NFS, any problem would cause the entire system to lock up.
To prevent this, I started to use [autofs](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/storage_administration_guide/nfs-autofs) to mount the drives in the LXC containers and VMs instead.
This worked fine until Proxmox started its periodic backups.
Any issue with the NFS during backup caused the whole process to hang, locking up the VMs and LXC containers.
This could be partially avoided by using the "stop" backup mode, but it still resulted in almost daily debugging sessions where I had to restart Proxmox-related services.

After running all services as LXC containers, I realized that updating them and keeping up with all security updates was labor-intensive.
So, I started to look into migrating everything to Docker Compose.
This transition turned out great because I could manage my config files in a git repo and keep the relevant data separate, streamlining updates and maintenance.

To resolve these issues and because I was having a lot of fun, I decided to build a dedicated NAS running TrueNAS Scale, not that I *really* needed one, but mostly because I could.
This new setup included high-performance components, ensuring both stability and quiet operation.
I used "Manufacturer Recertified" [Western Digital Ultrastar DC HC550 HDDs](https://www.westerndigital.com/products/internal-drives/data-center-drives/ultrastar-dc-hc550-hdd?sku=0F38356), known for their reliability and performance.
I have 6 x 16TB = 96TB now with the option to add 2 more 3.5" drives, 2 nvme M.2 drives, and 1 SATA 2.5" SDD.
Now, I run all services that previously relied on NFS locally on TrueNAS via a Debian [systemd-nspawn container](https://wiki.debian.org/nspawn) managed with a new script called [Jailmaker](https://github.com/Jip-Hop/jailmaker), which leverages the systemd-nspawn program in TrueNAS Scale (not to be confused with FreeBSD jails).
Inside this systemd-nspawn container, I run Debian with Docker.
For managing Docker Compose files, I use [Dockge](https://github.com/louislam/dockge), which provides a nice web UI for easy management.

Along the way, I got familiar with ZFS and grew to love it for its amazing snapshotting and data integrity features.
ZFS has been a game-changer, providing robust data protection and ease of management.
Initially, [I used mirrored vdevs](https://jrs-s.net/2015/02/06/zfs-you-should-use-mirror-vdevs-not-raidz/), but I recently switched to RAIDZ2 for the added storage capacity and [the promise of OpenZFS 2.3 supporting expansion of RAIDZ vdevs](https://github.com/openzfs/zfs/pull/15022#issuecomment-1802428899).
I also use ZFS for my Proxmox VMs and LXC containers, who's backups I store on the NAS via rsync in a cronjob to another jail running plain Debian (no more NFS on the Proxmox host for me...)

This journey from a simple NUC running Home Assistant to a Proxmox cluster and dedicated NAS has been very time-consuming but a lot of fun.
The lessons learned and the improvements in stability and performance have made the effort worthwhile.
If you're considering building your own homelab, investing in reliable hardware and being prepared for a bit of trial and error can make all the difference.

For completeness, here are the components for each machine in my homelab:

### NUC Components

| Name         | Full Name                   | Server | Price  | Quantity | Cost   | Date       |
| ------------ | --------------------------- | ------ | ------ | -------- | ------ | ---------- |
| NUC8i3BEH    | Intel NUC Kit NUC8i3BEH     | NUC    | 278.3  | 1        | 278.3  | 2020-02-22 |
| 500GB M2 SSD | Samsung 970 EVO M.2 500GB   | NUC    | 94.99  | 1        | 94.99  | 2020-02-21 |
| 32 GB RAM    | TEAMGROUP 32GB DDR4 3200MHz | NUC    | 58.99  | 1        | 58.99  | 2024-05-01 |
| 4TB SSD      | Crucial P3 Plus 4TB NVMe    | NUC    | 226.99 | 1        | 226.99 | 2024-04-27 |
<!-- | 16 GB DDR4   | Crucial 8GB DDR4 2400 MT/s  | NUC    | 25.52  | 2        | 51.04  | 2020-02-21 | -->

### HP Components

| Name                    | Full Name                   | Server | Price | Quantity | Cost   | Date       |
| ----------------------- | --------------------------- | ------ | ----- | -------- | ------ | ---------- |
| 64 GB RAM               | TEAMGROUP 32GB DDR4 3200MHz | HP     | 57.99 | 2        | 115.98 | 2024-05-02 |
| HP EliteDesk 800 G4 SFF | HP EliteDesk 800 G4 SFF     | HP     | 164   | 1        | 164    | 2024-04-27 |
<!-- | SDD enclosure           | UGREEN SSD Enclosure        | HP     | 16.98 | 1        | 16.98  | 2024-04-27 | -->


### NAS Components

| Name           | Full Name                               | Server | Price  | Quantity | Cost   | Date       |
| -------------- | --------------------------------------- | ------ | ------ | -------- | ------ | ---------- |
| 16 TB HDD      | Western Digital Ultrastar DC HC550 16TB | NAS    | 159.99 | 2        | 319.98 | 2024-05-01 |
| 16 TB HDD      | Western Digital Ultrastar DC HC550 16TB | NAS    | 187.5  | 4        | 750    | 2024-06-21 |
| Motherboard    | Q670 8-bay NAS motherboard              | NAS    | 203.21 | 1        | 203.21 | 2024-06-22 |
| CPU i5 13500T  | Intel Core i5-13500T                    | NAS    | 180.88 | 1        | 180.88 | 2024-06-22 |
| PSU SFX        | FSP Dagger Pro 650W                     | NAS    | 87.13  | 1        | 87.13  | 2024-06-21 |
| Jonsbo N3 case | JONSBO N3 Mini-ITX NAS Case             | NAS    | 187.51 | 1        | 187.51 | 2024-06-16 |
| CPU cooler     | Thermalright AXP90 X36 CPU cooler       | NAS    | 21.83  | 1        | 21.83  | 2024-06-25 |
| 64 GB DDR5 RAM | CORSAIR VENGEANCE 64GB DDR5             | NAS    | 162.13 | 1        | 162.13 | 2024-06-29 |

Notes on the NAS components:

- The 13500T is a 35W TDP CPU I bought on eBay, which will help keep the system cool and quiet.
- I bought the motherboard from AliExpress because it seems to be the only mini-ITX motherboard that supports 8 SATA drives, and also comes with 2x2.5GbE ports, 3xM.2 slots, and a full sized PCIe slot.
- The motherboard uses Intel I225-V 2.5GbE controllers, which are notoriously bad, initially `iperf3` maxed out at 100Mbps. The internet is full with people complaining about these controllers auto-negotiating to 100Mbps, however, for me it showed 1Gbps. After trying all suggestions I could find (there are few), as a last resort I connecting the NAS directly to my ASUS XT8 router instead of the NETGEAR GS305 switch, and now I got 1Gbps speeds. So I bought a new managed TL-SG108E switch, which now also gives me 1Gbps speeds. I'm not sure what the issue was, but I'm happy it's resolved.
