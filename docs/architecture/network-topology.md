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
                         │  10.0.0.1  │
                         └───────┬───────┘
                                 │
                    ┌────────────┴────────────┐
                    │     10.0.0.0/24      │
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
| proxmox-0 | 10.0.0.10 | Primary hypervisor |
| proxmox-1 | 10.0.0.11 | Secondary hypervisor |
| proxmox-2 | 10.0.0.12 | Tertiary hypervisor |
| proxmox-3 | 10.0.0.13 | Quaternary hypervisor |

### K3s Cluster Nodes
| Node | IP | Role |
|------|-----|------|
| k3s-cp-1 | 10.0.1.10 | Control plane (primary) |
| k3s-cp-2 | 10.0.1.11 | Control plane |
| k3s-cp-3 | 10.0.1.12 | Control plane |
| k3s-worker-1 | 10.0.1.14 | Worker |

### Infrastructure VMs
| VM | IP | Purpose |
|----|-----|---------|
| gateway | 10.0.0.20 | Gateway/VPN |
| docker-host | 10.0.0.21 | Docker host (legacy) |
| dns-primary | 10.0.0.22 | AdGuard DNS (backup) |
| dns-secondary | 10.0.0.23 | AdGuard DNS (primary) |
| homebridge | 10.0.0.24 | Homebridge |
| scraper | 10.0.2.35 | Web scraping |

### Special IPs
| IP | Purpose |
|----|---------|
| 10.0.0.2 | AdGuard admin (redirects to dns-secondary) |
| 10.0.2.31 | Traefik LoadBalancer (MetalLB) |
| 100.64.0.1 | app-server (Tailscale) |

### MetalLB Pool
- **Range**: 10.0.2.30 - 10.0.2.50
- **Mode**: Layer 2
- **Currently Allocated**: 10.0.2.31 (Traefik)

## DNS Configuration

### AdGuard Home Servers
- **Primary**: dns-secondary (10.0.0.23)
- **Secondary**: dns-primary (10.0.0.22)

### DNS Rewrites
| Domain Pattern | Target IP |
|----------------|-----------|
| `*.cluster.local` | 10.0.2.31 |
| `*.cluster.local` | 10.0.2.31 |
| `*.cluster.local` | 10.0.2.31 |
| `*.nox` | 10.0.0.21 |
| `adguard-primary.cluster.local` | 10.0.0.22 |
| `adguard-secondary.cluster.local` | 10.0.0.23 |

### Service URLs
| Service | URL |
|---------|-----|
| Rancher | https://rancher.cluster.local |
| Grafana | http://grafana.cluster.local |
| Prometheus | http://prometheus.cluster.local |
| BookStack | http://docs.cluster.local |
| Homarr | http://dashboard.cluster.local |
| Homer | http://home.cluster.local |
| Uptime Kuma | http://uptime.cluster.local |
| ArgoCD | http://argo.cluster.local |

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
      ▼ (DNS: *.cluster.local → 10.0.2.31)
┌─────────────────┐
│    MetalLB      │
│  10.0.2.31  │
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
