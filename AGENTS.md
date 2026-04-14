# Skills Repository

This repo contains shared agent skills installed via the `skills` CLI.

## Skill Format

Each skill lives in its own directory under `skills/`. The directory must contain a `SKILL.md` file.

### SKILL.md Structure

```markdown
---
name: skill-name
description: One-line summary of what the skill does
---

# Skill Name

Instructions for the agent follow here.
```

- **Frontmatter** (YAML between `---` fences) is required. It must include `name` and `description`.
- **Body** contains the actual instructions the agent will follow when the skill is active.

### Directory Layout

```
skills/
  my-skill/
    SKILL.md              # Required - skill definition
    resources/            # Optional - helper scripts, templates, reference files
      helper.sh
```

## Conventions

- Directory names: **kebab-case** (e.g., `code-review`, `deploy-helper`)
- The skill definition file must be named **`SKILL.md`** (uppercase)
- Prefix internal/template skills with `_` (e.g., `_template`)
- Keep `description` in frontmatter under 100 characters
- Write skill instructions as clear, actionable steps the agent can follow
- Use `resources/` for any supporting files the skill references

## Writing Good Skills

- Start with a "When to use" section so the agent knows when to activate the skill
- Be specific and imperative in instructions — tell the agent exactly what to do
- Include examples of expected input/output when helpful
- Keep skills focused on a single task or workflow
