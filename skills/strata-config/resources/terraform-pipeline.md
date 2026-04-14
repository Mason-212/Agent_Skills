# Terraform Pipeline Configuration

## Minimal Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  package:
    - terraform-package:
        packages:
          - path: ./terraform-test-1
            version: 2.1.5-$$BUILD_NUMBER
  publish:
    - terraform-publish
```

## Managed Steps

| Step | Stage | Parameters |
|------|-------|------------|
| `terraform-package` | package | `packages` (list of path/version) |
| `terraform-publish` | publish | (none) |

## Package Properties

Each entry under `packages:` accepts:
- `path` -- path to the terraform directory (required)
- `version` -- version string (optional; defaults to `$$GIT_SHA` if omitted)

## Versioning Strategies

```yaml
# Auto-version defaults to $$GIT_SHA (no version specified)
- terraform-package:
    packages:
      - path: ./terraform-test-1

# Auto-version using $$BUILD_NUMBER
- terraform-package:
    packages:
      - path: ./terraform-test-1
        version: 2.1.5-$$BUILD_NUMBER

# Manual versioning
- terraform-package:
    packages:
      - path: ./terraform-test-1
        version: 2.1.5
```

Available env vars for version strings: `$$BUILD_NUMBER` (required if using others), `$$GIT_BRANCH`, `$$GIT_COMMIT`, `$$GIT_SHA`.

## V1 to V2 Migration

To test an existing V1 Strata Terraform pipeline in V2 before converting, add `run_in_v2: true` to the existing `.strata.yml`.

## Key Notes

- Production branch builds use the version specified in `.strata.yml`.
- Dev/PR builds are always versioned as `<artifact_name>_<git_branch_or_pr_number>_<git_short_commit_sha>.tar.gz` regardless of specified version.
- Only `_`, `-`, `.` are supported as special characters in version strings.
- `$$BUILD_NUMBER` is required if you want to use `$$GIT_BRANCH`, `$$GIT_COMMIT`, or `$$GIT_SHA` in the version string.
- `terraform-publish` publishes packaged artifacts to S3.
- Use the `gridwrapper` macro in Spinnaker pipelines to consume these artifacts for deployment.
