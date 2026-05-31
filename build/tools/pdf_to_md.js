import { execFileSync } from "child_process";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import fs from "fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export function listTools() {
  return [
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
  ];
}

export async function handleCall(request) {
  try {
    const args = request.params.arguments;
    const scriptPath = join(__dirname, "../../plugins/pdf_to_md/scripts/pdf2md.py");

    // Check if Python script exists
    if (!fs.existsSync(scriptPath)) {
      return {
        content: [
          {
            type: "text",
            text: `Error: Python script not found at ${scriptPath}. Please ensure pdf2md.py is in the plugins/pdf_to_md/scripts/ directory.`,
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

    // Execute Python script (using execFileSync to prevent command injection)
    const result = execFileSync("python3", cmdArgs, {
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
