# MSI Pipeline Configuration

## Minimal Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  publish:
    - msi-publish
```

Without parameters, `msi-publish` searches recursively from the repo root for all `.msi` files.

## With Directory Paths

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  publish:
    - msi-publish:
        artifactory:
          directories:
            - path: './out'
            - path: './files'
```

## With Custom Version

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  publish:
    - msi-publish:
        artifactory:
          version: "1.2.3"
```

## Managed Steps

| Step | Stage | Parameters | Description |
|------|-------|------------|-------------|
| `msi-publish` | publish | `artifactory.directories[].path` (list of directory paths to search), `artifactory.version` (custom version string) | Searches for `.msi` files and publishes them to the org's MSI artifactory repository |

## Key Notes

- Default version format is `{branch name}-{build number}` unless overridden with `artifactory.version`.
- When `directories` is specified, only those paths are searched recursively for `.msi` files.
- When `msi-publish` is used alone without parameters, the entire repo is searched recursively.
- Typically paired with a Windows build step (`runner: remote-windows`) to produce the `.msi` files first.
- This pipeline is in **pilot phase** -- the design or implementation may change.
