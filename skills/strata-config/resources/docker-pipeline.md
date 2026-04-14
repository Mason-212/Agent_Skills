# Docker Pipeline Configuration

## Minimal Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  build:
    - step:
        name: run-unit-tests
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9_java_build
        commands:
          - mvn -V -Dorg.slf4j.simpleLogger.log.org.apache.maven.cli.transfer.Slf4jMavenTransferListener=warn --batch-mode clean test
  package:
    - docker-build:
        images:
          - dockerfile: ./Dockerfile
            build-context: .
            image-name: my-service
  publish:
    - docker-push
```

## Managed Steps

| Step | Stage | Parameters |
|------|-------|------------|
| `docker-build` | package | `images` (list), `parallel` (bool), `build-args` (list of key/value), `parallel-execution-limit` (int, default 5) |
| `docker-push` | publish | `parallel-execution-limit` (int, default 5) |
| `docker-compose-up` | integration-test | `background` (bool, default true), `docker-compose-files` (list), `environment` (list), `output-logs` (bool), `output-process-list` (bool), `process-list-frequency` (int, default 30), `project-name` (string) |
| `docker-compose-down` | integration-test | (none) |

## docker-build Image Properties

Each entry under `images:` accepts:
- `dockerfile` -- path to Dockerfile (default `./Dockerfile`)
- `build-context` -- build context directory (defaults to directory containing the Dockerfile)
- `image-name` -- **required** when `images` key is set; defaults to git repo name if `images` is omitted

## Build Args

Global build-args apply to all images. Per-image build-args override globals with the same key.

```yaml
package:
  - docker-build:
      build-args:
        - key: globalkey
          value: globalValue
      images:
        - image-name: my-image
          build-args:
            - key: globalkey
              value: localOverride
            - key: localKey
              value: localValue
```

Supported env variables for build-args: `ITEST_IMAGE_TAG`, `DOCKER_REGISTRY_HOST`, `GIT_ORG_AND_REPO`, `GIT_COMMIT`, `BUILD_URL`, `IS_PRODUCTION_BRANCH`, `DOCKER_DEFAULT_AVAILABLE_REGISTRY_ORGS`, `DVA_DOCKER_REGISTRY_HOST`.

## Production Tags

On production branches, `docker-push` publishes with tags: `latest`, `{BUILD_NUMBER}`, `{GIT_COMMIT}`, `{BUILD_NUMBER}-{GIT_COMMIT}`, and any custom git tags created before the push step.

To tag non-production/PR builds with custom tags in dev ECR:

```yaml
global:
  enable-publish-tags-to-ecr-dev: true
```

## Multi-Architecture Builds

```yaml
global:
  target-architecture:
    - x86_64
    - aarch64
```

## Parallel Execution Limit

```yaml
global:
  parallel-execution-limit: 3  # default is 5, applies to all stages

# Or per-stage:
package:
  - docker-build:
      parallel-execution-limit: 3
publish:
  - docker-push:
      parallel-execution-limit: 3
```

## Key Notes

- The `docker-build` step automatically stages images to Artifactory and ECR with itest tags: `<GIT_ORG>-<GIT_REPO>-<BRANCH/PR>-<BUILD_NUMBER>-itest`.
- Nexus URL and read-only credentials are passed automatically to `docker-build` for use in Dockerfiles via `--mount`.
- Docker syntax version declaration at line 1 of the Dockerfile is mandatory to use `--mount` for credentials.
- Do **not** use `pwd` or `.` for volume mounts; use the `BUILD_WORKSPACE` environment variable instead.
- The `--build-arg` key cannot contain special characters except underscore (`_`).
- Git tag must be created **before** `docker-push` in the publish stage for custom git tag publishing.
- `git-push-tags` managed step runs by default; if added explicitly, place it before `docker-push`.
