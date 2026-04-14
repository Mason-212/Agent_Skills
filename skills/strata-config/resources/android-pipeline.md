# Android Pipeline Configuration

## Minimal Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  build:
    - android-build
    - step:
        name: publish-to-maven-local
        image: docker.repo.local.sfdc.net/sfci/docker-mobile/sfdc_rhel9_jdk17_android/sfdc-rhel9-jdk17-android:latest
        commands:
          - ./gradlew publishToMavenLocal
  publish:
    - publish-jar:
        exact-artifact-match: true
        artifacts:
          - groupId: "com.salesforce.example"
            artifactId: "my-android-lib"
```

## Custom Gradle Tasks Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  build:
    - android-build:
        assembleDebugTasks:
          - customAssembleDebugTask
          - additionalCustomTask
        assembleTasks:
          - customAssembleTask
        checkTasks:
          - customCheckTask
        includeNdk: false
    - step:
        name: publish-to-maven-local
        image: docker.repo.local.sfdc.net/sfci/docker-mobile/sfdc_rhel9_jdk17_android/sfdc-rhel9-jdk17-android:latest
        commands:
          - ./gradlew publishToMavenLocal
  publish:
    - publish-jar:
        exact-artifact-match: true
        artifacts:
          - groupId: "com.salesforce.example"
            artifactId: "my-android-artifact"
```

## Managed Steps

| Step | Stage | Parameters | Description |
|------|-------|------------|-------------|
| `android-build` | build | `assembleDebugTasks` (list), `assembleTasks` (list), `checkTasks` (list), `includeNdk` (bool, default false) | Configures Nexus credentials, bootstraps Gradle, runs assemble and check tasks |
| `publish-jar` | publish | `exact-artifact-match` (bool), `artifacts` (list of groupId/artifactId) | Validates GAV mapping and publishes jars/aars from local `.m2` to Nexus |

## Default Build Behavior

The `android-build` step runs these Gradle tasks by default:

- **PR builds:** `gradle assembleDebug`
- **Branch builds:** `gradle assemble`
- **All builds:** `gradle check`

Override with `assembleDebugTasks`, `assembleTasks`, and `checkTasks` parameters.

## Build Secrets

The `android-build` step supports reading secrets. Compressed files are extracted and the path is available via `$android_build_secrets`:

- `.gz` secrets -- extracted, `build_secrets.sh` sourced automatically
- `.zip` secrets -- extracted, `build_secrets.sh` sourced automatically
- `.txt` secrets -- sourced directly
- Other file types are skipped with a warning

## Key Notes

- You **must** run `publishToMavenLocal` before `publish-jar`; the step reads from the local `.m2` repository.
- Always use the `sfdc_rhel9_jdk17_android` image for custom steps -- it has Nexus configuration, shared `/root/.gradle` and `/root/.m2/` volumes, and the Android SDK.
- The `android-build` step automatically uses the same image.
- Set `includeNdk: true` if your project requires the Android Native Development Kit.
- Gradle wrapper files must be checked into the repo: `gradlew`, `gradle/wrapper/gradle-wrapper.properties`, `gradle/wrapper/gradle-wrapper.jar`.
- If publishing to Nexus, register in the GAV Mapping repository and ensure `team-dva-strata` has publish permissions.
- This pipeline is **in development** -- the design or implementation may change.
