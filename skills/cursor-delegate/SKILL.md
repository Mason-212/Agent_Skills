---
name: cursor-delegate
description: Delegate tasks to the Cursor agent CLI in headless mode
---

# Cursor Delegate

## When to Use
- The user asks you to delegate work to Cursor (e.g., "ask Cursor to...", "have Cursor...", "delegate to Cursor...")
- The user wants Cursor to review, fix, write, refactor, or analyze code
- The user explicitly requests a task be run through the Cursor agent
- The user wants a second opinion or parallel work stream from another AI agent

## Prerequisites
- The `cursor-agent` CLI must be installed. If it is not available on `$PATH`, instruct the user to install it: `curl -fsSL https://cursor.com/install | bash`
- Authentication: either `CURSOR_API_KEY` environment variable or prior `cursor-agent login`
- If authentication status is uncertain, verify with `cursor-agent status` before delegating

## Operating Procedure

1. **Parse the user's intent.** Distill the request into a clear, self-contained prompt for Cursor. Include relevant file paths, constraints, and any context Cursor will need to act independently. The prompt must be understandable without access to the current conversation history.

2. **Determine the working directory.** Always run `cursor-agent` from the current project workspace root so Cursor has full project context. Never run it from an unrelated directory.

3. **Preflight check (write tasks only).** Quickly inspect the repo state with `git status`. Proceed without asking unless something looks genuinely risky — for example, uncommitted changes in files that Cursor is about to modify, or a request so ambiguous that Cursor could cause unintended damage. A dirty worktree alone is not a reason to pause.

4. **Construct the command.** Build the command with the standard flags:
   ```bash
   cursor-agent -p --force --trust --model "gpt-5.4-high" "<prompt>"
   ```

5. **Execute the command.** Run the constructed command from the project working directory. Use a 10-minute (600 second) execution timeout — Cursor tasks can take several minutes depending on complexity. Do not interrupt or timeout prematurely.

6. **Report results.** Present a concise summary of what Cursor did:
   - Actions taken: files changed, commands run, analysis produced
   - Key findings or outputs
   - Any errors or warnings Cursor reported
   - For long outputs, summarize the key points and offer to show the full output if the user wants it
   - On failure (non-zero exit, auth error, model not found), report the error clearly and suggest remediation

## Default Configuration

| Setting | Value | Flag |
|---------|-------|------|
| Mode | Headless | `-p` |
| Commands & file writes | Auto-approve | `--force` |
| Workspace trust | Auto-trust | `--trust` |
| Model | GPT-5.4 1M High | `--model "gpt-5.4-high"` |
| Output format | Text | (default) |

If the user requests a different model, run `cursor-agent --list-models` to find the correct model ID and substitute it in the `--model` flag.

## Important Constraints
- Always run `cursor-agent` from the project working directory — never from an unrelated path
- Only use headless mode (`-p`) — never launch the interactive TUI
- Do not modify Cursor configuration files (`~/.cursor/`, `.cursor/`)
- If authentication fails, instruct the user to run `cursor-agent login` or set the `CURSOR_API_KEY` environment variable
- Report Cursor's full output — do not silently swallow errors or partial results
- If Cursor exits with a non-zero status, report the error and suggest next steps (e.g., re-auth, check model availability, retry)
- If Cursor modifies files outside the scope the user requested, flag this to the user
- Allowed commands: `cursor-agent` with its flags, `cursor-agent status`, `cursor-agent login`, `cursor-agent --list-models`

## Examples

**PR review:**
```bash
cursor-agent -p --force --trust --model "gpt-5.4-high" \
  "Review the changes on this branch for bugs, security issues, and code quality problems. Compare against the base branch."
```

**Bug fix:**
```bash
cursor-agent -p --force --trust --model "gpt-5.4-high" \
  "Fix the failing test in src/utils/parser.test.ts. Run the test suite to verify the fix."
```

**Code generation:**
```bash
cursor-agent -p --force --trust --model "gpt-5.4-high" \
  "Add input validation to the signup form in src/components/SignupForm.tsx. Validate email format, password strength, and required fields."
```

**Code explanation:**
```bash
cursor-agent -p --force --trust --model "gpt-5.4-high" \
  "Explain how the authentication middleware works in src/middleware/auth.ts. Trace the request flow from entry to token validation."
```
