# Developer Guide

Development workflow for skills and MCP plugins.

---

## Daily Workflow

### 1. Edit
```bash
# Edit skills or plugins
vim skills/my-skill/SKILL.md
vim plugins/all/my-plugin/index.js
```

### 2. Sync
```bash
# From repo root
./scripts/dev_refresh_skills_and_tools.sh
```

**What it does**:
- Auto-discovers skills from `skills/*/SKILL.md`
- Auto-discovers MCP plugins from `plugins/{all,claude,cursor}/*/`
- Installs to `~/.claude/` and `~/.cursor/`
- Agent-scoped (respects directory structure)

### 3. Restart
- **Claude Code**: Restart or `/reload-plugins`
- **Cursor**: Cmd+Shift+P → Developer: Reload Window

---

## Scripts Reference

### `dev_refresh_skills_and_tools.sh`
Sync everything (skills + plugins) to local agents.

```bash
# Normal (local development)
./scripts/dev_refresh_skills_and_tools.sh

# GitHub mode (for sharing)
TOOLS_MODE=github ./scripts/dev_refresh_skills_and_tools.sh

# Target specific agents
SKILLS_AGENTS="cursor claude-code" ./scripts/dev_refresh_skills_and_tools.sh
```

---

### `dev_refresh_claude_cursor_md.sh`
Refreshes AI behavioral guidelines across Claude and Cursor. Run this when you update `docs/behavioral/CLAUDE_USER.md`.

```bash
./scripts/dev_refresh_claude_cursor_md.sh
```

**What it does**:
- Copies `CLAUDE_USER.md` → `~/.claude/CLAUDE.md` (Claude global config)
- Merges guidelines into `~/.cursorrules` (Cursor global config)
- Optionally updates per-project Cursor config:
  - If `AGENTS.md` is not git-tracked → appends to `AGENTS.md`
  - If `AGENTS.md` is git-tracked → writes `.cursor/rules/personal-guidelines.mdc` + gitignores it locally (via `.git/info/exclude`)
- Optionally runs headless verification via `claude` and `cursor-agent` CLIs

**Golden source**: `docs/behavioral/CLAUDE_USER.md`

---

### `dev_refresh_skills_and_tools_for_claude_desktop.sh` 🆕
Build unified MCP server with **BOTH tools AND skills (as prompts)**.

**PRIMARY USE CASE: Claude Desktop**
- Claude Desktop doesn't support skills directory (`~/.claude/skills/`)
- MCP prompts are the ONLY way to get skills in Claude Desktop
- Also works for Claude Code and Cursor (alternative approach)

```bash
# Manual setup (default) - Shows copy-paste config
./scripts/dev_refresh_skills_and_tools_for_claude_desktop.sh

# Auto-configure (requires jq) - Automatically updates config files
./scripts/dev_refresh_skills_and_tools_for_claude_desktop.sh --auto-configure
```

**What it does**:
1. Auto-discovers all skills from `skills/*/SKILL.md`
2. Generates prompt handlers for each skill
3. Builds enhanced unified server with:
   - **Tools**: organize_markdown, convert_pdf_to_md
   - **Prompts**: git-commit, pr-review, critique-me, etc. (all 16 skills)
4. **Configuration** (choose one):
   - **Manual (default)**: Shows copy-paste ready config for all 3 agents
   - **Auto-configure**: Uses `jq` to automatically update config files (creates backups)

**Auto-configure requirements**:
- `jq` must be installed: `brew install jq` (macOS) or `apt-get install jq` (Linux)
- Automatically updates:
  - Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json`
  - Claude Code: `~/.claude/settings.json`
  - Cursor: `~/.cursor/mcp.json`
- Creates timestamped backups before modifying files

---

## Two Approaches: Traditional vs Claude Desktop Script

| Aspect | Traditional Script | Claude Desktop Script |
|--------|-------------------|----------------------|
| **Script** | `dev_refresh_skills_and_tools.sh` | `dev_refresh_skills_and_tools_for_claude_desktop.sh` |
| **Skills delivery** | Copy to `~/.claude/skills/` | Serve via MCP prompts |
| **Tools delivery** | Individual MCP plugins | Unified MCP server |
| **Claude Desktop** | ❌ Skills don't work | ✅ Everything works |
| **Setup** | Automatic (script configures) | Manual (default) or Auto (`--auto-configure`) |
| **Configuration** | Always automatic | Choice: manual copy-paste or auto with flag |
| **Use when** | Claude Code, Cursor | **Claude Desktop** (primary), or any agent |

### Configuration Modes Comparison

| Mode | Command | How It Works | Safety |
|------|---------|--------------|--------|
| **Traditional** | `./scripts/dev_refresh_skills_and_tools.sh` | Always auto-configures | ✅ Proven, tested |
| **Manual** | `./scripts/dev_refresh_skills_and_tools_for_claude_desktop.sh` | Shows config, you copy-paste | ✅ Safest (you control) |
| **Auto-configure** | `./scripts/...for_claude_desktop.sh --auto-configure` | Uses `jq` to auto-update | ⚠️ Creates backups first |

**Recommendation**:
- **Claude Desktop users**: Use Claude Desktop script with `--auto-configure` (ONLY option for skills)
- **Claude Code/Cursor users**: Use traditional script (simpler, automatic)
- **Developers wanting single source**: Use Claude Desktop script with `--auto-configure`
- **Safety-conscious users**: Use manual mode (default), review config before adding

---

The refresh script also configures individual plugins automatically (backward compatible):
```bash
# This still works and configures each plugin separately
./scripts/dev_refresh_skills_and_tools.sh
```

Individual plugins are auto-discovered from:
- `plugins/all/*` - Configured in ALL agents
- `plugins/claude/*` - Claude Code only
- `plugins/cursor/*` - Cursor only

**Choose unified server for**:
- Local development (faster iteration)
- Single configuration simplicity
- Bypassing network/npm issues

**Choose individual plugins for**:
- Production GitHub-based distribution
- Selective tool installation
- Agent-specific tools

---

## Adding New Skill

```bash
# 1. Create skill directory
mkdir -p skills/my-skill

# 2. Create SKILL.md
cat > skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: Does something useful
---

# My Skill

When the user asks for X:
1. Do this
2. Then that
3. Finally this
EOF

# 3. Optional: Add resources
mkdir -p skills/my-skill/resources
# Add helper scripts, templates, etc.

# 4. Sync
./scripts/dev_refresh_skills_and_tools.sh

# 5. Test
# Claude Code: /reload-plugins
# In conversation: /my-skill
```

---

## Adding New MCP Plugin

### Universal Plugin (works everywhere)
```bash
# 1. Create in plugins/all/
mkdir -p plugins/all/my-tool
cd plugins/all/my-tool

# 2. Initialize
npm init -y
npm install @modelcontextprotocol/sdk

# 3. Create MCP server
cat > index.js << 'EOF'
#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  {
    name: "my-tool",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "my_action",
      description: "Does something useful",
      inputSchema: {
        type: "object",
        properties: {
          param: {
            type: "string",
            description: "Parameter description",
          },
        },
        required: ["param"],
      },
    },
  ],
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "my_action") {
    // Do something with args.param
    return {
      content: [
        {
          type: "text",
          text: `Result: ${args.param}`,
        },
      ],
    };
  }

  throw new Error(`Unknown tool: ${name}`);
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
EOF

# 4. Make executable
chmod +x index.js

# 5. Sync
cd ../../..
./scripts/dev_refresh_skills_and_tools.sh

# 6. Restart agent
# Tools should now be available
```

---

### Claude-Specific Plugin
```bash
# Same as above, but use plugins/claude/ instead of plugins/all/
mkdir -p plugins/claude/my-tool
# ... rest same ...
```

**When to use `plugins/claude/`**: Plugin uses Claude Code-specific features (e.g., `/goal` command)

---

## Agent Scoping

Place plugins in the right directory based on compatibility:

```
plugins/
  ├── all/       → Works in ALL agents (Claude Code + Cursor)
  ├── claude/    → Claude Code only (uses /goal, etc.)
  └── cursor/    → Cursor only
```

**Decision tree**:
- Uses Claude Code-specific features? → `plugins/claude/`
- Uses Cursor-specific features? → `plugins/cursor/`
- Works everywhere? → `plugins/all/`

---

## Testing

### goal-wizard Test Suite

**Automated test script** for goal-wizard plugin that exercises all verification types:

```bash
# 1. Sync and restart
./scripts/dev_refresh_skills_and_tools.sh
# Restart Claude Code

# 2. Run interactive test suite
./plugins/claude/goal-wizard/test_goal_wizard.sh
```

**What it tests**:
- ✅ Smoke test (file creation)
- ✅ Structural verification (type hints, docstrings)
- ✅ Behavioral verification (existing tests)
- ✅ Safety guardrails

**Features**:
- Interactive guidance through each test
- Automated test file creation
- Shows exact commands to run in Claude Code
- Automated result verification
- Color-coded pass/fail output
- Test summary with pass/fail counts

**See also**: `plugins/claude/goal-wizard/TEST_PROCEDURE.md` for detailed manual test procedures

---

### Test Skill

### Skill Not Appearing
```bash
# 1. Verify SKILL.md exists
ls -la skills/my-skill/SKILL.md

# 2. Re-sync
./scripts/dev_refresh_skills_and_tools.sh

# 3. Reload agent
# Claude Code: /reload-plugins
# Cursor: Reload Window

# 4. Check installed
npx skills list -g | grep my-skill
```

---

### MCP Plugin Not Loading
```bash
# 1. Check configuration
cat ~/.claude/settings.json | jq '.mcpServers."my-tool"'

# 2. Test MCP server manually
node plugins/all/my-tool/index.js
# Should start without errors, wait for input

# 3. Check Claude Code startup logs for MCP errors

# 4. Verify dependencies installed
cd plugins/all/my-tool
npm install
```

---

### Wrong Agent Scope
```bash
# Move to correct directory
mv plugins/all/my-tool plugins/claude/

# Re-sync
./scripts/dev_refresh_skills_and_tools.sh

# Restart agent
```

---

## Environment Variables

```bash
# Development mode (local paths)
TOOLS_MODE=local ./scripts/dev_refresh_skills_and_tools.sh

# Sharing mode (GitHub URLs)
TOOLS_MODE=github ./scripts/dev_refresh_skills_and_tools.sh

# Target specific agents
SKILLS_AGENTS="cursor claude-code" ./scripts/dev_refresh_skills_and_tools.sh

# Use local repo for unpushed changes (auto-detected if run from repo)
SKILLS_PACKAGE_PATH="$(pwd)" ./scripts/dev_refresh_skills_and_tools.sh
```

---

## Common Commands

```bash
# Sync everything
./scripts/dev_refresh_skills_and_tools.sh

# List skills
npx skills list -g

# Remove old skill
npx skills remove -g old-skill-name -y

# Check MCP config
cat ~/.claude/settings.json | jq '.mcpServers'

# Test MCP server
node plugins/all/my-tool/index.js

# Find skill files
find skills/ -name "SKILL.md"

# Find MCP plugins
find plugins/ -name "index.js"
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Sync all | `./scripts/dev_refresh_skills_and_tools.sh` |
| Reload (Claude) | `/reload-plugins` |
| Reload (Cursor) | Cmd+Shift+P → Reload Window |
| List skills | `npx skills list -g` |
| Check MCP | `cat ~/.claude/settings.json \| jq .mcpServers` |
| Test MCP | `node plugins/all/my-tool/index.js` |
