# Maven Pipeline Configuration

## Minimal Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  publish:
    - maven-publish
```

## Managed Steps

| Step | Stage | Parameters |
|------|-------|------------|
| `maven-publish` | publish | `auto-versioning-publish` (bool, default false), `maven-publish-jar-image` (string), `maven-publish-jar-args` (string) |
| `publish-jar` | publish | `artifacts` (list of groupId/artifactId), `exact-artifact-match` (bool) |
| `maven-verify` | integration-test | `maven-publish-jar-image` (string), `maven-publish-jar-args` (string), `verify-production-branches` (bool, default true) |
| `mvn-prepare-release` | build | `continue-on-fail` (bool, default true) |
| `mvn-auto-version-update` | publish | `version-type-to-increment` (list: MAJOR/MINOR/PATCH), `continue-on-fail` (bool, default true) |

## Method 1: Publish All Jars (maven-publish)

By default runs `mvn deploy` on production branches. Publishes all jars created in the pipeline.

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  publish:
    - maven-publish
```

### With Multi-Module Maven Release Plugin

```yaml
stages:
  publish:
    - maven-publish:
        auto-versioning-publish: true  # required for multi-module release
        maven-publish-jar-image: custom-image  # optional
        maven-publish-jar-args: "-Dfoo=bar"    # optional
```

## Method 2: Publish Specific Artifacts (publish-jar)

Requires symlink of `.m2/repository` and running `mvn install` before publish.

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  build:
    - step:
        name: mvn-build
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9_java_build:latest
        commands:
          - rm -rf /root/.m2/repository/
          - ln -s /cix/tmp/.strata/.m2/repository /root/.m2/repository
          - mvn install
  publish:
    - publish-jar:
        artifacts:
          - groupId: "com.salesforce.sfci.managed"
            artifactId: "managed-jar"
```

## Maven Verify (Integration Test)

```yaml
stages:
  integration-test:
    - maven-verify
```

Optional args: `maven-publish-jar-image`, `maven-publish-jar-args`, `verify-production-branches` (set false to skip on production branches).

## Auto Versioning

Combine `mvn-prepare-release` (build stage) with `mvn-auto-version-update` (publish stage) for automated release versioning.

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - main
stages:
  build:
    - mvn-prepare-release:
        continue-on-fail: false
  publish:
    - mvn-auto-version-update:
        version-type-to-increment: ['PATCH']
        continue-on-fail: false
```

- `mvn-prepare-release` removes `-SNAPSHOT` from pom version and creates a local git commit.
- `mvn-auto-version-update` creates a git tag (`$artifactid.$version`), auto-increments the version, and pushes a snapshot commit.

## Key Notes

- Default build image is `docker-images/sfdc_rhel9_java_rpmbuild/java8`.
- For `publish-jar`, you **must** symlink `.m2/repository` to `/cix/tmp/.strata/.m2/repository`.
- For `publish-jar`, you **must** run `mvn install` before the publish stage.
- Use `exact-artifact-match: true` in `publish-jar` when artifact IDs have similar names.
- Publishing to Nexus requires GAV Mapping registration (PR to the GAV Mapping repo).
- The `team-dva-strata` user needs Nexus publish permissions for your nexus path.
- For GEC (github.com) repos, GAV mapping is not supported; add repo to the feature.yaml skip list instead.
