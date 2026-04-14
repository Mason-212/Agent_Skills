# Secrets and Build Parameters

## Vault Secrets

SFCI Managed provides Vault secrets through file-path environment variables. Source the secrets file in your step commands to load secrets as environment variables.

### Usage

```yaml
stages:
  build:
    - step:
        name: build-with-secrets
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
        commands:
          - source $build_secrets_file_path
          - echo "Secret loaded: $MY_SECRET_VAR"
```

```yaml
stages:
  post-publish:
    - step:
        name: notify
        image: docker.repo.local.sfdc.net/sfci/kuleana/stampy-p3-image:43
        commands:
          - source $post_publish_secrets_file_path
          - ./send-notification.sh
```

### Secret File Path Variables

| Variable | Stage |
|----------|-------|
| `$build_secrets_file_path` | build |
| `$post_publish_secrets_file_path` | post-publish |

## Build Parameters

Build parameters allow passing data from the Jenkins UI into pipeline steps. They are defined under `global.parameters` in `.strata.yml`.

### Key Rules

- All user-defined parameters are exposed as environment variables with the **`PARAMETERS_`** prefix to avoid conflicts with SFCI environment variables.
- Changes to the `parameters` section take **one build execution** with the old configuration before the new configuration is reflected.
- Parameter values are **trimmed** by default for all types.

### Parameter Types

| Type | Description | Extra Attributes |
|------|-------------|------------------|
| `string` | Free-form text input. | `default`, `description`, `required` |
| `boolean` | Toggle (`true`/`false`). | `default`, `description` |
| `choice` | Dropdown selection from a list. | `default`, `description`, `choices` (list) |

### Parameter Attributes

| Attribute | Required | Description |
|-----------|----------|-------------|
| `name` | Yes | Parameter name. Accessed as `PARAMETERS_<name>` in steps. |
| `type` | Yes | One of: `string`, `boolean`, `choice`. |
| `default` | No | Default value shown in Jenkins UI. |
| `description` | No | Help text displayed in Jenkins UI. |
| `required` | No | When `true`, the parameter must be filled (applies to `string`). |
| `choices` | No | List of options (required for `choice` type). |

### Full Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  parameters:
    - name: "GIT_COMMIT"
      default: "string-test"
      description: "Custom git commit override"
      type: "string"
      required: true
    - name: "StringParam"
      default: "string-test1"
      type: "string"
      description: "A string parameter"
    - name: "test23"
      default: "false"
      description: "A boolean toggle"
      type: "boolean"
    - name: "test_environment"
      default: "prod"
      description: "Target environment"
      type: "choice"
      choices:
        - dev
        - prod
        - test
  production-branches:
    - master
```

### Accessing Parameters in Steps

Declare each parameter in the step's `environment` block using the `PARAMETERS_` prefix:

```yaml
stages:
  build:
    - step:
        name: mvn-test
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
        environment:
          - name: PARAMETERS_GIT_COMMIT
          - name: PARAMETERS_StringParam
          - name: PARAMETERS_test23
          - name: PARAMETERS_test_environment
          - name: GIT_COMMIT  # this is the SFCI env var, different from PARAMETERS_GIT_COMMIT
        commands:
          - echo "$PARAMETERS_GIT_COMMIT $PARAMETERS_StringParam"
          - echo "$PARAMETERS_test_environment"
```

### Using Parameters in Docker Build Args

Parameters can be passed as build arguments to `docker-build` steps:

```yaml
stages:
  package:
    - docker-build:
        build-args:
          - key: VERSION_NUMBER
            value: ${PARAMETERS_VERSION_NUMBER}
          - key: TEST_ENV
            value: ${PARAMETERS_TEST_ENV}
        images:
          - image-name: my-image
            build-args:
              - key: ARTIFACTORY_REPO
                value: ${PARAMETERS_ARTIFACTORY_REPO}
```

### Using Parameters in Build Descriptions

Reference parameters in `build-description` with the `PARAMETERS_` prefix:

```yaml
global:
  build-description: "Build $BUILD_NUMBER triggered by ${PARAMETERS_USERNAME}"
```
