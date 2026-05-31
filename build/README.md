# Unified MCP Server

Single entry point for all MCP tools in the thomaschangsf/skills repository.

## Why Use This?

Instead of configuring multiple MCP servers:
```json
{
  "mcpServers": {
    "organize_md": { "command": "node", "args": ["/path/to/plugins/organize_md/index.js"] },
    "pdf_to_md": { "command": "node", "args": ["/path/to/plugins/pdf_to_md/index.js"] }
  }
}
```

Use one unified server:
```json
{
  "mcpServers": {
    "thomaschangsf-custom-skills": {
      "command": "node",
      "args": ["/path/to/skills/build/index.js"]
    }
  }
}
```

## Benefits

- ✅ Single configuration entry
- ✅ No network dependency (works with local clone)
- ✅ No npm caching errors
- ✅ All tools available through one server
- ✅ Easier to develop and test locally

## Setup

1. Clone the repository:
   ```bash
   git clone git@github.com:thomaschangsf/skills.git
   cd skills
   ```

2. Install build dependencies:
   ```bash
   cd build
   npm install
   ```

3. Configure Claude Code (`~/.claude/settings.json`):
   ```json
   {
     "mcpServers": {
       "thomaschangsf-custom-skills": {
         "command": "node",
         "args": ["/ABSOLUTE/PATH/TO/skills/build/index.js"],
         "env": {}
       }
     }
   }
   ```

4. Restart Claude Code or run `/reload-plugins`

## Available Tools

- `organize_markdown` - Organize markdown files: move images, add heading numbers
- `convert_pdf_to_md` - Convert PDFs to Markdown with table extraction

## Development

To add a new tool:

1. Create handler module: `build/tools/my_tool.js`
2. Export `listTools()` and `handleCall(request)` functions
3. Import in `build/index.js` and add to `TOOL_HANDLERS` array
4. Reinstall dependencies: `cd build && npm install`

## Testing

```bash
# Test the server directly
node build/index.js

# Should output:
# thomaschangsf-skills MCP server running on stdio
# Available tools: organize_markdown, convert_pdf_to_md
```

## Troubleshooting

**"Cannot find module" errors**: 
```bash
cd build && npm install
```

**"Python script not found"**:
- Ensure Python scripts exist at `plugins/{name}/scripts/*.py`
- Paths are resolved relative to build directory

**Tool not showing in Claude**:
- Check server starts without errors: `node build/index.js`
- Verify absolute path in settings.json
- Restart Claude Code
