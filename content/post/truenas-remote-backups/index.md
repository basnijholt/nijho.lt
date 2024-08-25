---
title: "💽 Friend-to-Friend TrueNAS Backups: Secure, Decentralized Storage Without the Cloud"
subtitle: "A Step-by-Step Guide to Setting Up Encrypted ZFS Replication with a Trusted Friend"
summary: |
    Learn how to create a secure, decentralized backup system using TrueNAS and ZFS replication.
    This guide shows you how to partner with a friend for mutual backups, leveraging the 
    power of ZFS while maintaining network isolation and data privacy.
projects: []
date: '2024-08-24T00:00:00Z'
draft: false
featured: false

authors:
  - admin

tags:
  - homelab
  - proxmox
  - nas
  - zfs

categories:
  - technology
  - tutorial
  - level:intermediate
---

## The Challenge: Escaping the Cloud

I recently wrote about my [homelab]({{< ref "/post/homelab" >}}) and how I use TrueNAS on my NAS for data storage.
Most self-hosters are looking for ways to "de-cloud" themselves, taking control of their data away from big tech companies, and reducing monthly subscription fees.
One subscription cost that many of us still rely on is cloud storage for backups.
Personally, I use Rclone to back up my most essential data to Backblaze B2, but now that my data is growing, I'm looking for a more cost-effective solution.

Luckily, I have a friend who also uses TrueNAS and is looking for a similar solution.

TrueNAS offers built-in replication tasks that allow us to efficiently replicate our data to another TrueNAS system.
Unfortunately, this requires root access to the remote system, which is a security risk we're not willing to take.

So, how can we set up remote ZFS replication with a friend, maintaining our de-clouded status, without compromising the security of our TrueNAS systems?

## The Requirements

1. Use TrueNAS's built-in replication tasks (uses `zfs send` and `zfs receive` for efficient replication, much faster than `rsync`)
2. Replicate to a friend's system with ZFS capabilities
3. Avoid granting root access to each other's TrueNAS systems
4. Maintain control over the allocated backup space
5. Keep our data private and out of corporate clouds

## The Solution: TrueNAS VM on hypervisor and iSCSI Backup Storage on TrueNAS

After exploring various options, we've found a secure and efficient solution using a hybrid VM setup that keeps us firmly in control of our data. Here's the high-level overview:

1. Create a TrueNAS VM on a local hypervisor (e.g., Proxmox)
2. Set up an iSCSI target on your TrueNAS for backup storage
3. Connect the iSCSI target as an additional disk to the VM and format it with ZFS
4. Give your friend secure access to this VM
5. Your friend sets up replication tasks to this VM's iSCSI-connected storage

## Why This Works

- **Security**: No need for root access on each other's TrueNAS systems and data can be encrypted on the iSCSI storage with fried's keys
- **Performance**: VM OS runs from fast local storage, while backups use dedicated iSCSI storage
- **Flexibility**: Easy to manage and update the VM independently of backup storage
- **Efficiency**: Minimizes data transfer over iSCSI for system operations
- **De-Clouded**: Your data stays between you and your friend, no cloud services involved

## Step-by-Step Setup

### On your main TrueNAS

1. Create a new zvol for backup storage
   - Navigate to Storage > Pools > [Your Pool] > zvols
   - Click "ADD zvol"
   - Name it (e.g., "friend_backup")
   - Set an appropriate size
2. Set up an iSCSI target
   - Go to Sharing > Block Shares (iSCSI)
   - Click "Add" under Targets
   - Give it a name and create
   - Under Extents, click "Add", select the zvol you created
   - Under Associated Targets, add your new target and extent

### On Proxmox

1. Mount the iSCSI in Proxmox
   - Go to Datacenter > Storage > Add > iSCSI
   - Enter your TrueNAS IP and the target name
2. Create a TrueNAS VM
   - Download TrueNAS ISO to `/var/lib/vz/template/iso`
   - Click "Create VM"
   - Select the TrueNAS ISO
   - In the "Hard Disk" step, add two SCSI disks:
     - One on local storage (for OS)
     - One on the iSCSI storage (for backups)
3. Install TrueNAS
   - Start the VM and open console
   - Install TrueNAS on the local disk
4. Configure TrueNAS VM
   - Access the TrueNAS web interface
   - Create a ZFS pool on the iSCSI disk

### Set up secure access

1. Install and configure Tailscale (or preferred VPN)
   - On both your system and the TrueNAS VM
   - Use a self-hosted Headscale server for more control

### For your friend

1. Provide VPN access to the TrueNAS VM
2. They can now set up replication tasks to the VM's iSCSI storage using the TrueNAS web interface and their own encryption keys

### Repeat the process

- Follow the same steps on your friend's system, reversing roles

## Considerations

- **Network**: Ensure your internet connection can handle the data transfer
- **Initial Seeding**: For large datasets, consider initial seeding in person
- **Encryption**: Use encryption when for the replicated datasets and VPN access for added security
- **Testing**: Thoroughly test the setup before relying on it for critical backups
- **Trust**: Choose your backup partner wisely - the other person will have access to the TrueNAS VM but not its data (if encrypted)
- **VM Maintenance**: Regularly update and maintain the VM's operating system

## Conclusion

This friend-to-friend setup offers TrueNAS users an effective approach to remote backups. By creating mutual TrueNAS VMs, we've established a secure, decentralized backup solution with several advantages:

1. **Privacy and Security**: Each friend has their own remote TrueNAS VM, with data remaining private when properly encrypted. Importantly, while you grant your friend access to your network, it's limited to only the backup VM. You can firewall off the rest of your network, maintaining overall system security.

2. **Full ZFS Feature Set**: This setup allows us to use ZFS features like snapshot-based backups, incremental replication, and data integrity checks.

3. **Flexible Backup Strategies**: We can back up entire filesystems and maintain multiple snapshot versions.

4. **De-clouded Solution**: By partnering with a trusted friend, we've created a backup system that keeps our data out of corporate clouds, reducing costs and increasing control.

5. **Scalability**: As data needs grow, we can add additional iSCSI targets in Proxmox and incorporate these new virtual disks into our ZFS pool.

6. **Network Isolation**: Despite allowing access for backups, your main network remains protected. You control exactly what your backup partner can access, limiting potential security risks.

This solution represents a step towards data sovereignty and community-based storage. It's secure, efficient, and independent of large tech companies, while still maintaining tight control over your network access.

Remember to regularly test your backup and restore processes, and periodically review your firewall rules. With this setup, you have a comprehensive, friend-to-friend backup solution that doesn't compromise your overall network security.

Happy backing up!
