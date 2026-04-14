# NPM Pipeline Configuration

## Minimal Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - main
stages:
  build:
    - npm-setup
    - step:
        name: npm-build
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9_nodejs18
        commands:
          - cp -rf .npmrc /root/.npmrc
          - npm install
          - npm run test
  publish:
    - npm-publish:
        update-npmignore: true
```

## Managed Steps

| Step | Stage | Parameters |
|------|-------|------------|
| `npm-setup` | build | `yarn-modern` (bool), `npmrc-path` (string) |
| `npm-publish` | publish | `update-npmignore` (bool) |
| `lerna-publish` | publish | (none) |
| `npm-semantic-release` | publish | (none) |

## Monorepo Example (Yarn + Lerna)

Requires Yarn 2.0+ (`yarn-modern: true`), lerna as a dev dependency, and a valid `lerna.json`.

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - main
stages:
  build:
    - npm-setup:
        yarn-modern: true
    - step:
        name: yarn-build
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9_nodejs18/sfdc_rhel9_nodejs18_build
        commands:
          - yarn install
          - yarn build
          - yarn test
  publish:
    - lerna-publish
```

## Semantic Release Example

Requires `semantic-release` as a dev dependency and a valid configuration file. Automatically computes the next version from conventional commits, creates a git tag and GitHub Release.

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - main
stages:
  build:
    - npm-setup:
        yarn-modern: true
    - step:
        name: yarn-build
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9_nodejs18/sfdc_rhel9_nodejs18_build
        commands:
          - yarn install
          - yarn build
          - yarn test
  publish:
    - npm-semantic-release
```

## Key Notes

- `npm-setup` configures Nexus read-only credentials and internal Nexus repositories for pulling dependencies.
- Use `npmrc-path` parameter in `npm-setup` if the `.npmrc` should not be placed in the project directory.
- `npm-publish` sets up read-write credentials and runs `npm publish` to the `npmjs-internal` Nexus repo.
- `update-npmignore: true` updates `.npmignore` to exclude build-related files from the published package.
- `lerna-publish` requires `yarn-modern: true` in `npm-setup` (Yarn 2.0+).
- Use Node 18+ base images (`sfdc_rhel9_nodejs18`); Node 16 is EOL.
- The pipeline supports bundling artifacts into Docker images and/or publishing to Nexus.
