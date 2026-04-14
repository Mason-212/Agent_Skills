# SFDX Pipeline Configuration

This file covers both SFDX Metadata Package and SFDX Managed Package pipelines.

---

## SFDX Metadata Package

### Minimal Example

```yaml
global:
  email-reply-to: owning-team@salesforce.com
  production-branches:
    - release-234
    - release-236
stages:
  package:
    - sfdx-metadata-package:
        enabled: true
  integration-test:
    - sonarqube:
        enabled: false
```

### Testing Mode

```yaml
stages:
  package:
    - sfdx-metadata-package:
        enabled: true
        testing: true
  publish:
    - git-push-tags:
        enabled: false
```

### Required File: artifactMetadata.json

Place at repo root (or in `transferScripts/`):

```json
{
  "include_paths": ["sfdx", "custom"],
  "output_dir": "artifact",
  "release_tag": "ubo-packageable-metadata",
  "release_version": "236.0"
}
```

- `include_paths` -- directories to include in the zip
- `output_dir` -- where the artifact zip is written
- `release_tag` -- tag name prefix for the git tag
- `release_version` -- package version string

### Workflow

1. Create a branch and update `release_version` in `artifactMetadata.json`.
2. Open and merge a PR to a production branch.
3. Pipeline creates a zip, uploads to S3 RC bucket (`esvc-us-east-2-sfdx-metadata`), registers with AMG, and creates a git tag.

---

## SFDX Managed Package

### Minimal Example

```yaml
global:
  email-reply-to: owning-team@salesforce.com
  production-branches:
    - master
stages:
  package:
    - sfdx-managed-package
  integration-test:
    - sonarqube:
        enabled: false
  publish:
    - sfdx-managed-publish
```

### Testing Mode

```yaml
stages:
  package:
    - sfdx-managed-package:
        testing: true
```

### Required File: sfdx-manifest.json

```json
{
  "user": "healthcloud",
  "package": {
    "id": "03315000000SgBx",
    "version": "04t4W000002kaNA"
  }
}
```

- `user` -- S3 ingest bucket username (do not include the `sfdx-` prefix; it is added automatically)
- `package.id` -- package ID (remains consistent)
- `package.version` -- version ID (changes each release)

### Workflow

1. Upload the package file to S3 ingest bucket (`esvc-us-east-2-sfdx-package-ingest`).
2. Create a branch and update `package.version` in `sfdx-manifest.json`.
3. Open and merge a PR to a production branch.
4. Pipeline transfers the package to S3 RC bucket (`esvc-us-east-2-sfdx-package`) and registers with AMG.

---

## Managed Steps

| Step | Stage | Parameters | Description |
|------|-------|------------|-------------|
| `sfdx-metadata-package` | package | `enabled` (bool), `testing` (bool) | Zips repo contents per `artifactMetadata.json`, uploads to S3, registers with AMG |
| `sfdx-managed-package` | package | `testing` (bool) | Transfers managed package from ingest bucket to RC bucket |
| `sfdx-managed-publish` | publish | (none) | Publishes the managed package and registers with AMG |
| `git-push-tags` | publish | `enabled` (bool) | Creates git tags for the build (disable during testing) |
| `sonarqube` | integration-test | `enabled` (bool) | SonarQube analysis (can be disabled) |

## Key Notes

- Both pipelines only transfer/publish on merges to `production-branches`; PR builds validate but do not publish.
- Use `testing: true` to dry-run without S3 transfers or AMG registration.
- Disable `git-push-tags` during testing to avoid tag conflicts.
- The `transferScripts/` directory in your repo should contain helper scripts referenced by the pipeline.
