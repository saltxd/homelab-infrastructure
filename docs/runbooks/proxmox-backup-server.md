# Proxmox Backup Server (PBS)

## Overview

PBS provides deduplicated, incremental backups for all Proxmox VMs across the cluster. Installed on proxmox-0 using external USB SSD storage.

## Server Details

| Property | Value |
|----------|-------|
| Container | LXC 100 on proxmox-0 |
| IP Address | 10.0.0.20 |
| Web UI | https://10.0.0.20:8007 |
| Login | root@pam / CHANGE_ME_PBS_PASSWORD |
| Datastore | main (/mnt/datastore) |
| Storage | 465GB USB SSD (ext4) |
| PVE Storage Name | pbs-main |

## Retention Policy

Configured via daily prune job:
- **keep-last:** 2
- **keep-daily:** 7
- **keep-weekly:** 4
- **keep-monthly:** 3

## Usage

### Manual Backup (single VM)
```bash
# From any Proxmox node
vzdump <VMID> --storage pbs-main --mode snapshot --compress zstd
```

### Scheduled Backups
Configure backup jobs in Proxmox Datacenter > Backup using storage `pbs-main`.

### Restore VM
```bash
# List available backups
pvesm list pbs-main

# Restore to original location
qmrestore <backup-path> <VMID>

# Restore to different node
qmrestore <backup-path> <VMID> --storage <target-storage>
```

## Benefits

- **Deduplication:** Similar VMs (K3s nodes) share common data blocks - expect 10-30x space savings
- **Incremental:** Only changed data transferred after first backup
- **Verification:** Built-in backup verification
- **Central storage:** All backups in one location vs scattered across nodes

## Maintenance

### Check datastore status
```bash
ssh proxmox-0 "pct exec 100 -- proxmox-backup-manager datastore status main"
```

### Verify backups
```bash
ssh proxmox-0 "pct exec 100 -- proxmox-backup-manager verify main"
```

### Garbage collection
```bash
ssh proxmox-0 "pct exec 100 -- proxmox-backup-manager garbage-collection run main"
```

## Physical Setup

USB NVMe enclosure (SSK RTL9210B chip) connected to proxmox-0 USB 3.0 port. Drive is bind-mounted into the PBS container at /mnt/datastore.

## Storage Notes

The 465GB SSD is currently allocated for backups only. If you want to use some capacity for other purposes (e.g., Plex), consider:
- Reducing retention (fewer keep-* values)
- Being selective about which VMs to backup to PBS
- Using vzdump to local storage for non-critical VMs

---
*Created: 2026-02-01*
