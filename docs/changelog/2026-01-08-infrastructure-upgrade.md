# Infrastructure Upgrade - 2026-01-08

## Summary

Major infrastructure upgrade transforming the homelab from a single-node K3s cluster to a production-grade HA configuration with comprehensive monitoring and documentation.

## Changes

### K3s HA Cluster Upgrade

**Before:**
- Single control plane (k3s-cp-1) with SQLite backend
- No redundancy, single point of failure

**After:**
- 3 control planes with embedded etcd quorum
- 1 dedicated worker node
- Automatic failover capability
- Production-grade resilience

**Nodes Added:**
| Node | IP | Role | Host |
|------|-----|------|------|
| k3s-cp-2 | 10.0.1.11 | Control Plane | proxmox-1 |
| k3s-cp-3 | 10.0.1.12 | Control Plane | proxmox-2 |
| k3s-worker-1 | 10.0.1.14 | Worker | proxmox-1 |

### New Services Deployed

1. **Rancher** (https://rancher.cluster.local)
   - Kubernetes cluster management
   - Multi-cluster visibility

2. **BookStack** (http://docs.cluster.local)
   - Documentation platform
   - MySQL backend
   - Auto-updater integration

3. **Homarr** (http://dashboard.cluster.local)
   - Interactive dashboard
   - Service status monitoring
   - Widget-based customization

4. **Homer** (http://home.cluster.local)
   - Static dashboard backup
   - YAML-based configuration

5. **Uptime Kuma** (http://uptime.cluster.local)
   - Service availability monitoring
   - DNS, API, HTTP monitors

### Monitoring Expansion

**node_exporter Deployed To:**
- All 4 Proxmox hosts (proxmox-0, proxmox-1, proxmox-2, proxmox-3)
- All VMs with node_exporter capability
- dns-secondary (AdGuard DNS server)

**Prometheus Configuration:**
- Added scrape configs for all infrastructure
- Custom job definitions for proxmox-nodes, homelab-vms

**Grafana:**
- Added Homelab Overview dashboard
- Configured additional datasources

### Automation Built

**BookStack Auto-Updater** (`~/Forge/bookstack-updater/`)
- Python script with Jinja2 templates
- Parses audit results from `~/audit-results/`
- Updates BookStack via REST API
- Discord webhook notifications
- Weekly cron (Sundays 2am)

**Files Created:**
- `bookstack_updater.py` - Main script
- `init_bookstack.py` - Initial setup
- `config.yaml` - Configuration
- `templates/*.md.j2` - Documentation templates

### Infrastructure Cleanup

**VMs Deleted (4):**
- fz-vault (unused Vault instance)
- wt-zabbix (replaced by Prometheus)
- wt-docker (consolidated to docker-host)
- win-badusb-lab (unused)

**Docker Containers Removed (17):**
- From docker-host: Portainer, Watchtower, duplicated services
- Consolidated monitoring to K3s

**Resources Freed:**
- ~32GB disk space
- 4 fewer VMs to maintain
- Simplified architecture

### DNS Configuration

**AdGuard Home Entries Updated:**
- `*.cluster.local` → 10.0.2.31 (Traefik LB)
- `*.cluster.local` → 10.0.2.31
- `*.cluster.local` → 10.0.2.31

### Configuration Files Created

**Manifests:**
- `bookstack.yaml` - BookStack + MySQL
- `homarr.yaml` - Homarr dashboard
- `homer-config.yaml` - Homer ConfigMap

**Documentation:**
- K3s HA Cluster Reference
- Service inventory
- Network topology
- Runbooks

## Lessons Learned

1. **etcd Migration**: Requires careful coordination, backup first
2. **Homarr v1.x**: Uses port 7575, not 3000; needs 1Gi+ memory
3. **BookStack**: Requires APP_KEY for Laravel encryption
4. **NFS Mounts**: Worker nodes need nfs-common installed
5. **DNS Wildcards**: Simplify ingress management

## Rollback Plan

If issues arise:
1. Control planes can be removed from cluster
2. Original k3s-cp-1 remains functional
3. etcd can be restored from snapshot
4. Services persist on NFS storage

## Verification Checklist

- [x] All 4 nodes showing Ready
- [x] etcd members healthy (3/3)
- [x] All services responding HTTP 200
- [x] Prometheus scraping all targets
- [x] Grafana dashboards loading
- [x] BookStack accessible and documented
- [x] Homarr dashboard configured
- [x] DNS resolution working

## Next Steps

1. Set up automated etcd snapshots
2. Configure alerting rules in Prometheus
3. Add TLS certificates for HTTPS
4. Implement backup automation
5. Create disaster recovery runbook

---

*This changelog documents work completed on January 7-8, 2026*
