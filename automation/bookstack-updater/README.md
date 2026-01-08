# BookStack Auto-Updater

Automated documentation updater for homelab infrastructure using BookStack API.

## Overview

This tool automatically audits your homelab infrastructure and updates BookStack documentation with current state information. It uses Jinja2 templates to generate formatted Markdown pages.

## Features

- Runs homelab audit scripts to collect current infrastructure state
- Parses audit results from JSON/text files
- Updates BookStack pages via REST API
- Supports dry-run mode for testing
- Discord webhook notifications for update status
- Weekly cron job automation

## Prerequisites

- Python 3.9+
- BookStack instance with API access enabled
- BookStack API token (create in UI: Profile → My Account → API Tokens)

## Installation

```bash
cd ~/Forge/bookstack-updater
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Edit `config.yaml` with your BookStack API credentials:

```yaml
bookstack:
  url: http://docs.k3s.nox
  api_token_id: "your-token-id"      # From BookStack UI
  api_token_secret: "your-secret"    # From BookStack UI

audit:
  script: ~/homelab-audit.sh
  results_dir: ~/audit-results/

notifications:
  discord_webhook: ""  # Optional Discord webhook URL
```

### Getting API Token

1. Log in to BookStack at http://docs.k3s.nox
2. Click your profile icon → "My Account"
3. Go to "API Tokens" tab
4. Click "Create Token"
5. Name it "Homelab-Automation"
6. Copy the Token ID and Secret to config.yaml

## Usage

### Run Full Update

```bash
# Run audit and update docs
./bookstack_updater.py --audit --update

# Dry run (no actual updates)
./bookstack_updater.py --audit --update --dry-run

# With Discord notification
./bookstack_updater.py --audit --update --notify
```

### Individual Operations

```bash
# Just run audit (collect data)
./bookstack_updater.py --audit

# Just update docs (use existing audit data)
./bookstack_updater.py --update

# Verbose output
./bookstack_updater.py --audit --update --verbose
```

## Templates

Templates are Jinja2 files in `templates/`:

| Template | Purpose |
|----------|---------|
| `network.md.j2` | Network topology, VLANs, IP ranges |
| `proxmox.md.j2` | Proxmox node inventory |
| `vms.md.j2` | Virtual machine inventory |
| `k3s.md.j2` | K3s cluster state (nodes, deployments) |

### Template Variables

Templates receive audit data as context:

```python
{
    "proxmox_nodes": [...],  # From proxmox-nodes.json
    "vms": [...],            # From proxmox-vms.json
    "k3s_nodes": [...],      # From k3s-nodes.txt
    "k3s_deployments": [...], # From k3s-deployments.txt
    "timestamp": "2026-01-07T21:00:00"
}
```

## Cron Setup

Add to crontab for weekly updates:

```bash
# Edit crontab
crontab -e

# Add weekly job (Sundays at 2am)
0 2 * * 0 cd ~/Forge/bookstack-updater && ./venv/bin/python bookstack_updater.py --audit --update --notify >> ~/logs/bookstack-update.log 2>&1
```

## BookStack Structure

The initialization script creates:

```
Infrastructure/
  ├── Network Topology
  ├── Proxmox Nodes
  ├── Virtual Machines
  └── DNS & Routing

K3s Cluster/
  ├── Cluster Overview
  ├── Deployments
  ├── Services & Ingress
  └── Storage

Runbooks/
  ├── Incident Response
  ├── Backup & Recovery
  ├── Maintenance
  └── Troubleshooting

Services/
  ├── Monitoring (Grafana/Prometheus)
  ├── Dashboard (Homer/Homarr)
  ├── DNS (AdGuard)
  └── GPT-OS
```

## Files

```
bookstack-updater/
├── bookstack_updater.py  # Main script
├── init_bookstack.py     # Initial setup script
├── config.yaml           # Configuration
├── requirements.txt      # Python dependencies
├── templates/
│   ├── network.md.j2
│   ├── proxmox.md.j2
│   ├── vms.md.j2
│   └── k3s.md.j2
└── README.md
```

## Troubleshooting

### API Authentication Errors

Ensure your API token is valid and has write permissions:
```bash
curl -H "Authorization: Token <id>:<secret>" http://docs.k3s.nox/api/books
```

### Missing Audit Data

Run the audit first:
```bash
./bookstack_updater.py --audit
ls ~/audit-results/
```

### Connection Issues

Verify BookStack is accessible:
```bash
curl http://docs.k3s.nox/login
```

## Related

- BookStack: http://docs.k3s.nox
- Homarr Dashboard: http://dashboard.k3s.nox
- Homer Dashboard: http://home.k3s.nox
- Grafana: http://grafana.k3s.nox
