# GitHub Integration and Webhook Setup

## Onboarding Your Organization

To integrate with SFCI Managed, complete these steps:

### 1. Register Your Organization

Add your GitHub organization to the `yaml-driven-pipelines.yaml` file via pull request. Your org name must be registered for SFCI to build your projects and set commit statuses.

### 2. Add Service Users as Org Owners

Add the following service users as **owners** (not just members) of your GitHub organization:

| Service User | Purpose |
|---|---|
| `svc-dva-strata` | Sets statuses, pushes tags, interacts with repos during builds |
| `svc-sfci` | Runs onboarding jobs, provisions Jenkins, onboards to DFIU and Snyk automerge |
| `tok-sfci343` | Required for auto-merge functionality |

Owner access is required at the org level due to company-wide restrictions on git.soma. Adding at the org level covers all repositories automatically.

### 3. Install SFCI-GitHub-App

Install the **SFCI-GitHub-App** on your organization and select **All repositories**.

### 4. Install SonarQube as a Service GitHub App

Install the SonarQube as a Service GitHub app for repositories in your org to enable analysis.

For git.soma repos, this also enables SonarQube PR decoration.
For GitHub Enterprise Cloud (`github.com`) repos, SonarQube PR decoration is not currently supported; results are still available in the SonarQube dashboard and build logs.

## GitHub Enterprise Cloud (github.com) Notes

When onboarding GEC/GEC-EMU repositories:

- Use HTTPS URLs, not SSH, when cloning other repositories in unit tests or submodules.
- Accept the SFCI GitHub App's checks API permission request to enable enhanced status checks.
- Do not promise SonarQube PR decoration on github.com repos.

## Webhook Setup

Webhooks trigger builds immediately on push/PR events without Jenkins polling. There are two methods:

### Method 1: Strata GitHub App (Recommended for 1P)

The Strata GitHub App configures webhooks and events automatically. Requires a `.strata.yml` file in the repository. Does **not** work for Falcon instances (`sfcirelease.sfci.buildndeliver-s.aws-esvc1-useast2.aws.sfdc.cl`).

### Method 2: Manual Webhook Configuration

#### For Falcon Instances

1. Navigate to your org: **Settings > Hooks > Add Webhook**.
2. **Payload URL**: `https://sfcirelease.sfci.buildndeliver-s.aws-esvc1-useast2.aws.sfdc.is/strata-<org>/github-webhook/`
   - URL ends with `.is` (not `.cl` like the Jenkins URL).
   - URL is case-sensitive and must be all lowercase.
   - Must end with a trailing slash after `github-webhook/`.
3. Select **Let me select individual events** and enable:
   - **Issue comment** -- retrigger builds via "Jenkins test this please" comment.
   - **Merge groups** -- events for merge queue builds.
   - **Pull requests** -- build new PRs instantly.
   - **Pushes** -- build new commits instantly.
   - **Repositories** -- build new repos instantly.

#### For 1P Instances

1. Navigate to your repository: **Settings > Hooks > Add Webhook**.
2. **Payload URL**: `https://dva-ci.internal.salesforce.com/github-webhook/`
3. **Content type**: `application/json`
4. Select **Let me select individual events** and enable:
   - **Issue comment**
   - **Pull requests**
   - **Pushes**
   - **Repositories**

## Retriggering Builds

Comment `Jenkins test this please` on a PR to retrigger the build for the latest commit. This uses the **Issue comment** webhook event (not Pull request review comment), since issue comments are associated with the entire PR.
