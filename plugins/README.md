# MCP Tools

This directory contains MCP (Model Context Protocol) servers that extend Claude Code with specialized capabilities.

## Directory Structure

```
plugins/
├── README.md              # This file
├── pdf_to_md/            # PDF to Markdown conversion tool
│   ├── package.json
│   ├── index.js          # MCP server
│   ├── scripts/
│   │   └── pdf2md.py     # Python conversion script
│   └── README.md
└── <future-tool>/        # Add more tools here
```

## Tools vs Skills

| Aspect | Skills (`skills/`) | Tools (`plugins/`) |
|--------|-------------------|------------------|
| **Type** | Prompt-based instructions | Executable MCP servers |
| **Purpose** | Orchestrate existing tools | Provide new capabilities |
| **Installation** | Via `npx skills` CLI | Via Claude Code settings.json |
| **Usage** | Guides Claude's workflow | Direct tool calls by Claude |
| **Best for** | Multi-step processes | Atomic operations, external APIs |

## Installation & Usage

### Development (Local Testing)

1. **Auto-configure** (recommended):
   ```bash
   ./scripts/dev_refresh_skills_and_tools.sh
   # Or explicitly set local mode:
   TOOLS_MODE=local ./scripts/dev_refresh_skills_and_tools.sh
   ```
   This configures both Claude Code and Cursor automatically.

2. **Manual configuration**:

   **Claude Code** - Add to `~/.claude/settings.json`:
   ```json
   {
     "mcpServers": {
       "pdf_to_md": {
         "command": "node",
         "args": ["/absolute/path/to/skills/plugins/pdf_to_md/index.js"],
         "env": {}
       }
     }
   }
   ```

   **Cursor** - Add to `~/.cursor/mcp.json`:
   ```json
   {
     "mcpServers": {
       "pdf_to_md": {
         "type": "stdio",
         "command": "node",
         "args": ["/absolute/path/to/skills/plugins/pdf_to_md/index.js"]
       }
     }
   }
   ```

3. **Restart Claude Code or Cursor** to load the MCP server

### Sharing (GitHub Installation)

1. **Push to GitHub**:
   ```bash
   git add plugins/
   git commit -m "Add MCP tools"
   git push
   ```

2. **Update configuration mode**:
   ```bash
   TOOLS_MODE=github ./scripts/dev_refresh_skills_and_tools.sh
   ```

   Or manually update configurations:

   **Claude Code** (`~/.claude/settings.json`):
   ```json
   {
     "mcpServers": {
       "pdf_to_md": {
         "command": "npx",
         "args": ["-y", "github:thomaschangsf/skills#plugins/pdf_to_md"],
         "env": {}
       }
     }
   }
   ```

   **Cursor** (`~/.cursor/mcp.json`):
   ```json
   {
     "mcpServers": {
       "pdf_to_md": {
         "type": "stdio",
         "command": "npx",
         "args": ["-y", "github:thomaschangsf/skills#plugins/pdf_to_md"]
       }
     }
   }
   ```

3. **Share with others** - They can add the same GitHub configuration to their settings

## Available Tools

### pdf_to_md

Convert PDFs to Markdown with table extraction and diagram reconstruction.

**Prerequisites**: Python with `pypdf` (and optionally `pdfplumber`)

**Usage**: Ask Claude to "convert this PDF to markdown" and it will automatically use the tool.

**See**: [plugins/pdf_to_md/README.md](pdf_to_md/README.md) for details

## Creating New Tools

1. **Create tool directory**: `plugins/<tool-name>/`

2. **Add required files**:
   ```
   plugins/<tool-name>/
   ├── package.json       # NPM package definition
   ├── index.js          # MCP server (must be executable)
   └── README.md         # Documentation
   ```

3. **MCP server template** (index.js):
   ```javascript
   #!/usr/bin/env node
   import { Server } from "@modelcontextprotocol/sdk/server/index.js";
   import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

   const server = new Server({
     name: "tool-name",
     version: "1.0.0",
   }, {
     capabilities: { tools: {} }
   });

   server.setRequestHandler("plugins/list", async () => ({
     tools: [{
       name: "your_tool_name",
       description: "What your tool does",
       inputSchema: {
         type: "object",
         properties: {
           param1: { type: "string", description: "Parameter description" }
         },
         required: ["param1"]
       }
     }]
   }));

   server.setRequestHandler("plugins/call", async (request) => {
     if (request.params.name === "your_tool_name") {
       // Your tool logic here
       return {
         content: [{ type: "text", text: "Result" }]
       };
     }
   });

   const transport = new StdioServerTransport();
   await server.connect(transport);
   ```

4. **Make executable**: `chmod +x plugins/<tool-name>/index.js`

5. **Test locally**: Run `./scripts/dev_refresh_skills_and_tools.sh`

6. **Share**: Push to GitHub and others can use via `github:thomaschangsf/skills#plugins/<tool-name>`

## Maintenance

### Refresh Configuration

After adding/modifying tools, run:
```bash
./scripts/dev_refresh_skills_and_tools.sh
```

This will:
- ✅ Refresh all skills to `~/.cursor/skills`, `~/.claude/skills`, `~/.agents/skills`
- ✅ Update MCP tool configurations in `~/.claude/settings.json` and `~/.cursor/mcp.json`
- ✅ Create backups of existing settings

### Switch Modes

```bash
# Development mode (absolute paths)
TOOLS_MODE=local ./scripts/dev_refresh_skills_and_tools.sh

# Sharing mode (GitHub URLs)
TOOLS_MODE=github ./scripts/dev_refresh_skills_and_tools.sh
```

### Verify Installation

Check Claude Code startup logs for:
```
[MCP] Starting server: pdf_to_md
[MCP] Server pdf_to_md initialized successfully
```

## Troubleshooting

**Tool not showing up**:
- Restart the IDE completely (Claude Code or Cursor)
- Check config files have correct configuration:
  - Claude Code: `~/.claude/settings.json`
  - Cursor: `~/.cursor/mcp.json`
- Verify tool's `index.js` is executable: `chmod +x plugins/<tool>/index.js`

**"Module not found" errors**:
- Run `npm install` in the tool directory to install dependencies
- For GitHub installs, `npx` should auto-install dependencies

**Python script errors** (pdf_to_md):
- Install Python dependencies: `pip install pypdf pdfplumber`
- Verify Python 3 is available: `python3 --version`

## Resources

- [MCP Documentation](https://modelcontextprotocol.io)
- [MCP SDK](https://github.com/modelcontextprotocol/sdk)
- [Claude Code Docs](https://docs.anthropic.com)
