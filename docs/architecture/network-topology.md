# Network Topology

## Overview

The homelab network consists of a single flat subnet with service segmentation via DNS and ingress routing.

## Network Diagram

```
                              Internet
                                  │
                                  ▼
                         ┌───────────────┐
                         │    Router     │
                         │  192.168.1.1  │
                         └───────┬───────┘
                                 │
                    ┌────────────┴────────────┐
                    │     192.168.1.0/24      │
                    │      Main Network       │
                    └────────────┬────────────┘
                                 │
     ┌───────────────────────────┼───────────────────────────┐
     │                           │                           │
     ▼                           ▼                           ▼
┌─────────────┐           ┌─────────────┐           ┌─────────────┐
│  Proxmox    │           │   DNS       │           │  K3s LB     │
│  Hosts      │           │  Servers    │           │  (Traefik)  │
│ .185-.189   │           │  .206,.211  │           │   .231      │
└─────────────┘           └─────────────┘           └─────────────┘
```

## IP Allocation

### Proxmox Hosts
| Host | IP | Role |
|------|-----|------|
| fortzero | 192.168.1.185 | Primary hypervisor |
| watchtower | 192.168.1.186 | Secondary hypervisor |
| sigil | 192.168.1.188 | Tertiary hypervisor |
| scryer | 192.168.1.189 | Quaternary hypervisor |

### K3s Cluster Nodes
| Node | IP | Role |
|------|-----|------|
| fz-k3s | 192.168.1.190 | Control plane (primary) |
| wt-k3s | 192.168.1.191 | Control plane |
| sg-k3s-control | 192.168.1.192 | Control plane |
| wt-k3s-worker | 192.168.1.194 | Worker |

### Infrastructure VMs
| VM | IP | Purpose |
|----|-----|---------|
| fz-gate | 192.168.1.201 | Gateway/VPN |
| fz-docker | 192.168.1.205 | Docker host (legacy) |
| fz-dns | 192.168.1.206 | AdGuard DNS (backup) |
| wt-dns | 192.168.1.211 | AdGuard DNS (primary) |
| fz-hb | 192.168.1.216 | Homebridge |
| scr-scraper | 192.168.1.235 | Web scraping |

### Special IPs
| IP | Purpose |
|----|---------|
| 192.168.1.2 | AdGuard admin (redirects to wt-dns) |
| 192.168.1.231 | Traefik LoadBalancer (MetalLB) |
| 100.69.25.25 | sg-scribe (Tailscale) |

### MetalLB Pool
- **Range**: 192.168.1.230 - 192.168.1.250
- **Mode**: Layer 2
- **Currently Allocated**: 192.168.1.231 (Traefik)

## DNS Configuration

### AdGuard Home Servers
- **Primary**: wt-dns (192.168.1.211)
- **Secondary**: fz-dns (192.168.1.206)

### DNS Rewrites
| Domain Pattern | Target IP |
|----------------|-----------|
| `*.k3s.nox` | 192.168.1.231 |
| `*.home.lab` | 192.168.1.231 |
| `*.homelab.internal` | 192.168.1.231 |
| `*.nox` | 192.168.1.205 |
| `adguard-fz.nox` | 192.168.1.206 |
| `adguard-wt.nox` | 192.168.1.211 |

### Service URLs
| Service | URL |
|---------|-----|
| Rancher | https://rancher.homelab.internal |
| Grafana | http://grafana.k3s.nox |
| Prometheus | http://prometheus.k3s.nox |
| BookStack | http://docs.k3s.nox |
| Homarr | http://dashboard.k3s.nox |
| Homer | http://home.k3s.nox |
| Uptime Kuma | http://uptime.k3s.nox |
| ArgoCD | http://argo.k3s.nox |

## Kubernetes Networking

### Pod Network
- **CNI**: Flannel
- **Mode**: VXLAN
- **Pod CIDR**: 10.42.0.0/16

### Service Network
- **Service CIDR**: 10.43.0.0/16
- **Cluster DNS**: 10.43.0.10

### Ingress Flow

```
Client Request
      │
      ▼ (DNS: *.k3s.nox → 192.168.1.231)
┌─────────────────┐
│    MetalLB      │
│  192.168.1.231  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Traefik      │
│ (Ingress Ctrl)  │
└────────┬────────┘
         │ (Host-based routing)
         ▼
┌─────────────────┐
│  K8s Service    │
│  (ClusterIP)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Pods        │
└─────────────────┘
```

## Firewall Rules

### Required Ports (K3s)
| Port | Protocol | Purpose |
|------|----------|---------|
| 6443 | TCP | K3s API Server |
| 2379-2380 | TCP | etcd client/peer |
| 10250 | TCP | Kubelet API |
| 8472 | UDP | Flannel VXLAN |

### Service Ports
| Port | Protocol | Service |
|------|----------|---------|
| 80 | TCP | HTTP (Traefik) |
| 443 | TCP | HTTPS (Traefik) |
| 9100 | TCP | node_exporter |
| 9090 | TCP | Prometheus |
| 3000 | TCP | Grafana |
