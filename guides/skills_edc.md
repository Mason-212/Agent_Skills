# EDC Skills Guide

> **Salesforce-specific:** These skills are for internal Salesforce infrastructure (Falcon, PCSK, Strata). They work with the `edc-python` repository's ray-serve deployments on the einstein functional domain.

## At a Glance

| Skill | Purpose | When to Use |
|---|---|---|
| **falcon-k8s** | Configure kubectl + falcon credentials for a Falcon-managed namespace. Prereq for the EDC skills. | First step: connecting to any Falcon cluster |
| **edc-pr-test** | Deploy an edc-python PR's image as a private RayService on ray016, POST through the dev1 proxy, verify in Splunk, bounce on each /loop tick. | Testing ray-serve runtime changes in PRs |
| **edc-splunk-tail** | Standalone Splunk wrapper around the monitoring MCP for the same ray pods. Use when you don't need the full deploy loop. | Verifying logs after a request, investigating past failures |

---

## Hard-coded Targets

All EDC skills target the same cluster/namespace:

| Field | Value |
|---|---|
| **Falcon Instance** | `dev1-uswest2` |
| **Functional Domain** | `einstein` |
| **Cluster** | `ray016` |
| **Namespace** | `ids` |
| **Falcon Context** | `ray016_dev1_uswest2_einstein` |
| **PCSK Role** | `PCSKAdministratorAccessRole` |
| **Proxy URL** | `https://ray016.sfproxy.einstein.dev1-uswest2.aws.sfdc.cl/serving/` |
| **Splunk API** | `https://splunk-api-preprod.log-analytics.monitoring.aws-esvc1-useast2.aws.sfdc.cl` |

---

## Workflow Integration

### Quick Test Flow (One-time Setup + Verify)

```
1. /falcon-k8s → Connect kubectl to ray016
2. /edc-pr-test → Deploy PR image to private RayService
3. POST test request through proxy
4. Verify logs appear in Splunk
```

### Recurring Test Loop

```
1. /falcon-k8s → Connect kubectl to ray016
2. /edc-pr-test → Initial deploy
3. /loop 10m /edc-pr-test refresh → Auto-bounce pods every 10 min to pick up latest CI builds
4. POST test requests between ticks
5. /edc-splunk-tail → Query specific taskId logs
6. /loop stop → When done
```

### Standalone Log Investigation

```
1. /falcon-k8s → Connect kubectl to ray016
2. /edc-splunk-tail → Query Splunk for specific time window, taskId, or error pattern
```

---

## Phase Diagram

```
Setup → Deploy → Test → Verify → Iterate
  ↓       ↓       ↓       ↓         ↓
falcon  edc-pr  POST   edc-spl   /loop
-k8s    -test   req    unk-tail  refresh
```

---

## Key Concepts

### 1. Test RayService Naming (Critical)

**`edc-pr-test` uses a hard-coded test service name that you MUST customize:**

- Default: `edc-inference-tn-test` (where `tn` = original author's initials)
- **Fork before use:** Replace `tn` with your own initials in the skill
- **Why:** Two engineers sharing one test service will overwrite each other's deploys
- **Where to update:** `metadata.name`, `rayservice` header, kubectl label selector, Splunk pod-name glob

The master service `edc-inference` is never touched — your test service runs in parallel.

### 2. Image Tag Strategy

**Floating tag (default):**
- Tag: `jenkins-a360-edc-python-PR-<PR>-latest-itest`
- Behavior: `kubectl delete pod` picks up newest CI build (no YAML edit needed)
- Use: Normal inner-loop testing

**Pinned tag (reproducibility):**
- Tag: `jenkins-a360-edc-python-PR-<PR>-<build>-itest`
- Behavior: Pod bounce is no-op; must re-render YAML and re-apply
- Use: Bug repro tied to specific build

### 3. Splunk Index Macros (New Convention)

**As of 2026-04-08, use macro form:**

```spl
`indexes_for_distapps("dev1-uswest2")`
```

**NOT the legacy form:**
```spl
index=distapps falcon_instance=dev1-uswest2
```

**Key differences:**
- Backticks mandatory (`` `...` ``)
- FI argument is bare form: `"dev1-uswest2"` (NOT `"aws-dev1-uswest2"`)
- No separate `falcon_instance=` filter (encoded in macro arg)
- ~39% faster on large queries

### 4. Pod Name Matching (Most Common Failure)

**Splunk queries return 0 rows if the pod name glob doesn't match:**

Pods are named: `<rayservice-name>-...-head-...` / `<rayservice-name>-...-worker-...`

Query must use: `k8s_pod_name=<rayservice-name>*`

**Always resolve dynamically before querying:**
```bash
kubectl get rayservice -n ids -o name | grep -v '/edc-inference$'
```

### 5. Time Windows in Splunk

**Best practice:** Pin to ±5 seconds around the request in epoch seconds

```bash
T0=$(date '+%s')  # Capture BEFORE the request
# ...make request...
# Query with: earliest=$((T0 - 5)) latest=$((T0 + 5))
```

**Why:**
- Splunk relative tokens (`-15m`, `now`) resolve in PST/PDT
- Test pods have chatter from earlier traffic
- Wide windows mix unrelated logs

If 0 rows, widen to ±30s once (Ray task scheduling delay).

---

## Prerequisites

### Before Using Any EDC Skill

1. **Falcon CLI** installed: https://docs.internal.salesforce.com/falcon/cli/home/
2. **kubectl** installed: https://kubernetes.io/docs/tasks/tools/install-kubectl-macos/
3. **PCSK Access:**
   - Active permissions in PCSK (not exported as environment variables)
   - If you have AWS credentials exported in your current terminal, start a new session
4. **gh CLI** logged into `git.soma.salesforce.com` (for edc-pr-test)
5. **devbar CLI** authenticated (for Strata Jenkins queries): `devbar auth login`

### PCSK Account Question

**None of the skills document which PCSK account to request initially.** They assume you've already completed PCSK onboarding.

**To determine which account you need:**
1. Ask your team which Falcon Instance/Functional Domain you'll work in
2. Run: `falcon context show --all`
3. Find the matching FI/FD row and note the **Account Id** column
4. Request PCSK access to that specific AWS account

---

## Common Operations

### Deploy a New Test Service

```bash
/falcon-k8s
# Answer: ray016_dev1_uswest2_einstein
# Answer: PCSKAdministratorAccessRole

/edc-pr-test
# Provide: PR number (e.g., 856)
# Skill resolves image tag, renders manifest, applies, waits for ready
# Makes test POST, verifies in Splunk
```

### Refresh Existing Test Service (Pick Up Latest Build)

```bash
/edc-pr-test refresh
# Bounces pods (floating tag → pulls latest image)
# Waits for ready, POSTs, verifies
```

### Recurring Test Loop

```bash
/loop 10m /edc-pr-test refresh
# Bounces every 10 min
# Make POSTs between ticks
# /loop stop when done
```

### Query Splunk for a Specific Request

```bash
/edc-splunk-tail
# Provide: taskId from your POST body
# Provide: time window (e.g., "last 15 minutes" or specific T0)
# Returns: logs filtered to that request
```

### Cleanup Test Service

```bash
kubectl delete rayservice edc-inference-tn-test -n ids
# (Replace 'tn' with your initials)
```

---

## Troubleshooting

### "0 rows from Splunk" Checklist

1. **Pod name mismatch** — Most common. Re-run `kubectl get rayservice -n ids` and verify glob
2. **Time window too narrow** — Widen to ±30s once
3. **Pod was bounced** — Old name is gone, re-resolve current rayservice name
4. **Service not running** — `kubectl get pods -n ids -l ray.io/cluster=<name>` should show Running pods
5. **Splunk ingestion lag** — Rare, wait ~30s and retry

### "Permission Denied" for MCP Tools

If a subagent can't access `mcp__plugin_falcon_vmcp-falcon__get_worker_build_logs`:
- Grant the tool in the subagent's allowed list
- Or run the query in the main agent context

### "devbar auth login" Token Expired

Tokens last ~1 hour. When Strata MCP returns `upstream HTTP 401`:
```bash
! devbar auth login
# (Runs in your terminal, SSO in browser)
```

### Can't Push to ECR

`PCSKAdministratorAccessRole` has **read-only** access to the Strata stage ECR. Local `docker build` works but `docker push` fails with `ecr:InitiateLayerUpload` denied. This is intentional — wait for Jenkins CI to build and publish.

### Stalled CI Build

If a build stalls for >2 hours (check `Completed Stages`, not `Estimated Remaining`):
- Tear down the test rayservice: `kubectl delete rayservice edc-inference-tn-test -n ids`
- Don't leave idle test services consuming cluster capacity
- Re-deploy after fresh image publishes

---

## Strata Jenkins Polling Gotchas

When using the Falcon MCP to query Jenkins build status:

1. **`Invoke worker job: SUCCESS` is dispatch, not verdict** — The outer stage reports SUCCESS when the worker is queued, even if tests later fail. Always re-check `get_worker_build_logs` after the build completes.

2. **`get_worker_build_logs` 404 has two meanings:**
   - "Worker job hasn't been created yet" (during Build stage)
   - "Worker is healthy, nothing to report" (during/after Package stage)
   - Disambiguate by checking outer build's stage list

3. **`Estimated Remaining` never decrements** — It's a cached historical median. Use `Completed Stages` list for progress.

4. **Worker job URL not directly queryable** — Only `get_worker_build_logs` can access it.

---

## Density-Routing Integration Suite

After routing-revival changes land (W-22816211, PR #856), verify all three routes:

### Route A — RUN_PC (sparse, no seeds)

```bash
T0=$(date '+%s')
curl -X POST 'https://ray016.sfproxy.einstein.dev1-uswest2.aws.sfdc.cl/serving/' \
  -H 'rayservice: edc-inference-tn-test' \
  -H 'ray-app-path: /api/v1' -H 'ray-app-endpoint: async-tasks' \
  -H 'Content-Type: application/json' \
  -d '{"taskId": "route-test-pc-001", "data": {"taskType": "causalAnalysis", ...}}'
```

**Expected in Splunk:**
- `flow_step=02b_route_decided` with `route=RUN_PC`, `final_density<0.30`
- `algorithm_name=PC`

### Route B — RUN_MMHC (seeded)

Same body with seed edges → `route=RUN_MMHC` (seed short-circuits density check)

### Route C — ROUTE_TO_LLM (dense)

Force via `EDC_PRECHECK_D_LLM=0.0` env override (CSV fixture is naturally sparse). Expected:
- `flow_step=02b_route_decided` with `route=ROUTE_TO_LLM`
- `NotImplementedError` (LLM dispatch not yet implemented)
- HTTP 501 from proxy

---

## Related Skills

- **falcon-k8s** — Foundation for all EDC workflows
- **edc-pr-test** — Deploy and test loop
- **edc-splunk-tail** — Standalone log queries
- **edc-splunk** — General Splunk query writer (uses knowledge base)

---

## Quick Selection Guide

| You want to... | Use |
|---|---|
| Connect to ray016 for the first time | `falcon-k8s` |
| Test a PR's ray-serve changes | `edc-pr-test` |
| Auto-refresh to pick up new CI builds | `/loop 10m /edc-pr-test refresh` |
| Verify logs for a specific request | `edc-splunk-tail` |
| Investigate a past failure | `edc-splunk-tail` (15-day retention) |
| Write a custom Splunk query | `edc-splunk` |
| Clean up your test service | `kubectl delete rayservice ...` |
