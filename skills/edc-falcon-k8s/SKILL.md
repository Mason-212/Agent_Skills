---
name: edc-falcon-k8s
description: Configure local kubectl to talk to a Falcon-managed Kubernetes cluster — handles PCSK credentials, fkp-kubeconfig.sh setup, context switching, and namespace in one step. Also supports port-forwarding with saved service configs.
---

# Falcon K8s Setup

> Configure kubectl for a Falcon-managed Kubernetes namespace. Handles PCSK credential requests, fkp-kubeconfig.sh, context switching, and namespace setup in one conversational flow.

## When to Use

Activate this skill when:
- The user wants to switch to a Falcon context / namespace (e.g., "switch to dev1-uswest2 einstein-edc")
- The user wants to configure kubectl for a Falcon cluster
- The user mentions a Falcon Instance, Functional Domain, or namespace they want to connect to
- The user mentions "falcon kube", "falcon credentials", or asks about connecting to their k8s cluster
- The user wants to port-forward to a service in a Falcon cluster

## When NOT to Use

- Non-Falcon Kubernetes clusters (e.g., EKS direct, GKE, minikube)
- CI/CD pipeline k8s configuration (use service accounts instead)
- When the user only needs to run `kubectl` commands and is already configured

## Prerequisites

The user must have:
- **Falcon CLI** installed (https://docs.internal.salesforce.com/falcon/cli/home/)
- **kubectl** installed (https://kubernetes.io/docs/tasks/tools/install-kubectl-macos/)
- **Docker Desktop** running — kubectl on Mac requires it
- **PCSK Access** — active permissions in PCSK for the target account

**Important:** If the user has previously exported PCSK AWS credentials in their current terminal session, they must start a new session first. Existing `AWS_*` environment variables conflict with the authentication process.

---

## Core Workflow

### Step 0: Check for Saved Service Configs

Before anything else, list available saved service configs:

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

Display the loaded values and confirm with the user, then skip to Step 6 (Configure Credentials) using the loaded PCSK values, and proceed to port-forward via `resources/port-forwarding.md`.

If no saved configs exist (or user says 'new'), continue below.

---

### Step 1: Parse User Intent

Users typically provide context like:
- "switch to dev1-uswest2 einstein-edc namespace"
- "connect to prod1-useast1 cdp"
- "falcon k8s for einstein FD dev1-uswest2 einstein-edc"

Extract from their request:
- **Falcon Instance** (e.g., `aws-dev1-uswest2`, `aws-prod1-useast1`)
- **Functional Domain** (e.g., `einstein-edc`, `cdp`, `cdp001`)
- **Namespace** (e.g., `einstein-edc`, `ids`) — often same as Functional Domain

If the user doesn't provide enough detail, ask what's missing.

---

### Step 2: Ask the User for Role

Ask the user which PCSK role to use:

> "Which PCSK role do you want to use?"
> 1. **PCSKDeveloperRole** (default)
> 2. **PCSKAdministratorAccessRole**

Use their choice for all subsequent `falcon credentials` commands. If they don't specify or say "default", use `PCSKDeveloperRole`.

---

### Step 3: List Available Contexts

Show all available falcon contexts:

```bash
falcon context show --all
```

This outputs a table like:

```
Name                                                   │ FI                     │ FD            │ Cell   │ Account Id   │ Cluster Account Label
edc_director1_dev1_uswest2_cdp001                      │ dev1-uswest2           │ cdp001        │ (none) │ 123456789012 │ default
einstein_ai_gateway048_dev1_uswest2_cdp001             │ dev1-uswest2           │ cdp001        │ (none) │ 234567890123 │ default
ray016_dev1_uswest2_einstein                           │ dev1-uswest2           │ einstein      │ (none) │ 345678901234 │ default
```

Match the user's request against the **FI** and **FD** columns. If multiple contexts match, present the options and ask the user to pick.

The **Name** column is what gets passed to `falcon context apply`.

---

### Step 4: Switch Falcon Context

Apply the matching context by name:

```bash
falcon context apply <Name>
```

For example: `falcon context apply edc_director1_dev1_uswest2_cdp001`

---

### Step 5: Resolve Namespace

If the user provided a namespace, use it. Otherwise retrieve from the active falcon context:

```bash
falcon context show --output json | jq -r '.[0].name_space'
```

If this returns empty or `null`, ask the user to provide a namespace explicitly.

---

### Step 6: Configure Credentials

#### Path A — Falcon-standard clusters (most cases)

Try configuring existing credentials first:

```bash
falcon credentials config --role <ROLE>
```

If this fails (no existing credentials for that role), the next step depends on the role:

**For PCSKDeveloperRole:**

Ask the user for confirmation before requesting:

> "No existing developer credentials found. I can create a credentials request with reason 'Development'. Would you like me to proceed, or would you prefer to create the request separately and come back?"

If the user agrees, ask how long they need access:

> "How long do you need credentials for?"
> 1. **8h**
> 2. **48h**
> 3. **168h** (1 week)
> 4. **744h** (1 month)

Then ask for a details/reason string:

> "What details would you like to provide for the request? (default: 'for development')"

If the user doesn't provide one or says "default", use `"for development"`.

Then request with all flags to avoid interactive prompts:

```bash
falcon credentials request --role PCSKDeveloperRole --duration <DURATION> --major-reason Development --details '<DETAILS>'
falcon credentials config --role PCSKDeveloperRole
```

**For PCSKAdministratorAccessRole:**

Do NOT attempt to request admin credentials. Tell the user:

> "No existing admin credentials found. PCSKAdministratorAccessRole requires prior approval. Please request and get approval for admin access through PCSK first, then come back and re-run this skill."

Stop the workflow here until the user has their admin approval in place.

---

#### Path B — PCSK Just-in-Time clusters (e.g., prediction-services, einstein-psvc accounts)

Some clusters live in restricted AWS accounts that are **not** reachable via standard `falcon credentials`. These require a separate PCSK JIT flow and manual `fkp-kubeconfig.sh` setup.

Ask the user:

> "Does your target service live in a PCSK just-in-time account (e.g., `aws-dev4-uswest2-einstein-psvc`)?"

If yes, follow this path:

**Step 6B-1: Request PCSK JIT Access**

> TLDR: The cluster lives in a restricted AWS account. PCSK issues short-lived credentials that prove you're authorized.

1. Go to https://pcsk-just-in-time.sfproxy.ast-preprod.aws-esvc1-useast2.aws.sfdc.cl/
2. Request credentials for the target account (e.g., `aws-dev4-uswest2-einstein-psvc`, Account ID from `.env.local` or from the user)
3. Get approval — ask the user which Slack channel handles approval for this service, or check `.env.local` for `PCSK_APPROVAL_SLACK`

**Step 6B-2: Export PCSK Credentials**

Once approved, the PCSK portal gives you `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`. Export them:

```bash
export AWS_ACCESS_KEY_ID="<your-access-key>"
export AWS_SECRET_ACCESS_KEY="<your-secret-key>"
```

> **Warning:** Do NOT export these in a session where you also need `falcon credentials config`. They conflict. Use a fresh terminal.

**Step 6B-3: Clone and Run fkp-kubeconfig.sh**

> TLDR: `fkp-kubeconfig.sh` uses your PCSK credentials to generate a `kubeconfig` entry pointing `kubectl` at the right cluster endpoint.

```bash
# Clone the script (one-time setup)
git clone https://git.soma.salesforce.com/sam/script.git
cd script

# Run the kubeconfig script — get the account ID, cluster name, namespace, and region from the user or .env.local
./fkp-kubeconfig.sh -s <pcsk-account-id> -c <cluster-name> -n <namespace> -r <region>

# Example for prediction-services:
# ./fkp-kubeconfig.sh -s 699497180728 -c sam-processing1 -n prediction-services -r us-west-2
```

Ask the user for the four parameters if not in `.env.local`:
- `-s`: PCSK account ID (e.g., `699497180728`)
- `-c`: cluster name (e.g., `sam-processing1`)
- `-n`: namespace (e.g., `prediction-services`)
- `-r`: AWS region (e.g., `us-west-2`)

**Step 6B-4: Verify**

```bash
export NAMESPACE=<namespace>
kubectl get pods -n ${NAMESPACE}
```

If pods are listed, kubectl is correctly connected. Skip Steps 7–9 and go to port-forwarding.

---

### Step 7: Configure Kubernetes (Path A only)

```bash
falcon kube config
```

---

### Step 8: Set Namespace (Path A only)

```bash
kubectl config set-context --current --namespace=<NAMESPACE>
```

---

### Step 9: Verify

Confirm the setup is working:

```bash
kubectl config view --minify
```

Show the user their active context and namespace.

---

## Saving Config for Future Sessions

After a successful connection, offer to save the values for this service:

> "Would you like me to save these values so you can reconnect faster next time?
> I'll save them to `resources/.env.<service-name>.local` (git-ignored)."

Each service gets its own file — multiple services coexist cleanly:

```
resources/.env.ai-byoc-proxy.local
resources/.env.edc-inference-service.local
resources/.env.my-other-service.local
```

Template for a new file `resources/.env.<service-name>.local`:

```bash
# Service config for <service-name> — git-ignored, never commit.
# Do NOT include AWS credentials here — get those from PCSK at connection time.

# ── Service identity ──────────────────────────────────────────────────────────
SERVICE_NAME=<service-name>
NAMESPACE=<namespace>
POD_PREFIX=<pod-name-prefix>
CONTAINER_PORT=<container-port>
LOCAL_PORT=<local-port>

# ── Falcon / Kubernetes cluster ───────────────────────────────────────────────
FALCON_INSTANCE=<e.g., aws-dev4-uswest2>
FALCON_DOMAIN=<e.g., einstein>
CLUSTER_NAME=<e.g., sam-processing1>
CLUSTER_REGION=<e.g., us-west-2>
SAM_ACCOUNT_ID=<account-id-for-fkp-kubeconfig>

# ── PCSK Just-in-Time credentials (Path B only) ──────────────────────────────
PCSK_ACCOUNT_NAME=<e.g., aws-dev4-uswest2-einstein-psvc>
PCSK_ACCOUNT_ID=<account-id>
PCSK_APPROVAL_SLACK=<slack-channel>
PCSK_URL=https://pcsk-just-in-time.sfproxy.ast-preprod.aws-esvc1-useast2.aws.sfdc.cl/

# ── Health check (run after port-forward to verify) ──────────────────────────
HEALTH_CHECK_CURL='curl -s http://localhost:<local-port>/health'
```

---

## Error Handling

### Namespace Retrieval Fails
If no namespace is provided and `falcon context show` returns nothing:
- Ask the user to provide a namespace explicitly
- Or ask them to set up a Falcon context first: `falcon context apply`

### Credential Request Fails
If both `falcon credentials config` and `falcon credentials request` fail for the chosen role:
- Verify PCSK access is active for that role
- Ensure no stale AWS credential exports exist in the current session (`env | grep AWS`)
- Suggest starting a new terminal session if AWS env vars are present

### fkp-kubeconfig.sh Fails
- Verify `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are exported and not expired
- Verify the PCSK JIT request was approved
- Check that `git.soma.salesforce.com/sam/script.git` was cloned successfully

---

## Example Usage

**User:**
```
I want to switch to falcon context for einstein FD dev1-uswest2 einstein-edc namespace
```

**Agent:**
1. Parses: FI=`aws-dev1-uswest2`, FD=`einstein-edc`, namespace=`einstein-edc`
2. Asks: "Which PCSK role? 1) PCSKDeveloperRole 2) PCSKAdministratorAccessRole"
3. User picks admin
4. Runs `falcon context apply <matching-context>`
5. Runs `falcon credentials config --role PCSKAdministratorAccessRole`
6. Runs `falcon kube config`
7. Runs `kubectl config set-context --current --namespace=einstein-edc`
8. Shows `kubectl config view --minify`

**User:**
```
connect to prediction-services in aws-dev4-uswest2-einstein-psvc
```

**Agent:**
1. Recognizes PCSK JIT account pattern → Path B
2. Checks `.env.local` for saved values
3. Directs user to PCSK JIT portal with saved account label/ID
4. Exports credentials, clones script, runs `fkp-kubeconfig.sh` with saved params
5. Verifies `kubectl get pods -n prediction-services`
6. Offers to port-forward (reads `resources/port-forwarding.md`)

---

## Detailed Reference

For specific operations after kubectl is configured, read the relevant resource file:

- **Port forwarding** — `resources/port-forwarding.md`: How to forward local ports to services in the cluster

---

## Recommended Readings

- [Falcon CLI docs](https://docs.internal.salesforce.com/falcon/cli/home/)
- Falcon Inner-Loop Testing for AI Gateway
- Testing AI Gateway using the FIT inner loop
