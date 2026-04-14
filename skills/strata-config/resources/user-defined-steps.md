# User-Defined Steps

User-defined steps use CIX definition syntax to run custom work within SFCI Managed pipeline stages. Most examples are Linux container steps, but Windows pipelines can also run `step:` blocks on `remote-windows`.

## Single Step (`step:`)

A single step runs one unit of work with optional commands. In Linux pipelines this is usually a container step; in Windows pipelines it can target a Windows runner.

### Attributes for Linux Container Steps

| Attribute | Required | Description |
|-----------|----------|-------------|
| `name` | Yes | Step identifier. Cannot use reserved stage names (`precheck`, `build`, `package`, `integration-test`, `publish`, `post-publish`). |
| `image` | Yes | Docker image to run. Must be from Artifactory (no Docker Hub access). |
| `commands` | No | List of shell commands. If omitted, the image's entrypoint runs. Commands execute in a folder mounted with your repo code. |
| `environment` | No | List of environment variables injected into the container. Each entry has `name` and optionally `value`. |
| `when` | No | Conditional execution. List of operator conditions (see below). |
| `user` | No | Container user as `'UID:GID'` string, e.g. `'0:0'` for root. |
| `workspace-mount-point` | No | Custom path where the repo workspace is mounted inside the container. |
| `continue-on-fail` | No | When `true`, pipeline continues even if this step fails. |
| `background` | No | When `true`, step runs in background. |
| `runner` | No | Execute the step on a remote Linux agent with `remote-linux`. Workspace is snapshotted to/from the runner. |

### Basic Example

```yaml
stages:
  build:
    - step:
        name: mvn-test
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_centos7_java_build
        environment:
          - name: VAR
            value: VAL
        commands:
          - mvn verify
```

### Windows Runner Steps

Windows pipelines can run `step:` blocks on a Windows agent without specifying an `image`:

```yaml
stages:
  build:
    - step:
        name: windows-build
        runner: remote-windows
        commands:
          - ./my-power-shell-script.ps1
    - step:
        name: package-results
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
        commands:
          - ./zip-my-results.sh
```

Use the Windows pipeline reference when the request mixes Windows and Linux steps so the YAML stays valid for both environments.

## Grouped Steps (`steps:`)

A `steps:` block groups multiple `step:` definitions. Steps inside can run in parallel or sequentially.

### Attributes

| Attribute | Required | Description |
|-----------|----------|-------------|
| `name` | Yes | Group identifier. |
| `parallel` | No | When `true`, enclosed steps run in parallel. Default: `false`. |
| `pipeline` | Yes | List of `step:` or nested `steps:` blocks. |

### Parallel Execution Example

```yaml
stages:
  build:
    - steps:
        name: parallel-steps
        parallel: true
        pipeline:
          - step:
              name: step-1
              image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_centos7_java_build
              commands:
                - echo 'Hello from step one!'
          - step:
              name: step-2
              image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_centos7_java_build
              commands:
                - echo 'Hello from step two!'
```

### Nested Sequential Steps in Parallel

You can nest `steps:` blocks to run groups of sequential steps in parallel with each other:

```yaml
stages:
  build:
    - steps:
        name: Multi-linux-agents
        parallel: true
        pipeline:
          - steps:
              name: group-a
              pipeline:
                - step:
                    name: step-1
                    image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
                    commands:
                      - echo "sequential step 1 in group A"
                - step:
                    name: step-2
                    image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
                    commands:
                      - echo "sequential step 2 in group A"
          - steps:
              name: group-b
              pipeline:
                - step:
                    name: step-3
                    image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
                    commands:
                      - echo "runs in parallel with group A"
```

## Conditional Execution (`when`)

The `when` attribute accepts a list of conditions. Each condition has an `operator`, `value`, and `other`.

| Operator | Description |
|----------|-------------|
| `EQ` | True when `value` equals `other`. |
| `NEQ` | True when `value` does not equal `other`. |
| `IS_SET` | True when `value` is set (non-empty). |
| `MATCHES` | True when `value` matches `other` as a regex. |
| `NOT_MATCHES` | True when `value` does not match `other` as a regex. |

### Conditional Example

Run a step only on production branches:

```yaml
- step:
    when:
      - operator: EQ
        value: $$IS_PRODUCTION_BRANCH
        other: 'true'
    name: Slack_Notification
    image: docker.repo.local.sfdc.net/sfci/kuleana/stampy-p3-image:43
    user: '0:0'
    environment:
      - name: GIT_COMMIT
    commands:
      - source $post_publish_secrets_file_path
      - source tnrp/notification.sh
```

## Workspace Mount Point

Override the default working directory inside the container:

```yaml
- step:
    name: workspace-test
    image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
    workspace-mount-point: /workspace
    commands:
      - pwd  # outputs /workspace
```

## Caveats and Docker Socket Restrictions

SFCI Managed V2 exposes `/var/run/docker.sock` with restricted access enforced by the **OPA-docker-authz** plugin. Requests to the Docker daemon are evaluated against these policies:

- Docker **privileged mode** is not supported.
- Additional **volumes and bind mounts** are not supported. Only `/var/run/docker-secondary.sock` and the workspace (`pwd`) can be mounted.
- `--volumes-from` flag is not allowed.
- Host **network mode** (`--net`), **IPC mode** (`--ipc`), and **PID mode** (`--pid`) cannot be set to `host`.
- Capabilities `NET_ADMIN`, `SYS_ADMIN`, `DAC_OVERRIDE`, and `DAC_READ_SEARCH` are not allowed.

Violating any of these policies causes the pipeline to fail with: `Authorization denied by plugin opa-docker-authz:latest`.

### Volume Path Errors

Ensure volume paths in Docker commands are within the SFCI workspace. Paths outside the workspace trigger the OPA authorization error.

### TestContainers Workaround

If the error occurs while running the TestContainers ryuk container, disable it by adding this environment variable to your step:

```yaml
environment:
  - name: TESTCONTAINERS_RYUK_DISABLED
    value: 'true'
```

### Requesting Privileged Docker Socket Access (Last Resort)

If you have a use case that requires privileged access:

1. Create a Work Item for SFCI under product tag `SFCI RTB : L1 - Customer support, operations`.
2. Raise a PR to add the repo to the exceptions list at `https://git.soma.salesforce.com/sfci/feature-rollout/blob/master/docker-socket/feature.yaml`.
3. Comment `/merge-request <description>` to notify the SFCI team on `#sfci-strata-dev`.
