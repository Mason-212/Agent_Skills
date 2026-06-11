---
name: falcon-k8s
description: Configure local kubectl to talk to a Falcon-managed Kubernetes cluster — handles context switching, credentials, kube config, and namespace in one step.
---

# Falcon K8s Setup

> Configure kubectl for a Falcon-managed Kubernetes namespace. Handles context switching, credential request/config, kube config, and namespace setup in one conversational flow.

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
- **PCSK Access** — active permissions in PCSK (not exported as environment variables)

**Important:** If the user has previously exported PCSK AWS credentials in their current terminal session, they must start a new session first. Existing environment variables conflict with the authentication process.

## Core Workflow

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

### Step 2: Ask the User for Role

Ask the user which PCSK role to use:

> "Which PCSK role do you want to use?"
> 1. **PCSKDeveloperRole** (default)
> 2. **PCSKAdministratorAccessRole**

Use their choice for all subsequent `falcon credentials` commands. If they don't specify or say "default", use `PCSKDeveloperRole`.

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

Match the user's request against the **FI** and **FD** columns. If multiple contexts match (e.g., same FI/FD but different services), present the options and ask the user to pick.

The **Name** column is what gets passed to `falcon context apply`.

### Step 4: Switch Falcon Context

Apply the matching context by name:

```bash
falcon context apply <Name>
```

For example: `falcon context apply edc_director1_dev1_uswest2_cdp001`

### Step 5: Resolve Namespace

If the user provided a namespace, use it. Otherwise retrieve from the active falcon context:

```bash
falcon context show --output json | jq -r '.[0].name_space'
```

If this returns empty or `null`, ask the user to provide a namespace explicitly.

### Step 6: Configure Credentials

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

Do NOT attempt to request admin credentials. Admin access requires prior approval. Tell the user:

> "No existing admin credentials found. PCSKAdministratorAccessRole requires prior approval. Please request and get approval for admin access through PCSK first, then come back and re-run this skill."

Stop the workflow here until the user has their admin approval in place.

### Step 7: Configure Kubernetes

```bash
falcon kube config
```

### Step 8: Set Namespace

```bash
kubectl config set-context --current --namespace=<NAMESPACE>
```

### Step 9: Verify

Confirm the setup is working:

```bash
kubectl config view --minify
```

Show the user their active context and namespace.

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
/falcon-k8s prod1-useast1 cdp
```

**Agent:**
1. Parses: FI=`aws-prod1-useast1`, FD=`cdp`
2. Asks about role, user says default
3. Switches falcon context
4. Retrieves namespace from context
5. Configures credentials with `PCSKDeveloperRole`
6. Runs `falcon kube config`
7. Sets namespace
8. Confirms with `kubectl config view --minify`

## Detailed Reference

For specific operations after kubectl is configured, read the relevant resource file:

- **Port forwarding** — `resources/port-forwarding.md`: How to forward local ports to services in the cluster

---

## Recommended Readings

- [Falcon CLI docs](https://docs.internal.salesforce.com/falcon/cli/home/)
- Falcon Inner-Loop Testing for AI Gateway
- Testing AI Gateway using the FIT inner loop
