# Windows Pipeline Configuration

## Minimal Example

```yaml
global:
  email-reply-to: your-team@salesforce.com
stages:
  build:
    - step:
        name: windows-build
        runner: remote-windows
        commands:
          - ./my-power-shell-script.ps1
    - step:
        name: normal-linux-step
        image: docker.repo.local.sfdc.net/sfci/docker-images/sfdc_rhel9
        commands:
          - ./zip-my-results.sh
```

## Managed Steps

There are no pipeline-specific managed steps for Windows. Use `runner: remote-windows` on any user-defined step to execute on a Windows agent. Standard compliance steps (credential scanning, GUS, codeowners, sonarqube) still run automatically.

## Key Notes

- Set `runner: remote-windows` on a step to run it on a Windows agent instead of the default Linux container.
- Do **not** set `image:` on Windows steps; the `runner` key replaces it.
- The workspace is shared between Linux and Windows steps in the same pipeline.
- You can mix Windows and Linux steps in the same stage.
- For publishing Windows artifacts (e.g., MSI), see the MSI pipeline resource.
- Pre-installed software on Windows agents: JDK 17, Docker, Git, Node.js 20, Python 3.9, Go, Maven, .NET 4.7.2, .NET SDK 8.0.205, Visual Studio 2017/2022 Professional, Visual Studio 2017/2022 Build-Tools.
