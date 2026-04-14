# Gradle Pipeline Configuration

## Minimal Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  build:
    - gradle-setup
    - step:
        name: gradle-build
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_gradle_sfci:latest
        commands:
          - ./gradlew test build publishToMavenLocal
  publish:
    - publish-jar:
        exact-artifact-match: true
        artifacts:
          - groupId: "com.salesforce.example"
            artifactId: "my-library"
```

## Docker Packaging Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  build:
    - gradle-setup
    - step:
        name: gradle-build
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_gradle_sfci:latest
        commands:
          - ./gradlew shadowJar
  package:
    - docker-build:
        images:
          - image-name: gradle-docker-v2-test
  publish:
    - docker-push
```

## Managed Steps

| Step | Stage | Parameters | Description |
|------|-------|------------|-------------|
| `gradle-setup` | build | (none) | Configures Nexus read-only credentials, bootstraps the Gradle wrapper |
| `publish-jar` | publish | `exact-artifact-match` (bool), `artifacts` (list of groupId/artifactId) | Validates GAV mapping and publishes jars from local `.m2` to Nexus |
| `docker-build` | package | `images` (list with `image-name`) | Builds a Docker image containing the artifact |
| `docker-push` | publish | (none) | Pushes the Docker image to the registry |

## Key Notes

- You **must** run `publishToMavenLocal` during your build before using `publish-jar`; the step reads from the local `.m2` repository.
- Always use the `sfdc_gradle_sfci` image -- it is configured for internal Nexus and remaps `/root/.gradle` and `/root/.m2/` to shared volumes.
- The Gradle wrapper files must be checked into the repo: `gradlew`, `gradle/wrapper/gradle-wrapper.properties`, `gradle/wrapper/gradle-wrapper.jar`.
- If publishing to Nexus, register your package in the GAV Mapping repository and ensure `team-dva-strata` has publish permissions.
- Set `exact-artifact-match: true` on `publish-jar` when you have multiple artifacts with similar names.
