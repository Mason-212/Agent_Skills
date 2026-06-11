---
name: edc-splunk-tail
description: Query Splunk logs for the edc-inference-service ray pods on dev1 ray016 via the monitoring MCP server. Filters by k8s_pod_name (must match the deployed RayService name) and supports tailing by task ID, error level, branch (PC vs MMHC), or arbitrary SPL refinement. Use when verifying that ray-serve logging statements fired as expected, after a POST through the dev1 proxy, or to debug a behavior that the kubectl logs view doesn't surface.
---

# EDC Splunk Tail

> Lightweight wrapper around `mcp__plugin_monitoring_vmcp-monitoring__query_splunk` for the `edc-inference-service` ray pods. The verification flow inside `edc-pr-test` (Step 9) is the same shape as this skill — use this one when you don't need the full deploy/refresh loop, just the logs.

## When to Use

- You ran a request through the dev1 ray016 proxy (or directly from a kubectl exec) and want to confirm the service logged what you expected — dispatcher routing, executor branch (PC vs MMHC), task completion, error tracebacks.
- `kubectl logs` is showing only the head pod's startup output, but the actual work happens on a worker pod and you want all containers in one view.
- You're investigating a past failure (within 15 days) where the pod has since been bounced — Splunk has the history that `kubectl logs` doesn't.

## When NOT to Use

- Real-time pod tailing while iterating — `kubectl logs -f` is faster and cheaper.
- Logs older than 15 days — outside the MCP's search scope.
- Anything outside the dev1 `ray016` cluster — this skill hardcodes the filter.

## Hard-coded query inputs

| Field | Value |
| --- | --- |
| MCP tool | `mcp__plugin_monitoring_vmcp-monitoring__query_splunk` |
| `splunk_api_base_url` | `https://splunk-api-preprod.log-analytics.monitoring.aws-esvc1-useast2.aws.sfdc.cl` |
| Index selector | `` `indexes_for_distapps("dev1-uswest2")` `` — backtick-wrapped macro with FI argument (replaces `index=distapps falcon_instance=dev1-uswest2`; see "Index macros" below). **Verified against `edc-inference-tn-test*` pods 2026-06-10.** Do **not** use `index=*` — the MCP rejects it. |
| `functional_domain` | `einstein` |
| `k8s_cluster` | `sam-processing*1` |
| `k8s_namespace` | `ids` |
| `k8s_pod_name` | **derived dynamically** — see below |

## Index macros (new convention as of 2026-04-08, non-CDP rollout)

> **Verified empirically against our cluster on 2026-06-10.** Bare `dev1-uswest2` is the correct macro arg (the announcement docs and a coworker's PDF claimed `aws-`-prefixed; that returns 0 rows). Macro and legacy parse identically at small windows (~13s `head 5` over 30m); macro is ~39% faster on a 2h `head 10 level=INFO` query (14.5s vs 23.8s). **Use the macro form going forward — it's the new standard, drop-in compatible, and at worst the same speed as legacy.**

The IaC team is migrating off hardcoded `index=distapps` to dynamic macros that target the right backing indexes. Macros search both legacy `distapps` and any new dedicated indexes simultaneously, so they're safe drop-ins. CDP queries got their own announcement on Apr 9, 2026 with a hard cutover deadline of April 30, 2026; non-CDP service groups (us — `functional_domain=einstein`) got the macros on Apr 8, 2026 with no hard deadline, but aligning now avoids a forced migration later.

| Macro | Use when | Speed |
|-------|----------|-------|
| `` `indexes_for_distapps("<fi>")` `` | Specific Falcon Instance (we use this) | Fastest — up to ~2× faster on larger queries |
| `` `indexes_for_distapps("<fi1>", "<fi2>", ...)` `` | 2–5 specific Falcon Instances | Fast |
| `` `indexes_for_distapps_all_fi` `` | All Falcon Instances (no parentheses, no args) | Medium |
| `` `indexes_for_distapps` `` | Legacy catch-all, no FI scoping (no parentheses) | Slowest — same as old `index=distapps` |
| `` `indexes_for_servicegroup("cdp", "<fi>")` `` | **CDP only** — errors on any other service group | Fastest for CDP |
| `` `from_index_distapps` `` | **Deprecated** — replace with `` `indexes_for_distapps` `` | Don't use |

**For this skill** we use `` `indexes_for_distapps("dev1-uswest2")` `` — the fastest non-CDP form. Two important things:

1. **`falcon_instance=` filter is removed from the query.** It's now encoded as the macro argument. Keeping both is redundant; the macro is source-of-truth.
2. **Argument is the bare FI form** (`dev1-uswest2`), not the `aws-`-prefixed form. Verified empirically: `indexes_for_distapps("aws-dev1-uswest2")` returns 0 rows, `indexes_for_distapps("dev1-uswest2")` returns the expected pod logs. The PDF and some announcement examples used `aws-` — they're wrong for this FI. If extending to other FIs, sanity-check the arg shape with a one-row probe before trusting it.

`indexes_for_servicegroup` is **CDP-only** — it errors with `Invalid service_group. Currently only "cdp" is supported` for any other value. Don't try `("einstein", ...)` etc.

**Macro syntax notes:**
- Backticks are **mandatory** — `` `indexes_for_distapps("dev1-uswest2")` ``, not single quotes. Splunk evaluates backtick-wrapped tokens as macros at parse time; single quotes silently fail.
- The `_all_fi` and bare-name (catch-all) forms take **no parentheses**: `` `indexes_for_distapps_all_fi` ``, `` `indexes_for_distapps` ``. Argument forms do: `` `indexes_for_distapps("...")` ``.
- When calling Splunk via API/SDK (e.g. Python `splunklib`), specify a Splunk app context — macros may not resolve in the default system context (`"the macro has not been shared with this application"`). The monitoring MCP handles this transparently in our experience. If a query returns the macro-resolution error, fall back to legacy `index=distapps` for that call and flag it.

### Note on preprod rollout

The CDP announcement listed performance gains as "Noncore (prod) only initially — preprod and GIA2H may follow but timeline is not decided." Our cluster is `dev1-uswest2` → preprod. We saw ~39% speedup on a 2h INFO query and parity at smaller scales, so the macros do route to dedicated indexes here, at least partially. Don't promise prod-grade 2–3× speedups based on preprod alone.

## Critical: `k8s_pod_name` glob must match the deployed RayService

Pods are named `<rayservice-name>-...-head-...` / `<rayservice-name>-...-worker-...`. The Splunk filter glob must be `<rayservice-name>*`. If it doesn't match, you get **0 rows back, indistinguishable from "the service is broken"** — silent miss, very misleading.

Before any query, resolve the actual name:

```bash
kubectl get rayservice -n ids -o name | grep -v '/edc-inference$'
```

(That excludes the master `edc-inference` rayservice. The remainder are user test services like `edc-inference-tn-test` or `edc-inference-tuan-test`.) If multiple match, ask the user which one. If none match and the user hasn't named one, route them to `edc-pr-test` deploy mode first.

## Core query template

```
search `indexes_for_distapps("dev1-uswest2")`
       functional_domain=einstein
       k8s_cluster=sam-processing*1
       k8s_namespace=ids
       k8s_pod_name=<RAYSERVICE_NAME>*
       earliest=<RANGE_START>
       latest=<RANGE_END>
```

(Note: no `falcon_instance=` filter — encoded in the macro arg.)

**Time window — pin to ±5 seconds around the request, in PST.** Wide windows are the second-most-common cause of "I can't find my log" (after the `k8s_pod_name` glob mismatch), because the test pod has chatter from earlier traffic.

Recommended workflow:

1. Capture epoch seconds **immediately before** the request you want to trace: `date '+%s'`. Save as `T0`.
2. Query with `earliest=<T0 - 5> latest=<T0 + 5>` — epoch seconds, no timezone conversion needed.
3. If 0 rows, widen to ±30s once. Ray task scheduling can push log emission by a couple of seconds.

Splunk relative tokens (`-15m`, `now`, etc.) resolve in PST/PDT for preprod, matching the user's local clock. **Do not use UTC** — the user's browser URL and the MCP both default to PST, and a UTC offset silently shifts the window 7–8h and returns 0 rows. Epoch seconds sidestep this entirely.

For investigating a past incident where you don't know the exact moment, fall back to `earliest=-1h latest=now` and narrow with the taskId.

## Common refinements

Append to the base query as needed. Combine with `AND` / parens.

| Goal | Append |
|------|--------|
| Trace a single request end-to-end | `"<taskId>"` (the taskId from your POST body — propagates through dispatcher and Ray task logs) |
| Confirm executor branch | `("PC" OR "HillClimb" OR algorithm_name)` |
| Errors only | `(level=ERROR OR ERROR OR Exception OR Traceback)` |
| Ray task body only (skip head-pod startup chatter) | `k8s_container_name=ray-worker` |
| Dispatcher / FastAPI router | `k8s_container_name=ray-head` |
| Specific log line | quote the literal string, e.g. `"causal_discovery_executor:dispatching"` |

## Calling the MCP

```
mcp__plugin_monitoring_vmcp-monitoring__query_splunk(
  splunk_api_base_url="https://splunk-api-preprod.log-analytics.monitoring.aws-esvc1-useast2.aws.sfdc.cl",
  query="search `indexes_for_distapps(\"dev1-uswest2\")` functional_domain=einstein k8s_cluster=sam-processing*1 k8s_namespace=ids k8s_pod_name=<RAYSERVICE_NAME>* earliest=-15m latest=now",
  columns=["_time", "_raw", "k8s_pod_name", "k8s_container_name"]
)
```

The backticks around the macro must be preserved verbatim in the JSON string. The double-quotes around the FI arg need to be escaped (`\"`) inside the JSON. If you build the query in shell, prefer single quotes around the whole query so zsh doesn't try to interpret the backticks as command substitution.

Recommended `columns` set: `["_time", "_raw", "k8s_pod_name", "k8s_container_name"]`. Drop `k8s_container_name` if you've already filtered to one. Add `level` if you need to scan severity.

## Operational caveats (from the MCP itself)

- Don't use `index=*` — the index selector must be a backtick-wrapped macro (preferred) or `index=distapps` (legacy fallback only). The MCP rejects wildcard index.
- Search scope is the last 15 days.
- Result cap is 500 lines. If hunting for a needle, narrow with the taskId or container name first.
- Stats queries are capped at 5000 events.
- Query timeout is 60s; the service account is capped at 4 concurrent queries to Splunk.

## Empty-result diagnostics

If a query returns 0 rows, walk down this list before concluding "the service didn't log":

1. **`k8s_pod_name` glob mismatch** — the most common cause. Re-run `kubectl get rayservice -n ids` and compare. Pods named `<rayservice-name>-...-head-...` have to start with the rayservice name.
2. **Pod was bounced and the old name is gone** — the test service may have been recreated under a different name. Re-resolve.
3. **Time window doesn't cover the request** — POST happened earlier than `earliest`. Widen.
4. **Service genuinely isn't running** — `kubectl get pods -n ids -l ray.io/cluster=<RAYSERVICE_NAME>` should show pods in `Running` state. If it doesn't, this skill won't help — fix the deploy first via `edc-pr-test`.
5. **Splunk ingestion lag** — rare but possible. Wait ~30s and retry once.

## Browser fallback

If the MCP is unavailable or returns an unexpected error, the browser equivalent is:

```
https://splunk-web-preprod.log-analytics.monitoring.aws-esvc1-useast2.aws.sfdc.cl/en-US/app/search/search?q=search%20%60indexes_for_distapps(%22dev1-uswest2%22)%60%20functional_domain%3Deinstein%20k8s_cluster%3Dsam-processing*1%20k8s_namespace%3Dids%20k8s_pod_name%3D<RAYSERVICE_NAME>*&earliest=-15m&latest=now
```

(`%60` is the URL-encoded backtick around the macro; `%22` is the URL-encoded double quote around the FI arg. Don't add `falcon_instance=` — it's encoded in the macro arg.)

Prefer the MCP path — structured JSON beats screenshots when summarizing back.

## Related

- `edc-pr-test` Step 9 uses this same query shape inline. If the user is in the middle of a PR test loop, route there instead.
- `monitoring:splunk-logs-missing-host-service` — diagnoses the case where you'd expect logs but Splunk has no records of the host/service at all (different problem from "wrong glob").
