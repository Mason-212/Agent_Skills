---
name: edc-pcsk
description: Request PCSK just-in-time credentials for EDC BYOC testing accounts (762118572632 aws-dev4-uswest2-einstein-psvc and 681597392516 dev1-uswest2-einstein-ids). Guides the user through requesting access, getting Slack approval, and verifying credentials. Use when the user needs PCSK access for BYOC testing, port-forwarding to ai-byoc-proxy, or deploying to the EDC inference service.
disable-model-invocation: true
---

# EDC PCSK Request

Interactively walk the user through getting PCSK credentials. Drive each step — open the browser, run shell commands, post to Slack — and wait for user confirmation before proceeding to the next step.

## Accounts

| Account Name | Account ID | Role | Used For |
|---|---|---|---|
| `aws-dev4-uswest2-einstein-psvc` | `762118572632` | `PCSKDeveloperRole` | BYOC proxy (`ai-byoc-proxy`), BYOC code sandbox testing |
| `dev1-uswest2-einstein-ids` | `681597392516` | `PCSKAdministratorAccessRole` | EDC inference service (ray pod), admin-level deploys |

---

## Step 1: Which Account?

Ask the user:

> "Which account do you need PCSK for?
> 1. `762118572632` — aws-dev4-uswest2-einstein-psvc (BYOC proxy / code sandbox)
> 2. `681597392516` — dev1-uswest2-einstein-ids (EDC inference / ray pod, requires admin)
> 3. Both"

Wait for their answer. Store the selection for use in later steps.

---

## Step 2: Check PCSK Portal for Existing Approval

Open the PCSK portal in the browser:

```
https://pcsk-just-in-time.sfproxy.ast-preprod.aws-esvc1-useast2.aws.sfdc.cl/
```

Then ask:

> "In the portal, do you have an existing request for this account that still has time remaining?"

- **Yes, still valid** → Skip to Step 5 (re-export credentials from portal, no new request needed).
- **No / expired / not sure** → Continue to Step 3.

> Note: Your Mac's local `AWS_*` env vars expiring does NOT mean your PCSK approval expired. The portal is the source of truth.

---

## Step 3: Submit Request in Portal

Guide the user in the portal:

1. Search for the account name or paste the Account ID
2. Select it and click **Request**
3. **Always select the maximum available duration**

Then ask:

> "Have you submitted the request in the portal?"

Wait for confirmation before proceeding.

---

## Step 4: Post to Slack for Approval

Post the approval request to the correct Slack channel based on the account selected in Step 1:

| Account | Slack Channel |
|---|---|
| `762118572632` | `#agentforce-foundations-prediction-svc` |
| `681597392516` | `#ai-cloud-ray-support` |

Post this message (substitute account details):

```
Hi team, requesting PCSK access for BYOC testing.
Account: <account-name> (<account-id>)
Role: <role from Accounts table above>
Duration: <max available>
Reason: BYOC code sandbox integration testing
```

Then tell the user:

> "Message posted. You'll get a Slack notification when someone approves. Let me know when you see the approval."

Wait for the user to confirm approval before proceeding.

---

## Step 5: Export Credentials to Mac

Once approved, the portal shows `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`.

Tell the user:

> "Copy the credentials from the portal and paste them here — I'll run the export commands in a fresh terminal for you."

Run in a **fresh terminal** (warn the user if `AWS_*` vars are already set in the current session):

```bash
export AWS_ACCESS_KEY_ID="<from-portal>"
export AWS_SECRET_ACCESS_KEY="<from-portal>"
```

Check for conflicting vars first:

```bash
env | grep AWS
```

If any `AWS_*` vars are already exported, warn:

> "You have existing AWS credentials exported. These will conflict with PCSK. Please open a fresh terminal and re-run the export there."

---

## Step 6: Verify

Run in the terminal:

```bash
env | grep AWS
```

Confirm `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set. Tell the user:

> "Credentials are live. You're ready to proceed."

---

## Step 7: What's Next?

Based on the account, prompt the next action:

**For `762118572632` (BYOC proxy):**
> "Would you like me to port-forward to `ai-byoc-proxy` now? I can use the `/edc-falcon-k8s` skill."

**For `681597392516` (EDC inference):**
> "Would you like to run `fkp-kubeconfig.sh` to configure kubectl for the inference cluster?"

---

## Admin Credentials Note (681597392516 only)

`dev1-uswest2-einstein-ids` requires `PCSKAdministratorAccessRole`. Standard developer requests will be rejected. Confirm the user has admin access before Step 3.
