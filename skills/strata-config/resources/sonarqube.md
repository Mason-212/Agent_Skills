# SonarQube and Code Coverage

Use this reference when the request involves SonarQube enablement, PR decoration, coverage reports, `sonar-project.properties`, or troubleshooting scan results.

## Stage Placement

The managed `sonarqube` step belongs under `stages.integration-test`:

```yaml
stages:
  integration-test:
    - sonarqube:
        enabled: true
```

The step is built into managed pipelines and can be explicitly disabled with `enabled: false`.

## Coverage Files by Language

| Language | Coverage Tool | Expected File |
|----------|---------------|---------------|
| Java | JaCoCo | `target/jacoco.exec` |
| Groovy | JaCoCo | `target/jacoco.exec` |
| Python | `coverage` / `pytest-cov` | `coverage.xml` |
| Go | `go test -coverprofile` | `coverage.out` |

## PR Decoration

- For git.soma repos, install the **SonarQube as a Service GitHub app** to enable PR decoration.
- For GitHub Enterprise Cloud (`github.com`) repos, SonarQube PR decoration is not supported. Results are still available in the SonarQube dashboard and build logs.

## `sonar-project.properties`

Add `sonar-project.properties` at the repo root when you need to customize analysis behavior.

Example:

```properties
sonar.coverage.exclusions=integration-tests/*,test_unit.py
```

Common troubleshooting properties:

- `sonar.sources` - source directories relative to the repo root
- `sonar.tests` - test directories relative to the repo root
- `sonar.java.binaries` - compiled Java class directories; override this for non-standard layouts or multi-module repos

## Common Troubleshooting

### Test results or source files not showing up

Verify `sonar.sources` and `sonar.tests` point to the correct directories in `sonar-project.properties`.

### Java scan fails with `No files nor directories matching`

SonarQube defaults `sonar.java.binaries` to `target/classes`. If the project uses a different build layout, set `sonar.java.binaries` explicitly in `sonar-project.properties`.

### Coverage looks lower than expected

Review the default exclusions and add custom `sonar.coverage.exclusions` or related properties in `sonar-project.properties` when needed.

### Quality gate questions

SFCI uses a default quality gate and does not support custom quality gate configuration.

## Dashboard

Dashboard URL pattern:

```text
https://sonarqube.soma.salesforce.com/dashboard?id=<org>.<repo>
```
