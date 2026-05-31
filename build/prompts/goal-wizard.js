// Auto-generated prompt handler
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SKILL_NAME = "goal-wizard";
const PROMPT_NAME = "goal-wizard";
const DESCRIPTION = "Interactive wizard for /goal - guides setup with verification strategies and safety guardrails";

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
