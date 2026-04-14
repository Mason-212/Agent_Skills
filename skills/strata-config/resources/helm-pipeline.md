# Helm Pipeline Configuration

## Minimal Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  package:
    - helm-package:
        charts:
          - path: ./my-chart
            version: 1.0.0-$$BUILD_NUMBER
  publish:
    - helm-publish
```

## Managed Steps

| Step | Stage | Parameters |
|------|-------|------------|
| `helm-package` | package | `charts` (list of path/version) |
| `helm-publish` | publish | (none) |

## Chart Properties

Each entry under `charts:` accepts:
- `path` -- path to the chart directory (required)
- `version` -- version string (optional; if omitted, uses version from `chart.yaml`)

## Versioning Strategies

```yaml
- helm-package:
    charts:
      # 1) Auto-version using build number
      - path: /nginx
        version: 0.1.2-$$BUILD_NUMBER

      # 2) Using GIT_SHA
      - path: /redis
        version: 1.0.0-$$BUILD_NUMBER-$$GIT_SHA

      # 3) Manual versioning
      - path: /haproxy
        version: 4.0.4

      # 4) Use chart.yaml version (omit version attribute)
      - path: /nodejs
```

Available env vars for version strings: `$$BUILD_NUMBER`, `$$GIT_BRANCH`, `$$GIT_COMMIT`, `$$GIT_SHA`.

## Key Notes

- Production branch builds use the version specified in `.strata.yml` or `chart.yaml`.
- Dev/PR builds are always versioned as `<artifact_name>-<git_branch_or_pr_number>-<git_short_commit_sha>.tar.gz` regardless of specified version.
- Only `_`, `-`, `.` are supported as special characters in version strings.
- `helm-publish` publishes packaged charts to S3.
- Versioning is recommended to make artifacts immutable and enable easy rollbacks.
