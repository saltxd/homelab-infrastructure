# Homelab Infrastructure

Private repository for K3s HA cluster and homelab infrastructure management.

## Cluster Overview

- **4-node K3s HA cluster** with embedded etcd
- **3 control planes** with etcd quorum for high availability
- **1 worker node** for workload scheduling
- Production-grade monitoring and observability
- Self-documenting infrastructure with BookStack

## Quick Links

- [K3s HA Architecture](docs/architecture/k3s-ha-architecture.md)
- [Service Inventory](docs/architecture/service-inventory.md)
- [Network Topology](docs/architecture/network-topology.md)
- [Cluster Operations Runbook](docs/runbooks/cluster-operations.md)
- [Setup Guides](docs/setup-guides/)

## Cluster Nodes

| Node | Role | IP | Location |
|------|------|-----|----------|
| fz-k3s | Control Plane (Primary) | 192.168.1.190 | fortzero |
| wt-k3s | Control Plane | 192.168.1.191 | watchtower |
| sg-k3s-control | Control Plane | 192.168.1.192 | sigil |
| wt-k3s-worker | Worker | 192.168.1.194 | watchtower |

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Rancher | https://rancher.homelab.internal | Cluster management |
| Grafana | http://grafana.k3s.nox | Metrics & dashboards |
| Prometheus | http://prometheus.k3s.nox | Metrics collection |
| BookStack | http://docs.k3s.nox | Documentation |
| Homarr | http://dashboard.k3s.nox | Interactive dashboard |
| Homer | http://home.k3s.nox | Static dashboard |
| Uptime Kuma | http://uptime.k3s.nox | Status monitoring |

## Repository Structure

```
homelab-infrastructure/
├── k3s/                    # Kubernetes manifests and configs
│   ├── manifests/          # Service deployments
│   ├── node-configs/       # Per-node configuration
│   └── cluster-info/       # Cluster state documentation
├── automation/             # Automation scripts and tools
│   ├── bookstack-updater/  # Auto-documentation system
│   ├── homelab-audit/      # Infrastructure audit scripts
│   └── cleanup-scripts/    # Maintenance scripts
├── monitoring/             # Monitoring stack configs
│   ├── prometheus/         # Prometheus configuration
│   ├── grafana/            # Dashboards and datasources
│   └── node-exporter/      # Node exporter deployment
├── configs/                # Infrastructure configs
│   ├── dns/                # AdGuard DNS entries
│   ├── ssh/                # SSH configuration
│   └── cron/               # Scheduled jobs
├── docs/                   # Documentation
│   ├── architecture/       # System architecture
│   ├── setup-guides/       # Deployment guides
│   ├── runbooks/           # Operational procedures
│   └── changelog/          # Change history
└── reference/              # Quick reference docs
```

## Infrastructure

### Proxmox Cluster (4 nodes)
- **fortzero** (192.168.1.185) - Primary hypervisor
- **watchtower** (192.168.1.186) - Secondary hypervisor
- **sigil** (192.168.1.188) - Tertiary hypervisor
- **scryer** (192.168.1.189) - Quaternary hypervisor

### Network
- **MetalLB**: 192.168.1.230-250
- **Traefik LB**: 192.168.1.231
- **DNS**: AdGuard Home (wt-dns: 192.168.1.211, fz-dns: 192.168.1.206)

## Automation

### BookStack Auto-Updater
Automatically updates documentation weekly (Sundays 2am):
```bash
cd ~/Forge/bookstack-updater
./bookstack_updater.py --audit --update --notify
```

### Homelab Audit
Collects infrastructure state:
```bash
~/homelab-audit.sh
```

## Maintenance

### Check Cluster Health
```bash
kubectl get nodes
kubectl get pods -A
```

### Check etcd Status
```bash
ssh fz-k3s "sudo etcdctl member list"
```

### View Logs
```bash
kubectl logs -n <namespace> deployment/<name>
```

## Backups

- K3s cluster: etcd snapshots (automatic)
- BookStack: MySQL dumps + uploads volume
- Configs: This Git repository

---

Last Updated: 2026-01-08
