# Skills Repository Architecture

This repository contains two complementary systems for extending AI assistants: **Skills** and **Tools**.

## Directory Structure

```
skills/
├── skills/                    # Prompt-based orchestration
│   ├── convert-pdf-to-md/    # Workflow guidance for PDF conversion
│   ├── git-commit/           # Git commit workflow
│   └── ...                   # Other skills
├── tools/                     # MCP servers (executable tools)
│   ├── pdf_to_md/            # Direct PDF conversion execution
│   └── ...                   # Future tools
└── scripts/
    └── dev_refresh_skills_and_tools.sh  # Unified installation
```

## Skills vs Tools

### Skills (`skills/`)

**Nature**: Prompt-based instructions loaded into AI context  
**Format**: Markdown files with YAML frontmatter (`SKILL.md`)  
**Purpose**: Orchestrate existing capabilities with domain expertise  
**Installation**: Via `npx skills` CLI to `~/.cursor/skills`, `~/.claude/skills`, `~/.agents/skills`

**Use Skills for**:
- ✅ Multi-step workflows requiring decision-making
- ✅ Domain expertise and best practices guidance
- ✅ Situations where flexibility and adaptation are needed
- ✅ When no specialized tool exists yet

**Example**: `skills/convert-pdf-to-md/`
- Provides workflow guidance, decision trees, and best practices
- Explains when to use OCR, how to handle tables, diagram conversion strategies
- AI orchestrates native tools (Read, Bash, Write) following the guidance

### Tools (`tools/`)

**Nature**: Executable MCP (Model Context Protocol) servers  
**Format**: Node.js packages with `index.js` entry point  
**Purpose**: Provide atomic, specialized capabilities  
**Installation**: Configured in `~/.claude/settings.json` or `~/.cursor/mcp.json`

**Use Tools for**:
- ✅ Atomic operations with predictable behavior
- ✅ External service integrations (APIs, databases, browsers)
- ✅ Performance-critical operations
- ✅ Operations requiring specialized libraries or executables

**Example**: `tools/pdf_to_md/`
- Wraps Python script for direct execution
- Provides single tool call: `convert_pdf_to_md(pdf_path, options)`
- Faster, more reliable than orchestrating multiple steps
- AI calls tool directly when it recognizes PDF conversion need

## Complementary Design

Skills and tools work **together**, not in competition:

### Example: PDF Conversion

**Scenario 1**: New user without tool configured
- AI uses **skill** (`skills/convert-pdf-to-md/`)
- Orchestrates Read, Bash, Write following documented workflow
- User benefits from guidance even without tool setup

**Scenario 2**: User with MCP tool configured
- AI uses **tool** (`tools/pdf_to_md/`) for fast execution
- Falls back to **skill** if tool fails or user wants to understand process
- Best of both worlds: speed + flexibility

**Scenario 3**: Complex custom requirements
- AI combines both: uses **skill** for strategy, **tool** for execution
- Skill provides decision-making, tool handles heavy lifting
- Example: "Convert this PDF but use special table handling for financial data"

## Installation & Management

### Unified Installation Script

`scripts/dev_refresh_skills_and_tools.sh` manages both systems:

```bash
# Development mode (local paths)
./scripts/dev_refresh_skills_and_tools.sh

# Sharing mode (GitHub URLs)
TOOLS_MODE=github ./scripts/dev_refresh_skills_and_tools.sh
```

**What it does**:
1. Installs skills to:
   - `~/.cursor/skills/` (Cursor IDE)
   - `~/.claude/skills/` (Claude Code)
   - `~/.agents/skills/` (Cline/shared)

2. Configures tools in:
   - `~/.claude/settings.json` (Claude Code)
   - `~/.cursor/mcp.json` (Cursor IDE)

3. Auto-discovers new skills and tools (no script updates needed!)

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
3. Run refresh script: `./scripts/dev_refresh_skills_and_tools.sh`

#### Add a New Tool

1. Create directory: `tools/<tool-name>/`
2. Add `package.json`, `index.js` (must be executable)
3. Implement MCP server (see `tools/pdf_to_md/index.js` as template)
4. Run refresh script: `./scripts/dev_refresh_skills_and_tools.sh`

The script automatically discovers and configures new content!

## Configuration Modes

### Local Development Mode (default)

```bash
./scripts/dev_refresh_skills_and_tools.sh
```

**Tools configured with absolute paths**:
```json
{
  "mcpServers": {
    "pdf_to_md": {
      "command": "node",
      "args": ["/absolute/path/to/tools/pdf_to_md/index.js"]
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
TOOLS_MODE=github ./scripts/dev_refresh_skills_and_tools.sh
```

**Tools configured with GitHub URLs**:
```json
{
  "mcpServers": {
    "pdf_to_md": {
      "command": "npx",
      "args": ["-y", "github:thomaschangsf/skills#tools/pdf_to_md"]
    }
  }
}
```

**Benefits**:
- Share with others easily
- Version-controlled via Git
- No local path dependencies

## Design Principles

### 1. Separation of Concerns
- **Skills**: Strategic guidance and workflow orchestration
- **Tools**: Tactical execution of specialized operations

### 2. Progressive Enhancement
- Skills work standalone (graceful degradation)
- Tools enhance performance when available
- AI chooses best approach based on context

### 3. Discoverability
- Skills auto-discovered by `npx skills` CLI
- Tools auto-discovered by refresh script
- No manual configuration lists

### 4. Cross-Reference
- Skills document related tools
- Tools reference parent skills
- Clear relationship between complementary components

### 5. Flexibility
- Tools optional (skills work without them)
- Skills optional (tools work without them)
- Best results when both available

## IDE Support Matrix

| Feature | Cursor | Claude Code | Cline/Warp |
|---------|--------|-------------|------------|
| **Skills** | ✅ `~/.cursor/skills/` | ✅ `~/.claude/skills/` | ✅ `~/.agents/skills/` |
| **MCP Tools** | ✅ `~/.cursor/mcp.json` | ✅ `~/.claude/settings.json` | ❌ Not yet |
| **Auto-refresh** | ✅ | ✅ | ✅ (skills only) |

## Real-World Workflow

### Developer Workflow

1. **Create skill** for new capability:
   ```bash
   mkdir skills/my-new-feature
   vim skills/my-new-feature/SKILL.md
   ./scripts/dev_refresh_skills_and_tools.sh
   ```

2. **Test with AI** - skill provides guidance immediately

3. **Identify bottlenecks** - if orchestration is slow or complex

4. **Create tool** for performance:
   ```bash
   mkdir tools/my-new-feature
   # Implement MCP server
   ./scripts/dev_refresh_skills_and_tools.sh
   ```

5. **AI automatically uses tool** when available, falls back to skill if needed

### Team Workflow

1. **Developer** creates skill + tool locally (dev mode)
2. **Test** with both Cursor and Claude Code
3. **Push** to GitHub when ready
4. **Switch to GitHub mode**: `TOOLS_MODE=github ./scripts/dev_refresh_skills_and_tools.sh`
5. **Team members** run the same script to get updates
6. **Everyone benefits** from shared capabilities

## Examples

### Git Commit Skill (Orchestration Only)

**Location**: `skills/git-commit/`

**Why skill, not tool?**: 
- Requires judgment (commit message style, file selection)
- Uses existing git commands (no specialized execution needed)
- Benefits from context-aware orchestration

### PDF Conversion (Both Skill and Tool)

**Skill**: `skills/convert-pdf-to-md/`
- Workflow guidance, decision trees, best practices

**Tool**: `tools/pdf_to_md/`
- Fast atomic execution wrapping Python script

**Why both?**: 
- Skill: Educational, flexible, works without dependencies
- Tool: Performance, reliability, production use

### Future: Database Query Tool (Tool Only)

**Location**: `tools/db-query/` (hypothetical)

**Why tool, not skill?**:
- Requires database connection (external service)
- Security sensitive (credentials management)
- Performance critical (native SQL execution)
- No orchestration needed (atomic operation)

## Troubleshooting

### Skills not appearing
```bash
# Refresh skills
./scripts/dev_refresh_skills_and_tools.sh

# Restart IDE
# Cursor: Cmd+Shift+P → Developer: Reload Window
# Claude Code: Restart application
```

### Tools not loading
```bash
# Check config files
cat ~/.claude/settings.json    # Claude Code
cat ~/.cursor/mcp.json         # Cursor

# Verify tool structure
ls -la tools/pdf_to_md/        # Should have index.js, package.json
chmod +x tools/pdf_to_md/index.js  # Ensure executable

# Check backups if something went wrong
cat ~/.claude/settings.json.backup
```

### Script issues
```bash
# Requires jq for JSON manipulation
brew install jq  # macOS
apt-get install jq  # Linux

# Check tool discovery
bash -c 'find tools/ -mindepth 1 -maxdepth 1 -type d'
```

## Resources

- **Skills CLI**: [github.com/vercel-labs/skills](https://github.com/vercel-labs/skills)
- **MCP Protocol**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **MCP SDK**: [github.com/modelcontextprotocol/sdk](https://github.com/modelcontextprotocol/sdk)

## Future Enhancements

Potential improvements to the architecture:

1. **Tool Testing Framework**: Automated testing for MCP tools
2. **Skill Templates**: Starter templates for common skill patterns
3. **Dependency Management**: Declare skill → tool relationships explicitly
4. **Version Compatibility**: Handle breaking changes gracefully
5. **Performance Metrics**: Track skill vs tool performance comparison
6. **Usage Analytics**: Understand which skills/tools are most valuable
