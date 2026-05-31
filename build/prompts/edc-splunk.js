// Auto-generated prompt handler
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SKILL_NAME = "edc-splunk";
const PROMPT_NAME = "edc-splunk";
const DESCRIPTION = "Write, refine, and explain Splunk SPL using this repository's knowledge base of indexes, services, fields, example queries, and reference outputs. Use when the user asks for a Splunk query, wants help debugging filters or stats, or needs help interpreting Splunk results for documented services.";

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
