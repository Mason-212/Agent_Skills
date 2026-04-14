# Advanced Features

## Multi-Architecture Builds

Build Docker images for multiple architectures. By default, images build on x86 only.

```yaml
global:
  target-architecture:
    - x86_64
    - aarch64
```

Multi-arch is supported in both V1 and V2 pipelines. V1 uses underscores (`target_architecture`).

## Generic Parallel Execution (GPE) with Remote Runners

Run steps on remote agents outside the main build agent using `runner: remote-linux`. The workspace is snapshotted between main and runner agents.

**Overhead warning:** Each runner invocation snapshots the workspace to/from the remote agent. Use this for long-running or resource-heavy steps that benefit from parallelization.

**Optimization:** Sequential steps in the same group with `runner` reuse the same runner agent, avoiding repeated snapshotting.

```yaml
stages:
  build:
    - steps:
        name: Multi-linux-agents
        parallel: true
        pipeline:
          - steps:
              name: build-in-parallel
              pipeline:
                - step:
                    name: linux-step-1
                    image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
                    runner: remote-linux
                    commands:
                      - echo "hello linux 1"
                - step:
                    name: linux-step-2
                    image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
                    runner: remote-linux
                    commands:
                      - echo "hello linux 2"
          - steps:
              name: build-in-serial
              pipeline:
                - step:
                    name: linux-step-3
                    image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
                    runner: remote-linux
                    commands:
                      - echo "hello linux 3"
```

## Scheduled Builds

Configure automatic rebuild cadences under `global:`.

```yaml
global:
  rebuild-cadence: daily    # or: weekly
```

Custom cron schedule (minimum 30-minute interval, production branches only):

```yaml
global:
  rebuild-cadence: cron
  rebuild-cadence-config: "*/30 * * * *"
```

## Publish Controls

Only package and publish artifacts whose source files changed:

```yaml
global:
  publish-control: only-changed
```

Exclude specific artifact types from publish control:

```yaml
global:
  publish-control-disable-by-type:
    - docker
```

## PR Auto-Merge

Automatically send matching PRs to the merge queue. Requires merge queues enabled on the target branch.

```yaml
global:
  skip-gh-merge-queue-build: false  # recommended: false
  pr-automerge:
    pr-title:
      - Update README.md
      - r:.*Test PR.*
```

- `pr-title`: list of exact titles or regex patterns (prefixed with `r:`).
- Both `pr-automerge` and `pr-title` are required.
- Auto-merge does not bypass branch protection rules (approvals, required checks still apply).

## Merge Queues

Merge queues automate PR merges by validating changes against the latest target branch plus any queued PRs.

### Setup

1. **Enable webhook:** Add Merge Groups check to your org's GitHub webhook at `https://git.soma.salesforce.com/organizations/{ORG_NAME}/settings/hooks`.
2. **Enable branch protection:** Set "Require merge queue" in branch protection rules for the target branch.
3. **Set required status check:** Use `continuous-integration/sfci/build` as the required status check. Remove other checks that are not common to both PR and branch builds.
4. **Accept SFCI GitHub App permissions** (GitHub.com orgs only): Accept pending checks API permission.

### Key Behavior

- Merge queue runs an additional build before merging; not recommended for repos with infrequent PR merges.
- PRs no longer need to be manually updated with the latest target branch changes.
- Direct merges are blocked when merge queues are enabled; disable the branch protection rule for emergency merges.

## Enhanced Status Checks

SFCI provides the `continuous-integration/sfci/build` status check on all managed builds. This check:

- Runs in parallel with legacy `pr-head` and `pr-merge` checks.
- Provides a unified check that works across PR and branch contexts (required for auto-merge and merge queues).
- Dynamically updates to show the current stage in progress on the GitHub PR page.

For GitHub (GEC/GEC-EMU): accept the SFCI GitHub App's request for checks API access.

## Downstream Dependency Validation (Pre-Release)

Validate that upstream changes do not break downstream repositories. Configured as a managed step under `integration-test`.

### Configuration

```yaml
stages:
  integration-test:
    - downstream-dependencies:
        ignore-failures: false
        downstream-repos:
          - repo-url: https://git.soma.salesforce.com/org/downstream-repo
            branches:
              - main
              - core-256-patch
              - "github-default"
        packages-to-test:
          npm:
            - "@salesforce/lwr"
```

### Parameters

| Param | Default | Description |
|-------|---------|-------------|
| `downstream-repos` | *(required)* | List of downstream repos with `repo-url` and `branches`. |
| `packages-to-test` | *(required)* | Package manager and package names to test (e.g., `npm`). |
| `ignore-failures` | `false` | When `true`, downstream failures do not block the upstream PR. |

### Bypassing

- Set `ignore-failures: true` -- validation runs but failures are ignored.
- Add `@ignore-downstream-tests@` in a commit message to skip validation entirely.

## SonarQube / Code Coverage

For SonarQube setup, coverage files, `sonar-project.properties`, and troubleshooting, read `resources/sonarqube.md`.
Keep this file focused on broader platform features rather than detailed analysis debugging.

## Large Agent Types

Default agent: `m5.2xlarge` (8 GB RAM, 4 vCPUs, 150 GB EBS).

Large agent (requires budget approval): `c5d.18xlarge` (144 GB RAM, 72 vCPUs, 300 GB EBS) or `c6id.16xlarge` (128 GB RAM, 64 vCPUs).

```yaml
global:
  node-type: c5d.18xlarge
```

## GitHub Enterprise Cloud (GEC) Specifics

SFCI Managed supports GitHub Enterprise Cloud (github.com) repositories. Known limitations:

- **HTTPS cloning only**: To clone other repositories in unit tests or submodules, use the HTTPS URL, not SSH.
- **No SonarQube PR decorations**: The current SonarQube server cannot support multiple source-control systems for PR decoration. Quality results are not decorated on github.com PRs but can be viewed via the SonarQube dashboard link in build logs.
- **GitHub App permissions**: For GEC/GEC-EMU orgs, accept the SFCI GitHub App's request for checks API access to enable enhanced status checks.

## ALI Substrate Support

SFCI pipelines can run on ALI (Alibaba Cloud) substrate in addition to AWS. To add substrate support (e.g., `cag`, `aws`, `ali`) to user-defined steps, additional configuration is required. Refer to the SFCI substrate documentation for details on configuring `.strata.yml` for non-AWS substrates.
