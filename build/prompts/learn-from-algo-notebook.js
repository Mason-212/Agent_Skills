// Auto-generated prompt handler
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SKILL_NAME = "learn-from-algo-notebook";
const PROMPT_NAME = "learn-from-algo-notebook";
const DESCRIPTION = "Generate a Bloom's Taxonomy study guide from an algorithm Jupyter notebook";

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
