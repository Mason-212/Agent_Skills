# Bazel Pipeline Configuration

## Minimal Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  precheck:
    - bazel-precheck
  build:
    - bazel-build-and-test
  package:
    - bazel-package
  publish:
    - bazel-container-publish
```

## Managed Steps

| Step | Stage | Parameters |
|------|-------|------------|
| `bazel-precheck` | precheck | (none) |
| `bazel-build-and-test` | build | `bazel-options` (string), `bazel-targets` (string), `skipTests` (bool), `disable-bazel-cache` (bool) |
| `bazel-package` | package | `bazel-options` (string), `bazel-targets` (string) |
| `bazel-container-publish` | publish | (none) |

## Custom Options and Targets

```yaml
build:
  - bazel-build-and-test:
      bazel-options: <space separated list of options>
      bazel-targets: <space separated list of targets>
package:
  - bazel-package:
      bazel-options: <space separated list of custom options>
      bazel-targets: <space separated list of custom targets>
```

## Skip Tests

```yaml
build:
  - bazel-build-and-test:
      skipTests: true
```

## Disable Bazel Cache

Bazel cache is enabled by default in `bazel-build-and-test`.

```yaml
build:
  - bazel-build-and-test:
      disable-bazel-cache: true
```

## Team-Based Image Subpathing (Monorepos)

For monorepos with multiple teams, image names include team info to prevent collisions:
`<Registry-endpoint>/sfci/<org-name>/<repo-name>/<team-name>/<bazel-package-name>`

Team name is resolved by (in priority order):
1. A `load_docker_image_subpath.sh` script at repo root, `tools/docker/`, or `tools/scripts/` -- takes target name as input, outputs team name.
2. `@git-slug` entry in CODEOWNERS file matching the project path.

## Key Notes

- `bazel-precheck` detects changed files and determines affected bazel targets (diff-based for branches, PR file list for PRs).
- `bazel-build-and-test` runs both `bazel build` and `bazel test` to generate an OCI-compliant tarball.
- `bazel-package` packages artifacts from `bazel-build-and-test` and publishes them as itest images to Artifactory and ECR.
- `bazel-container-publish` publishes container images packaged by `bazel-package`.
- For custom steps, use the `sfdc_bazel` image which includes bazel, buildifier, go, java, and python3.
- If `load_docker_image_subpath.sh` returns "none", no team subpath is appended.
