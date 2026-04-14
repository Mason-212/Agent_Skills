# FCP Pipeline Configuration

## Minimal Example (Falcon S3 Publish)

```yaml
global:
  email-reply-to: your-team@salesforce.com
  jenkins-environment: true
  production-branches:
    - master
stages:
  build:
    - fcp-artifact-build
  package:
    - fcp-artifact-package
  publish:
    - fcp-artifact-publish
```

## 1P Promotion Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  jenkins-environment: true
  production-branches:
    - master
stages:
  build:
    - fcp-artifact-build:
        environment:
          - name: CHANGE_ID
            value: $$CHANGE_ID
          - name: COMMIT_ID
            value: $$GIT_COMMIT
        unit-test: tnrp/unittest
        package: tnrp/package
        build-image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9_docker_jq
        package-script-params: "-e ${CHANGE_ID} -c ${COMMIT_ID}"
  package:
    - fcp-artifact-package
  publish:
    - fcp-publish-1p:
        use-fcp-legacy-repo-path: true
        auto-promote: true
```

## PR Evaluation (Custom Step)

```yaml
stages:
  precheck:
    - step:
        name: run-pr-evaluation
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
        when:
          - operator: IS_SET
            value: $$CHANGE_TARGET
          - operator: NEQ
            value: $$BUILD_TYPE
            other: worker
        environment:
          - name: PR_EVALUATION
            value: tnrp/evaluate_pr
        commands:
          - echo -e "Executing PR evaluation...\n" && ${PR_EVALUATION}
```

## PR Evaluation (Managed Step)

```yaml
stages:
  precheck:
    - fcp-evaluate-pr:
        user: root
        image: docker.repo.local.sfdc.net/sfci/sfcd/vmf-schema/sfcd-vmf-validator:93
        script-path: tnrp/evaluate_pr
        script-params: '-i ${CHANGE_ID} -s ${GIT_COMMIT} -r ${GIT_REPO}'
        environment:
          - name: CHANGE_ID
            value: $$CHANGE_ID
```

## Auto-Merge Configuration

```yaml
global:
  pr-automerge:
    pr-title:
      - r:.*
  skip-gh-merge-queue-build: false
```

## Managed Steps

| Step | Stage | Parameters | Description |
|------|-------|------------|-------------|
| `fcp-evaluate-pr` | precheck | `image`, `user`, `script-path` (default: `tnrp/evaluate_pr`), `script-params`, `environment` | Runs PR evaluation script (optional) |
| `fcp-artifact-build` | build | `build-image` (default: `sfdc_rhel9_docker_jq`), `unit-test` (default: `tnrp/unittest`), `package` (default: `tnrp/package`), `package-script-params`, `utest-script-params`, `environment` | Runs unit tests and packaging scripts |
| `fcp-artifact-package` | package | (none) | Zips build artifacts from `build_artifacts` directory; versions with semver or `${year}.${month}${sprint}.${commit_time}` |
| `fcp-artifact-publish` | publish | (none) | Signs zip and publishes to Falcon S3 with latest file and manifest |
| `fcp-publish-1p` | publish | `auto-promote` (bool, default false), `use-fcp-legacy-repo-path` (bool) | Signs and publishes to `content_repo_rc` in artifactory; promotes to 1P kingdoms when auto-promote is true |
| `validate-change-case` | precheck | (none) | Explicit change case validation (use when custom steps must run before it) |

## Key Notes

- Change case annotation `@gus-change-case: <number>@` is required in PR title/commit/description for both S3 and 1P publishing.
- Promotion annotation `@run-fcp-promotion@` is required for 1P unless `auto-promote: true` is set.
- Default scripts are `tnrp/unittest` and `tnrp/package` relative to repo root.
- If using git commands in packaging scripts, add the workspace to safe directory: `git config --global --add safe.directory $(pwd)`.
- Vault secrets: source `$build_secrets_file_path` in custom steps.
- Staggering is not supported by SFCI; use Puppet-DIY for staggered deployments.
