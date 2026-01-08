# BookStack Documentation Update Workflow

## Quick Reference for Claude Code Sessions

### API Credentials Location
```
~/Forge/bookstack-updater/config.yaml
```

### BookStack URL
```
http://docs.k3s.nox
```

### API Token (for curl commands)
```bash
# Read from config
TOKEN_ID=$(grep api_token_id ~/Forge/bookstack-updater/config.yaml | awk '{print $2}' | tr -d '"')
TOKEN_SECRET=$(grep api_token_secret ~/Forge/bookstack-updater/config.yaml | awk '{print $2}' | tr -d '"')
AUTH="Token ${TOKEN_ID}:${TOKEN_SECRET}"
```

---

## Method 1: Direct API Updates (Recommended)

### List All Books
```bash
curl -s http://docs.k3s.nox/api/books \
  -H "Authorization: Token YOUR_TOKEN_ID:YOUR_TOKEN_SECRET" \
  | jq '.data[] | {id, name}'
```

### Get Book Contents (chapters/pages)
```bash
curl -s http://docs.k3s.nox/api/books/{BOOK_ID} \
  -H "Authorization: Token YOUR_TOKEN_ID:YOUR_TOKEN_SECRET" \
  | jq '.contents'
```

### Create New Page in Chapter
```bash
cat << 'EOF' | jq -Rs '{name: "Page Title", markdown: ., chapter_id: CHAPTER_ID}' > /tmp/page.json
# Your Markdown Content Here

Write your documentation in markdown format.
EOF

curl -X POST http://docs.k3s.nox/api/pages \
  -H "Authorization: Token YOUR_TOKEN_ID:YOUR_TOKEN_SECRET" \
  -H "Content-Type: application/json" \
  -d @/tmp/page.json
```

### Update Existing Page
```bash
cat << 'EOF' | jq -Rs '{name: "Page Title", markdown: .}' > /tmp/page.json
# Updated Content

New markdown content here.
EOF

curl -X PUT http://docs.k3s.nox/api/pages/{PAGE_ID} \
  -H "Authorization: Token YOUR_TOKEN_ID:YOUR_TOKEN_SECRET" \
  -H "Content-Type: application/json" \
  -d @/tmp/page.json
```

### Create New Chapter in Book
```bash
curl -X POST http://docs.k3s.nox/api/chapters \
  -H "Authorization: Token YOUR_TOKEN_ID:YOUR_TOKEN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"book_id": BOOK_ID, "name": "Chapter Name"}'
```

---

## Method 2: Use the Auto-Updater Script

### Run Manual Update
```bash
cd ~/Forge/bookstack-updater
source venv/bin/activate
python bookstack_updater.py --update
```

### Update Templates First
Templates are in `~/Forge/bookstack-updater/templates/*.md.j2`

Edit the Jinja2 templates, then run the updater.

---

## Current BookStack Structure

| Book ID | Name | Purpose |
|---------|------|---------|
| 5 | Infrastructure | Network, Proxmox, VMs, DNS |
| 10 | K3s Cluster | Cluster overview, deployments, services |
| 15 | Runbooks | Incident response, backup, maintenance |
| 20 | Services | Monitoring, DNS, Applications |

---

## Claude Code Session Prompt Template

Copy this to start a new session focused on docs:

```
I need to update my homelab documentation in BookStack.

BookStack API:
- URL: http://docs.k3s.nox
- Token ID: YOUR_TOKEN_ID
- Token Secret: YOUR_TOKEN_SECRET

Current books:
- Infrastructure (ID: 5) - Network, Proxmox, VMs
- K3s Cluster (ID: 10) - Cluster state, deployments
- Runbooks (ID: 15) - Operations procedures
- Services (ID: 20) - Service documentation

Please [describe what you want to document].

Use the BookStack REST API to create/update pages. Format content as markdown.
```

---

## Example: Add New Service Documentation

```bash
# 1. Find the Services book chapters
curl -s http://docs.k3s.nox/api/books/20 \
  -H "Authorization: Token YOUR_TOKEN_ID:YOUR_TOKEN_SECRET" \
  | jq '.contents[] | {id, name, type}'

# 2. Create page in appropriate chapter
cat << 'EOF' | jq -Rs '{name: "n8n", markdown: ., chapter_id: CHAPTER_ID}' > /tmp/page.json
# n8n Workflow Automation

## Overview
- **URL**: http://n8n.k3s.nox
- **Namespace**: automation
- **Purpose**: Workflow automation and integrations

## Credentials
Stored in `~/Forge/n8n-config.yaml`

## Workflows
1. Prometheus Alerts → Discord
2. Daily Homelab Report
3. GPT-OS Integration Webhook
EOF

curl -X POST http://docs.k3s.nox/api/pages \
  -H "Authorization: Token YOUR_TOKEN_ID:YOUR_TOKEN_SECRET" \
  -H "Content-Type: application/json" \
  -d @/tmp/page.json
```

---

## Tips

1. **Always use markdown format** - BookStack renders it nicely
2. **Use jq -Rs** to properly escape markdown for JSON
3. **Check existing pages first** - Avoid duplicates
4. **Update git repo after major changes**:
   ```bash
   cd ~/homelab-infrastructure
   git add -A && git commit -m "Update docs" && git push
   ```
