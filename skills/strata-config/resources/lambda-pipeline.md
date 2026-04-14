# Lambda Pipeline Configuration

## Minimal Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
  rebuild-cadence: daily
stages:
  package:
    - lambda-package:
        parallel: true
        lambdas:
          - path: .
            name: sample-app
  publish:
    - lambda-publish
```

## Managed Steps

| Step | Stage | Parameters | Description |
|------|-------|------------|-------------|
| `lambda-package` | package | `parallel` (bool, optional -- enables parallel packaging), `lambdas` (list of `path` + `name`) | Packages lambda function code into a container image and publishes to dev ECR |
| `lambda-publish` | publish | (none) | Publishes the container image to prod ECR (not yet available) |

## Global Configuration

| Parameter | Values | Description |
|-----------|--------|-------------|
| `rebuild-cadence` | `daily`, `weekly` | Timer-triggered rebuild frequency. Daily at 11:30 AM PT; weekly at 1:30 PM PT on Sundays |

## ECR Image Tags

**Dev registry** (from `lambda-package`):

- `<GIT_ORG>-<GIT_REPO>-<BRANCH/PR>-<BUILD_NUMBER>-itest`
- `<GIT_ORG>-<GIT_REPO>-<BRANCH/PR>-latest-itest`
- `itest` (local only, not pushed -- usable as shorthand in other steps)

**Prod registry** (from `lambda-publish`):

- `latest`
- `{BUILD_NUMBER}`
- `{GIT_COMMIT}`
- `{BUILD_NUMBER}-{GIT_COMMIT}`
- Any custom git tags created before calling this step

## Key Notes

- Currently supports Java and Python lambda functions only; Node.js support is in progress.
- Dockerfile image update is not automated; a weekly rebuild cadence generates new images with security patches.
- The `lambda-publish` step is **not yet available** as of this writing.
- Each entry in `lambdas` requires a `name`; `path` defaults to `.` (repo root).
- This pipeline is **in development** -- the design or implementation may change.
