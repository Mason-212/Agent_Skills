# Global Configuration Reference

All keys are defined under the `global:` section of `.strata.yml`.

| Key | Default | Type | Description |
|-----|---------|------|-------------|
| `email-reply-to` | *(required)* | string | Email address for build notifications. Supports comma-separated multiple addresses. Distribution lists must accept postings by email. |
| `email-only-last-committer-on-dev-branch` | `false` | boolean | When `true`, dev/PR branch builds email only the last committer instead of `email-reply-to`. |
| `log-level` | `warn` | string | Log verbosity. Common values: `warn`, `debug`. |
| `num-artifacts-to-keep` | *(unset)* | integer | Number of builds for which archived files (`strata_published_artifacts.yaml`, `amg_artifact_metadata.yaml`) are kept. Does not affect RPMs, Docker images, etc. |
| `number-of-builds-to-keep` | *(unset)* | integer | Number of builds to store in Jenkins. |
| `production-branches` | `null` | list | Branches used for production releases. Supports regex prefixed with `r:`. If empty or omitted, no production workflows execute. |
| `timeout` | *(unset)* | integer | Pipeline timeout in **minutes**. |
| `scheduled-build-compliance-required` | `false` | boolean | When `true`, validates that the work item in PR commit messages has a scheduled build in GUS. Runs during precheck stage. |
| `jenkins-environment` | `false` | boolean | When `true`, injects all Jenkins environment variables into every user-defined step automatically. Otherwise you must declare them explicitly in each step's `environment` block. |
| `attach-build-log` | `false` | boolean | Attach build log to the status email sent to the developer. |
| `publish-falcon-config-bundle` | `true` | boolean | Publishes falcon-config-bundle image plus corresponding Terraform and Helm artifacts to both Artifactory and ECR. |
| `validate-for-gov-cloud` | `false` | boolean | Runs Falcon Linter validations (silent mode) to catch issues when deploying into falc environments. |
| `pr-comment-file-path` | `strata_pr_comment.md` | string | Relative path to a Markdown file whose contents are posted as a PR comment during PR builds. |
| `enable-console-logging` | `true` | boolean | Set to `false` to disable live logging to the Jenkins console. Logs are still persisted as build artifacts. |
| `publish-control` | *(unset)* | string | Set to `only-changed` to generate only the artifacts whose source files changed. |
| `publish-control-disable-by-type` | `none` | list | Artifact types that publish control should **not** affect. |
| `enable-concurrent-builds` | `true` | boolean | Set to `false` to disable concurrent builds. |
| `publish-to-falcon` | `true` | boolean | Publish build artifacts to Falcon. |
| `skip-publish-to-artifactory` | `false` | boolean | When `true`, Docker images are not published to Artifactory (still published to Dev and PROD ECR). |
| `skip-publish-falcon-config-bundle-to-artifactory` | `false` | boolean | When `true`, falcon-config bundles and fit bundle images skip Artifactory (still published to Dev and PROD ECR). |
| `target-architecture` | *(unset)* | list | Architectures for multi-arch image builds. Values: `x86_64`, `aarch64`. |
| `enable-safe-repo-pilot` | `false` | boolean | Opt in to the 3PP Safe Repo pilot. |
| `pipeline-initial-build-number` | *(unset)* | integer | Override the pipeline's initial build number. |
| `publish-custom-versions-to-dev` | `false` | boolean | When `true`, publishes custom-versioned Docker tags to Dev ECR for production branch builds. Custom version scheme must be defined as a map in `production-branches`. |
| `rebuild-cadence` | *(unset)* | string | Scheduled build cadence. Values: `daily`, `weekly`, `cron`. |
| `rebuild-cadence-config` | *(unset)* | string | Cron expression when `rebuild-cadence: cron`. Minimum interval is 30 minutes. |
| `node-type` | `m5.2xlarge` | string | Agent instance type. Default has 8 GB RAM, 4 vCPUs, 150 GB EBS. Large options: `c5d.18xlarge` (144 GB RAM, 72 vCPUs, 300 GB EBS) or `c6id.16xlarge` (128 GB RAM, 64 vCPUs) -- requires budget approval. |
| `build-description` | *(unset)* | string | Custom build description. Supports env vars (`$BUILD_NUMBER`, `${BUILD_NUMBER}`) and build parameters (`${PARAMETERS_<name>}`). |
| `parameters` | *(unset)* | list | Build parameters passed via Jenkins UI. See secrets-and-parameters reference. |
| `skip-gh-merge-queue-build` | `false` | boolean | When `true`, skips the merge queue build and auto-merges if no new commits on target and no conflicts. Recommended to keep `false`. |
| `pr-automerge` | *(unset)* | map | Enable auto-merge of PRs matching specified titles. Requires merge queues enabled. Contains `pr-title` list. |

## Example

```yaml
global:
  email-reply-to: my-team@salesforce.com
  email-only-last-committer-on-dev-branch: false
  log-level: debug
  production-branches:
    - main
    - r:release_\d+\.\d+.*
  timeout: 60
  rebuild-cadence: daily
  target-architecture:
    - x86_64
    - aarch64
  enable-concurrent-builds: true
  publish-control: only-changed
  node-type: m5.2xlarge
  build-description: "Build $BUILD_NUMBER by ${PARAMETERS_USERNAME}"
```
