# Skills

Shared agent skills for Salesforce engineers, compatible with the [skills CLI](https://github.com/anthropics/skills) (skills.sh v1.4.5+).

## Installation (Cursor + Private Repo)

### Prerequisites

This repo is private, so the skills CLI must clone it over SSH. Before you begin:

1. **SSH key exists** — if not, generate one:

```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
```

2. **SSH key added to GitHub** — copy your public key and add it at [github.com/settings/keys](https://github.com/settings/keys):

```bash
cat ~/.ssh/id_ed25519.pub | pbcopy
```

3. **SSH key loaded in agent** — keys are not loaded automatically after a reboot. Load it:

```bash
ssh-add ~/.ssh/id_ed25519
```

To auto-load on every login, add this to `~/.ssh/config`:

```
Host github.com
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_ed25519
```

4. **Verify access** — you should see your key fingerprint and a successful connection:

```bash
ssh-add -l                # should list your key
ssh -T git@github.com     # should say "Hi <user>! You've successfully authenticated"
```

### Step 1: Install Skills

```bash
npx skills add -g -y git@github.com:thomaschangsf/skills.git
```

This installs all skills globally to `~/.agents/skills/` for every detected agent (Claude Code, Cursor, Gemini CLI, etc.).

> **Important:** You must use the SSH URL (`git@github.com:...`). HTTPS URLs will silently hang waiting for credentials and time out after 60 seconds.

### Step 2: Link Skills into Cursor

The skills CLI installs to `~/.agents/skills/` (the universal agent directory), but Cursor discovers skills from `~/.cursor/skills/` and does not follow symlinks. Copy the skills into Cursor's directory:

```bash
mkdir -p ~/.cursor/skills
for skill in ~/.agents/skills/*/; do
  name=$(basename "$skill")
  [ ! -e "$HOME/.cursor/skills/$name" ] && cp -R "$skill" "$HOME/.cursor/skills/$name"
done
```

### Step 3: Reload Cursor

Reload the window so Cursor picks up the new skills:

**Cmd+Shift+P → Developer: Reload Window**

### Verify

```bash
npx skills list -g          # lists all installed skills
ls ~/.cursor/skills/        # should show all skill directories
```

### Updating

When skills are updated upstream, pull the latest versions, then re-copy into Cursor:

```bash
npx skills update -g

# Re-copy updated skills into Cursor (overwrites old copies)
for skill in ~/.agents/skills/*/; do
  name=$(basename "$skill")
  rm -rf "$HOME/.cursor/skills/$name"
  cp -R "$skill" "$HOME/.cursor/skills/$name"
done
```

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
| `commit` | Create a git commit with a well-formatted message describing the changes | `npx skills add -g git@github.com:thomaschangsf/skills.git -s commit` |
| `cursor-delegate` | Delegate tasks to the Cursor agent CLI in headless mode | `npx skills add -g git@github.com:thomaschangsf/skills.git -s cursor-delegate` |
| `gus` | Query, create, and update GUS work items, sprints, and teams via the Salesforce CLI | `npx skills add -g git@github.com:thomaschangsf/skills.git -s gus` |
| `gws-google-docs` | Use the gws CLI to search, read, create, and import Google Docs across Drive and shared drives | `npx skills add -g git@github.com:thomaschangsf/skills.git -s gws-google-docs` |
| `pr` | Create a pull request using the GitHub CLI | `npx skills add -g git@github.com:thomaschangsf/skills.git -s pr` |
| `pr-review` | Review a GitHub pull request for bugs, risks, and quality issues | `npx skills add -g git@github.com:thomaschangsf/skills.git -s pr-review` |
| `strata-config` | Create or debug `.strata.yml` for SFCI Managed pipelines: stages, steps, globals | `npx skills add -g git@github.com:thomaschangsf/skills.git -s strata-config` |

### Install All Skills

```bash
npx skills add -g git@github.com:thomaschangsf/skills.git --all
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
