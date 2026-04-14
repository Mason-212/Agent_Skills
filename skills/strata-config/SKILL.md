---
name: strata-config
description: "Create or debug `.strata.yml` for SFCI Managed pipelines: stages, steps, globals"
---

# Strata Configuration

## When to Use

Activate this skill when:
- Creating a new `.strata.yml` file for an SFCI Managed pipeline
- Reviewing, explaining, modifying, or debugging an existing `.strata.yml`
- Adding managed steps (docker-build, docker-push, helm, terraform, npm, maven, etc.)
- Configuring pipeline stages, user-defined steps, environment variables, secrets, or build parameters
- Choosing between a managed pipeline type and a custom-container pipeline
- Setting up integration tests, publish controls, schedules, merge queues, multi-arch builds, or runner agents
- Onboarding a new org or repo to SFCI Managed (webhooks, service users, GitHub App)

## Operating Procedure

1. Identify the user's goal: create, update, review, explain, or debug.
2. Identify the pipeline type or artifact type involved. If it is unclear, ask before drafting YAML.
3. Before answering, read the relevant references:
   - Always read `resources/global-config-reference.md` and `resources/user-defined-steps.md` for any `.strata.yml` change.
   - Read `resources/managed-steps-reference.md` whenever the request involves a managed step.
   - Read the matching pipeline-type reference for the artifact being built or published.
   - Read `resources/advanced-features.md` for scheduling, publish controls, multi-arch, remote runners, merge queues, auto-merge, GEC limitations, or agent sizing.
   - Read `resources/sonarqube.md` for SonarQube setup, code coverage, `sonar-project.properties`, and troubleshooting analysis issues.
   - Read `resources/environment-variables.md` and `resources/secrets-and-parameters.md` when the request mentions environment variables, Vault secrets, Jenkins parameters, or custom build descriptions.
   - Read `resources/github-setup.md` when the request involves onboarding, webhooks, service users, or GitHub App installation.
4. Do not invent keys, step names, or parameters. Prefer documented names, valid stage placement, and examples from the references.
5. Validate the draft or review against the checklist below before responding.
6. In the response, surface assumptions, prerequisites, and any pilot-status limitations instead of silently guessing.

## Validation Checklist

Before finalizing a `.strata.yml` recommendation, verify:
- `global.email-reply-to` is present
- `production-branches` is set intentionally, or intentionally omitted/empty when no production workflow should run
- Every managed step is placed in a valid stage
- User-defined step names do not reuse stage names
- Custom step images come from `docker.repo.local.sfdc.net`
- `when` conditions and version strings use `$$` SFCI variables where required
- The config does not rely on unsupported features such as privileged mode, bind mounts, or additional volumes
- Pipeline-specific prerequisites are called out, especially for publish behavior, tagging, or required paired steps
- Any pilot or in-development feature is labeled clearly in the answer

## Quick Start

Minimal working Docker pipeline:

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master

stages:
  build:
    - step:
        name: unit-tests
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
        commands:
          - echo "run tests"
  package:
    - docker-build:
        images:
          - image-name: my-service
            dockerfile: Dockerfile
  publish:
    - docker-push
```

## File Structure

A `.strata.yml` has two top-level keys:

- **`global:`** - Pipeline-wide settings (email, production branches, timeouts, etc.)
- **`stages:`** - Ordered pipeline stages containing managed and user-defined steps

## Pipeline Stages

| Stage | Purpose |
|-------|---------|
| `precheck` | Policy compliance checks on PRs/branches, such as credential scanning and codeowner validation. |
| `build` | Build and unit test your code using user-defined steps. |
| `package` | Produce deployment artifacts (docker images, jars, helm charts, terraform archives, etc.). |
| `integration-test` | Run integration tests and analysis steps such as `sonarqube`, typically via docker-compose, managed steps, or custom steps. |
| `publish` | Release packages on successful builds. Handles signing, staging to S3/ECR/Artifactory. |
| `post-publish` | Post-release steps (notifications, deployments, cleanup). |

All stages are optional. Simple pipelines may only define `build`.

## Core Step Syntax

**User-defined step** (usually runs your commands in a Linux container, or on a Windows runner for Windows pipelines):
```yaml
- step:
    name: my-step                    # Required, must not conflict with stage names
    image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9  # Required for Linux container steps
    commands:                        # Optional (defaults to image entrypoint or runner shell)
      - echo "hello"
    environment:                     # Optional
      - name: MY_VAR
        value: my-value
      - name: BUILD_NUMBER          # Value auto-injected if omitted
    when:                            # Optional conditional
      - operator: EQ
        value: $$IS_PRODUCTION_BRANCH
        other: 'true'
    user: '0:0'                      # Optional, run as specific user
    workspace-mount-point: /workspace  # Optional, custom mount path
    continue-on-fail: true           # Optional, don't fail pipeline on error
    background: true                 # Optional, run as background service
    runner: remote-linux             # Optional for Linux remote execution; Windows pipelines can use remote-windows
```

Windows example:
```yaml
- step:
    name: windows-build
    runner: remote-windows
    commands:
      - ./my-power-shell-script.ps1
```

**Parallel steps** (run multiple steps concurrently):
```yaml
- steps:
    name: parallel-group
    parallel: true
    pipeline:
      - step:
          name: step-1
          image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
          commands:
            - echo "runs in parallel"
      - step:
          name: step-2
          image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
          commands:
            - echo "runs in parallel"
```

**Managed step** (preset functionality with parameters):
```yaml
- docker-build:
    images:
      - image-name: my-service
        dockerfile: Dockerfile
```

## Detailed Reference

Use these files as a routing table. Read only the files relevant to the task, but always start with the global and step syntax references before drafting or editing YAML.

### Configuration Reference
- [Global Configuration Keys](resources/global-config-reference.md) - All global keys with types, defaults, descriptions
- [User-Defined Steps](resources/user-defined-steps.md) - CIX step syntax, conditionals, parallel, background
- [Managed Steps Reference](resources/managed-steps-reference.md) - All managed step names and parameters
- [Environment Variables](resources/environment-variables.md) - Auto-injected variables available in steps
- [Secrets and Parameters](resources/secrets-and-parameters.md) - Vault secrets, build parameters

### Pipeline Types
- [Docker](resources/docker-pipeline.md) - Docker build/push/compose
- [Maven](resources/maven-pipeline.md) - Maven build and publish
- [NPM](resources/npm-pipeline.md) - NPM/Lerna/semantic-release
- [Python](resources/python-pipeline.md) - Python library publishing
- [Helm](resources/helm-pipeline.md) - Helm chart packaging
- [Terraform](resources/terraform-pipeline.md) - Terraform module publishing
- [Bazel](resources/bazel-pipeline.md) - Bazel build and test
- [Buildpacks](resources/buildpacks-pipeline.md) - Cloud Native Buildpacks
- [Gradle](resources/gradle-pipeline.md) - Gradle build and publish
- [SBT](resources/sbt-pipeline.md) - Scala Build Tool
- [RPM](resources/rpm-pipeline.md) - RPM packaging and 1P promotion
- [FCP](resources/fcp-pipeline.md) - FCP pipeline
- [Windows](resources/windows-pipeline.md) - Windows agent builds
- [MSI](resources/msi-pipeline.md) - Microsoft Software Installer
- [SFDX](resources/sfdx-pipeline.md) - Salesforce DX metadata and managed packages
- [Lambda](resources/lambda-pipeline.md) - AWS Lambda deployment
- [Android](resources/android-pipeline.md) - Android builds
- [Terraform Provider](resources/terraform-provider-pipeline.md) - Terraform provider packaging and publish flow (pilot)
- [Custom Containers](resources/custom-containers-pipeline.md) - Build your own pipeline with user-defined steps and your own container images (pilot)

If the repo does not fit a documented managed pipeline type, fall back to the custom-container reference plus `resources/user-defined-steps.md` instead of forcing a managed-step solution.
This is also the safest fallback for generic unit-test/custom-container repos and planned cases like Go library workflows.

### Features
- [Integration Testing](resources/integration-testing.md) - Docker-compose patterns, service connectivity
- [Advanced Features](resources/advanced-features.md) - Multi-arch, GPE, auto-merge, merge queues, scheduling, GEC limitations, ALI substrate
- [SonarQube](resources/sonarqube.md) - SonarQube enablement, coverage files, `sonar-project.properties`, troubleshooting
- [Publish to Core](resources/publish-to-core.md) - Core packaging and deployment
- [GitHub Setup](resources/github-setup.md) - Org onboarding, service users, webhook configuration

## Best Practices

1. **`email-reply-to` is required** - Set to your team's distribution list
2. **Always set `production-branches`** - Without it, no production workflows execute
3. **Use RHEL9 images** - Prefer `sfdc_rhel9` over deprecated CentOS 7 images
4. **Artifactory-only images** - Strata has no Docker Hub access; all images must be from `docker.repo.local.sfdc.net`
5. **Version your images** - Pin image tags instead of using `latest` in production
6. **Use `r:` prefix for regex branches** - e.g., `r:release_\d+\.\d+.*`
7. **Avoid privileged mode** - Docker privileged mode is not supported in SFCI Managed
8. **No bind mounts** - Additional volumes and bind mounts are not supported
9. **Use `$$` for SFCI variables** in `when` conditions - e.g., `$$IS_PRODUCTION_BRANCH`
10. **Keep stages focused** - Build in `build`, package in `package`, test in `integration-test`
11. **Label pilot features clearly** - Call out when a pipeline type or feature is pilot or in development
