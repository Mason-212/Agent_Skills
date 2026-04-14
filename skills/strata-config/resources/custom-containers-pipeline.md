# Custom Containers Pipeline Configuration

## Status

This pipeline pattern is in **pilot phase**. Call that out when recommending it.

## When to Use

Use this approach when:
- The repo does not match a documented managed pipeline type
- The team needs full control over build and test logic
- The pipeline can be expressed with user-defined `step` and `steps` blocks running in approved container images
- The workflow is a generic or planned case, such as a Go library flow without first-class managed-pipeline support

For unsupported or planned pipeline types, prefer this pattern over guessing a managed-step workflow.

## Minimal Example

```yaml
global:
  email-reply-to: sfci-team+smoketests@salesforce.com
  log-level: debug
  production-branches:
    - master
    - version1.2
stages:
  build:
    - step:
        name: user-defined-build1
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
        commands:
          - echo "user defined build 1"
    - step:
        name: user-defined-build2
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
        commands:
          - echo "user defined build 2"
  integration-test:
    - step:
        name: itest-override
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
        commands:
          - echo "itest override"
    - step:
        name: workspace-test
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
        workspace-mount-point: /workspace
        commands:
          - |
            if [[ $(pwd) != /workspace ]]; then
              exit 1
            fi
```

## Building Blocks

This pattern does **not** introduce pipeline-specific managed steps. It relies on:
- User-defined `step` blocks for individual actions
- Nested `steps` blocks for serial or parallel groups
- Global settings from `global:`

Read these references before drafting YAML:
- `user-defined-steps.md`
- `global-config-reference.md`
- `environment-variables.md`
- `secrets-and-parameters.md` when secrets or Jenkins parameters are involved

## Key Notes

- SFCI Managed V2 runs on Strata and still requires normal onboarding/prerequisites.
- Use only approved images hosted in `docker.repo.local.sfdc.net`.
- `workspace-mount-point` can be used when commands expect a specific working directory.
- Keep stage intent clear: build/unit-test in `build`, integration tests in `integration-test`, publish logic in `publish`.
- Unsupported container features still apply here: no privileged mode, no bind mounts, no extra volumes.

## Recommendation Heuristic

Prefer a documented managed pipeline when one exists for the artifact type. Use this custom-container pattern only when:
- No managed pipeline fits
- The repo has unusual build steps that managed pipelines do not support
- The user explicitly wants to own the full step logic
