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
│   k3s-cp-1      │          │   k3s-cp-2      │          │ k3s-cp-3│
│  (Primary)    │◄────────►│  (Secondary)  │◄────────►│  (Tertiary)   │
│ 10.0.1.10 │          │ 10.0.1.11 │          │ 10.0.1.12 │
│   proxmox-0    │          │  proxmox-1   │          │    proxmox-2      │
└───────────────┘          └───────────────┘          └───────────────┘
        │                            │                            │
        │                   etcd replication                      │
        │                            │                            │
        └────────────────────────────┼────────────────────────────┘
                                     │
                                     ▼
                          ┌───────────────┐
                          │ k3s-worker-1 │
                          │   (Worker)    │
                          │ 10.0.1.14 │
                          │  proxmox-1   │
                          └───────────────┘
```

## Node Specifications

### Control Plane Nodes

| Node | IP | Host | vCPU | RAM | Disk | Role |
|------|-----|------|------|-----|------|------|
| k3s-cp-1 | 10.0.1.10 | proxmox-0 | 4 | 8GB | 80GB | Primary control plane, etcd leader |
| k3s-cp-2 | 10.0.1.11 | proxmox-1 | 4 | 8GB | 80GB | Control plane, etcd member |
| k3s-cp-3 | 10.0.1.12 | proxmox-2 | 4 | 8GB | 80GB | Control plane, etcd member |

### Worker Nodes

| Node | IP | Host | vCPU | RAM | Disk | Role |
|------|-----|------|------|-----|------|------|
| k3s-worker-1 | 10.0.1.14 | proxmox-1 | 4 | 8GB | 80GB | Workload scheduling |

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
--server https://10.0.1.10:6443
```

### TLS SANs
- 10.0.1.10, 10.0.1.11, 10.0.1.12
- k3s-cp-1.cluster.local, k3s-cp-2.cluster.local, k3s-cp-3.cluster.local

## Migration History

### SQLite to etcd Migration (2026-01-07)
1. Original cluster: Single node k3s-cp-1 with SQLite
2. Enabled embedded etcd on k3s-cp-1
3. Joined k3s-cp-2 as second control plane
4. Joined k3s-cp-3 as third control plane
5. Added k3s-worker-1 as dedicated worker
6. Validated etcd quorum and failover

## Networking

### Pod Network
- **CNI**: Flannel (VXLAN)
- **Pod CIDR**: 10.42.0.0/16
- **Service CIDR**: 10.43.0.0/16

### Load Balancing
- **MetalLB**: Layer 2 mode, IP pool 10.0.2.30-250
- **Traefik**: Ingress controller at 10.0.2.31

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
