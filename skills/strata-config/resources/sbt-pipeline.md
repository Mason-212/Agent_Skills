# SBT Pipeline Configuration

## Minimal Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  build:
    - sbt-setup
    - step:
        name: sbt-build
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_centos7_sbt:51
        commands:
          - sbt test publishM2
  publish:
    - publish-jar:
        exact-artifact-match: true
        artifacts:
          - groupId: "com.salesforce.example"
            artifactId: "my-sbt-lib"
```

## Adding Extra Nexus Repositories

```yaml
stages:
  build:
    - sbt-setup:
        additional-repositories:
          - artifactory-k8s-einstein
```

## Managed Steps

| Step | Stage | Parameters | Description |
|------|-------|------------|-------------|
| `sbt-setup` | build | `additional-repositories` (list of repo names) | Configures Nexus read-only credentials and internal repositories (central, releases, thirdparty, sbt-plugin-releases) |
| `publish-jar` | publish | `exact-artifact-match` (bool), `artifacts` (list of groupId/artifactId) | Validates GAV mapping and publishes jars from local `.m2` to Nexus |

## Key Notes

- You **must** run `publishM2` during your build before using `publish-jar`; the step reads from the local `.m2` repository.
- Always use the `sfdc_centos7_sbt` image -- it is configured for internal Nexus and remaps `/root/.m2/` to a shared volume.
- By default, `sbt-setup` configures these Nexus repos: central, releases, thirdparty, sbt-plugin-releases. Use `additional-repositories` to add more.
- If publishing to Nexus, register your package in the GAV Mapping repository and ensure `team-dva-strata` has publish permissions.
- Set `exact-artifact-match: true` on `publish-jar` when you have multiple artifacts with similar names.
- This pipeline is in **pilot phase** -- the design or implementation may change.
