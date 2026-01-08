# K3s Cluster Operations Runbook

## Quick Reference

### Check Cluster Health
```bash
# Node status
kubectl get nodes -o wide

# All pods status
kubectl get pods -A

# Events (recent issues)
kubectl get events -A --sort-by='.lastTimestamp' | tail -20
```

### Check etcd Status
```bash
# From any control plane
ssh fz-k3s "sudo etcdctl member list"
ssh fz-k3s "sudo etcdctl endpoint status --cluster -w table"
ssh fz-k3s "sudo etcdctl endpoint health --cluster"
```

## Common Operations

### View Service Logs
```bash
# Deployment logs
kubectl logs -n <namespace> deployment/<name> --tail=100

# Pod logs with follow
kubectl logs -n <namespace> <pod-name> -f

# Previous container logs (after crash)
kubectl logs -n <namespace> <pod-name> --previous
```

### Restart a Deployment
```bash
kubectl rollout restart deployment/<name> -n <namespace>

# Watch rollout status
kubectl rollout status deployment/<name> -n <namespace>
```

### Scale a Deployment
```bash
# Scale up/down
kubectl scale deployment/<name> -n <namespace> --replicas=3

# Check current replicas
kubectl get deployment/<name> -n <namespace>
```

### Access Pod Shell
```bash
kubectl exec -it -n <namespace> <pod-name> -- /bin/sh
# or for bash
kubectl exec -it -n <namespace> <pod-name> -- /bin/bash
```

## Node Management

### Drain Node (for maintenance)
```bash
# Safely evict pods
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Allow scheduling again
kubectl uncordon <node-name>
```

### Add Control Plane Node
```bash
# Get join token from existing control plane
ssh fz-k3s "sudo cat /var/lib/rancher/k3s/server/node-token"

# On new node
curl -sfL https://get.k3s.io | K3S_TOKEN=<token> sh -s - server \
  --server https://192.168.1.190:6443 \
  --disable traefik \
  --disable servicelb
```

### Add Worker Node
```bash
# Get agent token
ssh fz-k3s "sudo cat /var/lib/rancher/k3s/server/node-token"

# On new node
curl -sfL https://get.k3s.io | K3S_TOKEN=<token> sh -s - agent \
  --server https://192.168.1.190:6443
```

### Remove Node
```bash
# Drain first
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Delete from cluster
kubectl delete node <node-name>

# On the node itself, uninstall K3s
# Control plane:
/usr/local/bin/k3s-uninstall.sh
# Worker:
/usr/local/bin/k3s-agent-uninstall.sh
```

## Backup & Restore

### etcd Snapshot
```bash
# Create snapshot
ssh fz-k3s "sudo k3s etcd-snapshot save --name manual-backup"

# List snapshots
ssh fz-k3s "sudo k3s etcd-snapshot ls"

# Snapshots stored at: /var/lib/rancher/k3s/server/db/snapshots/
```

### Restore from Snapshot
```bash
# Stop K3s on all servers first
# Then on one server:
sudo k3s server \
  --cluster-reset \
  --cluster-reset-restore-path=/var/lib/rancher/k3s/server/db/snapshots/<snapshot-name>
```

## Troubleshooting

### Node NotReady
```bash
# Check kubelet status on node
ssh <node> "sudo systemctl status k3s"
ssh <node> "sudo journalctl -u k3s -n 100"

# Check node conditions
kubectl describe node <node-name>
```

### Pod Stuck in Pending
```bash
# Check events
kubectl describe pod -n <namespace> <pod-name>

# Common causes:
# - Insufficient resources
# - Node selector/affinity issues
# - PVC binding issues
```

### Pod CrashLoopBackOff
```bash
# Check logs
kubectl logs -n <namespace> <pod-name> --previous

# Check container exit code
kubectl describe pod -n <namespace> <pod-name> | grep -A5 "Last State"

# Common causes:
# - Application errors
# - Missing environment variables
# - Resource limits too low
```

### Service Not Accessible
```bash
# Check service
kubectl get svc -n <namespace>

# Check endpoints
kubectl get endpoints -n <namespace> <service-name>

# Check ingress
kubectl get ingress -n <namespace>

# Test from inside cluster
kubectl run test --rm -it --image=busybox -- wget -O- http://<service>.<namespace>.svc
```

### etcd Issues
```bash
# Check etcd health
ssh fz-k3s "sudo etcdctl endpoint health --cluster"

# Check member list
ssh fz-k3s "sudo etcdctl member list -w table"

# If member is unhealthy, check K3s logs
ssh <node> "sudo journalctl -u k3s | grep etcd"
```

## Maintenance Windows

### Rolling Upgrade Procedure
1. Backup etcd snapshot
2. Drain and upgrade workers first
3. Drain and upgrade control planes one at a time
4. Verify cluster health after each node
5. Uncordon all nodes

### K3s Version Upgrade
```bash
# On each node (workers first, then control planes)
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.xx.x sh -

# Verify version
kubectl get nodes
```

## Emergency Procedures

### Complete Cluster Recovery
1. Stop all K3s services on all nodes
2. On primary control plane, restore from etcd snapshot
3. Start K3s on primary
4. Rejoin other control planes
5. Rejoin workers

### Single Control Plane Failure
- Cluster remains operational with 2/3 control planes
- Fix failed node and rejoin
- Do NOT remove failed node from etcd until recovered

### Quorum Loss (2+ control planes down)
- Cluster becomes read-only
- Restore from etcd snapshot required
- Follow complete cluster recovery procedure
