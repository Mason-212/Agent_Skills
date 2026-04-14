# Buildpack Pipeline Configuration

## Minimal Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - main
stages:
  package:
    - buildpack-package
  publish:
    - buildpack-publish
```

## Managed Steps

| Step | Stage | Parameters |
|------|-------|------------|
| `buildpack-package` | package | `buildpacks` (list), `parallel` (bool, default false) |
| `buildpack-publish` | publish | (none) |

## Buildpack Properties

Each entry under `buildpacks:` accepts:
- `name` -- buildpack name (defaults to git repo name)
- `path` -- path to buildpack source (defaults to repo root)
- `builder-image` -- builder image to use (defaults to `buildpacks/sfdc_builders/builder`)
- `command` -- build command: `build`, `buildpack package`, or `builder create` (defaults to `build`)
- `config` -- path to config file like `package.toml` (optional, mutually exclusive with `path`)

## Single Buildpack with Custom Options

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - main
stages:
  package:
    - buildpack-package:
        buildpacks:
          - name: sample-buildpack-python
            path: python-app
            builder-image: docker.repo.local.sfdc.net/docker-sam/buildpacks/sfdc_centos7_cnb:builder
  publish:
    - buildpack-publish
```

## Multiple Buildpacks

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - main
stages:
  package:
    - buildpack-package:
        parallel: true
        buildpacks:
          - name: sample-buildpack-python
            path: python-app
            builder-image: docker.repo.local.sfdc.net/docker-sam/buildpacks/sfdc_centos7_cnb:builder
          - name: sample-buildpack-java
            path: java-app
            command: buildpack package
          - name: sample-buildpack-node
            path: node-app
  publish:
    - buildpack-publish
```

## Generate Buildpack Builders

```yaml
stages:
  package:
    - buildpack-package:
        buildpacks:
          - name: my-builder-image
            command: buildpack package
            config: package.toml
  publish:
    - buildpack-publish
```

## Multi-Architecture Buildpacks

Requires RHEL9 base images (CentOS 7/6 not supported with aarch64).

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - main
  target-architecture:
    - x86_64
    - aarch64
stages:
  package:
    - buildpack-package:
        buildpacks:
          - name: my-builder-image
            command: buildpack package
            config: package.toml
  publish:
    - buildpack-publish
```

## Key Notes

- Both `builder-image` and `command` are validated against an allowlist of authorized images and commands.
- Allowed commands: `build`, `buildpack package`, `builder create`.
- Per-buildpack `builder-image` and `command` override global settings.
- Multi-arch builds trigger two builds (main + worker). Both must pass for PR checks to succeed.
- If worker job does not exist, run "Scan Organization Now" in the worker folder on the Strata instance.
- Supported buildpacks: all from `git.soma.salesforce.com/buildpacks/sfdc_builders`, plus Heroku JVM, Node.js, Gradle, and Procfile buildpacks.
- For local development, use the `pack` CLI with `docker.repo.local.sfdc.net/sfci/buildpacks/sfdc_builders/builder:latest` as default builder.
