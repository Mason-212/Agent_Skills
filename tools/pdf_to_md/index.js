#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { execSync } from "child_process";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import fs from "fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const server = new Server(
  {
    name: "pdf-to-md-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Register the convert_pdf_to_md tool
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "convert_pdf_to_md",
      description: "Convert PDF to Markdown with table extraction and diagram reconstruction",
      inputSchema: {
        type: "object",
        properties: {
          pdf_path: {
            type: "string",
            description: "Path to the PDF file to convert",
          },
          output_path: {
            type: "string",
            description: "Output path for the Markdown file (optional, defaults to input name with .md extension)",
          },
          extract_assets: {
            type: "string",
            description: "Directory path for extracted assets (tables, figures). Optional.",
          },
          pages: {
            type: "string",
            description: "Page range to convert, e.g., '1-3,7'. Optional, processes all pages if not specified.",
          },
          use_ocr: {
            type: "boolean",
            description: "Force OCR for scanned PDFs. Optional, auto-detects if not specified.",
          },
          use_llm: {
            type: "boolean",
            description: "Use local vision model for diagram reconstruction. Optional.",
          },
          use_api: {
            type: "boolean",
            description: "Use hosted vision model API for diagram reconstruction. Optional.",
          },
          table_format: {
            type: "string",
            enum: ["pipe", "csv"],
            description: "Output format for tables: 'pipe' (Markdown) or 'csv'. Optional, defaults to 'pipe'.",
          },
        },
        required: ["pdf_path"],
      },
    },
  ],
}));

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "convert_pdf_to_md") {
    try {
      const args = request.params.arguments;
      const scriptPath = join(__dirname, "scripts", "pdf2md.py");

      // Check if Python script exists
      if (!fs.existsSync(scriptPath)) {
        return {
          content: [
            {
              type: "text",
              text: `Error: Python script not found at ${scriptPath}. Please ensure pdf2md.py is in the scripts/ directory.`,
            },
          ],
          isError: true,
        };
      }

      // Build command arguments
      const cmdArgs = [scriptPath, args.pdf_path];

      if (args.output_path) {
        cmdArgs.push("-o", args.output_path);
      }

      if (args.extract_assets) {
        cmdArgs.push("--extract-assets", args.extract_assets);
      }

      if (args.pages) {
        cmdArgs.push("--pages", args.pages);
      }

      if (args.use_ocr) {
        cmdArgs.push("--use-ocr");
      }

      if (args.use_llm) {
        cmdArgs.push("--use-llm");
      }

      if (args.use_api) {
        cmdArgs.push("--use-api");
      }

      if (args.table_format) {
        cmdArgs.push("--table-format", args.table_format);
      }

      // Execute Python script
      const result = execSync(`python3 ${cmdArgs.join(" ")}`, {
        encoding: "utf-8",
        maxBuffer: 10 * 1024 * 1024, // 10MB buffer for large outputs
      });

      return {
        content: [
          {
            type: "text",
            text: result || "PDF conversion completed successfully.",
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error converting PDF: ${error.message}\n\nStderr: ${error.stderr || "N/A"}`,
          },
        ],
        isError: true,
      };
    }
  }

  return {
    content: [
      {
        type: "text",
        text: `Unknown tool: ${request.params.name}`,
      },
    ],
    isError: true,
  };
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("PDF to Markdown MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error in main():", error);
  process.exit(1);
});
