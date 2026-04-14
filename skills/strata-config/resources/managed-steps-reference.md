# Managed Steps Reference

A comprehensive list of all managed (built-in) steps available in SFCI Managed V2 pipelines.

## Summary Table

| Managed Step | Valid Stage(s) | Pipeline Type | Description |
|---|---|---|---|
| `docker-build` | package | Docker | Builds Docker image(s) and stages them to Artifactory and ECR with itest tags |
| `docker-push` | publish | Docker | Publishes Docker images to Artifactory and ECR with production tags |
| `docker-compose-up` | integration-test | Docker | Spins up containers using a Docker Compose file |
| `docker-compose-down` | integration-test | Docker | Stops all running containers and removes volumes |
| `maven-publish` | publish | Maven | Publishes jars to Nexus via `mvn deploy` or multi-module Maven release plugin |
| `maven-verify` | integration-test | Maven | Runs `mvn --batch-mode verify` for validation |
| `publish-jar` | publish | Maven, Gradle, SBT, Android | Publishes specific JAR/AAR artifacts to Nexus by groupId/artifactId |
| `mvn-prepare-release` | build | Maven | Removes SNAPSHOT from pom version to create a release version |
| `mvn-auto-version-update` | publish | Maven | Auto-increments version, creates git tag, pushes next SNAPSHOT version |
| `npm-setup` | build | NPM | Configures Nexus read-only credentials and internal NPM repositories |
| `npm-publish` | publish | NPM, Core | Publishes NPM package to the npmjs-internal Nexus repository |
| `lerna-publish` | publish | NPM | Handles multi-package publishing for JavaScript monorepos using Lerna |
| `npm-semantic-release` | publish | NPM | Auto-computes next version from conventional commits, creates git tag and GitHub release |
| `python-publish` | publish | Python | Publishes Python wheel and tar packages to Nexus |
| `helm-package` | package | Helm | Packages Helm charts from specified paths with versioning |
| `helm-publish` | publish | Helm | Publishes packaged Helm charts to S3 |
| `terraform-package` | package | Terraform | Bundles Terraform packages from specified paths with versioning |
| `terraform-publish` | publish | Terraform | Publishes Terraform packages to S3 |
| `bazel-precheck` | precheck | Bazel | Detects changed files and finds corresponding Bazel targets |
| `bazel-build-and-test` | build | Bazel | Runs bazel build and test commands to generate OCI-compliant tarballs |
| `bazel-package` | package | Bazel | Packages artifacts from bazel-build-and-test and publishes as itest images |
| `bazel-container-publish` | publish | Bazel | Publishes container images packaged in bazel-package step |
| `buildpack-package` | package | Buildpack | Packages Cloud Native Buildpacks using CNB tooling |
| `buildpack-publish` | publish | Buildpack | Publishes packaged buildpack images to Artifactory and ECR |
| `gradle-setup` | build | Gradle | Configures Nexus credentials and bootstraps the Gradle wrapper |
| `sbt-setup` | build | SBT | Configures Nexus credentials and internal SBT repositories |
| `rpm-package` | package | RPM | Builds RPMs using configurable images and commands; implicitly triggers rpm-stage and rpm-publish |
| `rpm-stage` | build, package | RPM | Publishes unsigned RPMs to staging repos; implicitly triggers rpm-publish on production branches |
| `rpm-publish` | publish | RPM | Signs and publishes RPMs to release repositories |
| `rpm-publish-1p` | publish | RPM | Promotes RPM artifacts to 1P Salesforce data centers |
| `fcp-evaluate-pr` | precheck | FCP | Runs PR evaluation scripts as a managed step |
| `fcp-artifact-build` | build | FCP | Runs unit test and packaging scripts for FCP artifacts |
| `fcp-artifact-package` | package | FCP | Zips packaged FCP files into a versioned artifact |
| `fcp-artifact-publish` | publish | FCP | Publishes signed FCP zip artifact to Falcon S3 |
| `fcp-publish-1p` | publish | FCP | Publishes and promotes FCP artifacts to 1P data centers |
| `validate-change-case` | precheck | FCP | Validates GUS change case in PR title or commit message |
| `msi-publish` | publish | MSI | Publishes .msi packages to the org's MSI Artifactory repository |
| `lambda-package` | package | Lambda | Packages Lambda function code into container images for ECR |
| `lambda-publish` | publish | Lambda | Publishes Lambda container images to production ECR |
| `android-build` | build | Android | Configures Nexus, bootstraps Gradle, runs assemble and check tasks for Android |
| `sfdx-metadata-package` | package | SFDX Metadata | Packages SFDX metadata into a zip for S3 transfer and AMG registration |
| `sfdx-managed-package` | package | SFDX Package | Packages SFDX managed packages for transfer |
| `sfdx-managed-publish` | publish | SFDX Package | Publishes SFDX managed packages to S3 RC bucket and registers with AMG |
| `git-push-tags` | publish | All | Pushes git tags created during production branch builds (added by default) |
| `sonarqube` | integration-test | All | Runs SonarQube code analysis (built-in, can be enabled/disabled) |
| `core-packager` | build | Core | Converts Node repositories into Maven-like folder structure for core deployment |
| `core-deploy` | publish | Core | Deploys off-core repository artifacts to the Salesforce core app |
| `downstream-dependencies` | integration-test | All (NPM) | Validates upstream changes do not break specified downstream repositories |
| `terraform-package-provider` | package | Terraform Provider | Packages Terraform providers using goreleaser for multiple OS/arch combinations |
| `terraform-publish-provider` | publish | Terraform Provider | Publishes packaged Terraform providers to the Terraform Provider buckets |

## Step Details

### docker-build
- **Stage**: package
- **Pipeline Type**: Docker
- **Description**: Builds Docker image(s) and stages them to Artifactory and ECR with itest tags. Images are tagged as `<GIT_ORG>-<GIT_REPO>-<BRANCH/PR>-<BUILD_NUMBER>-itest` and `<GIT_ORG>-<GIT_REPO>-<BRANCH/PR>-latest-itest`. Also builds with a simple `itest` tag for local pipeline use.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `images` | list | Single image named after git repo | List of images to build |
| `images[].dockerfile` | string | `./Dockerfile` | Path to the Dockerfile |
| `images[].build-context` | string | Directory of Dockerfile | Docker build context path |
| `images[].image-name` | string | Git repo name | Required when `images` key is set |
| `build-args` | list | none | Global build arguments (key/value pairs) applied to all images |
| `images[].build-args` | list | none | Per-image build arguments that override globals |
| `parallel` | boolean | false | Enable parallel image builds |
| `parallel-execution-limit` | integer | 5 | Max number of concurrent build operations |

**Example YAML:**
```yaml
stages:
  package:
    - docker-build:
        images:
          - dockerfile: ./Dockerfile
            image-name: my-service
```

---

### docker-push
- **Stage**: publish
- **Pipeline Type**: Docker
- **Description**: Publishes Docker images to Artifactory and ECR on production branches with tags: `latest`, `{BUILD_NUMBER}`, `{GIT_COMMIT}`, `{BUILD_NUMBER}-{GIT_COMMIT}`, and any custom git tags.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `parallel-execution-limit` | integer | 5 | Max number of concurrent push operations |

**Example YAML:**
```yaml
stages:
  publish:
    - docker-push
```

---

### docker-compose-up
- **Stage**: integration-test
- **Pipeline Type**: Docker
- **Description**: Spins up containers using a Docker Compose file for integration testing.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `background` | boolean | true | Run in background (false runs in foreground like V1) |
| `output-logs` | boolean | true | Output container logs (when running in background) |
| `output-process-list` | boolean | true | Periodically run `docker-compose ps -a` |
| `process-list-frequency` | integer | 30 | Frequency in seconds to display process list |
| `docker-compose-files` | list | `["docker-compose.yml"]` | List of compose YAML files |
| `environment` | map | `{}` | Additional environment variables for compose files |
| `project-name` | string | `src` | Custom project name for docker-compose |

**Example YAML:**
```yaml
stages:
  integration-test:
    - docker-compose-up:
        docker-compose-files:
          - docker-compose.yml
```

---

### docker-compose-down
- **Stage**: integration-test
- **Pipeline Type**: Docker
- **Description**: Stops all running containers and removes container volumes.

| Parameter | Type | Default | Description |
|---|---|---|---|
| (none) | - | - | No parameters |

**Example YAML:**
```yaml
stages:
  integration-test:
    - docker-compose-down
```

---

### maven-publish
- **Stage**: publish
- **Pipeline Type**: Maven
- **Description**: Publishes jars to Nexus. Supports two variants: (1) `mvn deploy` for all jars, or (2) multi-module Maven release plugin for auto-versioned releases.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `auto-versioning-publish` | boolean | false | Set to true to use multi-module Maven release plugin |
| `maven-publish-jar-image` | string | `docker-images/sfdc_rhel9_java_rpmbuild/java8` | Docker image for running maven commands |
| `maven-publish-jar-args` | string | none | Additional arguments for `mvn deploy` or release plugin |
| `publish-core-packager` | boolean | false | Set to true when publishing core-packager Maven artifacts |

**Example YAML:**
```yaml
stages:
  publish:
    - maven-publish
```

---

### maven-verify
- **Stage**: integration-test
- **Pipeline Type**: Maven
- **Description**: Runs `mvn --batch-mode verify` for integration validation.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `maven-publish-jar-image` | string | `docker-images/sfdc_rhel9_java_rpmbuild/java8` | Docker image for running maven verify |
| `maven-publish-jar-args` | string | none | Additional arguments for `mvn verify` |
| `verify-production-branches` | boolean | true | If false, step is skipped on production branches |

**Example YAML:**
```yaml
stages:
  integration-test:
    - maven-verify
```

---

### publish-jar
- **Stage**: publish
- **Pipeline Type**: Maven, Gradle, SBT, Android
- **Description**: Publishes specific JAR/AAR artifacts to Nexus by groupId and artifactId. Validates GAV mapping before publishing.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `artifacts` | list | (required) | List of artifacts with `groupId` and `artifactId` |
| `artifacts[].groupId` | string | (required) | Maven groupId of the artifact |
| `artifacts[].artifactId` | string | (required) | Maven artifactId of the artifact |
| `exact-artifact-match` | boolean | false | Match exact artifact IDs (useful when IDs have similar names) |

**Example YAML:**
```yaml
stages:
  publish:
    - publish-jar:
        exact-artifact-match: true
        artifacts:
          - groupId: "com.salesforce.myteam"
            artifactId: "my-library"
```

---

### mvn-prepare-release
- **Stage**: build
- **Pipeline Type**: Maven
- **Description**: Removes SNAPSHOT from the pom version to create a release version. Creates a git commit with message "prepare for release" (not pushed).

| Parameter | Type | Default | Description |
|---|---|---|---|
| `continue-on-fail` | boolean | true | Whether to continue the build if this step fails |

**Example YAML:**
```yaml
stages:
  build:
    - mvn-prepare-release:
        continue-on-fail: false
```

---

### mvn-auto-version-update
- **Stage**: publish
- **Pipeline Type**: Maven
- **Description**: Creates a git tag with `$artifactid.$version`, auto-increments version, creates next SNAPSHOT, and pushes a commit.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `version-type-to-increment` | list | (required) | One of: `MAJOR`, `MINOR`, `PATCH` |
| `continue-on-fail` | boolean | true | Whether to continue the build if this step fails |

**Example YAML:**
```yaml
stages:
  publish:
    - mvn-auto-version-update:
        version-type-to-increment: ['PATCH']
```

---

### npm-setup
- **Stage**: build
- **Pipeline Type**: NPM
- **Description**: Configures Nexus read-only credentials and internal Nexus repositories for pulling/proxying NPM dependencies. Generates `.npmrc` file.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `yarn-modern` | boolean | false | Set to true to also configure Yarn 2.0+ for pulling packages from Nexus |
| `npmrc-path` | string | Project directory | Custom path for the generated .npmrc file |

**Example YAML:**
```yaml
stages:
  build:
    - npm-setup:
        yarn-modern: true
```

---

### npm-publish
- **Stage**: publish
- **Pipeline Type**: NPM
- **Description**: Sets up read-write Nexus credentials and runs `npm publish` to the npmjs-internal Nexus repository.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `update-npmignore` | boolean | false | Update .npmignore to prevent including build files in the package |
| `safe-version` | boolean | false | Use safe versioning (for core publish workflows) |

**Example YAML:**
```yaml
stages:
  publish:
    - npm-publish:
        update-npmignore: true
```

---

### lerna-publish
- **Stage**: publish
- **Pipeline Type**: NPM
- **Description**: Handles multi-package publishing for JavaScript monorepos using Lerna. Requires lerna as a dev dependency and a valid `lerna.json` config. Requires Yarn Modern (2.0+).

| Parameter | Type | Default | Description |
|---|---|---|---|
| (none) | - | - | No documented parameters |

**Example YAML:**
```yaml
stages:
  publish:
    - lerna-publish
```

---

### npm-semantic-release
- **Stage**: publish
- **Pipeline Type**: NPM
- **Description**: Automatically computes next release version from conventional commits, creates a git tag and GitHub Release with generated release notes. Requires semantic-release as a dev dependency.

| Parameter | Type | Default | Description |
|---|---|---|---|
| (none) | - | - | No documented parameters |

**Example YAML:**
```yaml
stages:
  publish:
    - npm-semantic-release
```

---

### python-publish
- **Stage**: publish
- **Pipeline Type**: Python
- **Description**: Publishes Python wheel (.whl) and tar (.tar.gz) packages to Nexus. Packages must be in the `dist` directory at workspace root and follow the `sfdc-` prefix naming convention.

| Parameter | Type | Default | Description |
|---|---|---|---|
| (none) | - | - | No documented parameters |

**Example YAML:**
```yaml
stages:
  publish:
    - python-publish
```

---

### helm-package
- **Stage**: package
- **Pipeline Type**: Helm
- **Description**: Packages Helm charts. Supports versioning via `$$BUILD_NUMBER`, `$$GIT_BRANCH`, `$$GIT_COMMIT`, `$$GIT_SHA`, manual version strings, or Chart.yaml.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `charts` | list | (required) | List of charts to package |
| `charts[].path` | string | (required) | Path to the chart directory |
| `charts[].version` | string | From chart.yaml | Version string (supports `$$BUILD_NUMBER`, `$$GIT_SHA`, etc.) |

**Example YAML:**
```yaml
stages:
  package:
    - helm-package:
        charts:
          - path: ./my-chart
            version: 1.0.0-$$BUILD_NUMBER
```

---

### helm-publish
- **Stage**: publish
- **Pipeline Type**: Helm
- **Description**: Publishes packaged Helm charts to S3.

| Parameter | Type | Default | Description |
|---|---|---|---|
| (none) | - | - | No documented parameters |

**Example YAML:**
```yaml
stages:
  publish:
    - helm-publish
```

---

### terraform-package
- **Stage**: package
- **Pipeline Type**: Terraform
- **Description**: Bundles Terraform packages. Supports versioning via `$$BUILD_NUMBER`, `$$GIT_BRANCH`, `$$GIT_COMMIT`, `$$GIT_SHA`, or manual version. Defaults to `$$GIT_SHA` if no version specified.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `packages` | list | (required) | List of packages to bundle |
| `packages[].path` | string | (required) | Path to the Terraform directory |
| `packages[].version` | string | `$$GIT_SHA` | Version string (supports env var substitution) |

**Example YAML:**
```yaml
stages:
  package:
    - terraform-package:
        packages:
          - path: ./terraform-module
            version: 1.0.0-$$BUILD_NUMBER
```

---

### terraform-publish
- **Stage**: publish
- **Pipeline Type**: Terraform
- **Description**: Publishes packaged Terraform modules to S3.

| Parameter | Type | Default | Description |
|---|---|---|---|
| (none) | - | - | No documented parameters |

**Example YAML:**
```yaml
stages:
  publish:
    - terraform-publish
```

---

### bazel-precheck
- **Stage**: precheck
- **Pipeline Type**: Bazel
- **Description**: Detects changed files via `git diff` and finds corresponding Bazel targets. For branch builds, diffs between HEAD and first parent. For PR builds, finds all files in the PR.

| Parameter | Type | Default | Description |
|---|---|---|---|
| (none) | - | - | No documented parameters |

**Example YAML:**
```yaml
stages:
  precheck:
    - bazel-precheck
```

---

### bazel-build-and-test
- **Stage**: build
- **Pipeline Type**: Bazel
- **Description**: Runs bazel build and test commands to generate OCI-compliant tarballs. Supports bazel cache by default.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `bazel-options` | string | none | Space-separated list of bazel command options |
| `bazel-targets` | string | none | Space-separated list of bazel targets |
| `skipTests` | boolean | false | Set to true to skip bazel test and only run bazel build |
| `disable-bazel-cache` | boolean | false | Disable bazel remote cache |

**Example YAML:**
```yaml
stages:
  build:
    - bazel-build-and-test:
        bazel-options: "--verbose_failures"
        bazel-targets: "//src/..."
```

---

### bazel-package
- **Stage**: package
- **Pipeline Type**: Bazel
- **Description**: Packages artifacts from bazel-build-and-test and publishes them as itest images to Artifactory and ECR.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `bazel-options` | string | none | Space-separated list of custom bazel options |
| `bazel-targets` | string | none | Space-separated list of custom bazel targets |

**Example YAML:**
```yaml
stages:
  package:
    - bazel-package
```

---

### bazel-container-publish
- **Stage**: publish
- **Pipeline Type**: Bazel
- **Description**: Publishes container images that were packaged in the bazel-package step to production registries.

| Parameter | Type | Default | Description |
|---|---|---|---|
| (none) | - | - | No documented parameters |

**Example YAML:**
```yaml
stages:
  publish:
    - bazel-container-publish
```

---

### buildpack-package
- **Stage**: package
- **Pipeline Type**: Buildpack
- **Description**: Packages Cloud Native Buildpacks using CNB tooling. Supports single and multiple buildpacks with configurable builder images and commands.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `buildpacks` | list | Single buildpack from repo root | List of buildpacks to package |
| `buildpacks[].name` | string | Git repo name | Name of the buildpack |
| `buildpacks[].path` | string | Repository root | Path to the buildpack source |
| `buildpacks[].builder-image` | string | `buildpacks/sfdc_builders/builder` | Builder image to use |
| `buildpacks[].command` | string | `build` | Build command (`build`, `buildpack package`, `builder create`) |
| `buildpacks[].config` | string | none | Config file path (mutually exclusive with `path`) |
| `parallel` | boolean | false | Enable parallel buildpack packaging |

**Example YAML:**
```yaml
stages:
  package:
    - buildpack-package:
        buildpacks:
          - name: my-app
            path: ./app
```

---

### buildpack-publish
- **Stage**: publish
- **Pipeline Type**: Buildpack
- **Description**: Publishes packaged buildpack images to Artifactory and ECR.

| Parameter | Type | Default | Description |
|---|---|---|---|
| (none) | - | - | No documented parameters |

**Example YAML:**
```yaml
stages:
  publish:
    - buildpack-publish
```

---

### gradle-setup
- **Stage**: build
- **Pipeline Type**: Gradle
- **Description**: Configures Nexus read-only credentials for internal repositories and runs the Gradle wrapper to bootstrap and download the correct version of Gradle.

| Parameter | Type | Default | Description |
|---|---|---|---|
| (none) | - | - | No documented parameters |

**Example YAML:**
```yaml
stages:
  build:
    - gradle-setup
```

---

### sbt-setup
- **Stage**: build
- **Pipeline Type**: SBT
- **Description**: Configures Nexus read-only credentials and internal SBT repositories (central, releases, thirdparty, sbt-plugin-releases).

| Parameter | Type | Default | Description |
|---|---|---|---|
| `additional-repositories` | list | none | Additional Nexus repositories to configure beyond defaults |

**Example YAML:**
```yaml
stages:
  build:
    - sbt-setup:
        additional-repositories:
          - artifactory-k8s-einstein
```

---

### rpm-package
- **Stage**: package
- **Pipeline Type**: RPM
- **Description**: Builds RPMs by running a package generation command inside specified Docker images. Implicitly triggers `rpm-stage` and `rpm-publish`.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `package-repository` | string | (required) | Repository name for the RPMs |
| `package-generation-command` | string | `make package` | Command to generate the RPM |
| `package-generation-mount-point` | string | `/tmp/project` | Mount point for the project in the container |
| `package-generation-images` | list | `[sfdc_rhel9_java_rpmbuild]` | Docker images for RPM building |

**Example YAML:**
```yaml
stages:
  package:
    - rpm-package:
        package-repository: my-repo-name
```

---

### rpm-stage
- **Stage**: build | package
- **Pipeline Type**: RPM
- **Description**: Publishes unsigned RPMs to staging repositories. Implicitly triggers `rpm-publish` on production branches.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `package-repository` | string | (required when not using rpm-package) | Repository name |
| `publish-to-falcon` | boolean | false | Stage RPMs to S3 in Falcon |

**Example YAML:**
```yaml
stages:
  build:
    - rpm-stage:
        package-repository: my-repo-name
```

---

### rpm-publish
- **Stage**: publish
- **Pipeline Type**: RPM
- **Description**: Signs and publishes RPMs to release repositories in Artifactory.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `package-repository` | string | (required when used standalone) | Repository name for publishing |

**Example YAML:**
```yaml
stages:
  publish:
    - rpm-publish:
        package-repository: my-repo-name
```

---

### rpm-publish-1p
- **Stage**: publish
- **Pipeline Type**: RPM
- **Description**: Promotes RPM artifacts from release repositories to 1P Salesforce data centers. Requires change case validation.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `auto-promote` | boolean | true | Toggle automatic promotion to 1P |
| `rpm-patterns` | list | All RPMs in build | Regex patterns to select specific RPMs for promotion |
| `source-rpm-repos` | list | `[rpm-rc-signed, rpm-rc-signed-v2]` | Source repositories in Artifactory |
| `destinations` | list | `[all]` | Data centers to promote to |
| `canary-only` | boolean | false | If true, promotes only to canary repositories |

**Example YAML:**
```yaml
stages:
  publish:
    - rpm-publish-1p:
        auto-promote: true
        canary-only: false
```

---

### fcp-evaluate-pr
- **Stage**: precheck
- **Pipeline Type**: FCP
- **Description**: Runs PR evaluation scripts as a managed step. Optional if you already have a custom step for PR evaluation.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `image` | string | `sfci/docker-images/sfdc_rhel9_docker_jq` | Docker image for running the script |
| `user` | string | none | User to run the container as (e.g., `root`) |
| `script-path` | string | `tnrp/evaluate_pr` | Path to the PR evaluation script |
| `script-params` | string | none | Parameters for the evaluation script |
| `environment` | list | none | Additional environment variables |

**Example YAML:**
```yaml
stages:
  precheck:
    - fcp-evaluate-pr:
        script-path: tnrp/evaluate_pr
```

---

### fcp-artifact-build
- **Stage**: build
- **Pipeline Type**: FCP
- **Description**: Runs unit test and packaging scripts for FCP workflows.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `build-image` | string | `sfci/docker-images/sfdc_rhel9_docker_jq` | Docker image for running scripts |
| `unit-test` | string | `tnrp/unittest` | Path to the unit test script |
| `package` | string | `tnrp/package` | Path to the packaging script |
| `package-script-params` | string | none | Additional parameters for the packaging script |
| `utest-script-params` | string | none | Additional parameters for the unit test script |
| `environment` | list | none | Additional environment variables |

**Example YAML:**
```yaml
stages:
  build:
    - fcp-artifact-build:
        unit-test: tnrp/unittest
        package: tnrp/package
```

---

### fcp-artifact-package
- **Stage**: package
- **Pipeline Type**: FCP
- **Description**: Converts results from the `fcp-artifact-build` packaging script into a versioned zip artifact. Copies files into `build_artifacts` directory which gets zipped. Versioned via semantic versioning or `${year}.${month}${sprint}.${commit_time}` format.

| Parameter | Type | Default | Description |
|---|---|---|---|
| (none) | - | - | No documented parameters |

**Example YAML:**
```yaml
stages:
  package:
    - fcp-artifact-package
```

---

### fcp-artifact-publish
- **Stage**: publish
- **Pipeline Type**: FCP
- **Description**: Creates latest file, signs the zip artifact, and publishes the FCP artifact, signed manifest, and latest file to Falcon S3. Validates change case from PR title or commit message.

| Parameter | Type | Default | Description |
|---|---|---|---|
| (none) | - | - | No documented parameters |

**Example YAML:**
```yaml
stages:
  publish:
    - fcp-artifact-publish
```

---

### fcp-publish-1p
- **Stage**: publish
- **Pipeline Type**: FCP
- **Description**: Signs zip artifact, publishes to `content_repo_rc` in Artifactory, and promotes to 1P data centers. Validates change case and promotion annotations.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `auto-promote` | boolean | false | Toggle automatic promotion to 1P kingdoms |
| `use-fcp-legacy-repo-path` | boolean | false | Use old Firefly path format (`GIT_REPO/VERSION/...` instead of `GIT_ORG/GIT_REPO/VERSION/...`) |

**Example YAML:**
```yaml
stages:
  publish:
    - fcp-publish-1p:
        auto-promote: true
```

---

### validate-change-case
- **Stage**: precheck
- **Pipeline Type**: FCP
- **Description**: Validates GUS change case in PR title, commit message, or PR description. Useful when custom steps need to run before change case validation.

| Parameter | Type | Default | Description |
|---|---|---|---|
| (none) | - | - | No documented parameters |

**Example YAML:**
```yaml
stages:
  precheck:
    - validate-change-case
```

---

### msi-publish
- **Stage**: publish
- **Pipeline Type**: MSI
- **Description**: Publishes .msi packages to the organization's MSI Artifactory repository. Recursively searches for .msi files.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `artifactory.directories` | list | Repository root | List of directory paths to search recursively for .msi files |
| `artifactory.directories[].path` | string | `.` | Directory path to search |
| `artifactory.version` | string | `{branch}-{build_number}` | Release version for published files |

**Example YAML:**
```yaml
stages:
  publish:
    - msi-publish:
        artifactory:
          directories:
            - path: './out'
          version: "1.0.0"
```

---

### lambda-package
- **Stage**: package
- **Pipeline Type**: Lambda
- **Description**: Packages Lambda function code into container images and publishes to dev ECR.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `parallel` | boolean | false | Enable parallel packaging |
| `lambdas` | list | (required) | List of Lambda functions to package |
| `lambdas[].path` | string | `.` | Path to the Lambda function source |
| `lambdas[].name` | string | (required) | Name of the Lambda function |

**Example YAML:**
```yaml
stages:
  package:
    - lambda-package:
        lambdas:
          - path: .
            name: my-lambda
```

---

### lambda-publish
- **Stage**: publish
- **Pipeline Type**: Lambda
- **Description**: Publishes Lambda container images to production ECR with tags: `latest`, `{BUILD_NUMBER}`, `{GIT_COMMIT}`, `{BUILD_NUMBER}-{GIT_COMMIT}`, and custom git tags. (Note: marked as "NOT yet available" in docs.)

| Parameter | Type | Default | Description |
|---|---|---|---|
| (none) | - | - | No documented parameters |

**Example YAML:**
```yaml
stages:
  publish:
    - lambda-publish
```

---

### android-build
- **Stage**: build
- **Pipeline Type**: Android
- **Description**: Configures Nexus read-only credentials, bootstraps Gradle, configures Android SDK, and runs default assemble/check tasks. For PRs runs `assembleDebug`; for branches runs `assemble`.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `assembleDebugTasks` | list | `[assembleDebug]` | Custom Gradle tasks for PR builds |
| `assembleTasks` | list | `[assemble]` | Custom Gradle tasks for branch builds |
| `checkTasks` | list | `[check]` | Custom Gradle check/test tasks |
| `includeNdk` | boolean | false | Include Android Native Development Kit |

**Example YAML:**
```yaml
stages:
  build:
    - android-build:
        assembleDebugTasks:
          - customAssembleDebugTask
        checkTasks:
          - customCheckTask
```

---

### sfdx-metadata-package
- **Stage**: package
- **Pipeline Type**: SFDX Metadata
- **Description**: Packages SFDX metadata into a zip file for S3 transfer and AMG (Artifact Metadata and Governance) registration. Uses `artifactMetadata.json` for configuration.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `enabled` | boolean | true | Enable/disable the step |
| `testing` | boolean | false | Testing mode -- no S3 transfers or AMG registration |

**Example YAML:**
```yaml
stages:
  package:
    - sfdx-metadata-package:
        enabled: true
```

---

### sfdx-managed-package
- **Stage**: package
- **Pipeline Type**: SFDX Package
- **Description**: Packages SFDX managed packages for transfer. Uses `sfdx-manifest.json` for configuration.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `testing` | boolean | false | Testing mode -- no S3 transfers or AMG registration |

**Example YAML:**
```yaml
stages:
  package:
    - sfdx-managed-package
```

---

### sfdx-managed-publish
- **Stage**: publish
- **Pipeline Type**: SFDX Package
- **Description**: Publishes SFDX managed packages to the S3 RC bucket and registers new versions with AMG.

| Parameter | Type | Default | Description |
|---|---|---|---|
| (none) | - | - | No documented parameters |

**Example YAML:**
```yaml
stages:
  publish:
    - sfdx-managed-publish
```

---

### git-push-tags
- **Stage**: publish
- **Pipeline Type**: All
- **Description**: Pushes any git tags created during a production branch build using the `svc-dva-strata` service account. This step is added by default in all pipelines but can be explicitly configured.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `enabled` | boolean | true | Enable/disable tag pushing |

**Example YAML:**
```yaml
stages:
  publish:
    - git-push-tags:
        enabled: true
```

---

### sonarqube
- **Stage**: integration-test
- **Pipeline Type**: All
- **Description**: Runs SonarQube code quality and coverage analysis. Built into pipelines by default.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `enabled` | boolean | true | Enable/disable SonarQube analysis |

**Example YAML:**
```yaml
stages:
  integration-test:
    - sonarqube:
        enabled: false
```

---

### core-packager
- **Stage**: build
- **Pipeline Type**: Core
- **Description**: Converts Node.js repositories into a Maven-like folder structure for core deployment. Supports communities core-packager and nucleus core-packager CLIs.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `core-package-config` | string | `core-package.config.json` | Path to core packager config JSON file |
| `npm-package` | string | `communities/core-packager` | Core-packager CLI to use |
| `npm-version` | string | `latest` | CLI version |
| `core-pkg-args` | string | default arguments | Additional arguments (destination argument not accepted) |

**Example YAML:**
```yaml
stages:
  build:
    - core-packager
```

---

### core-deploy
- **Stage**: publish
- **Pipeline Type**: Core
- **Description**: Deploys off-core repository artifacts to the Salesforce core app by calling the itest API. Posts the offcore autobuild link on the git PR.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `annotations` | string | `@markfixed@` | CL annotations |
| `ftest-labels` | string | `~ignore,auracontainer.itest` | Ftest labels for offcore autobuild check |
| `ab-enabled` | boolean | false | AB testing enablement |
| `project-modules` | list | none | Override default artifact name with module_name and properties_name |
| `skip-itest` | string | null | Itests to skip |
| `submit` | boolean | false | Submit to precheckin autobuild |

**Example YAML:**
```yaml
stages:
  publish:
    - core-deploy:
        submit: true
        ftest-labels: "~ignore,my.itest"
```

---

### downstream-dependencies
- **Stage**: integration-test
- **Pipeline Type**: All (currently supports NPM packages)
- **Description**: Validates that upstream changes do not break specified downstream repositories. Publishes a temporary artifact from the upstream PR, creates temporary branches in downstream repos, updates their package config to reference the new version, and reports results back to the upstream PR. **Pre-release feature.**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `downstream-repos` | list | *(required)* | List of downstream repos to validate. Each entry has `repo-url` (string) and `branches` (list). Use `"github-default"` to validate the downstream repo's default branch. |
| `packages-to-test` | map | *(required)* | Package manager and package names to test (e.g., `npm: ["@salesforce/lwr"]`). |
| `ignore-failures` | boolean | `false` | When `true`, downstream failures do not block the upstream PR. |

**Bypassing:** Add `@ignore-downstream-tests@` in a commit message to skip validation entirely.

**Example YAML:**
```yaml
stages:
  integration-test:
    - downstream-dependencies:
        ignore-failures: false
        downstream-repos:
          - repo-url: https://git.soma.salesforce.com/org/downstream-repo
            branches:
              - main
              - "github-default"
        packages-to-test:
          npm:
            - "@salesforce/lwr"
```

---

### terraform-package-provider
- **Stage**: package
- **Pipeline Type**: Terraform Provider (pilot)
- **Description**: Packages Terraform providers using goreleaser. Builds for `linux_amd64`, `linux_arm64`, `darwin_amd64`, `darwin_arm64`, and `windows_amd64`. Enforces provider naming and semantic versioning conventions.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `project_name` | string | Git repo name | Terraform provider name. Must match `^terraform-provider-...` naming rules. Dashes allowed inside; underscores invalid. |
| `version` | string | *(required)* | Semantic version for the release. Must pass semver validation. |
| `builds` | map | none | Goreleaser build config subset: `dir`, `main`, `mod_timestamp`, `flags`, `asmflags`, `gcflags`, `ldflags`, `env`, `tags`. |

PR builds auto-version as `<current_git_tag_or_0.0.0>-<PR#>-<short_commit>`. Production builds use the specified `version` and push a matching git tag.

**Example YAML:**
```yaml
stages:
  package:
    - terraform-package-provider:
        project_name: terraform-provider-firebom
        version: 0.0.2
        builds:
          flags:
            - -mod=vendor
          ldflags:
            - -s -w
```

---

### terraform-publish-provider
- **Stage**: publish
- **Pipeline Type**: Terraform Provider (pilot)
- **Description**: Publishes packaged Terraform providers to the Terraform Provider buckets used by the Terraform Private Registry. Must be present in `.strata.yml` to enable publishing.

| Parameter | Type | Default | Description |
|---|---|---|---|
| (none) | - | - | No documented parameters |

**Example YAML:**
```yaml
stages:
  publish:
    - terraform-publish-provider
```
