# Terraform Provider Pipeline Configuration

## Status

This pipeline type is in **pilot phase**. Call that out when recommending it.

## Minimal Example

```yaml
global:
  email-reply-to: owning-team@salesforce.com
  production-branches:
    - master
stages:
  build:
    - step:
        name: run-tests
        image: docker.repo.local.sfdc.net/sfci/sfdc-pcg/iac_centos7_golang_build
        commands:
          - make testall
  package:
    - terraform-package-provider:
        project_name: terraform-provider-firebom
        version: 0.0.2
        builds:
          flags:
            - -mod=vendor
          ldflags:
            - -s -w
            - -extldflags "-static"
            - -X git.soma.salesforce.com/sfdc-pcg/terraform-provider-firebom/firebom.Version=${VERSION}
            - -X git.soma.salesforce.com/sfdc-pcg/terraform-provider-firebom/firebom.Commit=${COMMIT}
            - -X git.soma.salesforce.com/sfdc-pcg/terraform-provider-firebom/firebom.Branch=${BRANCH}
            - -X git.soma.salesforce.com/sfdc-pcg/terraform-provider-firebom/firebom.BuildUser=${BUILD_USER}
            - -X git.soma.salesforce.com/sfdc-pcg/terraform-provider-firebom/firebom.BuildTime=${BUILD_TIME}
  publish:
    - terraform-publish-provider
```

## Managed Steps

| Step | Stage | Parameters |
|------|-------|------------|
| `terraform-package-provider` | package | `project_name`, `version`, `builds` |
| `terraform-publish-provider` | publish | (none) |

`terraform-publish-provider` must be present to publish provider artifacts.

## Required Fields

### `terraform-package-provider.project_name`
- Terraform provider name
- Defaults to the git repository name if omitted
- Must match the provider naming rules enforced by the pipeline
- Dashes are allowed inside the name, but leading/trailing dashes are not
- Underscores are invalid

### `terraform-package-provider.version`
- Required release version for the provider
- Must follow semantic versioning
- Update the version in `.strata.yml` when merging to the production branch for a new release

## Optional Build Configuration

`builds` maps to a limited subset of goreleaser build configuration. Supported fields include:
- `dir`
- `main`
- `mod_timestamp`
- `flags`
- `asmflags`
- `gcflags`
- `ldflags`
- `env`
- `tags`

These fields are passed into the provider packaging flow; do not assume other goreleaser fields are available.

## Artifact Behavior

### PR Artifacts

PR builds version the provider automatically as:

```text
<current_git_tag_or_0.0.0>-<PR-number>-<short-commit>
```

This avoids manual version bumps for every PR build.

### Production Artifacts

On production branches, the pipeline publishes the version specified in `.strata.yml` and pushes a matching git tag for the release.

## Known Limitations

- Recommended to list only one production branch for this pipeline type.
- The pipeline currently builds providers for:
  - `linux_amd64`
  - `linux_arm64`
  - `darwin_amd64`
  - `darwin_arm64`
  - `windows_amd64`

## Key Notes

- This pipeline packages and publishes Terraform providers to the Terraform Provider buckets used by the Terraform Private Registry.
- The pipeline is intended for Terraform providers, not ordinary Terraform modules. For modules, use `terraform-pipeline.md` instead.
- Validate the provider name and version carefully before suggesting YAML; the pipeline enforces both.
