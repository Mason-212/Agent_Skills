# PR Review Workflows

This guide shows how to use different skills and plugins for code review at various quality bars.

## Review Tools Comparison

| Tool | Bar | Use Case | Requires Local Checkout |
|------|-----|----------|------------------------|
| **pr-review-remote** | Correctness & Safety | "Is this safe to merge?" | ❌ No - works with remote URLs |
| **git-review** | Correctness & Safety | Same as pr-review-remote for local branches | ✅ Yes - local git directory |
| **pr-review-toolkit** | Quality & Improvement | "Can we make this better?" | ✅ Yes - analyzes local changes |
| **critique-me** | Architecture & Design | "Is the design sound?" | ✅ Yes - analyzes local files/specs |

## Understanding Tools vs Plugins

### Native Claude Tools (NOT Extensible)
- `Bash`, `Read`, `Edit`, `Write`, `Agent`
- Built into Claude Code
- Fixed functionality

### How to Extend Claude
**MCP Plugins** add new tools to Claude:
- Plugins contain: agents, MCP servers, commands (invocable via `/`)
- Once enabled, plugin tools become indistinguishable from native tools
- Example: `pr-review-toolkit` plugin adds quality analysis tools

```
Claude's capabilities = Native Tools + MCP Plugin Tools
```

---

## Workflow 1: Quality Review with Local Checkout

**Goal**: Deep quality analysis - tests, types, simplification, error handling

**Prerequisites**: PR checked out locally

### Step 1: Checkout PR Locally

```bash
# Navigate to review directory
cdgReview

# Checkout PR to local directory
gu pr_review_v2 <REMOTE-PR-URL>

# Start Claude Code
claude
```

### Step 2: Verify Local Changes

```
You: "How many files do you see in this pull request?"
Claude: [Lists changed files from git diff]
```

### Step 3: Install PR Review Toolkit Plugin

The `pr-review-toolkit` is an MCP plugin that adds specialized review agents.

```bash
# Browse and install plugins
/plugin

# Reload plugins after installation
/reload-plugins
```

### Step 4: Run Quality Reviews

The toolkit provides specialized review agents for different quality dimensions:

```bash
# Run all reviews in parallel (recommended)
/pr-review-toolkit:review-pr all parallel

# Or run specific reviews
/pr-review-toolkit:review-pr tests
/pr-review-toolkit:review-pr errors
/pr-review-toolkit:review-pr types
/pr-review-toolkit:review-pr simplify
```

### Review Agents & Scopes

The `pr-review-toolkit` plugin includes these specialized agents:

| Agent | Focus Area | Default Scope | Fallback |
|-------|-----------|---------------|----------|
| **code-reviewer** | General code quality | git diff (unstaged) | Files specified in prompt |
| **pr-test-analyzer** | Test coverage & quality | PR diff or git diff | Test files in changes |
| **silent-failure-hunter** | Error handling gaps | Recent changes | Files with error handling |
| **comment-analyzer** | Documentation quality | Modified files | Files with comments |
| **type-design-analyzer** | Type system design | New/modified types | Files with type definitions |
| **code-simplifier** | Code complexity | Recently touched code | Current session edits |

### Step 5: Use Correctness Review (Same Bar as Remote)

For merge-safety checks on your local branch (same bar as `pr-review-remote`):

```bash
/git-review
```

This checks for:
- Bugs and logical errors
- Security vulnerabilities
- Breaking changes and regressions

### Step 6: Use Design/Architecture Review

For high-level architectural validation:

```bash
# Review with specific rubrics
/critique-me Rubrics: 1,2,3 @docs/design.md

# Review with all rubrics
/critique-me Rubrics: 6 @docs/design.md
```

**Available Rubrics**:
1. **Anti-AI-slop** - Detect superficial or low-quality AI-generated patterns
2. **Blind-spots** - Identify missing edge cases and assumptions
3. **Stress-test-decisions** - Challenge architectural choices
4. **Code-quality** - General code quality assessment
5. **ML-design** - Machine learning system design patterns
6. **Everything** - Run all rubrics (1-5)

---

## Workflow 2: Remote Review (No Local Checkout)

**Goal**: Quick correctness & safety check without cloning

**Prerequisites**: Just a PR URL

### Use Case: Merge Safety Check

Check if a PR is safe to merge without checking it out locally:

```bash
/pr-review-remote https://github.com/org/repo/pull/123
```

**What it checks**:
- ✅ Bugs and logical errors
- ✅ Security vulnerabilities
- ✅ Breaking changes
- ✅ Regression risks
- ✅ API contract violations

**What it DOES NOT check** (requires local checkout):
- ❌ Test quality and coverage depth
- ❌ Type system design
- ❌ Code simplification opportunities
- ❌ Silent error handling gaps

---

## Complete Example Session

### Scenario: Review PR for Quality Before Merge

```bash
# 1. Checkout PR locally
cdgReview
gu pr_review_v2 https://git.soma.salesforce.com/a360/edc-python/pull/769
claude

# 2. Verify files
You: "How many files changed in this PR?"
Claude: "Found 12 files changed: 8 Python files, 3 test files, 1 config"

# 3. Install toolkit (first time only)
/plugin
# Select and install pr-review-toolkit
/reload-plugins

# 4. Run comprehensive quality review
/pr-review-toolkit:review-pr all parallel

# Claude spawns multiple agents in parallel:
# - code-reviewer: Analyzes code patterns
# - pr-test-analyzer: Reviews test coverage
# - silent-failure-hunter: Checks error handling
# - comment-analyzer: Reviews documentation
# - type-design-analyzer: Reviews type design
# - code-simplifier: Suggests simplifications

# 5. Check merge safety (correctness bar)
/git-review

# 6. Review architectural decisions
/critique-me Rubrics: 2,3 @docs/design.md

# 7. Make improvements based on feedback
# [Edit code based on review findings]

# 8. Final safety check
/git-review
```

---

## Decision Tree: Which Tool to Use?

```
Need to review code?
│
├─ Don't have PR checked out locally?
│  └─→ Use: /pr-review-remote <URL>
│      Bar: Correctness & Safety
│
├─ Have PR checked out locally?
│  │
│  ├─ Just checking merge safety?
│  │  └─→ Use: /git-review
│  │      Bar: Correctness & Safety (same as pr-review-remote)
│  │
│  ├─ Want quality improvements?
│  │  └─→ Use: /pr-review-toolkit:review-pr all parallel
│  │      Bar: Quality (tests, types, simplification, error handling)
│  │
│  └─ Reviewing architecture/design?
│     └─→ Use: /critique-me Rubrics: 1,2,3 @design-doc.md
│         Bar: Architecture & Design
│
└─ Want everything?
   └─→ Run all three:
       1. /pr-review-toolkit:review-pr all parallel (quality)
       2. /git-review (safety)
       3. /critique-me (architecture)
```

---

## Comparison: Skills vs Plugins

### Skills (Prompt-Based)
- `pr-review-remote` - Skill that orchestrates remote PR review
- `git-review` - Skill that orchestrates local git review
- `critique-me` - Skill that applies rubric-based critique

**How they work**: Load instructions into Claude's context to guide review workflow

### Plugins (MCP Servers)
- `pr-review-toolkit` - Plugin that provides specialized review agents
- Each agent is a tool that Claude can call directly

**How they work**: External MCP servers that Claude calls like native tools

### When to Use Each

**Use Skills when**:
- You want guided workflows with human judgment
- The task requires orchestration of multiple steps
- Flexibility and adaptation are important

**Use Plugins when**:
- You want specialized, atomic operations
- Performance is critical
- You want parallel agent execution
- The operation is well-defined and repeatable

---

## Tips & Best Practices

### 1. Combine Tools for Complete Coverage

```bash
# Quality → Safety → Architecture
/pr-review-toolkit:review-pr all parallel
/git-review
/critique-me Rubrics: 6 @design.md
```

### 2. Use Parallel Execution for Speed

```bash
# All quality checks run concurrently
/pr-review-toolkit:review-pr all parallel
```

### 3. Focus Reviews with Specific Agents

```bash
# Just test coverage
/pr-review-toolkit:review-pr tests

# Just error handling
/pr-review-toolkit:review-pr errors
```

### 4. Use Remote Review for Quick Checks

```bash
# No clone needed - great for quick safety checks
/pr-review-remote https://github.com/org/repo/pull/123
```

### 5. Use Critique for Design Docs

```bash
# Before implementation - validate design
/critique-me Rubrics: 2,3 @docs/design.md

# After implementation - validate architecture
/critique-me Rubrics: 6 @src/
```

---

## Common Questions

**Q: Can I use pr-review-toolkit without local checkout?**  
A: No, it requires local files to analyze. Use `/pr-review-remote` for remote review.

**Q: What's the difference between git-review and pr-review-remote?**  
A: Same correctness bar, but `git-review` works on local branches, `pr-review-remote` works with remote URLs.

**Q: Should I run all reviews every time?**  
A: For important PRs: yes. For minor changes: just `/pr-review-remote` or `/git-review`.

**Q: How do I install plugins?**  
A: Use `/plugin` command in Claude Code to browse and install.

**Q: Can I create my own review plugin?**  
A: Yes! See `plugins/` directory for examples. Plugins are MCP servers with specialized agents.

---

## Related Documentation

- **Skills**: `skills/pr-review-remote/`, `skills/git-review/`, `skills/critique-me/`
- **Plugins**: `plugins/` (MCP server examples)
- **Architecture**: `ARCHITECTURE.md` (Skills vs Plugins design)
- **Installation**: `scripts/dev_refresh_skills_and_tools.sh`
