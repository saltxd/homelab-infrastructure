# K3s VM Memory Right-Sizing — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Shrink over-provisioned k3s VMs to data-backed sizes, reclaiming 10 GB of host memory across the cluster while preserving N-1 failover headroom.

**Architecture:** Rolling reboot pattern identical to the 2026-04-20 hotplug-activation pass: cordon → drain (--force handles Longhorn PDBs) → cold VM cycle via Proxmox → wait Ready → uncordon → verify etcd between each control-plane node. Order deliberately chosen from least-risky (sg-k3s-control, unaffected by the incident) to most-risky (sc-k3s, the Longhorn anchor).

**Tech Stack:** Proxmox QEMU (`qm shutdown/set/start`), k3s kubectl, Prometheus, Longhorn.

**Source data:** 4 parallel Sonnet subagent analyses of 48h-7d Prometheus data (2026-04-20) — each node's pre-incident p95 memory use, swap activity, major page fault rate, and N-1 failover absorption math. Full synthesis in session transcript.

**Final sizing target:**
| Node | Current | Target | Reclaim | Reason |
|---|---|---|---|---|
| fz-k3s | 13 GB | 13 GB | 0 | Longhorn gravity well (25 replicas); N-1 (wt dies) puts it at 82% of 13 GB; do NOT shrink below 12 GB |
| sc-k3s | 16 GB | **12 GB** | 4 GB | p95 5.34 GB post-bump; N-1 (wt dies) = 10.3 GB needed; 12 GB gives 1.8 GB margin |
| sg-k3s-control | 13 GB | **10 GB** | 3 GB | p95 51% on 10 GB pre-bump, unaffected by incident, 10 GB covers N-1 comfortably |
| wt-k3s-worker | 13 GB | **10 GB** | 3 GB | post-hardening p95 44% on 8 GB, zero swap/alerts; watchtower host at 12/15 used — shrink relieves host pressure |

---

## File Structure

Files to modify:
- Proxmox VM configs (via `qm set`, not direct file edit): `/etc/pve/nodes/<host>/qemu-server/<vmid>.conf` on scryer, sigil, watchtower.
- `/Users/mburkholz/Homelab/infrastructure-docs/k3s/manifests/` — no new manifest files; nothing to rewrite.
- `/Users/mburkholz/.claude/skills/homelab-infrastructure/SKILL.md` — update VM inventory table with final values.
- `/Users/mburkholz/.claude/CLAUDE.md` — update k3s memory line.
- `/Users/mburkholz/.claude/projects/-Users-mburkholz-Forge/memory/project_k3s_hotplug_descheduler.md` — append outcome.
- BookStack page 186 (prevention-landed) — append "Phase 1.5 — data-driven shrink" section.

---

## Pre-flight

### Task 0: Verify cluster baseline

**Files:** none (read-only commands)

- [ ] **Step 0.1: Confirm all 4 nodes Ready, etcd healthy, no abnormal pods**

```bash
ssh fz-k3s "kubectl get nodes && echo --- && kubectl get --raw '/readyz?verbose' 2>&1 | grep -E 'etcd|readyz' && echo --- && kubectl get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded 2>&1"
```

Expected: all 4 Ready, etcd ok, "No resources found"

- [ ] **Step 0.2: Record current memory state**

```bash
for h in fz-k3s sc-k3s sg-k3s-control wt-k3s-worker; do ssh $h "hostname && free -m | head -2"; done
ssh fz-k3s "kubectl top nodes"
```

Expected baseline: fz-k3s ~13 GB, sc-k3s ~16 GB, sg-k3s-control ~13 GB, wt-k3s-worker ~13 GB; all under 55% used.

- [ ] **Step 0.3: Verify Longhorn volume health**

```bash
ssh fz-k3s 'kubectl get volumes.longhorn.io -n longhorn-system -o json | jq -r ".items[] | select(.status.robustness!=\"healthy\" and .status.state==\"attached\") | .metadata.name"'
```

Expected: no output (no degraded attached volumes). Detached/unknown volumes are ok.

---

## Task 1: Shrink sg-k3s-control 13 → 10 GB

**Why first:** Subagent confirmed this node was completely unaffected by the Apr 20 incident. Shrink is lowest-risk. Frees 3 GB on sigil for sg-scribe breathing room.

**Files:**
- Modify: `/etc/pve/nodes/sigil/qemu-server/503.conf` (via `qm set`)

- [ ] **Step 1.1: Cordon sg-k3s-control**

```bash
ssh fz-k3s "kubectl cordon sg-k3s-control"
```

Expected: `node/sg-k3s-control cordoned`

- [ ] **Step 1.2: Drain (force for Longhorn PDBs)**

```bash
ssh fz-k3s "kubectl drain sg-k3s-control --ignore-daemonsets --delete-emptydir-data --force --timeout=420s"
```

Expected: all evictable pods evicted; final line `node/sg-k3s-control drained` OR timeout on `instance-manager` PDB (both acceptable — instance-manager will restart on node recovery). If timeout fires, verify only longhorn pods remain on the node before continuing.

- [ ] **Step 1.3: Set memory to 10 GB**

```bash
ssh sigil "qm set 503 -memory 10240"
```

Expected: `update VM 503: -memory 10240`

- [ ] **Step 1.4: Cold-cycle the VM (shutdown + start)**

```bash
ssh sigil "qm shutdown 503 --forceStop 1 --timeout 120" && sleep 3 && ssh sigil "qm status 503" && ssh sigil "qm start 503"
```

Expected: `status: stopped` then start. The `--forceStop 1` is required because qemu-guest-agent isn't installed on these VMs.

- [ ] **Step 1.5: Wait for SSH + k3s Ready**

```bash
for i in $(seq 1 15); do
  ssh -o ConnectTimeout=3 sg-k3s-control "uptime" 2>/dev/null && break
  sleep 5
done
for i in $(seq 1 15); do
  s=$(ssh fz-k3s "kubectl get node sg-k3s-control --no-headers" 2>&1 | grep sg-k3s-control | awk '{print $2}')
  echo "check $i: $s"
  [[ "$s" == "Ready,SchedulingDisabled" ]] && break
  sleep 10
done
```

Expected: SSH up within ~30s; node Ready within ~90s.

- [ ] **Step 1.6: Verify memory = 10 GB, etcd healthy**

```bash
ssh sg-k3s-control "free -m | head -2"
ssh fz-k3s "kubectl get --raw '/readyz?verbose' 2>&1 | grep -E 'etcd|readyz'"
```

Expected: `Mem: ~10000 ...`; `[+]etcd ok`, `readyz check passed`.

- [ ] **Step 1.7: Uncordon**

```bash
ssh fz-k3s "kubectl uncordon sg-k3s-control"
```

Expected: `node/sg-k3s-control uncordoned`

---

## Task 2: Shrink wt-k3s-worker 13 → 10 GB

**Why second:** Worker node, no quorum impact. Frees 3 GB on watchtower host (currently at 12/15 GB used — relieves real host-level pressure).

**Files:**
- Modify: `/etc/pve/nodes/watchtower/qemu-server/505.conf` (via `qm set`)

- [ ] **Step 2.1: Cordon wt-k3s-worker**

```bash
ssh fz-k3s "kubectl cordon wt-k3s-worker"
```

Expected: `node/wt-k3s-worker cordoned`

- [ ] **Step 2.2: Drain**

```bash
ssh fz-k3s "kubectl drain wt-k3s-worker --ignore-daemonsets --delete-emptydir-data --force --timeout=420s"
```

Expected: all evictable pods evicted; may timeout on instance-manager PDB.

- [ ] **Step 2.3: Set memory to 10 GB**

```bash
ssh watchtower "qm set 505 -memory 10240"
```

Expected: `update VM 505: -memory 10240`

- [ ] **Step 2.4: Cold-cycle the VM**

```bash
ssh watchtower "qm shutdown 505 --forceStop 1 --timeout 120" && sleep 3 && ssh watchtower "qm status 505" && ssh watchtower "qm start 505"
```

- [ ] **Step 2.5: Wait for Ready**

```bash
for i in $(seq 1 15); do
  ssh -o ConnectTimeout=3 wt-k3s-worker "uptime" 2>/dev/null && break
  sleep 5
done
for i in $(seq 1 15); do
  s=$(ssh fz-k3s "kubectl get node wt-k3s-worker --no-headers" 2>&1 | grep wt-k3s-worker | awk '{print $2}')
  echo "check $i: $s"
  [[ "$s" == "Ready,SchedulingDisabled" ]] && break
  sleep 10
done
```

- [ ] **Step 2.6: Verify memory + host headroom**

```bash
ssh wt-k3s-worker "free -m | head -2"
ssh watchtower "free -h | head -2"
```

Expected: guest ~10000 MB; watchtower host free should climb from ~3.2 GB → ~6+ GB.

- [ ] **Step 2.7: Uncordon**

```bash
ssh fz-k3s "kubectl uncordon wt-k3s-worker"
```

---

## Task 3: Shrink sc-k3s 16 → 12 GB

**Why last:** Longhorn gravity well for storage-pinned workloads. Subagent confirmed 12 GB is the safe floor (steady-state + N-1 = 10.3 GB needed; 12 GB gives 1.8 GB margin). Drain has more pods to move (~54 in prior cycle). Do this last so cluster has already stabilized from tasks 1 and 2.

**Files:**
- Modify: `/etc/pve/nodes/scryer/qemu-server/502.conf` (via `qm set`)

- [ ] **Step 3.1: Check that Longhorn volumes are healthy before disruption**

```bash
ssh fz-k3s 'kubectl get volumes.longhorn.io -n longhorn-system -o json | jq -r ".items[] | select(.status.robustness==\"degraded\") | .metadata.name"'
```

Expected: empty. If any degraded, wait for rebuild (from tasks 1-2) before proceeding.

- [ ] **Step 3.2: Cordon sc-k3s**

```bash
ssh fz-k3s "kubectl cordon sc-k3s"
```

- [ ] **Step 3.3: Drain**

```bash
ssh fz-k3s "kubectl drain sc-k3s --ignore-daemonsets --delete-emptydir-data --force --timeout=420s"
```

Expected: many pods evicted (likely 30-50); may timeout on instance-manager PDB.

- [ ] **Step 3.4: Set memory to 12 GB**

```bash
ssh scryer "qm set 502 -memory 12288"
```

Expected: `update VM 502: -memory 12288`

- [ ] **Step 3.5: Cold-cycle**

```bash
ssh scryer "qm shutdown 502 --forceStop 1 --timeout 120" && sleep 3 && ssh scryer "qm status 502" && ssh scryer "qm start 502"
```

- [ ] **Step 3.6: Wait for Ready + etcd** (control-plane: verify quorum)

```bash
for i in $(seq 1 15); do
  ssh -o ConnectTimeout=3 sc-k3s "uptime" 2>/dev/null && break
  sleep 5
done
for i in $(seq 1 18); do
  s=$(ssh fz-k3s "kubectl get node sc-k3s --no-headers" 2>&1 | grep sc-k3s | awk '{print $2}')
  echo "check $i: $s"
  [[ "$s" == "Ready,SchedulingDisabled" ]] && break
  sleep 10
done
ssh fz-k3s "kubectl get --raw '/readyz?verbose' 2>&1 | grep -E 'etcd|readyz'"
```

Expected: Ready within ~2 min (etcd rejoin); etcd ok.

- [ ] **Step 3.7: Verify memory = 12 GB**

```bash
ssh sc-k3s "free -m | head -2"
```

Expected: `Mem: ~12000 ...`

- [ ] **Step 3.8: Uncordon**

```bash
ssh fz-k3s "kubectl uncordon sc-k3s"
```

---

## Task 4: Post-shrink verification

**Files:** none (read-only commands)

- [ ] **Step 4.1: All nodes Ready, etcd healthy**

```bash
ssh fz-k3s "kubectl get nodes && echo --- && kubectl get --raw '/readyz?verbose' 2>&1 | grep -E 'etcd|readyz'"
```

Expected: all 4 Ready, etcd ok.

- [ ] **Step 4.2: All pods Running**

```bash
ssh fz-k3s "kubectl get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded 2>&1"
```

Expected: `No resources found`.

- [ ] **Step 4.3: Final memory per node + utilization**

```bash
for h in fz-k3s sc-k3s sg-k3s-control wt-k3s-worker; do echo "--- $h ---"; ssh $h "free -m | head -2"; done
ssh fz-k3s "kubectl top nodes"
```

Expected:
- fz-k3s: 13 GB total, <55% used
- sc-k3s: 12 GB total, <55% used
- sg-k3s-control: 10 GB total, <70% used
- wt-k3s-worker: 10 GB total, <70% used

If any node is >80% used, STOP and investigate before claiming completion.

- [ ] **Step 4.4: Longhorn all healthy**

```bash
ssh fz-k3s 'kubectl get volumes.longhorn.io -n longhorn-system -o json | jq -r ".items[] | select(.status.state==\"attached\") | select(.status.robustness!=\"healthy\") | .metadata.name + \" state=\" + .status.state + \" robustness=\" + .status.robustness"'
```

Expected: empty (Longhorn may still be rebuilding — give it 10 min if there are degraded entries, then recheck).

- [ ] **Step 4.5: Host-level reclaim on watchtower**

```bash
ssh watchtower "free -h | head -2"
```

Expected: `free` column should have climbed vs pre-plan baseline (~3.2 GB → ~6+ GB).

---

## Task 5: Update docs

**Files:**
- Modify: `/Users/mburkholz/.claude/skills/homelab-infrastructure/SKILL.md`
- Modify: `/Users/mburkholz/.claude/CLAUDE.md`
- Modify: `/Users/mburkholz/.claude/projects/-Users-mburkholz-Forge/memory/project_k3s_hotplug_descheduler.md`
- Append section to BookStack page 186 (prevention-landed)

- [ ] **Step 5.1: Update homelab skill VM inventory**

Update k3s VMID rows in the skill's VM table with final memory values (12, 12, 10, 10 GB respectively).

- [ ] **Step 5.2: Update CLAUDE.md k3s memory line**

Change the memory line in "Common Mistakes to Avoid" from old values (12/16/12/13) to (13/12/10/10).

- [ ] **Step 5.3: Update project memory note**

Append an "Outcome" section to `project_k3s_hotplug_descheduler.md` with the data-driven sizing decision and the 10 GB reclaim.

- [ ] **Step 5.4: Append to BookStack page 186**

Append "Phase 1.5 — Data-Driven Shrink" section with the 4-agent analysis table, final sizing, and the conclusion that user's "we were fine at 8 GB" hypothesis was right for 3 of 4 nodes.

- [ ] **Step 5.5: Commit + push any config-relevant changes**

There are no manifest changes this pass (Proxmox configs live in `/etc/pve/` and aren't in git). But update the BookStack page reference in any Homelab readmes if present.

```bash
git -C /Users/mburkholz/Homelab/infrastructure-docs status
```

Expected: either no staged changes (only docs in .claude and BookStack) OR if plans/ dir was committed, verify and push.

---

## Self-Review Checklist

Before executing:
1. **Spec coverage:** plan covers all 4 nodes? ✓ Task 1-3 explicit, Task 4 verifies. Task 5 documents.
2. **Placeholder scan:** no TBD, no "handle errors appropriately", every command written out? ✓
3. **Type consistency:** VMIDs match throughout (501 not 510, 502 not 520, 503, 505)? ✓
4. **Risk gate:** each task has an explicit failure/abort condition (Step 4.3 "if >80% STOP")? ✓
5. **Order rationale:** doing lowest-risk (sg) → low-risk (wt) → highest-risk (sc) with explicit reasoning? ✓
6. **Etcd quorum:** only one control-plane down at a time (Tasks 1 and 3 are CPs, Task 2 is worker; they execute sequentially)? ✓
7. **Rollback:** if sc-k3s shrink goes wrong, hotplug is enabled so `qm set 502 -memory 16384` is a live-recovery path? ✓
