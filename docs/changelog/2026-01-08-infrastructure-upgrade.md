# Infrastructure Upgrade - 2026-01-08

## Summary

Major infrastructure upgrade transforming the homelab from a single-node K3s cluster to a production-grade HA configuration with comprehensive monitoring and documentation.

## Changes

### K3s HA Cluster Upgrade

**Before:**
- Single control plane (fz-k3s) with SQLite backend
- No redundancy, single point of failure

**After:**
- 3 control planes with embedded etcd quorum
- 1 dedicated worker node
- Automatic failover capability
- Production-grade resilience

**Nodes Added:**
| Node | IP | Role | Host |
|------|-----|------|------|
| wt-k3s | 192.168.1.191 | Control Plane | watchtower |
| sg-k3s-control | 192.168.1.192 | Control Plane | sigil |
| wt-k3s-worker | 192.168.1.194 | Worker | watchtower |

### New Services Deployed

1. **Rancher** (https://rancher.homelab.internal)
   - Kubernetes cluster management
   - Multi-cluster visibility

2. **BookStack** (http://docs.k3s.nox)
   - Documentation platform
   - MySQL backend
   - Auto-updater integration

3. **Homarr** (http://dashboard.k3s.nox)
   - Interactive dashboard
   - Service status monitoring
   - Widget-based customization

4. **Homer** (http://home.k3s.nox)
   - Static dashboard backup
   - YAML-based configuration

5. **Uptime Kuma** (http://uptime.k3s.nox)
   - Service availability monitoring
   - DNS, API, HTTP monitors

### Monitoring Expansion

**node_exporter Deployed To:**
- All 4 Proxmox hosts (fortzero, watchtower, sigil, scryer)
- All VMs with node_exporter capability
- wt-dns (AdGuard DNS server)

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
- wt-docker (consolidated to fz-docker)
- win-badusb-lab (unused)

**Docker Containers Removed (17):**
- From fz-docker: Portainer, Watchtower, duplicated services
- Consolidated monitoring to K3s

**Resources Freed:**
- ~32GB disk space
- 4 fewer VMs to maintain
- Simplified architecture

### DNS Configuration

**AdGuard Home Entries Updated:**
- `*.k3s.nox` → 192.168.1.231 (Traefik LB)
- `*.home.lab` → 192.168.1.231
- `*.homelab.internal` → 192.168.1.231

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
2. Original fz-k3s remains functional
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
