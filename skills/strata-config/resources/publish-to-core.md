# Publish to Core

Publish an off-core repository to core using two managed steps: `core-packager` (build stage) and `core-deploy` (publish stage).

## Prerequisites

- Branch must follow the `core-{release}-{branch}` naming convention (e.g., `core-256-patch`). Publishing from main/master is not supported.
- Exclude your repo from semver by adding it to `semver/feature.yaml` in `sfci/feature-rollout`.
- For Maven repos, set pom.xml version to `${env.SFCI_PRODUCTION_BRANCH_BUILD_VERSION}`.

## core-packager (Build Stage)

Converts a Node.js repository into a Maven-like folder structure for core deployment. **Required for Node.js repos only**; Maven repos can skip this step.

Uses a CLI (communities `@communities/core-packager` or nucleus `@sfdc-internal/nucleus-core-packager`) with a config JSON as input.

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `core-package-config` | `core-package.config.json` | Config JSON file passed to the core-packager CLI |
| `npm-package` | `communities/core-packager` | Which core-packager CLI to use |
| `npm-version` | `latest` | CLI version |
| `core-pkg-args` | default arguments | Additional CLI arguments (destination argument not accepted) |

## core-deploy (Publish Stage)

Deploys to the core app by calling the itest API. The off-core autobuild link is posted on the git PR.

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `annotations` | `@markfixed@` | CL annotations |
| `ftest-labels` | `~ignore,auracontainer.itest` | Ftest labels for off-core autobuild check |
| `ab-enabled` | `false` | AB testing enablement |
| `project-modules` | - | Override default artifact name |
| `skip-itest` | null | String; itests to skip |
| `submit` | `false` | Submit to precheckin autobuild |

project-modules example:
```yaml
project-modules:
  - module_name: ui-iag-components
    properties_name: ui-iag-components.version
```

## Versioning

### Auto Versioning

Set production-branches with a regex pattern. The version auto-increments based on CI build number.

Example: branch `core-252-patch` translates to `252.<BUILDNUMBER>.0`.

```yaml
global:
  production-branches:
    - r:^core-(\d+)-(\w+): "{0}.$$BUILD_NUMBER.0"
```

### Custom Versioning

Specify a version source file in globals:

```yaml
global:
  core-pkg-version-source: package.json  # also accepts lerna.json or pom.xml
```

## Artifact Publishing

| Publish Type | Versioning | Strata Config |
|-------------|------------|---------------|
| npm | auto | `- npm-publish:` with `safe-version: true` |
| npm | custom | `- npm-publish` |
| maven | auto/custom | `- maven-publish:` with `publish-core-packager: true` |

## Complete Example

```yaml
global:
  email-reply-to: <>@salesforce.com
  production-branches:
    - r:^core-(\d+)-(\w+): "{0}.$$BUILD_NUMBER.0"
stages:
  build:
    - npm-setup:
        yarn-modern: true
    - step:
        name: yarn-validation
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9_nodejs20:latest
        commands:
          - yarn install
          - yarn test
    - core-packager
  publish:
    - npm-publish:
        safe-version: true
    - maven-publish:
        publish-core-packager: true
    - core-deploy:
        submit: true
```
