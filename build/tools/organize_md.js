import { execFileSync } from "child_process";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import fs from "fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export function listTools() {
  return [
    {
      name: "organize_markdown",
      description: "Organize markdown files: move images to companion directories, add sequential numbers to top 2 heading levels. Creates '{filename}_images' directory, moves images there, updates references, and numbers headings (e.g., '# 1 Title', '## 1.1 Subtitle').",
      inputSchema: {
        type: "object",
        properties: {
          markdown_path: {
            type: "string",
            description: "Path to the markdown file to organize",
          },
          search_root: {
            type: "string",
            description: "Root directory to search for images. Optional, defaults to markdown directory and parent.",
          },
          normalize_names: {
            type: "boolean",
            description: "Whether to normalize image filenames (convert spaces to hyphens). Optional, defaults to true.",
          },
          add_numbers: {
            type: "boolean",
            description: "Whether to add sequential numeric prefixes to top 2 heading levels. Optional, defaults to true.",
          },
          dry_run: {
            type: "boolean",
            description: "Preview changes without modifying files. Optional, defaults to false.",
          },
        },
        required: ["markdown_path"],
      },
    },
  ];
}

export async function handleCall(request) {
  try {
    const args = request.params.arguments;
    const scriptPath = join(__dirname, "../../plugins/organize_md/scripts/organize_images.py");

    // Check if Python script exists
    if (!fs.existsSync(scriptPath)) {
      return {
        content: [
          {
            type: "text",
            text: `Error: Python script not found at ${scriptPath}. Please ensure organize_images.py is in the plugins/organize_md/scripts/ directory.`,
          },
        ],
        isError: true,
      };
    }

    // Build command arguments
    const cmdArgs = [scriptPath, args.markdown_path];

    if (args.search_root) {
      cmdArgs.push("--search-root", args.search_root);
    }

    if (args.normalize_names === false) {
      cmdArgs.push("--no-normalize");
    }

    if (args.add_numbers === false) {
      cmdArgs.push("--no-numbers");
    }

    if (args.dry_run) {
      cmdArgs.push("--dry-run");
    }

    // Execute Python script (using execFileSync to prevent command injection)
    const result = execFileSync("python3", cmdArgs, {
      encoding: "utf-8",
      maxBuffer: 10 * 1024 * 1024, // 10MB buffer
    });

    return {
      content: [
        {
          type: "text",
          text: result || "Markdown organization completed successfully.",
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `Error organizing markdown: ${error.message}\n\nStderr: ${error.stderr || "N/A"}`,
        },
      ],
      isError: true,
    };
  }
}
