# n8n Deployment (sanitized template)

This directory contains a **sanitized template** version of the n8n + postgresql K8s manifests, with all secrets replaced by `changeme` placeholders and internal hostnames generalized (e.g. `n8n.cluster.local` instead of internal homelab DNS).

It is kept here for reference and as a starting point for anyone deploying their own n8n on K3s.

## Real working version

The actual operational manifests for the homelab — with real resource limits, internal hostnames, and references to live K8s Secrets — live in the **private** `saltxd/homelab-k3s` repo:

```
saltxd/homelab-k3s:automation/n8n/
```

Live secret values are managed in K8s, not in either repo:

```bash
# To recover any of the live secret values:
kubectl -n automation get secret n8n-secret      -o yaml
kubectl -n automation get secret postgresql-secret -o yaml
```

## Files

| File | Purpose |
|---|---|
| `n8n.yaml` | Deployment + Service + Ingress for n8n (placeholders for secrets) |
| `postgresql.yaml` | Deployment + Service + PVC for the n8n postgres (placeholder password) |
| `alertmanager-config.yaml` | Routes Prometheus alerts to n8n webhook for triage |
| `config.yaml.example` | Sample app-side config template (placeholder values) |
| `workflows/*.json` | Sanitized exports of the workflows in use, for documentation |

## Why split sanitized template / real working version

- The sanitized template is publishable as part of `saltxd/homelab-infrastructure` (public) — useful for anyone forking the homelab as a reference deployment
- Real values, internal hostnames, and resource sizing decisions specific to the Citadel cluster live in `saltxd/homelab-k3s` (private) where they don't leak operational details

If you find yourself needing to update both copies, check whether the change is *generic operational pattern* (template, both copies) or *Citadel-specific tuning* (private only).
