# Skills

Shared agent skills for Salesforce engineers, compatible with the [skills CLI](https://github.com/anthropics/skills) (skills.sh v1.4.5+).

## Installation

```bash
npx skills add -g git@git.soma.salesforce.com:cpredmore/skills.git
```

This will prompt you to select which skills to install and which agent(s) to install them for.

### Common Commands

| Command | Description |
|---------|-------------|
| `npx skills add -g <package>` | Install skills from a package |
| `npx skills list -g` | List installed skills |
| `npx skills remove -g [skills]` | Remove installed skills |
| `npx skills update -g` | Update all skills to latest versions |
| `npx skills add -g <package> -l` | List available skills without installing |

### Options

- `-g, --global` - Install globally (user-level) instead of project-level (default in examples above)
- `-a, --agent <agents>` - Specify target agents (`'*'` for all)
- `-s, --skill <skills>` - Specify skill names (`'*'` for all)
- `--all` - Shorthand for `--skill '*' --agent '*' -y`

## Available Skills

| Skill | Description | Install |
|-------|-------------|---------|
| `commit` | Create a git commit with a well-formatted message describing the changes | `npx skills add -g git@git.soma.salesforce.com:cpredmore/skills.git -s commit` |
| `cursor-delegate` | Delegate tasks to the Cursor agent CLI in headless mode | `npx skills add -g git@git.soma.salesforce.com:cpredmore/skills.git -s cursor-delegate` |
| `gus` | Query, create, and update GUS work items, sprints, and teams via the Salesforce CLI | `npx skills add -g git@git.soma.salesforce.com:cpredmore/skills.git -s gus` |
| `gws-google-docs` | Use the gws CLI to search, read, create, and import Google Docs across Drive and shared drives | `npx skills add -g git@git.soma.salesforce.com:cpredmore/skills.git -s gws-google-docs` |
| `pr` | Create a pull request using the GitHub CLI | `npx skills add -g git@git.soma.salesforce.com:cpredmore/skills.git -s pr` |
| `pr-review` | Review a GitHub pull request for bugs, risks, and quality issues | `npx skills add -g git@git.soma.salesforce.com:cpredmore/skills.git -s pr-review` |
| `strata-config` | Create or debug `.strata.yml` for SFCI Managed pipelines: stages, steps, globals | `npx skills add -g git@git.soma.salesforce.com:cpredmore/skills.git -s strata-config` |

### Install All Skills

```bash
npx skills add -g git@git.soma.salesforce.com:cpredmore/skills.git --all
```

## Guides

Step-by-step setup guides designed to be used with an AI agent. Point your agent at a guide file and ask it to walk you through the setup.

### Usage

Open your agent and reference the guide file directly:

```
Read @guides/<guide-file>.md and walk me through implementing it.
```

The agent will read the guide and lead you through each step interactively.

### Available Guides

| Guide | File | Description |
|-------|------|-------------|
| Google Workspace CLI Setup | `guides/google_setup.md` | Install and authenticate the `gws` CLI for Drive, Gmail, and Calendar access on a Salesforce macOS machine |

---

## Contributing

To add a new skill:

1. Create a new directory under `skills/` using kebab-case naming (e.g., `skills/my-new-skill/`)
2. Add a `SKILL.md` file with the required frontmatter (`name`, `description`) and instruction body
3. Optionally add a `resources/` subdirectory for helper scripts or reference files
4. Use `skills/_template/` as a starting point

See `skills/_template/SKILL.md` for the expected format.
