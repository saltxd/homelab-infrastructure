# K3s HA Cluster Expansion Toolkit

Safely expand a single-node K3s cluster to a 3-node HA configuration.

## Quick Start

```bash
# 1. First, run dry-run to see what will happen
./setup-ha-cluster.sh

# 2. If satisfied, execute the expansion
./setup-ha-cluster.sh --execute
```

## Target Architecture

**Control Planes (3 for HA quorum):**
- `fz-k3s` (192.168.1.190) - Existing primary
- `wt-k3s` (192.168.1.193) - Converting from worker
- `sg-k3s-control` (192.168.1.192) - Fresh VM

**Workers:**
- `wt-k3s-worker` (192.168.1.194) - Fresh VM

## Scripts

| Script | Purpose |
|--------|---------|
| `setup-ha-cluster.sh` | Master orchestrator - runs everything in order |
| `diagnose-k3s-failure.sh` | Diagnose issues on a node |
| `fix-wt-k3s.sh` | Clean up and rejoin wt-k3s |
| `join-control-plane.sh` | Join a new control plane |
| `join-worker.sh` | Join a new worker |
| `validate-ha-cluster.sh` | Comprehensive cluster validation |

## Usage

### Full Automated Setup

```bash
# Dry-run (shows what would happen)
./setup-ha-cluster.sh

# Execute all steps
./setup-ha-cluster.sh --execute

# Start from specific step
./setup-ha-cluster.sh --start-from 3 --execute

# Skip worker setup
./setup-ha-cluster.sh --skip-workers --execute
```

### Step-by-Step Manual Setup

```bash
# 1. Diagnose what's wrong with wt-k3s
./diagnose-k3s-failure.sh

# 2. Fix wt-k3s and join as control plane
./fix-wt-k3s.sh --execute

# 3. Join sg-k3s-control as control plane
./join-control-plane.sh --node sg-k3s-control --execute

# 4. Join worker
./join-worker.sh --node wt-k3s-worker --execute

# 5. Validate the cluster
./validate-ha-cluster.sh
```

### Validation

```bash
# Quick health check
./validate-ha-cluster.sh --quick

# Full validation
./validate-ha-cluster.sh

# Test HA failover (careful - stops one control plane!)
./validate-ha-cluster.sh --test-failover
```

## Safety Features

- **Dry-run by default** - Use `--execute` to make actual changes
- **etcd backups** - Automatic snapshots before changes
- **Verification** - Each step verifies success before proceeding
- **Rollback docs** - See TROUBLESHOOTING.md for recovery

## Configuration

Edit `config.sh` to modify:
- Node IPs and names
- K3s version
- Token
- Disabled components
- Critical workloads to validate

## Logs

All operations are logged to `./logs/` with timestamps.

## Prerequisites

- SSH access to all nodes (configured in `~/.ssh/config`)
- sudo access on all nodes
- K3s running on primary (fz-k3s)
- Network connectivity between all nodes

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for:
- Common issues and solutions
- Rollback procedures
- Emergency recovery
- Log locations

## Files

```
k3s-ha-expansion/
├── config.sh              # Configuration and credentials
├── setup-ha-cluster.sh    # Master orchestrator
├── diagnose-k3s-failure.sh
├── fix-wt-k3s.sh
├── join-control-plane.sh
├── join-worker.sh
├── validate-ha-cluster.sh
├── lib/
│   └── common.sh          # Shared functions
├── logs/                  # Operation logs
├── backups/               # kubeconfig backups
├── README.md
└── TROUBLESHOOTING.md
```
