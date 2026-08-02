# Skills & Tools Repository

Shared agent skills and MCP plugins for Claude Code and Cursor.

---

## Quick Start

```bash
# Clone and sync
git clone git@github.com:thomaschangsf/skills.git
cd skills
./scripts/dev_refresh_skills_and_tools.sh

# Restart Claude Code or Cursor
# Use: /git-commit, /goal-sandbox "add type hints", etc.
```

**For development workflow, see [DEV.md](DEV.md)**

---

## Core Concepts

### The Three Layers

```
┌─────────────────────────────────┐
│   Harness (Claude Code/Cursor) │  ← Application (provides /goal, /help)
└─────────────────────────────────┘
         ↓ loads      ↓ loads
    ┌─────────┐  ┌─────────┐
    │ Skills  │  │  Tools  │
    └─────────┘  └─────────┘
```

| What | Type | Example | How to Use |
|------|------|---------|------------|
| **Skills** | Instructions (markdown) | git-commit, pr-review | `/git-commit` or auto-activates |
| **Tools** | Capabilities (MCP plugins) | PDF converter, Splunk | Called automatically by Claude |
| **Harness** | Application commands | /goal, /reload-plugins | Type command directly |

### Skills (Instructions)
Markdown files that provide workflow instructions to Claude.

**Location**: `skills/<name>/SKILL.md`

**Example**: `/git-commit` → Analyzes changes → Creates well-formatted commit

### Tools (MCP Plugins)
External processes that add capabilities via Model Context Protocol.

**Location**: `plugins/{all,claude,cursor}/<name>/`

**Example**: Claude calls `convert_pdf_to_markdown` when you say "convert doc.pdf"

### Harness (Built-in Commands)
Application-provided commands like `/goal` for autonomous execution.

**Example**: `/goal "add type hints to billing.py"` → Claude works autonomously

---

## Repository Structure

```
skills/                    # Skill definitions (instructions)
  └── <name>/
      └── SKILL.md

plugins/                   # MCP plugins (tools)
  ├── all/                 # Works in all agents
  ├── claude/              # Claude Code only (uses /goal)
  └── cursor/              # Cursor only

scripts/
  ├── dev_refresh_skills_and_tools.sh       # Sync skills + plugins to local agents
  └── dev_refresh_claude_cursor_md.sh       # Refresh Claude/Cursor behavioral guidelines

docs/behavioral/
  └── CLAUDE_USER.md                        # Golden source for AI behavioral guidelines
```

**Agent scoping**: Place plugins in `all/`, `claude/`, or `cursor/` based on compatibility.

---

## Available Skills

### Git & GitHub
- **git-commit** - Well-formatted commits with Co-Authored-By
- **git-review** - Review local changes (same bar as PR review)
- **pr-create** - Open GitHub pull request
- **pr-review-remote** - Review remote PR for bugs, security, tests
- **pr-update-squashpush** - Squash and force-push

### Development
- **goal-sandbox** - Autonomous tasks with verification and safety guardrails
- **critique-me** - Rubrics-based code critique
- **spec-driven-development-slc** - Spec-first development workflow

### Domain-Specific
- **edc-splunk** - Write and refine Splunk SPL queries
- **gus** - Query Salesforce GUS work items

---

## Usage Examples

### Commit Changes
```
# In conversation:
Please commit these changes

# Or explicitly:
/git-commit
```

**What happens**: Runs git status/diff → Analyzes → Creates commit

---

### Review Before PR
```
/git-review
```

**What happens**: Reviews all local changes → Reports bugs, security issues, missing tests

---

### Autonomous Task with Safety
```
/goal-sandbox "Add type hints to billing.py"
```

**What happens**:
1. Wizard asks: "What test verifies success?"
2. You: "Run pytest tests/test_billing.py"
3. Claude works autonomously
4. Runs pytest after each change
5. Stops when tests pass ✅

**vs plain `/goal`**: goal-sandbox adds deterministic verification, safety guardrails, turn limits

---

### Convert PDF to Markdown
```
Convert contract.pdf to markdown
```

**What happens**: Claude calls `convert_pdf_to_markdown` tool automatically

---

## Common Commands

```bash
# Sync everything (after editing)
./scripts/dev_refresh_skills_and_tools.sh

# List installed skills
npx skills list -g

# Reload skills (Claude Code)
/reload-plugins

# Reload (Cursor)
Cmd+Shift+P → Developer: Reload Window
```

---

## Adding Content

### New Skill
```bash
mkdir -p skills/my-skill
cat > skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: Does something useful
---

# My Skill
Instructions...
EOF

./scripts/dev_refresh_skills_and_tools.sh
```

### New MCP Plugin
```bash
mkdir -p plugins/all/my-tool
cd plugins/all/my-tool
npm init -y
npm install @modelcontextprotocol/sdk
# Create index.js with MCP server
cd ../../..
./scripts/dev_refresh_skills_and_tools.sh
```

**See [DEV.md](DEV.md) for detailed development workflow**

---

## Prerequisites

### SSH Setup (Private Repo)
```bash
# Generate key
ssh-keygen -t ed25519 -C "your-email@example.com"

# Add to GitHub
cat ~/.ssh/id_ed25519.pub | pbcopy
# Paste at github.com/settings/keys

# Load key
ssh-add ~/.ssh/id_ed25519

# Auto-load (add to ~/.ssh/config)
Host github.com
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_ed25519
```

---

## Troubleshooting

**Skill not appearing:**
```bash
ls skills/my-skill/SKILL.md  # Verify exists
./scripts/dev_refresh_skills_and_tools.sh
# Restart agent
```

**MCP plugin not loading:**
```bash
cat ~/.claude/settings.json | grep my-tool  # Check config
# Restart Claude Code, check startup logs
```

**Wrong agent scope:**
```bash
mv plugins/all/my-tool plugins/claude/
./scripts/dev_refresh_skills_and_tools.sh
# Restart agent
```

---

## Environment Variables

```bash
# Local development (default)
TOOLS_MODE=local ./scripts/dev_refresh_skills_and_tools.sh

# GitHub URLs for sharing
TOOLS_MODE=github ./scripts/dev_refresh_skills_and_tools.sh

# Target specific agents
SKILLS_AGENTS="cursor claude-code" ./scripts/dev_refresh_skills_and_tools.sh
```

---

## `lib/aor` — Multi-Agent Python Library

`lib/aor` is a local Python library for building DAG-based multi-agent workflows using LangGraph. It powers the `aor-multiagent-*` skills.

### Setup

```bash
cd lib/aor
uv sync
```

### Quality checks (lint + typecheck + tests)

```bash
# From repo root:
uv run --project lib/aor check_aor

# Or from lib/aor directly:
cd lib/aor && uv run check_aor
```

This runs:
1. `ruff check` — linting across `agent/`, `orchestrator/`, `packs/`
2. `pyright` — static type checking
3. `pytest tests/` — 22 unit tests (no real LLM calls)

### Multi-Agent Packs

| Pack | Skill | What it does |
|------|-------|--------------|
| `multiagent_adversarial` | `aor-multiagent-adversarial` | Generator + critic loop with verification gate |
| `multiagent_roles` | `aor-multiagent-roles` | N agents with defined roles in sequence |
| `multiagent_solution_space` | `aor-multiagent-solution-space` | Fan-out N explorers, synthesize findings |

See `lib/aor/packs/README.md` for design rationale.

### Tracing with Arize Phoenix

Tracing is fully local — no account or API key needed. Traces appear in a browser UI at `http://localhost:6006`.

```bash
# 1. Configure
cp lib/aor/.env.example lib/aor/.env
# Edit lib/aor/.env and set: PHOENIX_TRACING=true

# 2. Start Phoenix (separate terminal)
cd lib/aor
uv run python -m phoenix.server.main serve
# Open http://localhost:6006

# 3. Run a pack — traces appear automatically
```

Each pack run produces one trace in Phoenix showing:
- Per-node spans (`aor.node.*`) with attempt number, prompt/response lengths
- LLM call spans (`aor.llm_call`) with provider, model, prompt and response lengths
- Policy decision spans (`aor.policy.*`) with action taken, next node, retry count

Set `PHOENIX_TRACING=false` (default) to disable with zero overhead.

---

## Documentation

- **[DEV.md](DEV.md)** - Development workflow, adding skills/plugins, troubleshooting
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed design for contributors
- **[AGENTS.md](AGENTS.md)** - Project-specific rules
- **[CLAUDE.md](CLAUDE.md)** - Project directives

---

## License

Private repository for internal use.
