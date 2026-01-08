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
| k3s-cp-1 | Control Plane (Primary) | 10.0.1.10 | proxmox-0 |
| k3s-cp-2 | Control Plane | 10.0.1.11 | proxmox-1 |
| k3s-cp-3 | Control Plane | 10.0.1.12 | proxmox-2 |
| k3s-worker-1 | Worker | 10.0.1.14 | proxmox-1 |

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Rancher | https://rancher.cluster.local | Cluster management |
| Grafana | http://grafana.cluster.local | Metrics & dashboards |
| Prometheus | http://prometheus.cluster.local | Metrics collection |
| BookStack | http://docs.cluster.local | Documentation |
| Homarr | http://dashboard.cluster.local | Interactive dashboard |
| Homer | http://home.cluster.local | Static dashboard |
| Uptime Kuma | http://uptime.cluster.local | Status monitoring |

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
- **proxmox-0** (10.0.0.10) - Primary hypervisor
- **proxmox-1** (10.0.0.11) - Secondary hypervisor
- **proxmox-2** (10.0.0.12) - Tertiary hypervisor
- **proxmox-3** (10.0.0.13) - Quaternary hypervisor

### Network
- **MetalLB**: 10.0.2.30-250
- **Traefik LB**: 10.0.2.31
- **DNS**: AdGuard Home (dns-secondary: 10.0.0.23, dns-primary: 10.0.0.22)

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
ssh k3s-cp-1 "sudo etcdctl member list"
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
