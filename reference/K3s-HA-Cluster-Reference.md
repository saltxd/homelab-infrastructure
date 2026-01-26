# K3s HA Cluster Reference

## Cluster Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    K3s HA Cluster                           │
├─────────────────────────────────────────────────────────────┤
│  Control Plane (etcd quorum)                                │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────────┐       │
│  │   fz-k3s    │ │   wt-k3s    │ │  sg-k3s-control  │       │
│  │  .1.190     │ │   .1.191    │ │     .1.193       │       │
│  │  (primary)  │ │             │ │                  │       │
│  └─────────────┘ └─────────────┘ └──────────────────┘       │
│                                                             │
│  Workers                                                    │
│  ┌──────────────┐                                           │
│  │ wt-k3s-worker│                                           │
│  │    .1.192    │                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

## Quick Access

| Service | URL | Notes |
|---------|-----|-------|
| Rancher | https://rancher.homelab.internal | Cluster GUI |
| Grafana | http://grafana.home.lab | Monitoring |
| Traefik | http://traefik.k3s.nox | Ingress dashboard |
| ArgoCD | http://argo.k3s.nox | GitOps |

## Node Details

| Node | IP | Role | SSH |
|------|-----|------|-----|
| fz-k3s | 192.168.1.190 | Control Plane (primary) | `ssh mburkholz@fz-k3s` |
| wt-k3s | 192.168.1.191 | Control Plane | `ssh mburkholz@wt-k3s` |
| sg-k3s-control | 192.168.1.193 | Control Plane | `ssh mburkholz@sg-k3s-control` |
| wt-k3s-worker | 192.168.1.192 | Worker | `ssh mburkholz@wt-k3s-worker` |

## Network

| Resource | IP/Range | Purpose |
|----------|----------|---------|
| MetalLB Pool | 192.168.1.231-239 | LoadBalancer IPs |
| Traefik LB | 192.168.1.231 | Ingress entry point |
| K3s API | 192.168.1.190:6443 | Kubernetes API |
| AdGuard DNS | 192.168.1.2 | DNS server (wt-dns) |

## Common Commands

```bash
# Check cluster status
ssh mburkholz@fz-k3s "kubectl get nodes -o wide"

# Check all pods
ssh mburkholz@fz-k3s "kubectl get pods -A"

# Check etcd health (run on any control plane)
ssh mburkholz@fz-k3s "sudo k3s etcd-snapshot list"

# View k3s logs
ssh mburkholz@fz-k3s "sudo journalctl -u k3s -f"

# Restart k3s on a node
ssh mburkholz@fz-k3s "sudo systemctl restart k3s"
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

AdGuard at `192.168.1.2` (wt-dns VM, SSH as root)

**DNS Rewrites:**
- `*.homelab.internal` → 192.168.1.231
- `*.k3s.nox` → 192.168.1.231
- `*.home.lab` → 192.168.1.231

**Config file:** `/opt/adguard/conf/AdGuardHome.yaml`

**Restart AdGuard:**
```bash
ssh root@192.168.1.2 "docker restart adguardhome"
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
| fortzero | 192.168.1.185 | 9100 |
| watchtower | 192.168.1.186 | 9100 |
| sigil | 192.168.1.188 | 9100 |
| scryer | 192.168.1.189 | 9100 |

### Other VMs (monitored via node_exporter)

| VM | IP | Port |
|----|-----|------|
| wt-dns | 192.168.1.211 | 9100 |

### Grafana Dashboards

| Dashboard | Description |
|-----------|-------------|
| **Homelab Overview** | Custom dashboard showing all hosts CPU/Memory/Disk |
| **Kubernetes / Nodes** | K3s node metrics |
| **Node Exporter / Nodes** | Detailed per-host metrics |
| **etcd** | etcd cluster health |

Access Grafana: http://grafana.home.lab
- Username: `admin`
- Password: `<set during helm install>`

### Adding New Hosts to Monitoring

1. Install node_exporter on the host:
```bash
ssh root@<host> "apt-get install -y prometheus-node-exporter && systemctl enable --now prometheus-node-exporter"
```

2. Add target to Prometheus scrape config:
```bash
ssh mburkholz@fz-k3s "kubectl get secret additional-scrape-configs -n observability -o jsonpath='{.data.additional-scrape-configs\.yaml}' | base64 -d"
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
ssh mburkholz@fz-k3s "kubectl get secret --namespace cattle-system bootstrap-secret -o go-template='{{.data.bootstrapPassword|base64decode}}'"
```

## Troubleshooting

### Node not Ready
```bash
# Check kubelet logs
ssh mburkholz@<node> "sudo journalctl -u k3s -n 100"

# Check node conditions
ssh mburkholz@fz-k3s "kubectl describe node <node-name>"
```

### etcd Issues
```bash
# Check etcd member list
ssh mburkholz@fz-k3s "sudo k3s etcd-snapshot list"

# Create manual snapshot
ssh mburkholz@fz-k3s "sudo k3s etcd-snapshot save --name manual-backup"
```

### MetalLB Not Assigning IPs
```bash
# Check speaker pods
ssh mburkholz@fz-k3s "kubectl get pods -n metallb-system"

# Restart speakers
ssh mburkholz@fz-k3s "kubectl rollout restart daemonset speaker -n metallb-system"
```

### DNS Not Resolving
```bash
# Test against AdGuard directly
nslookup rancher.homelab.internal 192.168.1.2

# Restart AdGuard
ssh root@192.168.1.2 "docker restart adguardhome"
```

---
*Last updated: 2026-01-07*
*Setup scripts: ~/Forge/k3s-ha-expansion/*
