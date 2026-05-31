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
