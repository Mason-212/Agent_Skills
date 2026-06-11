---
name: edc-pr-test
description: Test ray-serve runtime changes in services/edc_inference_service of edc-python by deploying the PR's image as a private RayService on dev1 ray016, hitting it through the dev1 proxy with a real causal-discovery POST, verifying log output in Splunk, and bouncing pods on each /loop tick to track the latest image. Service name fixed to edc-inference-tn-test.
---

# EDC PR Test Loop

Test an `edc-python` PR's ray-serve image on the shared `ray016` cluster (dev1-uswest2 / einstein / ids) without touching the master `edc-inference` rayservice.

## When to use

- PR diff in `git.soma.salesforce.com/a360/edc-python` touches the ray-serve runtime under `services/edc_inference_service/` (`app/main.py`, `app/tasks/`, the FastAPI dispatcher — anything baked into the `edc-inference-ray` image).
- Sanity check before invoking: `gh pr diff <PR> --repo git.soma.salesforce.com/a360/edc-python --name-only` includes runtime paths under `services/edc_inference_service/`.

Skip if the diff is docs/tests/scripts only, outside `services/edc_inference_service/`, or targets a non-dev cluster.

## Hard-coded targets

> **Fork before use.** The `tn` in `edc-inference-tn-test` is the original author's initials. Two engineers on the same cluster sharing one test rayservice will overwrite each other's deploys. Fork this skill, replace `tn` with your own initials (`metadata.name`, `rayservice` header, kubectl label selector, Splunk pod-name glob — all references), and re-pin in your local `~/.claude/skills/`. The `falcon-k8s` and `edc-splunk-tail` skills are cluster-scoped and don't need per-engineer adaptation, but verify the index macro arg matches your FI before trusting Splunk results (see `edc-splunk-tail` "Index macros" section).

| Field | Value |
| --- | --- |
| Cluster / namespace | `ray016` / `ids` (FI `dev1-uswest2`, FD `einstein`) |
| Falcon context | `ray016_dev1_uswest2_einstein` |
| PCSK role | `PCSKAdministratorAccessRole` |
| Test rayservice name | `edc-inference-tn-test` |
| Image repo | `871501607754.dkr.ecr.us-west-2.amazonaws.com/sfci/a360/edc-python/edc-inference-ray` (Strata stage ECR, ray016 has pull access) |
| Tag pattern | `jenkins-a360-edc-python-PR-<PR>-latest-itest` (floating, default) or `...-<build>-itest` (pinned) |
| Proxy URL | `https://ray016.sfproxy.einstein.dev1-uswest2.aws.sfdc.cl/serving/` |
| `rayservice` header | `edc-inference-tn-test` |
| Splunk API | `https://splunk-api-preprod.log-analytics.monitoring.aws-esvc1-useast2.aws.sfdc.cl` |
| Splunk filter | `` `indexes_for_distapps("dev1-uswest2")` functional_domain=einstein k8s_cluster=sam-processing*1 k8s_namespace=ids k8s_pod_name=<rayservice-name>* `` (macro form — `falcon_instance=` is encoded in the macro arg, see `edc-splunk-tail` for details) |

If the user's request implies different values, stop and ask — these are constant for safety.

## Tag choice (read once)

The cluster pulls images with `imagePullPolicy: Always`. Combined with the floating `latest-itest` tag, **`kubectl delete pod` is enough to pick up a new build** — no YAML edit, no re-apply. That's why the loop is cheap.

- **Default: floating `latest-itest` tag.** Pod-bounce refresh works.
- **Pinned `<build>-itest` tag** only when reproducibility matters (bug repro tied to a specific build). Pod-bounce is a no-op in this mode — must re-render YAML and re-apply.

## ~~Local-build shortcut~~ — does not work

~~Skip the ~75min CI cycle by building `Dockerfile.ray` locally (`docker buildx --platform=linux/amd64`), pushing to ECR `871501607754`, and bouncing pods.~~

**Don't try this.** Confirmed 2026-06-09: the PCSK `PCSKAdministratorAccessRole` has read-only access to `871501607754.dkr.ecr.us-west-2.amazonaws.com/sfci/a360/edc-python/edc-inference-ray`. `docker push` returns `denied: User ... is not authorized to perform: ecr:InitiateLayerUpload ... because no resource-based policy allows the ecr:InitiateLayerUpload action`. The Strata stage ECR's resource policy only grants write to Jenkins-issued credentials; that's intentional.

The local cross-arch buildx itself works fine (~12-14 min first build, 5-12 min subsequent — `uv sync` re-runs whenever any repo file changes invalidate `COPY . .`), it's just non-deployable. Push is the dead end, not the build. Wait for CI.

## Strata Jenkins polling gotchas

`get_build_status` and `get_worker_build_logs` interact in ways that can mislead a polling agent. Confirmed 2026-06-09 watching PR #856 #36 / PR #876 #2:

1. **`Invoke worker job: SUCCESS` is dispatch, not verdict.** The outer Strata pipeline reports the inner `Invoke worker job` stage as SUCCESS the moment the worker is *queued* — even if the worker's `pyright`, `pytest`, or `ruff` later fail. Always re-check `get_worker_build_logs` after the *overall* build flips out of `BUILDING`, then grep for `error:`, `FAILED`, `pyright`, `pytest`. Don't trust the outer SUCCESS alone.

2. **`get_worker_build_logs` 404 is also the "no errors to report" signal.** The MCP wraps `fetch_error_details` — a 404 *also* fires when the worker exists but has no failure logs to surface. So 404 covers two states: "worker job hasn't been created yet" (during outer Build stage) and "worker is healthy, nothing to report" (during/after Package stage). To disambiguate, check the outer build's stage list: a `Build (SUCCESS)` completed stage in `get_build_status` rules out the first case. Polling agents should retry on 404 only when stage list is short; treat 404 + `Build (SUCCESS)` as a green worker.

3. **Subagent permission gotcha.** A subagent without explicit permission for `mcp__plugin_falcon_vmcp-falcon__get_worker_build_logs` sees Claude's `permission denied`, which is indistinguishable in tone from Jenkins' 404. If you spawn a polling agent that needs the worker verdict, grant that tool in its allowed list — otherwise it'll silently fall back to the unreliable outer status.

4. **`Estimated Remaining` is cached, not live.** Strata's `get_build_status` returns an `Estimated Remaining` field that comes from the job's historical median and never decrements during a single build. Confirmed 2026-06-09 — value identical at 13:18 PDT and 15:19 PDT for PR #856 #36. Don't use it as a progress signal. Use the `Completed Stages` list instead.

5. **The worker job URL is not directly query-able.** `https://.../job/worker/.../PR-<n>/<build>/` returns 404 from `get_build_status`; only `get_worker_build_logs` can address it. So the only liveness signal during/after Package is the outer stage list and `get_published_artifacts` (which returns "None" status until Package completes).

6. **`devbar auth login` token expires mid-session.** The MCP returns `upstream HTTP 401: not authenticated — run 'devbar auth login' and retry`. Re-auth is a browser SSO; from inside the harness, prompt the user to type `! devbar auth login`. Tokens last ~1 hour in practice.

## Prerequisites

- `falcon-k8s` skill has been run for `ray016_dev1_uswest2_einstein` with `PCSKAdministratorAccessRole`. Verify with `kubectl config view --minify`; route to `falcon-k8s` if wrong.
- `gh` CLI logged into `git.soma.salesforce.com`.

## Modes

`kubectl get rayservice edc-inference-tn-test -n ids` decides:

- **Doesn't exist → deploy mode** (steps 1–9).
- **Exists → refresh mode** (steps 7–9 only: bounce + verify + Splunk).

## Deploy mode

### 1. Resolve the PR

```bash
PR=<NUMBER>     # the edc-python PR you're testing
gh pr view "$PR" --repo git.soma.salesforce.com/a360/edc-python \
  --json headRefName,headRefOid,state,title
```

### 2. Find the image tag

Use the falcon MCP server (it authenticates to Strata Jenkins natively; `curl` would hit OIDC redirect and return HTML).

```
job_url = https://sfcirelease.sfci.buildndeliver-s.aws-esvc1-useast2.aws.sfdc.cl/strata-a360/job/a360/job/edc-python/job/PR-<PR>/
```

1. `mcp__plugin_falcon_vmcp-falcon__list_builds_for_job(job_url)` → recent builds.
2. `mcp__plugin_falcon_vmcp-falcon__get_build_status(build_url)` for each, walking down to find the most recent `SUCCESS`.
3. `mcp__plugin_falcon_vmcp-falcon__get_published_artifacts(build_url)` on that build → filter to `Path: ./services/edc_inference_service/Dockerfile.ray` and ECR `871501607754.*`. Pick the floating tag (ends in `-latest-itest`) by default.

Set `IMAGE` to the full URL.

### 3. Pre-flight

```bash
kubectl config view --minify | grep -E 'namespace|cluster'
kubectl get rayservice edc-inference -n ids -o name
```

Both must succeed.

### 4. Render the manifest

Export the master, rewrite name + image, drop server-managed fields. Show the result back to the user — `metadata.name` must be `edc-inference-tn-test` and both container images must be the new tag, otherwise abort.

```bash
WORKDIR="$(mktemp -d -t edc-pr-test.XXXXXX)"
kubectl get rayservice edc-inference -n ids -o yaml > "$WORKDIR/edc-inference.yaml"

IMAGE="<from step 2>" yq -i '
  .metadata.name = "edc-inference-tn-test" |
  .metadata.annotations["artifact.spinnaker.io/name"] = "edc-inference-tn-test" |
  del(.metadata.annotations["kubectl.kubernetes.io/last-applied-configuration"]) |
  del(.metadata.resourceVersion, .metadata.uid, .metadata.creationTimestamp,
      .metadata.generation, .metadata.selfLink, .status) |
  (.spec.rayClusterConfig.headGroupSpec.template.spec.containers[]
     | select(.name == "ray-head").image) = strenv(IMAGE) |
  (.spec.rayClusterConfig.workerGroupSpecs[].template.spec.containers[]
     | select(.name == "ray-worker").image) = strenv(IMAGE)
' "$WORKDIR/edc-inference.yaml"
```

### 5. Apply

```bash
kubectl apply -f "$WORKDIR/edc-inference.yaml" -n ids
```

If `metadata.name` ever resolves to `edc-inference`, abort — that overwrites the shared service.

### 6. Wait for ready

```bash
kubectl wait --for=condition=Ready --timeout=10m rayservice/edc-inference-tn-test -n ids
```

Snapshot while waiting:

```bash
kubectl get pods -n ids -l ray.io/cluster=edc-inference-tn-test
kubectl get rayservice edc-inference-tn-test -n ids \
  -o jsonpath='{.status.activeServiceStatus.applicationStatuses}'
```

### 7. Bounce pods (also the entry point for refresh mode)

```bash
kubectl delete pods -n ids -l ray.io/cluster=edc-inference-tn-test
```

Then wait again as in step 6. (No-op if the deployed image uses a pinned tag — see "Tag choice" above.)

### 8. Verify with a real POST

Capture `T0=$(date '+%s')` immediately before, then:

```bash
curl -sS -X POST 'https://ray016.sfproxy.einstein.dev1-uswest2.aws.sfdc.cl/serving/' \
  -H 'accept: application/json' \
  -H 'rayservice: edc-inference-tn-test' \
  -H 'ray-app-path: /api/v1' \
  -H 'ray-app-endpoint: async-tasks' \
  -H 'x-request-timeout-mins: 10' \
  -H 'Content-Type: application/json' \
  -d '{
    "taskId": "graph-discovery-seeded-001",
    "data": {
      "taskType": "causalAnalysis",
      "operation": "discover",
      "algorithmName": "auto",
      "input": {"sourceType": "DATA_CLOUD_SQL", "dataspaceName": "default", "query": "SELECT 1"},
      "ontology": {"seedGraph": {"graph": {"graphFamily": "DAG",
        "edges": [{"source": "campaign_to_revenue_contribution_score",
                   "target": "monthly_recurring_revenue_score"}]}}}
    }
  }'
```

Expect 202. Browser-automation alternative: navigate to `/docs` on the same proxy and use Swagger UI's "Try it out".

On 4xx/5xx, dump head pod logs first:
```bash
kubectl logs -n ids -l ray.io/node-type=head,ray.io/cluster=edc-inference-tn-test --tail=200
```

### 9. Verify in Splunk

A 202 only proves the envelope was accepted. Confirm the dispatcher routed and the executor ran via `mcp__plugin_monitoring_vmcp-monitoring__query_splunk`:

```
splunk_api_base_url: https://splunk-api-preprod.log-analytics.monitoring.aws-esvc1-useast2.aws.sfdc.cl
query: search `indexes_for_distapps("dev1-uswest2")` functional_domain=einstein
       k8s_cluster=sam-processing*1 k8s_namespace=ids
       k8s_pod_name=edc-inference-tn-test*
       earliest=<T0-5> latest=<T0+5>
columns: ["_time", "_raw", "k8s_pod_name", "k8s_container_name"]
```

(Macro form is the new standard as of 2026-04-08; verified empirically and ~39% faster on larger queries. See `edc-splunk-tail` for the full rationale and fallback behavior. Legacy `index=distapps falcon_instance=dev1-uswest2` still works as a fallback if the macro returns 0 rows.)

**Two failure modes that look identical to "service emitted nothing":**

1. **`k8s_pod_name` glob mismatch.** Pods are named `<rayservice-name>-...-head-...` / `...-worker-...`, so the glob has to be `<rayservice-name>*`. If the user renamed the test service, the filter has to track. Resolve dynamically: `kubectl get rayservice -n ids -o name | grep -v '/edc-inference$'`.
2. **Wrong timezone.** Splunk preprod resolves relative tokens in PST/PDT — same as local. Don't pass UTC; epoch seconds (`date '+%s'`) sidestep the question.

Refinements:
- Trace one request: append `"<taskId>"`.
- Confirm executor branch: append `("PC" OR "HillClimb" OR algorithm_name)`.
- Errors only: append `(level=ERROR OR Exception OR Traceback)`.
- Worker only (skip head startup chatter): `k8s_container_name=ray-worker`.

If 0 rows, widen to `±30s` once before assuming silence is a real signal. Standalone `edc-splunk-tail` skill covers the same query shape outside the deploy loop.

## Refresh mode

Existing test service, want to pick up a newer image build:

```bash
kubectl get rayservice edc-inference-tn-test -n ids -o name || exit 1
# Pre-flight: bounce only works on a floating tag
kubectl get rayservice edc-inference-tn-test -n ids \
  -o jsonpath='{.spec.rayClusterConfig.headGroupSpec.template.spec.containers[?(@.name=="ray-head")].image}' \
  | grep -q 'latest-itest$' || {
    echo "Pinned tag deployed — bounce won't refresh. Re-deploy with a new tag instead."; exit 1;
  }
kubectl delete pods -n ids -l ray.io/cluster=edc-inference-tn-test
# Then steps 6 → 8 → 9
```

## Recurring loop

`/loop 10m /edc-pr-test refresh` bounces every 10 min so new builds get pulled within one tick. `/loop stop` when done — bounce is cheap but interrupts in-flight requests.

## Density-routing integration suite

Run after the routing-revival commit (W-22816211, PR #856) lands and CI republishes the floating tag. Three POSTs, one per route, each verified through Splunk. Unit tests cover the gate's decision logic in isolation; this suite covers everything that happens *outside* the Python process — the Ray actor jump, the rsyslog sidecar, the FastAPI exception handler, the structured-log field preservation through `cd6c1887`'s logger attach.

Capture a fresh `T0=$(date '+%s')` immediately before each POST. Splunk window is ±5s, so requests must not share one.

### Route A — RUN_PC (sparse, no seeds)

```bash
T0=$(date '+%s')
curl -sS -X POST 'https://ray016.sfproxy.einstein.dev1-uswest2.aws.sfdc.cl/serving/' \
  -H 'accept: application/json' \
  -H 'rayservice: edc-inference-tn-test' \
  -H 'ray-app-path: /api/v1' \
  -H 'ray-app-endpoint: async-tasks' \
  -H 'x-request-timeout-mins: 10' \
  -H 'Content-Type: application/json' \
  -d '{
    "taskId": "route-test-pc-001",
    "data": {
      "taskType": "causalAnalysis",
      "operation": "discover",
      "algorithmName": "auto",
      "input": {"sourceType": "DATA_CLOUD_SQL", "dataspaceName": "default", "query": "SELECT 1"}
    }
  }'
```

Splunk query (taskId-scoped, ±5s):

```
search `indexes_for_distapps("dev1-uswest2")` functional_domain=einstein
       k8s_cluster=sam-processing*1 k8s_namespace=ids
       k8s_pod_name=edc-inference-tn-test*
       "route-test-pc-001"
       earliest=<T0-5> latest=<T0+5>
```

Expected events:
- `flow_step=01_dispatch_start`, `02_ray_task_submitted` (head pod)
- `flow_step=02b_route_decided` with `route=RUN_PC`, `final_density<0.30`
- `flow_step=04_executor_start` (worker pod, PC branch)
- `flow_step=98_ray_worker_finished` with `algorithm_name=PC`

If `route=RUN_MMHC` lands instead → `d_pc` is too tight for the stub fixture; calibration issue, not wiring.

### Route B — RUN_MMHC (seeded)

Same body shape as Step 8 — `taskId: "route-test-mmhc-001"`, seed edge already present. Splunk should show:
- `flow_step=02b_route_decided` with `route=RUN_MMHC` (no density eval — seed_edges short-circuits)
- existing MMHC flow_steps to completion

### Route C — ROUTE_TO_LLM (dense)

The CSV stub fixture is sparse — the gate won't naturally route to LLM. Three options to force it; pick one:

1. **Threshold override (preferred for first verification)**: redeploy `edc-inference-tn-test` with `EDC_PRECHECK_D_LLM=0.0` so any non-trivial frame routes to LLM. Smokes the wiring; doesn't validate the threshold value itself.
2. **Wide synthetic fixture**: extend the dispatcher's stub-fixture loader to accept `fixtureName` and ship a "dense_50col" CSV. Right long-term shape; new code.
3. **Skip until #849 lands**: LLM dispatch raises `NotImplementedError` today, so its only observable behavior is `02b_route_decided` + `99_ray_worker_failed`. Option 1 covers both.

Splunk assertions (option 1):
- `flow_step=02b_route_decided` with `route=ROUTE_TO_LLM`, `final_density > d_llm`
- `flow_step=99_ray_worker_failed` with `NotImplementedError` and the gate's exception message
- HTTP 501 from the proxy (verify against FastAPI's exception handler — 500 means the handler isn't wired for `NotImplementedError`, separate fix)

### Triage table

| Symptom | Likely cause |
|---|---|
| `02b_route_decided` missing | `decide_route` not wired into `run_causal_discovery_pipeline` |
| `02b_route_decided` present, no downstream `04_executor_start` | Ray remote handle not awaited, or route switch raised silently — check head pod logs |
| All three routes report the same `route` | `PreCheckThresholds` defaults mis-tuned, or gate not reading the dataclass — log `corr_density` / `k2_density_used` / `final_density` to confirm |
| `02b_route_decided` appears before `01_dispatch_start` | Two test requests overlap in the same Splunk window — re-capture `T0` per route |

## Cleanup

```bash
kubectl delete rayservice edc-inference-tn-test -n ids
```

Confirm with the user first; don't delete an in-flight test service.

### Stalled-build cleanup

If the CI build feeding the test rayservice stalls for more than 2 hours (judge by the `Completed Stages` list, not `Estimated Remaining` — see gotcha #4 above), proactively tear down the test rayservice with the cleanup command instead of leaving it idle. A test service consuming head + worker pods on `ray016` for hours without serving real requests wastes cluster capacity. Re-run deploy mode after a fresh image publishes.

## Safety checks (every run)

1. Rendered `metadata.name == "edc-inference-tn-test"` exactly. Never `edc-inference`. Refuse to apply otherwise.
2. kubectl namespace is `ids`, cluster maps to `ray016`. Else route to `falcon-k8s`.
3. Image starts with `871501607754.dkr.ecr.us-west-2.amazonaws.com/sfci/a360/edc-python/edc-inference-ray:`.
4. Never run on a non-dev FI — proxy URL only resolves on dev1.

## Related

- `falcon-k8s` — kubectl context setup
- `edc-splunk-tail` — standalone Splunk queries when not running this loop
