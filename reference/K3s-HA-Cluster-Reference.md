# K3s HA Cluster Reference

## Cluster Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    K3s HA Cluster                           │
├─────────────────────────────────────────────────────────────┤
│  Control Plane (etcd quorum)                                │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────────┐       │
│  │   k3s-cp-1    │ │   k3s-cp-2    │ │  k3s-cp-3  │       │
│  │  .1.190     │ │   .1.191    │ │     .1.193       │       │
│  │  (primary)  │ │             │ │                  │       │
│  └─────────────┘ └─────────────┘ └──────────────────┘       │
│                                                             │
│  Workers                                                    │
│  ┌──────────────┐                                           │
│  │ k3s-worker-1│                                           │
│  │    .1.192    │                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

## Quick Access

| Service | URL | Notes |
|---------|-----|-------|
| Rancher | https://rancher.cluster.local | Cluster GUI |
| Grafana | http://grafana.cluster.local | Monitoring |
| Traefik | http://traefik.cluster.local | Ingress dashboard |
| ArgoCD | http://argo.cluster.local | GitOps |

## Node Details

| Node | IP | Role | SSH |
|------|-----|------|-----|
| k3s-cp-1 | 10.0.1.10 | Control Plane (primary) | `ssh admin@k3s-cp-1` |
| k3s-cp-2 | 10.0.1.11 | Control Plane | `ssh admin@k3s-cp-2` |
| k3s-cp-3 | 10.0.1.13 | Control Plane | `ssh admin@k3s-cp-3` |
| k3s-worker-1 | 10.0.1.12 | Worker | `ssh admin@k3s-worker-1` |

## Network

| Resource | IP/Range | Purpose |
|----------|----------|---------|
| MetalLB Pool | 10.0.2.31-239 | LoadBalancer IPs |
| Traefik LB | 10.0.2.31 | Ingress entry point |
| K3s API | 10.0.1.10:6443 | Kubernetes API |
| AdGuard DNS | 10.0.0.2 | DNS server (dns-secondary) |

## Common Commands

```bash
# Check cluster status
ssh admin@k3s-cp-1 "kubectl get nodes -o wide"

# Check all pods
ssh admin@k3s-cp-1 "kubectl get pods -A"

# Check etcd health (run on any control plane)
ssh admin@k3s-cp-1 "sudo k3s etcd-snapshot list"

# View k3s logs
ssh admin@k3s-cp-1 "sudo journalctl -u k3s -f"

# Restart k3s on a node
ssh admin@k3s-cp-1 "sudo systemctl restart k3s"
```

## Important Paths

### On Control Plane Nodes
| Path | Purpose |
|------|---------|
| `/etc/rancher/k3s/k3s.yaml` | Kubeconfig |
| `/var/lib/rancher/k3s/server/node-token` | Join token |
| `/var/lib/rancher/k3s/server/db/` | etcd data |
| `/etc/systemd/system/k3s.service` | K3s service config |

### On Worker Nodes
| Path | Purpose |
|------|---------|
| `/etc/systemd/system/k3s-agent.service` | K3s agent service |

### Local Mac
| Path | Purpose |
|------|---------|
| `~/.kube/config` | Kubeconfig (if copied) |
| `~/Forge/k3s-ha-expansion/` | Setup scripts |

## DNS Configuration

AdGuard at `10.0.0.2` (dns-secondary VM, SSH as root)

**DNS Rewrites:**
- `*.cluster.local` → 10.0.2.31
- `*.cluster.local` → 10.0.2.31
- `*.cluster.local` → 10.0.2.31

**Config file:** `/opt/adguard/conf/AdGuardHome.yaml`

**Restart AdGuard:**
```bash
ssh root@10.0.0.2 "docker restart adguardhome"
```

## Installed Components

| Component | Namespace | Purpose |
|-----------|-----------|---------|
| Traefik | kube-system | Ingress controller |
| MetalLB | metallb-system | LoadBalancer provider |
| cert-manager | cert-manager | TLS certificates |
| Rancher | cattle-system | Cluster management GUI |
| ArgoCD | argocd | GitOps |
| Prometheus/Grafana | observability | Monitoring |

## Homelab Monitoring

Prometheus scrapes metrics from the entire homelab, not just K3s.

### Proxmox Hypervisors (monitored via node_exporter)

| Node | IP | Port |
|------|-----|------|
| proxmox-0 | 10.0.0.10 | 9100 |
| proxmox-1 | 10.0.0.11 | 9100 |
| proxmox-2 | 10.0.0.12 | 9100 |
| proxmox-3 | 10.0.0.13 | 9100 |

### Other VMs (monitored via node_exporter)

| VM | IP | Port |
|----|-----|------|
| dns-secondary | 10.0.0.23 | 9100 |

### Grafana Dashboards

| Dashboard | Description |
|-----------|-------------|
| **Homelab Overview** | Custom dashboard showing all hosts CPU/Memory/Disk |
| **Kubernetes / Nodes** | K3s node metrics |
| **Node Exporter / Nodes** | Detailed per-host metrics |
| **etcd** | etcd cluster health |

Access Grafana: http://grafana.cluster.local
- Username: `admin`
- Password: `changeme`

### Adding New Hosts to Monitoring

1. Install node_exporter on the host:
```bash
ssh root@<host> "apt-get install -y prometheus-node-exporter && systemctl enable --now prometheus-node-exporter"
```

2. Add target to Prometheus scrape config:
```bash
ssh admin@k3s-cp-1 "kubectl get secret additional-scrape-configs -n observability -o jsonpath='{.data.additional-scrape-configs\.yaml}' | base64 -d"
# Edit and reapply the secret, then restart Prometheus
```

## K3s Version

- **Version:** v1.33.3+k3s1
- **Backend:** Embedded etcd (HA mode)
- **Disabled:** servicelb, traefik (using external)

## Credentials

### K3s Join Token
```
K10<TOKEN_REDACTED>::server:<SERVER_TOKEN_REDACTED>
```

### Rancher Bootstrap Password
Get from cluster:
```bash
ssh admin@k3s-cp-1 "kubectl get secret --namespace cattle-system bootstrap-secret -o go-template='{{.data.bootstrapPassword|base64decode}}'"
```

## Troubleshooting

### Node not Ready
```bash
# Check kubelet logs
ssh admin@<node> "sudo journalctl -u k3s -n 100"

# Check node conditions
ssh admin@k3s-cp-1 "kubectl describe node <node-name>"
```

### etcd Issues
```bash
# Check etcd member list
ssh admin@k3s-cp-1 "sudo k3s etcd-snapshot list"

# Create manual snapshot
ssh admin@k3s-cp-1 "sudo k3s etcd-snapshot save --name manual-backup"
```

### MetalLB Not Assigning IPs
```bash
# Check speaker pods
ssh admin@k3s-cp-1 "kubectl get pods -n metallb-system"

# Restart speakers
ssh admin@k3s-cp-1 "kubectl rollout restart daemonset speaker -n metallb-system"
```

### DNS Not Resolving
```bash
# Test against AdGuard directly
nslookup rancher.cluster.local 10.0.0.2

# Restart AdGuard
ssh root@10.0.0.2 "docker restart adguardhome"
```

---
*Last updated: 2026-01-07*
*Setup scripts: ~/Forge/k3s-ha-expansion/*
