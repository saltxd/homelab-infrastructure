# Service Inventory

Complete inventory of services deployed to the K3s cluster.

## Cluster Management

### Rancher
- **URL**: https://rancher.homelab.internal
- **Namespace**: cattle-system
- **Purpose**: Kubernetes cluster management UI
- **Components**: rancher, rancher-webhook

### ArgoCD
- **URL**: http://argo.k3s.nox
- **Namespace**: argocd
- **Purpose**: GitOps continuous deployment
- **Components**: argocd-server, argocd-repo-server, argocd-application-controller

## Monitoring Stack

### Prometheus
- **URL**: http://prometheus.k3s.nox
- **Namespace**: observability
- **Purpose**: Metrics collection and alerting
- **Scrape Targets**:
  - K3s nodes (kubelet, kube-proxy)
  - Proxmox hosts (node_exporter)
  - All VMs with node_exporter
- **Retention**: 15 days

### Grafana
- **URL**: http://grafana.k3s.nox
- **Namespace**: observability
- **Purpose**: Metrics visualization
- **Dashboards**:
  - Kubernetes cluster overview
  - Node exporter full
  - Homelab overview (custom)
- **Default Login**: admin (password in secrets)

### Uptime Kuma
- **URL**: http://uptime.k3s.nox
- **Namespace**: uptime-kuma
- **Purpose**: Service availability monitoring
- **Monitors**:
  - DNS servers (fz-dns, wt-dns)
  - K3s API health
  - Grafana, Rancher
  - GPT-OS health endpoint

### node_exporter
- **Deployed On**: All Proxmox hosts + VMs
- **Port**: 9100
- **Metrics**: CPU, memory, disk, network

## Dashboards

### Homarr
- **URL**: http://dashboard.k3s.nox
- **Namespace**: homarr
- **Purpose**: Interactive service dashboard
- **Features**:
  - Service status indicators
  - Customizable widgets
  - Icon library integration

### Homer
- **URL**: http://home.k3s.nox
- **Namespace**: homer
- **Purpose**: Static service dashboard (backup)
- **Config**: ConfigMap-based YAML

## Documentation

### BookStack
- **URL**: http://docs.k3s.nox
- **Namespace**: bookstack
- **Purpose**: Infrastructure documentation wiki
- **Components**:
  - BookStack (PHP application)
  - MySQL 8.0 database
- **Storage**:
  - mysql-data: 5Gi
  - bookstack-uploads: 5Gi
  - bookstack-config: 1Gi
- **Default Login**: admin@admin.com / password

## Networking

### Traefik
- **Namespace**: kube-system
- **Purpose**: Ingress controller
- **LoadBalancer IP**: 192.168.1.231
- **Features**:
  - HTTP/HTTPS routing
  - Automatic TLS (when configured)
  - Middleware support

### MetalLB
- **Namespace**: metallb-system
- **Purpose**: Bare-metal load balancer
- **IP Pool**: 192.168.1.230-250
- **Mode**: Layer 2

### CoreDNS
- **Namespace**: kube-system
- **Purpose**: Cluster DNS
- **Upstream**: AdGuard Home (192.168.1.211)

## Storage

### local-path-provisioner
- **Namespace**: kube-system
- **Purpose**: Dynamic local storage provisioning
- **Storage Class**: local-path (default)

## Resource Summary

| Namespace | Deployments | Services | Ingresses |
|-----------|-------------|----------|-----------|
| cattle-system | 2 | 3 | 1 |
| observability | 3 | 4 | 2 |
| uptime-kuma | 1 | 1 | 1 |
| bookstack | 2 | 2 | 1 |
| homarr | 1 | 1 | 1 |
| homer | 1 | 1 | 1 |
| metallb-system | 2 | 0 | 0 |

## Service Dependencies

```
                    ┌─────────────┐
                    │  AdGuard    │
                    │   (DNS)     │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Traefik  │ │ CoreDNS  │ │ MetalLB  │
        │(Ingress) │ │(Cluster) │ │   (LB)   │
        └────┬─────┘ └──────────┘ └────┬─────┘
             │                         │
             └────────────┬────────────┘
                          │
     ┌──────────┬─────────┼─────────┬──────────┐
     │          │         │         │          │
     ▼          ▼         ▼         ▼          ▼
┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
│ Rancher ││ Grafana ││BookStack││ Homarr  ││  Homer  │
└─────────┘└─────────┘└────┬────┘└─────────┘└─────────┘
                           │
                           ▼
                      ┌─────────┐
                      │  MySQL  │
                      └─────────┘
```
