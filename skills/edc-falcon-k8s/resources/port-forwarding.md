# Port Forwarding

Instructions for port-forwarding to services in a Falcon-managed Kubernetes cluster.

## Prerequisites

kubectl must be configured and pointing to the correct namespace. If not, run the main falcon-k8s workflow first (Steps 1–9 in SKILL.md).

**Also required:** Docker Desktop must be running on your Mac — `kubectl` depends on it for local networking.

---

## Step 0: Check for Saved Service Configs

Before doing anything, list available saved service configs:

```bash
ls resources/.env.*.local 2>/dev/null   # inside the edc-falcon-k8s skill directory
```

Each file is named `.env.<service-name>.local`. If one or more exist, ask:

> "I found saved configs for: `<service-name-1>`, `<service-name-2>`, ...
> Which service do you want to connect to? (or 'new' to set up a new one)"

If the user picks an existing service, load its file:

```bash
source resources/.env.<service-name>.local
```

Display the loaded values:

> - **SERVICE_NAME**: `<value>`
> - **NAMESPACE**: `<value>`
> - **POD_PREFIX**: `<value>`
> - **CONTAINER_PORT**: `<value>`
> - **LOCAL_PORT**: `<value>`

Then skip Steps 1–3 and jump straight to [Step 4: Port Forward](#step-4-port-forward).

If no saved configs exist (or user says 'new'), proceed through all steps.

---

## Step 1: Discover Namespace

If the user doesn't know their namespace, retrieve it from the active Falcon context:

```bash
falcon context show --output json | jq -r '.[0].name_space'
```

Or list all pods across namespaces to find where a service lives:

```bash
kubectl get pods --all-namespaces | grep <service-name-prefix>
```

The first column is the namespace. Set it:

```bash
export NAMESPACE=<namespace>
```

---

## Step 2: Find the Pod Name

List pods in the namespace, optionally filtering by service name:

```bash
kubectl get pods -n ${NAMESPACE}
# or filter:
kubectl get pods -n ${NAMESPACE} | grep <service-name-prefix>
```

The pod name is in the first column (e.g., `ai-byoc-proxy-788bbc7546-xcgpm`).

---

## Step 3: Find the Container Port

If you don't know the port, inspect the pod or service:

```bash
# From the pod spec:
kubectl get pod <pod-name> -n ${NAMESPACE} -o jsonpath='{.spec.containers[*].ports[*].containerPort}'

# From the service (cleaner):
kubectl get svc -n ${NAMESPACE} | grep <service-name-prefix>
kubectl get svc <service-name> -n ${NAMESPACE} -o jsonpath='{.spec.ports[*]}'
```

Ask the user which port to forward if multiple are listed.

---

## Step 4: Port Forward

```bash
# Forward pod port to local port
kubectl port-forward -n ${NAMESPACE} pod/<pod-name> <local-port>:<container-port>
```

Or forward via service (more stable — automatically picks a healthy pod):

```bash
kubectl port-forward -n ${NAMESPACE} svc/<service-name> <local-port>:<container-port>
```

Keep this terminal running. The service is now accessible at `http://localhost:<local-port>`.

---

## Step 5: Get AWS Credentials from PCSK

The port-forward is running but kubectl needed cluster credentials, not service credentials. To make API calls *into* the service (e.g. authenticated endpoints), you need short-lived AWS credentials from PCSK.

1. Open the PCSK URL in your browser (from your `.env.<service-name>.local`):
   ```
   ${PCSK_URL}
   ```
   Or for `ai-byoc-proxy`: `https://pcsk-just-in-time.sfproxy.ast-preprod.aws-esvc1-useast2.aws.sfdc.cl/`

2. Request access to the account `${PCSK_ACCOUNT_NAME}` (approval via Slack channel `${PCSK_APPROVAL_SLACK}` if required).

3. Once approved, PCSK shows `export` commands — copy and paste them into your terminal:
   ```bash
   export AWS_ACCESS_KEY_ID=...
   export AWS_SECRET_ACCESS_KEY=...
   export AWS_SESSION_TOKEN=...
   ```

4. Verify credentials are active:
   ```bash
   aws sts get-caller-identity
   ```

---

## Step 6: Verify the Port Forward

Run the health-check `curl` stored in your service config:

```bash
# If you loaded a .env.<service-name>.local file:
eval ${HEALTH_CHECK_CURL}
```

Or manually:

```bash
# ai-byoc-proxy example:
curl -s http://localhost:8080/manage/health/liveness
```

A `200 OK` (or JSON `{"status":"UP"}`) confirms the port-forward is working.

> **Service-specific curl:** The `HEALTH_CHECK_CURL` variable in your `.env.<service-name>.local` holds the right command for each service. Update it if your service uses a different health endpoint.

---

## Saving Config for Future Sessions

After a successful connection, offer to save the values for this service:

> "Would you like me to save these values so you can reconnect faster next time?
> I'll save them to `resources/.env.<service-name>.local` (git-ignored)."

Each service gets its own file. To see all saved services later, run:

```bash
ls resources/.env.*.local
```

Template (copy to `resources/.env.<service-name>.local` and fill in values):

```bash
# Service config for <service-name> — git-ignored, never commit.
# Do NOT include AWS credentials here — get those from PCSK at connection time.

# ── Service identity ──────────────────────────────────────────────────────────
SERVICE_NAME=
NAMESPACE=
POD_PREFIX=
CONTAINER_PORT=
LOCAL_PORT=

# ── Falcon / Kubernetes cluster ───────────────────────────────────────────────
FALCON_INSTANCE=
FALCON_DOMAIN=
CLUSTER_NAME=
CLUSTER_REGION=
SAM_ACCOUNT_ID=

# ── PCSK Just-in-Time credentials ────────────────────────────────────────────
PCSK_ACCOUNT_NAME=
PCSK_ACCOUNT_ID=
PCSK_APPROVAL_SLACK=
PCSK_URL=

# ── Health check (run after port-forward to verify) ──────────────────────────
HEALTH_CHECK_CURL='curl -s http://localhost:${LOCAL_PORT}/health'
```

---

## Common Options

Forward on a specific local address (e.g., to allow access from other machines):

> **Warning:** Binding to `0.0.0.0` exposes the forwarded port to all network interfaces. Only use this when you specifically need access from other machines.

```bash
kubectl port-forward svc/<service-name> --address 0.0.0.0 <local-port>:<remote-port>
```

Forward multiple ports at once:

```bash
kubectl port-forward svc/<service-name> <local-port1>:<remote-port1> <local-port2>:<remote-port2>
```

## Running in Background

```bash
kubectl port-forward svc/<service-name> <local-port>:<remote-port> &
```

To stop:

```bash
kill %1
# or:
ps aux | grep port-forward
```

---

## Troubleshooting

### "error: unable to forward port because pod is not running"
The service's backing pods may not be healthy. Check:

```bash
kubectl get pods -n ${NAMESPACE}
kubectl describe svc <service-name> -n ${NAMESPACE}
```

### Connection refused on localhost
- Verify the port-forward is still running (it can timeout or disconnect)
- Verify you're using the correct local port
- Re-run the port-forward command

### "unable to find a pod matching the label selector"
The service may have no endpoints. Check:

```bash
kubectl get endpoints <service-name> -n ${NAMESPACE}
```
