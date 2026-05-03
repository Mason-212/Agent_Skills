# Skills

Shared agent skills for Salesforce engineers, compatible with the [skills CLI](https://github.com/vercel-labs/skills) ([skills.sh](https://skills.sh)).

## Day-to-day workflow

Typical loop when **editing skills in this repository**:

1. **Change, commit, push** — Commit (and usually **push**) updates to `thomaschangsf/skills` **before** refreshing from the default remote, or the CLI installs an older tree from GitHub. For **unpushed** work, install from disk (see below).

2. **Refresh global installs** — From your shell (many people add `scripts/` to `PATH` via a profile such as `bash_salesforce.sh`):

   ```bash
   dev_refresh_skill_from_repo.sh
   ```

   From a clone of this repo you can always run:

   ```bash
   ./scripts/dev_refresh_skill_from_repo.sh
   ```

   **Unpushed commits:** set **`SKILLS_PACKAGE_PATH`** to this repo root so the install uses your working tree:

   ```bash
   SKILLS_PACKAGE_PATH="$(pwd)" ./scripts/dev_refresh_skill_from_repo.sh
   ```

3. **List global skills** — Always use **`-g`**:

   ```bash
   npx skills list -g
   ```

4. **Lower-level CLI** (same outcome as the script when using `SKILLS_SSH_URL`):

   ```bash
   SKILLS_GIT_REMOTE_PREFIX="${SKILLS_GIT_REMOTE_PREFIX:-git@github.com:thomaschangsf}"
   SKILLS_SSH_URL="${SKILLS_SSH_URL:-${SKILLS_GIT_REMOTE_PREFIX}/skills.git}"
   npx skills add -g -y "${SKILLS_SSH_URL}" \
     --agent cursor --agent claude-code --agent cline \
     --all --copy
   npx skills update -g
   ```

   Remove obsolete skill ids after renames (example — adjust names to whatever you are replacing):

   ```bash
   npx skills remove -g commit pr pr-review -y
   ```

5. **Branch helper** (optional):

   ```bash
   dev_start_branch_from_master.sh W-22029886-pi-connector
   ```

   Use **`GIT_BASE_BRANCH=main`** when the remote default is `main` instead of `master`.

### Cursor skill commands

In Cursor chat, invoke skills by name (with leading `/` if your client uses that pattern):

| Intent | Command |
|--------|---------|
| Rubrics-based critique (stress-test, blind spots, anti-slop, code, ML; infers paths) | `/critique-me` |
| Design / approach (scoped to branch vs default base) | `/code-design-critique` |
| Commit | `/git-commit` |
| Local code review (same bar as remote PR review) | `/git-review` |
| Open a GitHub pull request | `/pr-create` |
| Review an existing remote PR | `/pr-review-remote` |

## Installation (Cursor + Private Repo)

First-time setup below. For **ongoing edits, refresh, and CLI snippets**, use **[Day-to-day workflow](#day-to-day-workflow)**.

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

### Skills Git remote (shell variable)

Examples below use **`SKILLS_SSH_URL`**. Set it from **`SKILLS_GIT_REMOTE_PREFIX`** (SSH host and GitHub org or user—everything before `/skills.git`), or set **`SKILLS_SSH_URL`** directly if the repo is not named `skills`:

```bash
SKILLS_GIT_REMOTE_PREFIX="${SKILLS_GIT_REMOTE_PREFIX:-git@github.com:thomaschangsf}"
SKILLS_SSH_URL="${SKILLS_SSH_URL:-${SKILLS_GIT_REMOTE_PREFIX}/skills.git}"
```

Use the same lines in the shell where you run `npx skills` (or export them from your profile). The refresh script honors the same variables.

### Step 1: Install skills (Cursor, Claude Code, shared `~/.agents/skills`)

Each coding agent reads skills from its **own** global directory. Install this package explicitly for **Cursor**, **Claude Code**, and the **shared `~/.agents/skills`** tree (the skills CLI maps that path to the `cline` agent target—see the script header for why we use `cline` even if you do not use Cline).

Use **`--copy`** so each location gets real directories. Cursor often does not follow symlinks into another tree; copies avoid invisible or stale skills.

```bash
SKILLS_GIT_REMOTE_PREFIX="${SKILLS_GIT_REMOTE_PREFIX:-git@github.com:thomaschangsf}"
SKILLS_SSH_URL="${SKILLS_SSH_URL:-${SKILLS_GIT_REMOTE_PREFIX}/skills.git}"
npx skills add -g -y "${SKILLS_SSH_URL}" \
  --agent cursor --agent claude-code --agent cline \
  --all --copy
```

| Path | Agent flag | Used by |
|------|------------|---------|
| `~/.cursor/skills/` | `cursor` | Cursor |
| `~/.claude/skills/` | `claude-code` | Claude Code |
| `~/.agents/skills/` | `cline` | Shared personal skills directory in the open agent skills ecosystem (CLI global path for Cline/Warp) |

> **Important:** Use the SSH URL (`git@github.com:...`). HTTPS URLs can hang waiting for credentials and time out after 60 seconds.

### Step 2: Reload agents

- **Cursor:** **Cmd+Shift+P → Developer: Reload Window**
- **Claude Code:** Restart or reload so it picks up `~/.claude/skills/`.

### Verify

```bash
npx skills list -g
ls ~/.cursor/skills/ ~/.claude/skills/ ~/.agents/skills/
```

### Updating

See **[Day-to-day workflow](#day-to-day-workflow)** for `dev_refresh_skill_from_repo.sh`, **`SKILLS_PACKAGE_PATH`**, and lower-level **`npx skills`** commands.

### `dev_refresh_skill_from_repo`

The script [`scripts/dev_refresh_skill_from_repo.sh`](scripts/dev_refresh_skill_from_repo.sh) installs or refreshes the global package for **`cursor`**, **`claude-code`**, and **`cline`** (see paths in Step 1). It uses **`--copy`** so skills are materialized under each directory without symlink indirection.

**Optional env:**

- `SKILLS_GIT_REMOTE_PREFIX` — default `git@github.com:thomaschangsf` (SSH host and org/user; no `.git`).
- `SKILLS_SSH_URL` — full package URL; default `${SKILLS_GIT_REMOTE_PREFIX}/skills.git`.
- `SKILLS_PACKAGE_PATH` — absolute path to **this** repository root (the directory that contains `skills/`). When set, the script installs from that directory instead of cloning `SKILLS_SSH_URL`. Use this for **unpushed** renames or new skills; otherwise `npx skills add` only sees what is on **GitHub**.
- `SKILLS_AGENTS` — space-separated agent ids (default `cursor claude-code cline`).

**Listing global skills:** use **`npx skills list -g`**. Without **`-g`**, the CLI lists **project** skills for the current directory (often empty or different from your global install).

### Common Commands

| Command | Description |
|---------|-------------|
| `npx skills add -g <package>` | Install skills from a package |
| `npx skills list -g` | List installed skills |
| `npx skills remove -g [skills]` | Remove installed skills |
| `npx skills update -g` | Update all skills to latest versions |
| `npx skills add -g <package> -l` | List available skills without installing |
| `./scripts/dev_refresh_skill_from_repo.sh` | Refresh global installs under `~/.cursor/skills/`, `~/.claude/skills/`, and `~/.agents/skills/` |
| `./scripts/dev_start_branch_from_master.sh` | Create a new branch from up-to-date `origin/<GIT_BASE_BRANCH>` (default **`master`**; set **`GIT_BASE_BRANCH=main`** when the remote uses **`main`**); prompts for the branch name if omitted; untracked files do not block the switch |

### Options

- `-g, --global` - Install globally (user-level) instead of project-level (default in examples above)
- `-a, --agent <agents>` - Specify target agents (`'*'` for all)
- `-s, --skill <skills>` - Specify skill names (`'*'` for all)
- `--all` - Shorthand for `--skill '*' --agent '*' -y`

## Available Skills

Skills live under `skills/<skill-name>/SKILL.md`. Install a subset with **`-s <skill-name>`**, or use **`--all`** in [Day-to-day workflow](#day-to-day-workflow).

| Skill | Description | Install |
|-------|-------------|---------|
| `code-design-critique` | Design critique vs default base (`origin/master`, or **`GIT_BASE_BRANCH`**); commits + staged/unstaged | `npx skills add -g "${SKILLS_SSH_URL}" -s code-design-critique` |
| `critique-me` | Critique plans, specs, or pasted output with selectable rubrics; infers paths from message | `npx skills add -g "${SKILLS_SSH_URL}" -s critique-me` |
| `cursor-delegate` | Delegate tasks to the Cursor agent CLI in headless mode | `npx skills add -g "${SKILLS_SSH_URL}" -s cursor-delegate` |
| `edc-splunk` | Splunk SPL with this repo’s knowledge base (indexes, fields, examples) | `npx skills add -g "${SKILLS_SSH_URL}" -s edc-splunk` |
| `git-commit` | Create a git commit with a well-formatted message describing the changes | `npx skills add -g "${SKILLS_SSH_URL}" -s git-commit` |
| `git-review` | Review local branch + working tree vs default base (same bar as **`pr-review-remote`**) | `npx skills add -g "${SKILLS_SSH_URL}" -s git-review` |
| `gus` | Query, create, and update GUS work items, sprints, and teams via the Salesforce CLI | `npx skills add -g "${SKILLS_SSH_URL}" -s gus` |
| `gws-google-docs` | Use the `gws` CLI for Google Docs across Drive and shared drives | `npx skills add -g "${SKILLS_SSH_URL}" -s gws-google-docs` |
| `pr-create` | Create a pull request using the GitHub CLI | `npx skills add -g "${SKILLS_SSH_URL}" -s pr-create` |
| `pr-review-remote` | Review a remote GitHub pull request for bugs, risks, and quality issues | `npx skills add -g "${SKILLS_SSH_URL}" -s pr-review-remote` |
| `strata-config` | Create or debug `.strata.yml` for SFCI Managed pipelines | `npx skills add -g "${SKILLS_SSH_URL}" -s strata-config` |

Set `SKILLS_SSH_URL` (or `SKILLS_GIT_REMOTE_PREFIX`) as in [Skills Git remote](#skills-git-remote-shell-variable) before running these install commands.

### Install all skills

Same as the **`npx skills add … --all --copy`** block in [Day-to-day workflow](#day-to-day-workflow), followed by **`npx skills update -g`**. Prefer **`dev_refresh_skill_from_repo.sh`**, which runs both.

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

1. Create a new directory under `skills/` using kebab-case naming (e.g., `skills/my-new-skill/`).
2. Add a `SKILL.md` file with the required frontmatter (`name`, `description`) and instruction body (see [AGENTS.md](AGENTS.md) in this repo).
3. Optionally add a `resources/` subdirectory for helper scripts or reference files.
4. Copy structure and tone from an existing skill (e.g. `skills/git-commit/SKILL.md`) as a template.

Keep `description` in frontmatter under **100 characters**.
