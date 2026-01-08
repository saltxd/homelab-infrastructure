# K3s HA Cluster Architecture

## Overview

The homelab runs a production-grade 4-node K3s Kubernetes cluster with high availability through embedded etcd consensus.

## Cluster Topology

```
                    ┌─────────────────────────────────────┐
                    │         K3s HA Cluster              │
                    │      (Embedded etcd Quorum)         │
                    └─────────────────────────────────────┘
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        │                            │                            │
        ▼                            ▼                            ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│   fz-k3s      │          │   wt-k3s      │          │ sg-k3s-control│
│  (Primary)    │◄────────►│  (Secondary)  │◄────────►│  (Tertiary)   │
│ 192.168.1.190 │          │ 192.168.1.191 │          │ 192.168.1.192 │
│   fortzero    │          │  watchtower   │          │    sigil      │
└───────────────┘          └───────────────┘          └───────────────┘
        │                            │                            │
        │                   etcd replication                      │
        │                            │                            │
        └────────────────────────────┼────────────────────────────┘
                                     │
                                     ▼
                          ┌───────────────┐
                          │ wt-k3s-worker │
                          │   (Worker)    │
                          │ 192.168.1.194 │
                          │  watchtower   │
                          └───────────────┘
```

## Node Specifications

### Control Plane Nodes

| Node | IP | Host | vCPU | RAM | Disk | Role |
|------|-----|------|------|-----|------|------|
| fz-k3s | 192.168.1.190 | fortzero | 4 | 8GB | 80GB | Primary control plane, etcd leader |
| wt-k3s | 192.168.1.191 | watchtower | 4 | 8GB | 80GB | Control plane, etcd member |
| sg-k3s-control | 192.168.1.192 | sigil | 4 | 8GB | 80GB | Control plane, etcd member |

### Worker Nodes

| Node | IP | Host | vCPU | RAM | Disk | Role |
|------|-----|------|------|-----|------|------|
| wt-k3s-worker | 192.168.1.194 | watchtower | 4 | 8GB | 80GB | Workload scheduling |

## High Availability

### etcd Quorum
- **3 etcd members** provide fault tolerance
- **Quorum requirement**: 2 of 3 nodes must be available
- **Automatic leader election** on node failure
- **Data replication** across all control planes

### Failover Capabilities
- Any control plane can serve API requests
- Worker nodes automatically reconnect to available control planes
- Services continue running during control plane maintenance
- LoadBalancer IPs persist through node failures

## K3s Configuration

### Server Flags (Control Planes)
```bash
--disable traefik           # Using external Traefik
--disable servicelb         # Using MetalLB
--write-kubeconfig-mode 644
--embedded-registry         # Local container registry
```

### Agent Flags (Workers)
```bash
--server https://192.168.1.190:6443
```

### TLS SANs
- 192.168.1.190, 192.168.1.191, 192.168.1.192
- fz-k3s.k3s.nox, wt-k3s.k3s.nox, sg-k3s.k3s.nox

## Migration History

### SQLite to etcd Migration (2026-01-07)
1. Original cluster: Single node fz-k3s with SQLite
2. Enabled embedded etcd on fz-k3s
3. Joined wt-k3s as second control plane
4. Joined sg-k3s-control as third control plane
5. Added wt-k3s-worker as dedicated worker
6. Validated etcd quorum and failover

## Networking

### Pod Network
- **CNI**: Flannel (VXLAN)
- **Pod CIDR**: 10.42.0.0/16
- **Service CIDR**: 10.43.0.0/16

### Load Balancing
- **MetalLB**: Layer 2 mode, IP pool 192.168.1.230-250
- **Traefik**: Ingress controller at 192.168.1.231

## Storage

### Storage Classes
- **local-path** (default): Local node storage
- **nfs-client**: NFS-provisioned volumes (for multi-node access)

### Persistent Volumes
- BookStack: MySQL data (5Gi), uploads (5Gi)
- Homarr: SQLite database (1Gi)
- Prometheus: Metrics storage (50Gi)
- Grafana: Dashboards and config (1Gi)

## Related Documentation

- [Service Inventory](service-inventory.md)
- [Network Topology](network-topology.md)
- [Cluster Operations Runbook](../runbooks/cluster-operations.md)
