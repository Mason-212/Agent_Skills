# Environment Variables

SFCI Managed auto-injects environment variables into builds. You can access them in user-defined steps either by setting `jenkins-environment: true` globally or by declaring them explicitly in each step's `environment` block.

## Injecting Environment Variables

### Option 1: Global Injection

Set `jenkins-environment: true` in the global section to automatically inject all Jenkins environment variables into every user-defined step:

```yaml
global:
  jenkins-environment: true
```

### Option 2: Per-Step Declaration

Declare specific variables in a step's `environment` block. When only `name` is provided (no `value`), the variable is pulled from the build environment:

```yaml
- step:
    name: my-step
    image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
    environment:
      - name: BUILD_NUMBER        # injected from Jenkins
      - name: GIT_COMMIT          # injected from Jenkins
      - name: CUSTOM_VAR          # injected from Jenkins
        value: custom-value       # or set an explicit value
    commands:
      - echo "$BUILD_NUMBER"
```

## Common Auto-Injected Variables

The following variables are commonly available in builds (injected by Jenkins and SFCI):

| Variable | Description |
|----------|-------------|
| `BUILD_NUMBER` | Current build number in Jenkins. |
| `GIT_COMMIT` | SHA of the commit being built. |
| `IS_PRODUCTION_BRANCH` | Set to `true` when the build runs on a branch listed in `production-branches`. Available as `$$IS_PRODUCTION_BRANCH` in `when` conditions. |
| `BRANCH_NAME` | Name of the branch being built. |
| `JOB_NAME` | Name of the Jenkins job. |
| `WORKSPACE` | Path to the Jenkins workspace directory. |

## Build Parameters as Environment Variables

User-defined build parameters (declared under `global.parameters`) are exposed as environment variables with a `PARAMETERS_` prefix:

```yaml
environment:
  - name: PARAMETERS_GIT_COMMIT       # user-defined parameter
  - name: PARAMETERS_StringParam
  - name: GIT_COMMIT                  # SFCI env var (different from PARAMETERS_GIT_COMMIT)
```

See [secrets-and-parameters.md](secrets-and-parameters.md) for full details on defining build parameters.

## Using Variables in Build Descriptions

Environment variables can be referenced in `build-description` using `$VAR` or `${VAR}` syntax:

```yaml
global:
  build-description: "Build $BUILD_NUMBER triggered by ${PARAMETERS_USERNAME}"
```

## Secrets File Path Variables

SFCI provides file-path variables pointing to sourced secrets per stage:

| Variable | Available In | Description |
|----------|-------------|-------------|
| `$build_secrets_file_path` | build stage | Path to Vault secrets file for the build stage. |
| `$post_publish_secrets_file_path` | post-publish stage | Path to Vault secrets file for the post-publish stage. |

Source these files in your commands to load secrets:

```yaml
commands:
  - source $build_secrets_file_path
  - echo "$MY_SECRET"
```
