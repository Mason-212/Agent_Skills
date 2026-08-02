#!/usr/bin/env bash
# dev_refresh_skills_and_tools_for_claude_desktop.sh
#
# Build unified MCP server with BOTH tools AND prompts (skills)
#
# PRIMARY USE CASE: Claude Desktop
# - Claude Desktop doesn't support skills directory (~/.claude/skills/)
# - MCP prompts are the ONLY way to get skills in Claude Desktop
#
# Also works for Claude Code and Cursor (alternative to traditional script)
#
# What this does:
# 1. Auto-discover all skills from skills/*/SKILL.md
# 2. Generate prompt handlers for each skill
# 3. Build enhanced unified server with tools + prompts
# 4. Show configuration for all 3 agents (manual setup by default)
#
# Usage:
#   ./scripts/dev_refresh_skills_and_tools_for_claude_desktop.sh              # Manual config (show instructions)
#   ./scripts/dev_refresh_skills_and_tools_for_claude_desktop.sh --auto-configure  # Automatic config (uses jq)
#

set -euo pipefail

# Parse command line arguments
AUTO_CONFIGURE=false
if [[ "${1:-}" == "--auto-configure" ]]; then
  AUTO_CONFIGURE=true
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${REPO_ROOT}/build"

echo "═══════════════════════════════════════════════════════════════"
echo "  Unified MCP Server Build (Tools + Skills via MCP)"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "PRIMARY USE CASE: Claude Desktop"
echo "  (Claude Desktop doesn't support skills directory)"
echo ""
echo "This script will:"
echo "  1. Auto-discover all skills from skills/"
echo "  2. Generate prompt handlers for each skill"
echo "  3. Build unified MCP server with tools + prompts"
echo "  4. Show configuration for manual setup"
echo ""

# ---------------------------------------------------------------------------
# Check Prerequisites
# ---------------------------------------------------------------------------

if [[ ! -d "${BUILD_DIR}" ]]; then
  echo "❌ build/ directory not found at ${BUILD_DIR}"
  echo "   The build infrastructure should already exist."
  exit 1
fi

if [[ ! -f "${BUILD_DIR}/tools/organize_md.js" ]] || [[ ! -f "${BUILD_DIR}/tools/pdf_to_md.js" ]]; then
  echo "❌ Tool handlers not found in ${BUILD_DIR}/tools/"
  echo "   Please ensure the base unified server is set up first."
  exit 1
fi

# ---------------------------------------------------------------------------
# Phase 1: Generate Prompt Handlers from Skills
# ---------------------------------------------------------------------------

echo "🔨 Phase 1: Generating Prompt Handlers from Skills"
echo "─────────────────────────────────────────────────────────────────"

cd "${BUILD_DIR}"

# Install/update dependencies
if [[ ! -d "node_modules" ]]; then
  echo "Installing dependencies..."
  npm install
fi

# Create prompts directory
mkdir -p prompts

SKILLS_DIR="${REPO_ROOT}/skills"
skill_count=0
skill_names=()

if [[ ! -d "${SKILLS_DIR}" ]]; then
  echo "❌ Skills directory not found: ${SKILLS_DIR}"
  exit 1
fi

echo "Discovering and processing skills..."
echo ""

while IFS= read -r -d '' skill_file; do
  skill_dir="$(dirname "${skill_file}")"
  skill_name="$(basename "${skill_dir}")"

  # Read the entire skill file
  skill_content=$(<"${skill_file}")

  # Extract name from frontmatter (between first --- and second ---)
  frontmatter=$(echo "${skill_content}" | awk '/^---$/{flag=!flag;next}flag')
  prompt_name=$(echo "${frontmatter}" | grep "^name:" | head -1 | sed 's/^name:[[:space:]]*//')
  description=$(echo "${frontmatter}" | grep "^description:" | head -1 | sed 's/^description:[[:space:]]*//')

  if [[ -z "${prompt_name}" ]]; then
    echo "  ⚠️  Skipping ${skill_name}: no 'name' in frontmatter"
    continue
  fi

  if [[ -z "${description}" ]]; then
    echo "  ⚠️  Skipping ${skill_name}: no 'description' in frontmatter"
    continue
  fi

  # Generate handler file
  handler_file="prompts/${skill_name}.js"

  cat > "${handler_file}" << 'HANDLER_EOF'
// Auto-generated prompt handler
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SKILL_NAME = "SKILL_NAME_PLACEHOLDER";
const PROMPT_NAME = "PROMPT_NAME_PLACEHOLDER";
const DESCRIPTION = "DESCRIPTION_PLACEHOLDER";

export function getPrompt() {
  return {
    name: PROMPT_NAME,
    description: DESCRIPTION,
    arguments: [],
  };
}

export function getPromptMessages() {
  const skillPath = path.join(__dirname, `../../skills/${SKILL_NAME}/SKILL.md`);
  const content = fs.readFileSync(skillPath, "utf-8");

  // Remove YAML frontmatter
  const withoutFrontmatter = content.replace(/^---\n[\s\S]*?\n---\n/, "");

  return [
    {
      role: "user",
      content: {
        type: "text",
        text: withoutFrontmatter,
      },
    },
  ];
}
HANDLER_EOF

  # Replace placeholders (escape special chars for sed)
  escaped_prompt_name=$(echo "${prompt_name}" | sed 's/[\/&]/\\&/g')
  escaped_description=$(echo "${description}" | sed 's/[\/&]/\\&/g')

  sed -i.bak \
    -e "s/SKILL_NAME_PLACEHOLDER/${skill_name}/g" \
    -e "s/PROMPT_NAME_PLACEHOLDER/${escaped_prompt_name}/g" \
    -e "s/DESCRIPTION_PLACEHOLDER/${escaped_description}/g" \
    "${handler_file}"

  rm "${handler_file}.bak"

  skill_count=$((skill_count + 1))
  skill_names+=("${prompt_name}")
  echo "  ✓ ${prompt_name}"

done < <(find "${SKILLS_DIR}" -mindepth 2 -maxdepth 2 -name "SKILL.md" -type f -print0)

echo ""
echo "✅ Generated ${skill_count} prompt handlers"
echo ""

# ---------------------------------------------------------------------------
# Phase 2: Build Enhanced Unified Server
# ---------------------------------------------------------------------------

echo "🔨 Phase 2: Building Enhanced Unified Server"
echo "─────────────────────────────────────────────────────────────────"

# Backup existing index.js
if [[ -f "index.js" ]]; then
  cp index.js "index.js.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Generate enhanced index.js
cat > index.js << 'EOF_INDEX'
#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  GetPromptRequestSchema,
  ListPromptsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Import tool handlers
import * as organizeMd from "./tools/organize_md.js";
import * as pdfToMd from "./tools/pdf_to_md.js";

const TOOL_HANDLERS = [organizeMd, pdfToMd];

// Dynamically import prompt handlers
const PROMPT_HANDLERS = [];
const promptsDir = path.join(__dirname, "prompts");
if (fs.existsSync(promptsDir)) {
  const promptFiles = fs.readdirSync(promptsDir).filter(f => f.endsWith('.js'));
  for (const file of promptFiles) {
    try {
      const module = await import(`./prompts/${file}`);
      PROMPT_HANDLERS.push(module);
    } catch (error) {
      console.error(`Warning: Failed to load prompt handler ${file}:`, error.message);
    }
  }
}

const server = new Server(
  {
    name: "thomaschangsf-skills-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
      prompts: {},
    },
  }
);

// List all tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  const allTools = TOOL_HANDLERS.flatMap(handler => handler.listTools());
  return { tools: allTools };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const toolName = request.params.name;

  for (const handler of TOOL_HANDLERS) {
    const handlerTools = handler.listTools().map(t => t.name);
    if (handlerTools.includes(toolName)) {
      return await handler.handleCall(request);
    }
  }

  return {
    content: [
      {
        type: "text",
        text: `Unknown tool: ${toolName}`,
      },
    ],
    isError: true,
  };
});

// List all prompts (skills)
server.setRequestHandler(ListPromptsRequestSchema, async () => {
  const allPrompts = PROMPT_HANDLERS.map(handler => handler.getPrompt());
  return { prompts: allPrompts };
});

// Get prompt messages (skill content)
server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  const promptName = request.params.name;

  for (const handler of PROMPT_HANDLERS) {
    const prompt = handler.getPrompt();
    if (prompt.name === promptName) {
      return {
        messages: handler.getPromptMessages(),
      };
    }
  }

  throw new Error(`Unknown prompt: ${promptName}`);
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);

  const toolCount = TOOL_HANDLERS.flatMap(h => h.listTools()).length;
  const promptCount = PROMPT_HANDLERS.length;

  console.error("thomaschangsf-skills MCP server running on stdio");
  console.error(`Available tools (${toolCount}): ${TOOL_HANDLERS.flatMap(h => h.listTools()).map(t => t.name).join(", ")}`);
  console.error(`Available prompts (${promptCount}): ${PROMPT_HANDLERS.map(h => h.getPrompt().name).join(", ")}`);
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
EOF_INDEX

chmod +x index.js

echo "✅ Enhanced unified MCP server built successfully"
echo ""

cd "${REPO_ROOT}"

# ---------------------------------------------------------------------------
# Phase 3: Configuration
# ---------------------------------------------------------------------------

echo "📋 Phase 3: Configuration"
echo "─────────────────────────────────────────────────────────────────"
echo ""
echo "Unified MCP server ready at:"
echo "  ${BUILD_DIR}/index.js"
echo ""
echo "Capabilities:"
echo "  • Tools (2): organize_markdown, convert_pdf_to_md"
echo "  • Prompts/Skills (${skill_count}): ${skill_names[*]}"
echo ""

if [[ "${AUTO_CONFIGURE}" == "true" ]]; then
  # ---------------------------------------------------------------------------
  # Auto-Configure Mode
  # ---------------------------------------------------------------------------

  echo "🔧 Auto-Configuration Mode"
  echo "─────────────────────────────────────────────────────────────────"
  echo ""

  # Check for jq
  if ! command -v jq &> /dev/null; then
    echo "❌ jq not found. Required for auto-configuration."
    echo ""
    echo "Install jq:"
    echo "  macOS: brew install jq"
    echo "  Linux: apt-get install jq"
    echo ""
    exit 1
  fi

  CLAUDE_SETTINGS="${HOME}/.claude/settings.json"
  CLAUDE_DESKTOP_CONFIG="${HOME}/Library/Application Support/Claude/claude_desktop_config.json"
  CURSOR_MCP="${HOME}/.cursor/mcp.json"

  configured_count=0

  # Configure Claude Code
  if [[ -f "${CLAUDE_SETTINGS}" ]]; then
    echo "Configuring Claude Code..."
    cp "${CLAUDE_SETTINGS}" "${CLAUDE_SETTINGS}.backup.$(date +%Y%m%d_%H%M%S)"

    jq --arg path "${BUILD_DIR}/index.js" \
      '.mcpServers."thomaschangsf-custom-skills" = {"command": "node", "args": [$path], "env": {}}' \
      "${CLAUDE_SETTINGS}" > "${CLAUDE_SETTINGS}.tmp"
    mv "${CLAUDE_SETTINGS}.tmp" "${CLAUDE_SETTINGS}"

    echo "  ✅ ${CLAUDE_SETTINGS}"
    configured_count=$((configured_count + 1))
  else
    echo "  ⊘ Claude Code settings not found"
  fi

  # Configure Claude Desktop
  claude_desktop_dir="$(dirname "${CLAUDE_DESKTOP_CONFIG}")"
  if [[ -d "${claude_desktop_dir}" ]]; then
    echo "Configuring Claude Desktop..."

    if [[ ! -f "${CLAUDE_DESKTOP_CONFIG}" ]]; then
      mkdir -p "${claude_desktop_dir}"
      echo '{"mcpServers":{}}' > "${CLAUDE_DESKTOP_CONFIG}"
    else
      cp "${CLAUDE_DESKTOP_CONFIG}" "${CLAUDE_DESKTOP_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    jq --arg path "${BUILD_DIR}/index.js" \
      '.mcpServers."thomaschangsf-custom-skills" = {"command": "node", "args": [$path]}' \
      "${CLAUDE_DESKTOP_CONFIG}" > "${CLAUDE_DESKTOP_CONFIG}.tmp"
    mv "${CLAUDE_DESKTOP_CONFIG}.tmp" "${CLAUDE_DESKTOP_CONFIG}"

    echo "  ✅ ${CLAUDE_DESKTOP_CONFIG}"
    configured_count=$((configured_count + 1))
  else
    echo "  ⊘ Claude Desktop not found"
  fi

  # Configure Cursor
  if [[ -d "$(dirname "${CURSOR_MCP}")" ]]; then
    echo "Configuring Cursor..."

    if [[ ! -f "${CURSOR_MCP}" ]]; then
      mkdir -p "$(dirname "${CURSOR_MCP}")"
      echo '{"mcpServers":{}}' > "${CURSOR_MCP}"
    else
      cp "${CURSOR_MCP}" "${CURSOR_MCP}.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    jq --arg path "${BUILD_DIR}/index.js" \
      '.mcpServers."thomaschangsf-custom-skills" = {"type": "stdio", "command": "node", "args": [$path]}' \
      "${CURSOR_MCP}" > "${CURSOR_MCP}.tmp"
    mv "${CURSOR_MCP}.tmp" "${CURSOR_MCP}"

    echo "  ✅ ${CURSOR_MCP}"
    configured_count=$((configured_count + 1))
  else
    echo "  ⊘ Cursor not found"
  fi

  echo ""
  echo "✅ Auto-configured ${configured_count} agent(s)"
  echo ""
  echo "📋 Next Steps:"
  echo ""
  if [[ -f "${CLAUDE_SETTINGS}" ]]; then
    echo "  • Claude Code: Restart or run /reload-plugins"
  fi
  if [[ -f "${CLAUDE_DESKTOP_CONFIG}" ]]; then
    echo "  • Claude Desktop: Restart application"
  fi
  if [[ -d "$(dirname "${CURSOR_MCP}")" ]]; then
    echo "  • Cursor: Cmd+Shift+P → Developer: Reload Window"
  fi
  echo ""
  echo "🔍 Backups created with timestamp if files existed"
  echo ""

else
  # ---------------------------------------------------------------------------
  # Manual Configuration Mode (Default)
  # ---------------------------------------------------------------------------

  echo "═══════════════════════════════════════════════════════════════"
  echo "  CONFIGURATION (Choose Your Agent)"
  echo "═══════════════════════════════════════════════════════════════"
  echo ""
  echo "Copy and paste the configuration for your agent:"
echo ""
echo "─────────────────────────────────────────────────────────────────"
echo "1️⃣  CLAUDE DESKTOP (PRIMARY USE CASE)"
echo "─────────────────────────────────────────────────────────────────"
echo ""
echo "File: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo ""
echo "Add or merge this into the mcpServers section:"
echo ""
cat << EOF_CONFIG
{
  "mcpServers": {
    "thomaschangsf-custom-skills": {
      "command": "node",
      "args": ["${BUILD_DIR}/index.js"]
    }
  }
}
EOF_CONFIG
echo ""
echo "Then: Restart Claude Desktop"
echo ""
echo "─────────────────────────────────────────────────────────────────"
echo "2️⃣  CLAUDE CODE (Alternative to traditional script)"
echo "─────────────────────────────────────────────────────────────────"
echo ""
echo "File: ~/.claude/settings.json"
echo ""
echo "Add or merge this into the mcpServers section:"
echo ""
cat << EOF_CONFIG
{
  "mcpServers": {
    "thomaschangsf-custom-skills": {
      "command": "node",
      "args": ["${BUILD_DIR}/index.js"],
      "env": {}
    }
  }
}
EOF_CONFIG
echo ""
echo "Then: Restart Claude Code or run /reload-plugins"
echo ""
echo "─────────────────────────────────────────────────────────────────"
echo "3️⃣  CURSOR (Alternative to traditional script)"
echo "─────────────────────────────────────────────────────────────────"
echo ""
echo "File: ~/.cursor/mcp.json"
echo ""
echo "Add or merge this into the mcpServers section:"
echo ""
cat << EOF_CONFIG
{
  "mcpServers": {
    "thomaschangsf-custom-skills": {
      "type": "stdio",
      "command": "node",
      "args": ["${BUILD_DIR}/index.js"]
    }
  }
}
EOF_CONFIG
echo ""
echo "Then: Cmd+Shift+P → Developer: Reload Window"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "✨ Benefits of MCP approach:"
echo "   • Claude Desktop: ONLY way to get skills (no directory support)"
echo "   • Claude Code/Cursor: Alternative to traditional directory copy"
echo "   • Single source of truth (always uses latest from repo)"
echo "   • All capabilities through one MCP server"
echo ""
echo "🔄 To use traditional approach instead (Claude Code/Cursor only):"
echo "   ./scripts/dev_refresh_skills_and_tools.sh"
echo ""
echo "💡 TIP: Use --auto-configure flag to automatically update config files:"
echo "   ./scripts/dev_refresh_skills_and_tools_for_claude_desktop.sh --auto-configure"
echo ""

fi  # End of AUTO_CONFIGURE if-else
