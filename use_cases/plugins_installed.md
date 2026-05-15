## 1 Claude Plugins

All installed plugins can be found at: `~/.claude/plugins/cache/claude-plugins-official/`

### 1.1 pr-review-toolkit
    - see use_cases/pr_review.md

### 1.2 superpowers
A 7 step TDD developer workflow

| Phase | Command / Action | What Happens |
|-------|------------------|--------------|
| 1. Brainstorm | `/superpowers:brainstorm` | Claude asks Socratic questions about your goal, explores edge cases, and creates a Design Doc. It won't code until you sign this off. |
| 2. Planning | `/superpowers:write-plan` | It breaks the design into 2–5 minute tasks. Each task includes exact file paths, full code snippets, and verification steps. |
| 3. Git Worktree | Automatic | It creates an isolated workspace on a new branch. This prevents "messy" sessions and allows you to run multiple experiments in parallel. |
| 4. TDD (The Iron Law) | Enforced | RED-GREEN-REFACTOR: Claude must write a failing test first. If it writes production code before a test, the framework is designed to delete the code and force it to start with the test. |
| 5. Subagents | `/superpowers:execute-plan` | For each task, Claude spawns a "fresh" subagent. This prevents the "context drift" that happens in long chat sessions where the AI gets confused. |
| 6. Code Review | Automatic | Two-stage review: one agent checks if the code matches the plan (Spec Compliance), another checks for quality/security. |
| 7. Finalization | `/superpowers:finish-branch` | Verifies all tests one last time, then offers to Merge, PR, or discard the worktree. |

### 1.3 frontend-design
The frontend-design plugin is the aesthetic counterpart to the Superpowers plugin. While Superpowers focuses on engineering discipline (tests, plans, and logic), frontend-design focuses on visual quality and stopping "AI slop."

| Command | What it does |
|---------|--------------|
| `/frontend-design` | Starts a Guided Workflow. Claude will ask you about the "vibe" (e.g., Brutalist, Minimalist, Enterprise) before writing any CSS. |
| `/ui` | Generates a component with Design System Awareness. It checks your existing tailwind/CSS files to ensure the new component matches your project's colors and spacing. |
| `/layout` | Specifically handles Responsive Architecture. Instead of just making things "stack," it plans complex grid behaviors for mobile vs. desktop. |
| `/design` | "Quick Design Mode"—useful for when you have the logic done but want Claude to "make it look pretty" without changing the underlying code. |

### 1.4 skill-creator
The skill-creator plugin enables you to create, modify, improve, and evaluate agent skills with an iterative development workflow.

#### How to Run It
```bash
/skill-creator
```

#### What It Does
The skill-creator guides you through an iterative skill development lifecycle:

1. **Capture Intent** - Understand what the skill should do and when it should trigger
2. **Draft the Skill** - Create SKILL.md with proper frontmatter (name, description) and instructions
3. **Create Test Cases** - Generate realistic test prompts that users would actually say
4. **Run Evaluations** - Execute test cases with and without the skill (baseline comparison)
5. **Review Results** - Use the visual evaluation viewer to see outputs and provide feedback
6. **Iterate & Improve** - Refine the skill based on feedback and quantitative metrics
7. **Optimize Description** - Improve the skill's triggering accuracy through automated testing
8. **Package & Present** - Create a distributable .skill file

#### Key Features

| Feature | Description |
|---------|-------------|
| **Iterative Testing** | Run test cases with skill vs baseline (without skill or previous version) |
| **Visual Evaluation Viewer** | Web-based interface to review outputs, provide feedback, and compare iterations |
| **Quantitative Benchmarking** | Track pass rates, timing, and token usage across iterations |
| **Assertion-Based Grading** | Define objective checks (file existence, content validation, format compliance) |
| **Description Optimization** | Automated loop to improve skill triggering accuracy with should/shouldn't-trigger test queries |
| **Blind Comparison** | Advanced A/B testing for rigorous version comparison |

#### How It Evaluates Skill Quality

**Qualitative Evaluation:**
- User reviews actual outputs in the evaluation viewer
- Provides feedback on each test case (what worked, what didn't)
- Compares current iteration against previous iterations
- Focuses on real-world usability and output quality

**Quantitative Evaluation:**
- **Assertions**: Objective checks (e.g., "output.pdf exists", "contains required sections")
- **Pass Rate**: Percentage of assertions that passed across all test cases
- **Timing**: Duration and token usage (mean ± stddev) compared to baseline
- **Non-discriminating Checks**: Identifies assertions that always pass (not useful)
- **Variance Analysis**: Detects flaky tests or inconsistent behavior

**Triggering Accuracy:**
- Tests whether skill triggers on queries it should (true positives)
- Tests whether skill doesn't trigger on queries it shouldn't (true negatives)
- Iteratively optimizes the description field to maximize triggering accuracy
- Uses 60% train / 40% held-out test split to avoid overfitting

#### Workflow Example
```bash
# Start skill creation
/skill-creator

# Claude asks: What should this skill do? When should it trigger?
# You describe the intent and requirements

# Claude drafts SKILL.md, creates test cases, and spawns evaluation runs
# While tests run, Claude drafts quantitative assertions

# Evaluation viewer opens in browser with:
#   - Outputs tab: Review each test case, provide feedback
#   - Benchmark tab: View pass rates, timing, token usage

# You review outputs and provide feedback
# Claude improves the skill based on your feedback

# Process repeats until you're satisfied
# Claude offers to optimize the description for better triggering
# Claude packages the final .skill file for distribution
```

#### When to Use skill-creator

**Creating New Skills:**
- You have a workflow you want to capture as a reusable skill
- You need a specialized skill for a domain-specific task
- You want to encode best practices or patterns

**Improving Existing Skills:**
- A skill isn't triggering when it should
- A skill produces inconsistent or incorrect outputs
- You want to optimize performance (time, tokens)
- You need to add new capabilities to an existing skill

**Quality Assurance:**
- Validate that a skill works across different scenarios
- Compare different approaches or implementations
- Ensure skill improvements don't introduce regressions

---

### 1.5 plugin-dev
A comprehensive toolkit for developing Claude Code plugins with expert guidance on all plugin components.

#### How to Run It
```bash
/plugin-dev:create-plugin [optional description]
```

#### What It Does
The plugin-dev toolkit provides **7 specialized skills** for building high-quality Claude Code plugins:

| Skill | Purpose | Key Features |
|-------|---------|--------------|
| **plugin-structure** | Plugin organization and manifest | Directory layout, plugin.json, auto-discovery, ${CLAUDE_PLUGIN_ROOT} |
| **command-development** | Create slash commands | Frontmatter, arguments, bash execution, namespacing |
| **skill-development** | Create skills for plugins | Progressive disclosure, strong triggers, bundled resources |
| **agent-development** | Create autonomous agents | Frontmatter, system prompts, AI-assisted generation, triggering |
| **hook-development** | Event-driven automation | All hook events, prompt/command hooks, security validation |
| **mcp-integration** | Model Context Protocol servers | stdio/SSE/HTTP/WebSocket, authentication, tool usage |
| **plugin-settings** | Plugin configuration | .local.md files, YAML frontmatter, per-project settings |

#### The Guided Workflow: /plugin-dev:create-plugin

An end-to-end workflow command for creating plugins from scratch with an **8-phase process**:

1. **Discovery** - Understand plugin purpose and requirements
2. **Component Planning** - Determine needed skills, commands, agents, hooks, MCP
3. **Detailed Design** - Specify each component and resolve ambiguities
4. **Structure Creation** - Set up directories and manifest
5. **Component Implementation** - Create each component using AI-assisted agents
6. **Validation** - Run plugin-validator and component-specific checks
7. **Testing** - Verify plugin works in Claude Code
8. **Documentation** - Finalize README and prepare for distribution

#### Key Resources

**Utility Scripts:**
- `validate-hook-schema.sh` - Validate hooks.json structure
- `test-hook.sh` - Test hooks before deployment
- `hook-linter.sh` - Lint hook scripts for best practices
- `validate-agent.sh` - Validate agent files
- `parse-frontmatter.sh` - Parse YAML frontmatter from settings

**Working Examples:**
- 3 complete hook scripts (bash validation, write validation, context loading)
- 3 MCP server configurations (stdio, SSE, HTTP)
- 3 plugin layouts (minimal, standard, advanced)
- 3 settings examples (read-settings hook, create-settings command, templates)
- 10 complete command examples
- 4 production-ready agent examples

**Documentation:**
- ~11,000 words across 7 core skills
- ~10,000+ words of detailed reference guides
- Progressive disclosure (metadata → core → references)

#### When to Use plugin-dev

**Creating New Plugins:**
- Building a plugin from scratch with the guided workflow
- Need expert guidance on plugin architecture
- Want to follow Claude Code best practices

**Adding Components:**
- "Create a slash command for X" → command-development
- "Add a skill that does Y" → skill-development
- "Create an agent for Z" → agent-development
- "Add a hook to validate writes" → hook-development
- "Integrate database via MCP" → mcp-integration

**Plugin Configuration:**
- "How do I structure my plugin?" → plugin-structure
- "Store user preferences" → plugin-settings
- "Make my plugin configurable" → plugin-settings

#### Example Workflows

**Building a Database Plugin:**
```bash
# Get structure guidance
"What's the structure for a plugin with MCP integration?"

# Configure MCP server
"How do I configure an stdio MCP server for PostgreSQL?"

# Add cleanup automation
"Add a Stop hook to ensure connections close properly"
```

**Creating a Validation Plugin:**
```bash
# Create validation hooks
"Create hooks that validate all file writes for security"

# Test hooks
./validate-hook-schema.sh hooks/hooks.json
./test-hook.sh my-hook.sh test-input.json

# Organize plugin
"Organize my hooks and configuration files"
```

---

### 1.6 security-guidance
A security reminder hook that warns about potential security issues when editing files.

#### What It Does
Automatically detects and warns about security vulnerabilities and unsafe code patterns during file edits, including:

**Security Patterns Detected:**
- **GitHub Actions Workflow Injection** - Command injection in `.github/workflows/*.yml` files
- **Child Process Exec** - Unsafe `child_process.exec()` usage (recommends `execFile`)
- **eval() Injection** - Arbitrary code execution via `eval()`
- **new Function() Injection** - Code injection via dynamic function creation
- **XSS Vulnerabilities** - Cross-site scripting patterns
- **SQL Injection** - Unsafe database queries
- **Path Traversal** - Directory traversal vulnerabilities
- **Hardcoded Credentials** - API keys, passwords, tokens in code

#### How It Works
This is a **hook plugin** (not a command or skill):
- Automatically triggers during file edit operations
- Runs in the background via `security_reminder_hook.py`
- Provides contextual security warnings based on file path and content
- Uses pattern matching to detect common vulnerability patterns

#### Example Warnings

**GitHub Actions:**
```
⚠️ You are editing a GitHub Actions workflow file. Be aware of:
1. Command Injection: Never use untrusted input directly in run: commands
2. Use environment variables instead of ${{ github.event.issue.title }}
3. Review: https://github.blog/security/vulnerability-research/...
```

**Child Process Execution:**
```
⚠️ Security Warning: Using child_process.exec() can lead to command injection.
Use execFileNoThrow utility instead for safe command execution.
```

#### When It Triggers
Automatically during file edits when:
- Editing GitHub Actions workflow files (`.github/workflows/`)
- Code contains risky patterns (`exec(`, `eval(`, `new Function`)
- Detecting potential XSS, SQL injection, or path traversal
- Finding hardcoded credentials or secrets

#### Configuration
No manual invocation needed - this is a **background security hook** that protects your code automatically.

Logs security warnings to: `/tmp/security-warnings-log.txt`

---

### 1.7 code-review
Code review plugin for analyzing code quality, adherence to guidelines, and best practices.

**Status:** Installed but not yet documented. See plugin at `~/.claude/plugins/cache/claude-plugins-official/code-review/`

---

### 1.8 code-simplifier
Code simplification plugin for improving clarity, consistency, and maintainability.

**Status:** Installed but not yet documented. See plugin at `~/.claude/plugins/cache/claude-plugins-official/code-simplifier/`

---

### 1.9 pyright-lsp
Python language server integration using Pyright for type checking and IntelliSense.

**Status:** Installed but not yet documented. See plugin at `~/.claude/plugins/cache/claude-plugins-official/pyright-lsp/`