# Skills Repository Architecture

This repository contains three complementary systems for extending AI assistants: **Skills**, **MCPs**, and **Agent-Specific Plugins**.

## Directory Structure

```
skills/
├── skills/                    # Prompt-based orchestration
│   ├── think/                # Reasoning framework
│   ├── git-commit/           # Git commit workflow
│   └── ...                   # Other skills
├── mcps/                     # MCP servers (executable tools)
│   ├── nodejs/               # Node.js MCPs (using @modelcontextprotocol/sdk)
│   │   ├── pdf_to_md/       # PDF conversion tool
│   │   └── organize_md/     # Markdown organizer
│   └── python/               # Python MCPs (stdin/stdout protocol)
│       ├── yfinance/         # Yahoo Finance data
│       └── sec-edgar/        # SEC filings data
├── agent-specific/           # Agent-specific plugins
│   ├── claude/               # Claude Code-specific
│   │   └── goal-wizard/     # Goal sandbox helper
│   └── cu/                   # Claude Unleashed-specific
│       ├── cu-setup/         # CU setup diagnostic
│       ├── cu-wf-create/     # CU workflow creation
│       ├── cu-wf-run/        # CU workflow runner
│       └── wiki/             # CU documentation
├── docs/                     # Documentation
│   ├── behavioral/           # AI behavioral guidelines
│   │   └── CLAUDE_USER.md   # Golden source
│   └── guides/               # Setup and how-to guides
└── dev/                      # Development resources
    ├── apps/                 # Example applications
    │   ├── multi_agent_generator_evaluator_loop/  # Streamlit demo
    │   └── weather_forecast/                      # CLI example
    ├── lib/                  # Library code
    │   └── aor/             # Agent orchestration framework
    └── scripts/              # Utility scripts
        └── dev_refresh_skills_and_tools.sh  # Unified installation
```

## Three Extension Types

### 1. Skills (`skills/`)

**Nature**: Prompt-based instructions loaded into AI context  
**Format**: Markdown files with YAML frontmatter (`SKILL.md`)  
**Purpose**: Orchestrate existing capabilities with domain expertise  
**Installation**: Via `npx skills` CLI to `~/.cursor/skills`, `~/.claude/skills`, `~/.agents/skills`  
**Compatibility**: ✅ Universal (all AI agents)

**Use Skills for**:
- ✅ Multi-step workflows requiring decision-making
- ✅ Domain expertise and best practices guidance
- ✅ Situations where flexibility and adaptation are needed
- ✅ Orchestrating existing tools into complex workflows

**Example**: `skills/think/`
- Provides compression/decompression reasoning framework
- Guides agent through building, validating, and stress-testing mental models
- Can reference MCPs (e.g., "use yfinance MCP for stock data")
- AI follows instructions, makes decisions based on context

### 2. MCPs (Model Context Protocol servers) (`mcps/`)

**Nature**: Executable programs that provide new tools/capabilities  
**Format**: Node.js or Python programs with MCP protocol implementation  
**Purpose**: Add atomic operations, external APIs, new data sources  
**Installation**: Configured in `~/.claude/settings.json` or `~/.cursor/mcp.json`  
**Compatibility**: ✅ Universal (Cursor, Claude Code, any MCP-compatible agent)

**Two types of MCPs**:

#### Node.js MCPs (`mcps/nodejs/`)
- Use `@modelcontextprotocol/sdk` package
- Full-featured MCP servers
- Example: `mcps/nodejs/pdf_to_md/` - PDF conversion tool

#### Python MCPs (`mcps/python/`)
- Simple stdin/stdout JSON protocol
- Lightweight, no SDK dependency
- Example: `mcps/python/yfinance/` - Yahoo Finance API wrapper

**Use MCPs for**:
- ✅ Atomic operations with predictable behavior
- ✅ External service integrations (APIs, databases, stock data)
- ✅ Performance-critical operations
- ✅ Operations requiring specialized libraries or executables

**Example**: `mcps/python/yfinance/`
- Provides `get_company_overview` tool for fetching stock fundamentals
- Agent calls tool directly: `CallMcpTool("yfinance", "get_company_overview", {"symbol": "NVDA"})`
- Returns PE ratio, margins, growth rates, etc.
- Separates data fetching from reasoning logic

### 3. Agent-Specific Plugins (`agent-specific/`)

**Nature**: Agent-specific bundles combining skills + resources  
**Format**: Directory with agent-specific manifest (e.g., `.claude-plugin/plugin.json`)  
**Purpose**: Package skills with supporting files for specific agents  
**Installation**: Varies by agent (e.g., `~/.claude/plugins/` for Claude Code)  
**Compatibility**: ❌ Agent-specific (not portable)

**Use Agent-Specific Plugins for**:
- ✅ Bundling skill instructions with helper scripts
- ✅ Packaging templates, resources, or data files with a skill
- ✅ Agent-specific workflows (Claude Code, Claude Unleashed)
- ❌ NOT for universal tools (use MCPs instead)

**Supported Agents**:

#### Claude Code (`agent-specific/claude/`)
- Format: `.claude-plugin/plugin.json` manifest
- Installation: `~/.claude/plugins/`
- Example: `agent-specific/claude/goal-wizard/` - Goal sandbox helper

#### Claude Unleashed (`agent-specific/cu/`)
- Format: `SKILL.md` + resources
- Installation: Via `npx skills` (standard skills)
- Example: `agent-specific/cu/cu-setup/` - CU setup diagnostic
- Note: CU plugins are actually skills with CU-specific documentation

## How They Work Together

Skills, MCPs, and Claude Plugins are **complementary**, not competing:

### Skills Reference MCPs (Loose Coupling)

```
skills/think/SKILL.md:
  "First: Read tool guidance from quality/equity/taste.md
   Use yfinance MCP (primary) for stock fundamentals
   Use SEC Edgar MCP for deep-dive filings"
  
Agent workflow:
  1. Reads skill instructions
  2. Calls yfinance MCP: get_company_overview("NVDA")
  3. Calls SEC Edgar MCP: search_filing_text("NVDA", "10-K", ["RPO"])
  4. Follows reasoning framework from skill

Two separate artifacts with independent lifecycles:
  - Skill: Instructions (SKILL.md)
  - MCPs: Tools (registered separately in mcp.json)
```

### Claude Plugins Bundle Everything (Tight Coupling)

```
plugins-claude/goal-wizard/:
  .claude-plugin/plugin.json  ← declares skill + scripts + dependencies
  scripts/analyze_goal.py     ← bundled together
  resources/verifiers/        ← bundled together
  
One self-contained package:
  - Skill instructions
  - Python helper scripts  
  - Resources/templates
  
Only works in Claude Code (not universal)
```

### Example: Stock Analysis Workflow

**Scenario 1**: User asks `/think semiconductor stocks risk/reward`

1. **Skill** (`skills/think/`) provides reasoning framework:
   - Compression/decompression flow
   - Domain detection → loads equity quality plugin
   - Instructs: "Use yfinance for data, follow four-lens analysis"

2. **MCPs** provide data:
   - `yfinance`: Fetches PE ratios, margins, growth rates
   - `sec-edgar`: Pulls RPO from 10-K filings
   
3. **Agent** combines them:
   - Follows skill's reasoning structure
   - Calls MCPs for atomic data operations
   - Builds analysis using framework + data

**Key insight**: Skill and MCPs remain separate. Agent orchestrates both.

## Installation & Management

### Unified Installation Script

`dev/scripts/dev_refresh_skills_and_tools.sh` manages all three systems:

```bash
# Development mode (local paths)
./dev/scripts/dev_refresh_skills_and_tools.sh

# Sharing mode (GitHub URLs)
TOOLS_MODE=github ./dev/scripts/dev_refresh_skills_and_tools.sh
```

**What it does**:
1. **Installs skills** to:
   - `~/.cursor/skills/` (Cursor IDE)
   - `~/.claude/skills/` (Claude Code)
   - `~/.agents/skills/` (Cline/shared)

2. **Configures MCPs** in:
   - `~/.claude/settings.json` (Claude Code)
   - `~/.cursor/mcp.json` (Cursor IDE)
   - Discovers both Node.js MCPs (`mcps/nodejs/`) and Python MCPs (`mcps/python/`)

3. **Handles Agent-Specific Plugins**:
   - Copies to `~/.claude/plugins/` (Claude Code)
   - Discovers from `agent-specific/claude/`, `agent-specific/cu/`
   - Requires manual `/reload-plugins` in Claude Code

4. **Auto-discovers** new skills and MCPs (no script updates needed!)

### Adding New Content

#### Add a New Skill

1. Create directory: `skills/<skill-name>/`
2. Add `SKILL.md` with frontmatter:
   ```markdown
   ---
   name: skill-name
   description: One-line description
   ---
   # Instructions here
   ```
3. Run refresh script: `./dev/scripts/dev_refresh_skills_and_tools.sh`

#### Add a New MCP (Node.js)

1. Create directory: `mcps/nodejs/<tool-name>/`
2. Add `package.json`, `index.js` (must be executable)
3. Implement MCP server using `@modelcontextprotocol/sdk`
4. Run refresh script: `./dev/scripts/dev_refresh_skills_and_tools.sh`

#### Add a New MCP (Python)

1. Create directory: `mcps/python/<tool-name>/`
2. Add `pyproject.toml` (uv project), `server.py`
3. Implement stdin/stdout JSON protocol (see `mcps/python/yfinance/` as template)
4. Run refresh script: `./dev/scripts/dev_refresh_skills_and_tools.sh`

#### Add an Agent-Specific Plugin

**For Claude Code:**
1. Create directory: `agent-specific/claude/<plugin-name>/`
2. Add `.claude-plugin/plugin.json` manifest
3. Add skill files and helper scripts
4. Run refresh script, then `/reload-plugins` in Claude Code

**For Claude Unleashed:**
1. Create directory: `agent-specific/cu/<plugin-name>/`
2. Add `SKILL.md` with CU-specific instructions
3. Add supporting resources (guides, docs, scripts)
4. Run refresh script (installs as standard skill)

The script automatically discovers and configures new content!

## Configuration Modes

### Local Development Mode (default)

```bash
./dev/scripts/dev_refresh_skills_and_tools.sh
```

**MCPs configured with absolute paths**:
```json
{
  "mcpServers": {
    "yfinance": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/mcps/python/yfinance", "server.py"]
    },
    "pdf_to_md": {
      "type": "stdio",
      "command": "node",
      "args": ["/absolute/path/to/mcps/nodejs/pdf_to_md/index.js"]
    }
  }
}
```

**Benefits**:
- Test changes immediately
- No need to push to GitHub
- Edit-reload workflow

### GitHub Sharing Mode

```bash
TOOLS_MODE=github ./dev/scripts/dev_refresh_skills_and_tools.sh
```

**MCPs configured with GitHub URLs**:
```json
{
  "mcpServers": {
    "pdf_to_md": {
      "command": "npx",
      "args": ["-y", "github:thomaschangsf/skills#mcps/nodejs/pdf_to_md"]
    }
  }
}
```

**Benefits**:
- Share with others easily
- Version-controlled via Git
- No local path dependencies

## Comparison Table

| Feature | Skill | MCP | Agent-Specific Plugin |
|---------|-------|-----|-----------------------|
| **Format** | Markdown (SKILL.md) | Executable (JS/Python) | Bundle (skill + resources) |
| **Provides** | Instructions & workflow | Tools/APIs/data sources | Skills + helper scripts |
| **Used by** | All agents | All MCP-compatible agents | Specific agent only |
| **Discovery** | `npx skills` CLI | Config files (mcp.json) | Agent-specific manifest |
| **Installation** | `~/.cursor/skills/` | `~/.cursor/mcp.json` | Agent-specific (e.g., `~/.claude/plugins/`) |
| **Lifecycle** | Independent | Independent | Bundled together |
| **Coupling** | Loose (references MCPs) | Standalone | Tight (skill + scripts) |
| **Best for** | Multi-step workflows | Atomic operations | Agent-specific bundles |

## Design Principles

### 1. Separation of Concerns
- **Skills**: Strategic guidance and workflow orchestration
- **MCPs**: Tactical execution of specialized operations
- **Agent-Specific Plugins**: Agent-specific bundles (use sparingly)

### 2. Universal vs. Platform-Specific
- **Skills**: Universal (work in all agents)
- **MCPs**: Universal (work in all MCP-compatible agents)
- **Agent-Specific Plugins**: Platform-specific (Claude Code, Claude Unleashed, etc.)
  - **Prefer MCPs over Agent-Specific Plugins** for portability

### 3. Loose Coupling
- Skills **reference** MCPs but remain independent
- MCPs don't depend on skills
- Agent orchestrates both based on context
- **Avoid tight coupling** (use Agent-Specific Plugins only when bundling is essential)

### 4. Progressive Enhancement
- Skills work standalone (graceful degradation)
- MCPs enhance performance when available
- AI chooses best approach based on context

### 5. Discoverability
- Skills auto-discovered by `npx skills` CLI
- MCPs auto-discovered by refresh script (scans `mcps/nodejs/` and `mcps/python/`)
- Claude Plugins manually loaded via `/reload-plugins`
- No manual configuration lists needed

### 6. Data Source Hierarchy
- MCPs provide **tiered data access** with rate limit management
- Example: yfinance (primary, generous limits) → SEC Edgar (deep-dive, unlimited) → Alpha Vantage (fallback, limited)
- Skills instruct agents on **which MCP to use when**

### 7. Flexibility
- MCPs optional (skills can work without them using native tools)
- Skills optional (MCPs work standalone)
- Best results when both available

## IDE Support Matrix

| Feature | Cursor | Claude Code | Claude Unleashed |
|---------|--------|-------------|------------------|
| **Skills** | ✅ `~/.cursor/skills/` | ✅ `~/.claude/skills/` | ✅ Standard skills |
| **MCPs** | ✅ `~/.cursor/mcp.json` | ✅ `~/.claude/settings.json` | ❌ Not yet |
| **Agent-Specific Plugins** | ❌ No | ✅ `~/.claude/plugins/` | ✅ Via skills |
| **Auto-refresh** | ✅ | ✅ | ✅ (skills only) |

## Developer Workflow

### 1. Start with a Skill

```bash
mkdir skills/my-new-feature
vim skills/my-new-feature/SKILL.md
./dev/scripts/dev_refresh_skills_and_tools.sh
```

Test with AI - skill provides guidance immediately using existing tools.

### 2. Identify Performance Bottlenecks

If orchestration is slow, complex, or requires external APIs:

### 3. Create MCP for Atomic Operations

**For Node.js MCP:**
```bash
mkdir mcps/nodejs/my-feature
cd mcps/nodejs/my-feature
npm init
# Implement MCP using @modelcontextprotocol/sdk
./dev/scripts/dev_refresh_skills_and_tools.sh
```

**For Python MCP:**
```bash
mkdir mcps/python/my-feature
cd mcps/python/my-feature
uv init
# Create server.py with stdin/stdout protocol
./dev/scripts/dev_refresh_skills_and_tools.sh
```

### 4. Update Skill to Reference MCP

```markdown
---
name: my-feature
---
# My Feature

## Tool Strategy
- Use `my-feature` MCP for data fetching
- Fallback to native tools if MCP unavailable
```

### 5. Share with Team

```bash
git add skills/ mcps/
git commit -m "Add my-feature skill + MCP"
git push

# Switch to GitHub mode
TOOLS_MODE=github ./dev/scripts/dev_refresh_skills_and_tools.sh
```

Team members run the same script to get updates.

### When to Use Each Type

**Use Skill when:**
- Multi-step workflow with decision points
- Domain expertise / best practices needed
- Orchestrating existing tools into complex flow
- Educational / exploratory tasks

**Use MCP when:**
- Atomic operation (single, well-defined task)
- External API integration (stock data, SEC filings, databases)
- Performance-critical operation
- Requires specialized library

**Use Agent-Specific Plugin when:**
- **Rarely** - only for agent-specific bundles
- Experimental workflows not ready for universal adoption
- Tightly coupled skill + helper scripts for specific agent
- **Prefer converting to MCP once stable**

## Real-World Examples

### Example 1: Stock Analysis (Skill + MCPs)

**Skill**: `skills/think/`
- Provides compression/decompression reasoning framework
- Instructs: "Detect domain → load equity quality plugin → use yfinance MCP"
- **Why skill?** Multi-step workflow requiring judgment and domain expertise

**MCPs**: 
- `mcps/python/yfinance/` - Primary data source (PE ratios, margins, growth rates)
- `mcps/python/sec-edgar/` - Deep-dive filings (RPO, customer concentration)

**Why both?**
- Skill: Provides reasoning structure and quality standards
- MCPs: Provide atomic data operations
- **Agent orchestrates**: Follows skill's framework, calls MCPs for data

### Example 2: PDF Conversion (MCP Only)

**MCP**: `mcps/nodejs/pdf_to_md/`
- Wraps Python script for PDF conversion
- Provides single tool: `convert_pdf_to_md(path, options)`

**Why MCP, no skill?**
- Atomic operation (no complex orchestration needed)
- Performance-critical (native execution)
- Requires specialized library (pypdf, pdfplumber)

### Example 3: Git Commit (Skill Only)

**Skill**: `skills/git-commit/`
- Orchestrates git commands with judgment
- Determines commit message style, file selection
- Uses native Shell tool

**Why skill, no MCP?**
- Requires context-aware decision-making
- Uses existing git commands (no specialized execution)
- Benefits from flexible orchestration

### Example 4: Agent-Specific Plugins

**Claude Code Plugin**: `agent-specific/claude/goal-wizard/`
- Bundles skill instructions + Python verification scripts
- `.claude-plugin/plugin.json` declares dependencies
- Tightly couples skill with helper scripts

**Why Agent-Specific Plugin, not MCP?**
- Experimental/incomplete
- Tightly couples skill with helper scripts
- Claude Code-specific workflow

**Better approach**: Convert to universal MCP once stable

---

**Claude Unleashed Plugins**: `agent-specific/cu/`
- `cu-setup/` - CU setup diagnostic skill
- `cu-wf-create/` - CU workflow creation skill
- `cu-wf-run/` - CU workflow runner skill
- `wiki/` - Shared CU documentation

**Why Agent-Specific, not Universal?**
- CU-specific commands (`claude-unleashed daemon status`)
- CU-specific concepts (worktrees, daemon, workflows)
- References CU-specific documentation

**Note**: CU plugins are actually standard skills (via `SKILL.md`), just organized separately for clarity

## Troubleshooting

### Skills not appearing
```bash
# Refresh skills
./dev/scripts/dev_refresh_skills_and_tools.sh

# Restart IDE
# Cursor: Cmd+Shift+P → Developer: Reload Window
# Claude Code: Restart application
```

### MCPs not loading
```bash
# Check config files
cat ~/.claude/settings.json    # Claude Code
cat ~/.cursor/mcp.json         # Cursor

# Verify MCP structure
ls -la mcps/nodejs/pdf_to_md/   # Should have index.js, package.json
ls -la mcps/python/yfinance/    # Should have server.py, pyproject.toml

# Ensure executables are set
chmod +x mcps/nodejs/pdf_to_md/index.js
chmod +x mcps/python/yfinance/server.py

# Check backups if something went wrong
cat ~/.claude/settings.json.backup

# Restart Cursor CLI to activate MCPs
# (Cursor must be restarted after mcp.json changes)
```

### Python MCP not working
```bash
# Install dependencies in MCP directory
cd mcps/python/yfinance
uv sync

# Verify Python 3 available
python3 --version

# Test MCP manually
echo '{"method":"tools/list","params":{}}' | uv run server.py
```

### Claude Plugin not loading
```bash
# Reload plugins in Claude Code
/reload-plugins

# Check plugin manifest
cat plugins-claude/goal-wizard/.claude-plugin/plugin.json

# Verify Python dependencies
pip install pyyaml
```

### Script issues
```bash
# Requires jq for JSON manipulation
brew install jq  # macOS
apt-get install jq  # Linux

# Check MCP discovery
bash -c 'find mcps/nodejs/ -mindepth 1 -maxdepth 1 -type d'
bash -c 'find mcps/python/ -mindepth 1 -maxdepth 1 -type d'
```

## Resources

- **Skills CLI**: [github.com/vercel-labs/skills](https://github.com/vercel-labs/skills)
- **MCP Protocol**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **MCP SDK (Node.js)**: [github.com/modelcontextprotocol/sdk](https://github.com/modelcontextprotocol/sdk)
- **Python MCP Examples**: See `mcps/python/yfinance/`, `mcps/python/sec-edgar/`

## Future Enhancements

Potential improvements to the architecture:

1. **MCP Testing Framework**: Automated testing for MCP tools
2. **Skill Templates**: Starter templates for common skill patterns
3. **Explicit Dependencies**: Declare skill → MCP relationships in frontmatter
4. **Version Compatibility**: Handle breaking changes gracefully
5. **Performance Metrics**: Track skill vs MCP performance comparison
6. **Usage Analytics**: Understand which skills/MCPs are most valuable
7. **Agent-Specific Plugin Standards**: Define standards for each agent type
8. **Unified Python MCP SDK**: Create lightweight Python MCP SDK for consistency

## Summary: When to Use What

| Need | Use This | Example |
|------|----------|---------|
| Multi-step workflow with decision-making | **Skill** | `skills/think/` (reasoning framework) |
| Atomic operation with external API | **MCP** | `mcps/python/yfinance/` (stock data) |
| Portable tool across all agents | **MCP** | `mcps/nodejs/pdf_to_md/` (PDF conversion) |
| Agent-specific bundle | **Agent-Specific Plugin** | `agent-specific/claude/goal-wizard/` |
| Domain expertise + data fetching | **Skill + MCP** | Think skill references yfinance MCP |

**Golden Rule**: 
- **Prefer Skills + MCPs** (universal, loosely coupled)
- **Avoid Agent-Specific Plugins** unless agent-specific bundling is essential
- **Always separate** reasoning (skills) from data/tools (MCPs)
