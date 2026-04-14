# RPM Pipeline Configuration

## Minimal Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  package:
    - rpm-package:
        package-repository: my-repo-name
```

Using `rpm-package` implicitly triggers `rpm-stage` (unsigned RPMs to staging repos) and `rpm-publish` (signed RPMs to release repos on production branches).

## Custom Build with rpm-stage

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  build:
    - step:
        name: my-own-package-step
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9_java_rpmbuild
        commands:
          - rpmbuild -ba --buildroot=$(pwd)/buildroot
              --define "_rpmdir $(pwd)/output"
              --define "_sourcedir $(pwd)"
              tiny-rpm.spec
              --define "%my_release ${BUILD_NUMBER}"
    - rpm-stage:
        package-repository: my-repo-name
        publish-to-falcon: false
```

## Standalone rpm-publish

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  publish:
    - rpm-publish:
        package-repository: my-repo-name
```

## Full RPM 1P Pipeline Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  pr-automerge:
    pr-title:
      - r:.*
stages:
  package:
    - rpm-package:
        package-repository: my-repo-name
        package-generation-command: make package
        package-generation-mount-point: /tmp/project
        package-generation-images:
          - docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9_java_rpmbuild
    - rpm-stage
  publish:
    - rpm-publish
    - rpm-publish-1p:
        auto-promote: true
        canary-only: false
        rpm-patterns: ['r:.*my-rpm-.*']
        source-rpm-repos:
          - rpm-rc-signed
          - rpm-rc-signed-v2
        destinations:
          - all
```

## Managed Steps

| Step | Stage | Parameters | Description |
|------|-------|------------|-------------|
| `rpm-package` | package | `package-repository` (required), `package-generation-command` (default: `make package`), `package-generation-mount-point` (default: `/tmp/project`), `package-generation-images` (list; default: `sfdc_rhel9_java_rpmbuild`) | Builds RPMs in container, implicitly triggers stage and publish |
| `rpm-stage` | package/build | `package-repository` (required if no `rpm-package`), `publish-to-falcon` (bool, default false) | Publishes unsigned RPMs to staging repos; implicitly triggers `rpm-publish` on production branches |
| `rpm-publish` | publish | `package-repository` (required if standalone) | Publishes signed RPMs to release repos |
| `rpm-publish-1p` | publish | `auto-promote` (bool, default true), `rpm-patterns` (list of regex), `canary-only` (bool), `source-rpm-repos` (list), `destinations` (list, default `all`) | Promotes RPMs from artifactory release repos to 1P data centers |

## Key Notes

- RPMs must be in the workspace and follow the naming convention at https://sfdc.co/sfci-rpm-validations.
- Default container image is `sfdc_rhel9_java_rpmbuild` (produces el9 RPMs).
- For 1P promotion, RPMs must first be in `rpm-rc-signed` release repos (requires `rpm-publish`).
- Change case annotation `@gus-change-case: <number>@` is required in PR title, commit message, or PR description for 1P promotion.
- Promotion annotation `@run-mdp-promotion@` is required only if `auto-promote` is set to false.
- Use `pr-automerge` in global config for auto-merging PRs (regex titles supported with `r:` prefix).
- Vault secrets: source `$build_secrets_file_path` in custom steps to access credentials.
