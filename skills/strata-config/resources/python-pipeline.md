# Python Pipeline Configuration

## Minimal Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  build:
    - step:
        name: run-unit-tests
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9_python3
        commands:
          - pip install tox && tox
  package:
    - step:
        name: package-python
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9_python3
        commands:
          - pip install build virtualenv
          - python3 -m build
  publish:
    - python-publish
```

## Managed Steps

| Step | Stage | Parameters |
|------|-------|------------|
| `python-publish` | publish | (none) |

## Manylinux Wheel (x86_64)

For packages with C/C++ extensions that need cross-distribution compatibility.

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - main
stages:
  build:
    - step:
        name: python-build-packages
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9_python3
        commands:
          - yum install -y gcc
          - pip3 install wheel auditwheel patchelf
          - pip3 wheel `pwd` -w ./dist
          - auditwheel repair ./dist/sfdc_managed_manylinux_python*whl -w ./dist
  publish:
    - python-publish
```

## Manylinux Wheel (aarch64)

```yaml
global:
  email-reply-to: your-team@salesforce.com
  production-branches:
    - master
stages:
  build:
    - step:
        name: python-build-packages
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9_python3
        commands:
          - yum install -y python-devel gcc
          - pip3 install -i https://nexus-proxy.repo.local.sfdc.net/nexus/repository/pypi-all/simple wheel auditwheel patchelf
          - pip3 wheel `pwd` -w ./dist
          - auditwheel repair ./dist/<your-package>*whl -w ./dist
  publish:
    - python-publish
```

## Key Notes

- `python-publish` **must** be called from the `publish` stage (not any other stage).
- Packages must follow the naming convention: `sfdc-<your_package_name>.tar.gz` or `sfdc_<your_package_name>.whl`.
- Only wheel (`.whl`) and tar (`.tar.gz`) files are published.
- Built packages must be in a `dist/` directory at the root of the workspace at publish time.
- The package name checked is the one specified in `setup.py` or `setup.cfg`, not the generated filename.
- Register your git org/repo and package name in the `python-packages/feature.yaml` file in the `sfci/feature-rollout` repo.
- For GitHub.com/EMU repos, also add `gitScmUrl` in the feature.yaml entry.
- Published packages are accessible at: `https://nexus-proxy.repo.local.sfdc.net/nexus/content/groups/pypi-all/simple/{packageName}`
