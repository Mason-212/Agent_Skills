# Skills vs Plugins: Architecture & Usage Guide

Understanding when to use skills (prompt-based orchestration) versus plugins (MCP servers with external execution).

---

## Core Differences

| Aspect | Skills | Plugins |
|--------|--------|---------|
| **Context Access** | Full conversation, files, preferences, session state | Only explicit parameters |
| **Injection** | Full content → Claude's prompt | Schema only → Claude's prompt |
| **Execution** | Claude orchestrates native tools | External process executes |
| **Separation** | No separation (in Claude's context) | True separation (external process) |
| **Determinism** | Non-deterministic (context-dependent) | Can be deterministic (parameter-only) |
| **Parallelization** | Limited (shared context) | Excellent (isolated execution) |
| **Performance** | Depends on orchestration complexity | Fast atomic operations |
| **Development** | Write Markdown (SKILL.md) | Write Node.js MCP server |
| **State** | Stateless (reloaded each time) | Can maintain state in server process |
| **Best For** | Context-dependent tasks | Context-independent tasks |

---

## How They Work

### Skills: Prompt Injection

```
┌─────────────────────────────────────┐
│       Claude's Context              │
│                                     │
│  [Native Tools]                     │
│  - Read, Write, Edit, Bash          │
│                                     │
│  [Injected Skill Content]           │
│  ┌───────────────────────────────┐ │
│  │ # Convert PDF to Markdown     │ │
│  │                               │ │
│  │ ## When to Use                │ │
│  │ - User asks to convert PDF... │ │
│  │                               │ │
│  │ ## Operating Procedure        │ │
│  │ 1. Read PDF file              │ │
│  │ 2. Extract text...            │ │
│  │ 3. Format as Markdown...      │ │
│  └───────────────────────────────┘ │
│                                     │
│  Claude reads instructions and      │
│  orchestrates: Read → Bash → Write  │
└─────────────────────────────────────┘
```

**What's in Claude's prompt**:
- ✅ Complete SKILL.md content (instructions, workflow, examples)
- ✅ All text from the skill file

**Execution**:
- Claude follows the instructions
- Orchestrates native tools step-by-step
- Makes decisions based on context

### Plugins: External MCP Servers

```
┌─────────────────────────────────────┐
│       Claude's Context              │
│                                     │
│  [Native Tools]                     │
│  - Read, Write, Edit, Bash          │
│                                     │
│  [Plugin Tool Schema]               │
│  ┌───────────────────────────────┐ │
│  │ Tool: convert_pdf_to_md       │ │
│  │ Description: Convert PDF...   │ │
│  │ Parameters:                   │ │
│  │   - pdf_path: string          │ │
│  │   - output_path: string       │ │
│  └───────────────────────────────┘ │
│                                     │
│  Claude calls tool when appropriate │
└─────────────────────────────────────┘
                  │
                  │ stdio communication
                  ▼
┌─────────────────────────────────────┐
│    MCP Server (External Process)    │
│                                     │
│  plugins/pdf_to_md/index.js         │
│  ┌───────────────────────────────┐ │
│  │ Handle tool call:             │ │
│  │   - Receive parameters        │ │
│  │   - Execute Python script     │ │
│  │   - Process PDF file          │ │
│  │   - Return result             │ │
│  └───────────────────────────────┘ │
│                                     │
│  Implementation hidden from Claude  │
└─────────────────────────────────────┘
```

**What's in Claude's prompt**:
- ✅ Tool name: `convert_pdf_to_md`
- ✅ Tool description: "Convert PDF to Markdown..."
- ✅ Parameter schema: `{pdf_path: string, output_path: string, ...}`
- ❌ NOT the implementation (Python script, file I/O, logic)

**Execution**:
- Claude decides when to call the tool
- MCP server executes independently
- Returns result to Claude

---

## Point-by-Point Analysis

### 1. Skills are Good for Workflow Orchestration ✅ CORRECT

**Why**: Skills inject complete instructions into Claude's context at runtime.

**Example**: `skills/convert-pdf-to-md/SKILL.md`
```markdown
## Operating Procedure

### 1) Decide the policy
- Default: local/offline libraries only
- If user allows: enable opt-in paths

### 2) Identify PDF type
- Digital-text PDF: text extraction first
- Scanned PDF: OCR first

### 3) Extract content...
```

Claude reads this and orchestrates the workflow step-by-step, making decisions based on context (Is it scanned? Does user allow network calls?).

**Characteristics**:
- 🎯 Guided decision-making
- 🔄 Flexible adaptation to context
- 📝 Human-readable workflow
- 🧠 Claude's intelligence applied at each step

### 2. Plugins Provide Separation of Concern ⚠️ PARTIALLY CORRECT

**Original claim**: "appended to prompt at run time"

**Correction**: Only the **tool schema** is appended to the prompt, not the implementation.

**What this means**:

```python
# Claude's prompt contains this:
Tool: convert_pdf_to_md
Parameters:
  - pdf_path: string (Path to PDF file)
  - output_path: string (Output markdown path)

# Claude's prompt DOES NOT contain this:
execSync(`python3 ${scriptPath} ${pdf_path} -o ${output_path}`)
fs.readFileSync(...)
# etc.
```

**True separation**:
- **Interface** (tool schema) visible to Claude
- **Implementation** (Python script, file I/O) hidden in MCP server
- **Communication** via stdio (structured messages)

This is similar to:
```typescript
// Claude sees the interface
interface PdfConverter {
  convert_pdf_to_md(pdf_path: string, output_path: string): Promise<string>
}

// Implementation runs in external process
class PdfToMdServer implements PdfConverter {
  // Claude never sees this code
  async convert_pdf_to_md(pdf_path, output_path) {
    const result = execSync(`python3 pdf2md.py ${pdf_path}`)
    return result
  }
}
```

**Benefits of this separation**:
- 🔒 **Security**: Implementation code not in Claude's context
- 🚀 **Performance**: Native code execution (Python, Node.js, binaries)
- 📦 **Encapsulation**: Changes to implementation don't require prompt updates
- 🔧 **Specialized Logic**: Use any language/library in the server

### 3. Plugins Can Be Deterministic or Non-Deterministic ✅ CORRECT

**Deterministic Plugin Example**: `pdf_to_md`
```javascript
// Always returns same output for same input
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const result = execSync(`python3 pdf2md.py ${args.pdf_path}`)
  return { content: [{ type: "text", text: result }] }
})
```
Given the same PDF, produces the same Markdown (deterministic).

**Non-Deterministic Plugin Example**: Hypothetical `code-reviewer-mcp`
```javascript
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  // Plugin spawns Claude agent internally
  const agent = new ClaudeAgent()
  const review = await agent.reviewCode(args.code_path)
  return { content: [{ type: "text", text: review }] }
})
```
Different reviews each time due to LLM variance (non-deterministic).

**Key insight**: Plugin determinism depends on its implementation, not its nature as a plugin.

---

## The Context Principle: The Key Decision Factor

**The most important question**: Does this task need conversation/session context to execute correctly?

### What Context Each Receives

**Skills get everything in Claude's prompt**:
- ✅ Full conversation history
- ✅ All files Claude read this session
- ✅ User's working directory, git status
- ✅ Recent command outputs
- ✅ User preferences from CLAUDE.md
- ✅ Other loaded skills

**Plugins get only parameters**:
```javascript
// Plugin receives ONLY this:
{
  "name": "convert_pdf_to_md",
  "arguments": {
    "pdf_path": "/path/to/file.pdf",
    "output_path": "/path/to/output.md"
  }
}

// Plugin DOES NOT receive:
// - Conversation history ("user mentioned this is scanned")
// - User preferences ("prefers CSV tables")
// - File diffs or git context
// - Nothing unless explicitly in parameters
```

### The Simple Test

**"If I delete the conversation history, can this task still work with just parameters?"**

- **YES** → Plugin (context-independent)
- **NO** → Skill (context-dependent)

**Alternative test**: "Can I write a clean function signature without a 'context' parameter?"

```typescript
// Test 1: PDF Conversion
function convertPdf(pdfPath: string, outputPath: string): string
// ✅ Clean signature possible → Plugin

// Test 2: Commit Message
function generateCommit(diff: string): string
// ❌ Fails! Actually needs:
function generateCommit(
  diff: string,
  recentCommits: string[],      // From git log
  userIntent: string,            // From conversation
  conventions: CommitStyle       // From repo/preferences
): string
// ✅ Needs context parameter → Skill
```

### Trade-offs of Each Approach

| Aspect | Skills (Rich Context) | Plugins (Explicit Parameters) |
|--------|----------------------|------------------------------|
| **Context Access** | Everything in Claude's prompt | Only what you pass |
| **Pro** | No need to extract/pass context | Clean isolation, no context pollution |
| **Con** | Context dilution in prompt | Must explicitly pass everything needed |
| **Parallelization** | Limited (shared context) | Excellent (isolated execution) |
| **Determinism** | Hard (context changes) | Easy (same params → same output) |

### Example: Why Git Commit is a Skill

**Task**: Generate commit message from git diff

**Context needed**:
- ✅ Repo's commit message style (from `git log`)
- ✅ User's intent from conversation ("this is a hotfix")
- ✅ Conventional commit preferences
- ✅ Co-author attribution rules

**As a plugin**, you'd need:
```javascript
{
  name: "generate_commit",
  parameters: {
    diff: string,
    recent_commits: string[],        // Need 20+ commits
    commit_type: "feat"|"fix"|...,   // Need conversation
    user_preferences: object,         // Need session context
    co_authors: string[],             // Need repo context
    issue_numbers: string[]           // Need branch context
  }
}
```

At this point, **Claude gathering these parameters IS the orchestration** - just use a skill.

### Example: Why PDF Conversion Can Be a Plugin

**Task**: Convert PDF to Markdown

**Context needed**: NONE (or minimal)

```javascript
// Everything needed can be encoded in parameters
{
  name: "convert_pdf_to_md",
  parameters: {
    pdf_path: string,         // Core input
    output_path: string,      // Core output
    use_ocr: boolean,         // Optional: if user said "scanned"
    table_format: "csv"|"pipe" // Optional: if user has preference
  }
}
```

**Scenario**: User says "Convert report.pdf to markdown, but keep tables as CSV"

**Plugin approach**:
```javascript
// Claude extracts intent and passes explicitly:
{ pdf_path: "report.pdf", table_format: "csv" }
// ✅ Plugin is self-contained
```

**Skill approach**:
```markdown
# Skill reads conversation directly:
"User said: 'keep tables as CSV'"
# Skill orchestrates with this knowledge
```

Both work, but plugin is **cleaner** because the task is context-independent.

---

## When to Use Each

### Use Skills When:

✅ **Task needs conversation/session context**
```
Example: "Generate git commit message"
Needs: Repo style, user intent, conventions, recent changes
→ Can't be cleanly parameterized
```

✅ **Task depends on project patterns**
```
Example: "Review code for style consistency"
Needs: Project conventions, previous feedback, codebase patterns
→ Rich context required
```

✅ **Multi-step workflows with conditional logic**
```
Example: "Convert PDF but adapt based on whether it's scanned"
Needs: Conversation hints, file inspection, user preferences
→ Skill guides Claude through decisions
```

✅ **Domain expertise and best practices**
```
Example: "Follow these security review guidelines"
→ Skill provides expert knowledge for Claude to apply
```

### Use Plugins When:

✅ **Task is context-independent (clean function signature)**
```
Example: "Convert PDF to Markdown"
Parameters: (pdf_path, output_path, options)
→ No conversation context needed
```

✅ **Performance-critical with parallel execution needs**
```
Example: Process 100 PDFs simultaneously
→ Each plugin gets isolated execution, no context pollution
```

✅ **External service integration**
```
Example: Query database, call API, browser automation
→ Plugin handles authentication, connections, protocols
```

✅ **Specialized libraries required**
```
Example: PDF parsing (pypdf), image processing (Pillow)
→ Plugin wraps Python/Node.js libraries
```

✅ **Deterministic execution required**
```
Example: Image resize, file format conversion
→ Same inputs must produce same outputs
```

---

## Hybrid Approach: Skills + Plugins

The most powerful pattern combines both:

### Example: PDF Conversion

**Skill** (`skills/convert-pdf-to-md/`):
- Provides workflow guidance
- Explains when to use OCR vs text extraction
- Documents best practices
- Fallback when plugin unavailable

**Plugin** (`plugins/pdf_to_md/`):
- Fast atomic execution
- Wraps Python script
- Direct tool call

**User experience**:
```bash
# Without plugin configured
User: "Convert report.pdf to markdown"
Claude: [Reads skill] → Orchestrates Read/Bash/Write → Success

# With plugin configured  
User: "Convert report.pdf to markdown"
Claude: [Calls plugin] → Direct execution → Success (faster)

# Complex scenario
User: "Convert this scanned PDF but use special table handling"
Claude: [Uses skill for strategy] + [Calls plugin for execution]
       → Best of both worlds
```

---

## Real-World Examples

### Example 1: Git Commit (Skill Only)

**Why skill, not plugin?**

**Context test**: Can we write a clean function signature?
```typescript
// Try: function generateCommitMessage(diff: string): string
// ❌ FAILS - Actually needs:

function generateCommitMessage(
  diff: string,
  recentCommits: string[],        // From git log (repo conventions)
  conversationContext: string,    // "User said this is a hotfix"
  userPreferences: {              // Conventional commits preference
    conventionalCommits: boolean,
    coAuthors: string[]
  }
): string
```

**Requires rich context that Claude already has**:
- ✅ Repository commit message style (from git log)
- ✅ User's intent from conversation
- ✅ Project conventions
- ✅ Co-author attribution rules

**Would be awkward as plugin**: You'd need to pass all this context explicitly, which means Claude doing the gathering/orchestration anyway.

```
skills/git-commit/SKILL.md:
1. Run git status and git diff
2. Read recent commits to learn style
3. Analyze conversation for user intent
4. Draft commit message following conventions
5. Add co-author attribution
```

Claude orchestrates native Bash commands with full session context.

### Example 2: PDF Conversion (Both)

**Context test**: Can we write a clean function signature?
```typescript
function convertPdfToMarkdown(
  pdfPath: string,
  outputPath: string,
  options: {
    useOcr?: boolean,
    tableFormat?: "pipe" | "csv",
    extractAssets?: string
  }
): string
```
✅ **PASSES** - Clean signature, no conversation context needed

**Why plugin works**:
- Task is **context-independent**
- All user preferences can be encoded in parameters
- No need to read conversation history

**Why skill is also useful**:
- **Guidance** for edge cases (when to use OCR, how to handle complex tables)
- **Fallback** when plugin not configured
- **Documentation** of best practices

**Plugin** (`plugins/pdf_to_md/`):
- Fast Python script execution
- Direct file I/O
- Predictable output format
- Context-independent: same PDF + options → same output

**Skill** (`skills/convert-pdf-to-md/`):
- Workflow guidance (OCR detection, table handling strategies)
- Orchestration when plugin unavailable
- Best practices documentation

### Example 3: PR Review Toolkit (Plugin with Agents)

**Why plugin?**
- Spawns multiple specialized agents in parallel
- Coordinates agent communication
- Aggregates results

```javascript
// plugins/pr-review-toolkit/index.js
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  // Spawn multiple agents in parallel
  const agents = [
    new CodeReviewer(),
    new TestAnalyzer(),
    new TypeAnalyzer()
  ]
  
  const results = await Promise.all(
    agents.map(agent => agent.analyze(request.params.code_path))
  )
  
  return { content: [{ type: "text", text: aggregateResults(results) }] }
})
```

This is non-deterministic (LLM agents) but benefits from plugin architecture (parallel execution, coordination).

---

## Development Comparison

### Creating a Skill

```bash
# 1. Create directory
mkdir skills/my-skill

# 2. Write SKILL.md
cat > skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: One-line description
---

# Instructions

## When to Use
- Trigger condition 1
- Trigger condition 2

## Operating Procedure
1. Step 1
2. Step 2
3. Step 3
EOF

# 3. Install
./scripts/dev_refresh_skills_and_tools.sh
```

**Effort**: Low (write Markdown)  
**Language**: Markdown  
**Testing**: Use in Claude immediately

### Creating a Plugin

```bash
# 1. Create directory
mkdir plugins/my-plugin

# 2. Write package.json
cat > plugins/my-plugin/package.json << 'EOF'
{
  "name": "my-plugin-mcp",
  "version": "1.0.0",
  "dependencies": {
    "@modelcontextprotocol/sdk": "^0.5.0"
  }
}
EOF

# 3. Write MCP server
cat > plugins/my-plugin/index.js << 'EOF'
#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js"
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js"
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js"

const server = new Server(...)

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{ name: "my_tool", ... }]
}))

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  // Implementation
})

const transport = new StdioServerTransport()
await server.connect(transport)
EOF

# 4. Install dependencies
cd plugins/my-plugin && npm install

# 5. Make executable
chmod +x plugins/my-plugin/index.js

# 6. Register
cd ../.. && ./scripts/dev_refresh_skills_and_tools.sh
```

**Effort**: Medium-High (write Node.js, understand MCP protocol)  
**Language**: JavaScript/TypeScript  
**Testing**: Restart Claude Code, test tool call

---

## Summary Table

| Aspect | Skills | Plugins |
|--------|--------|---------|
| **Context Access** | Full conversation, files, preferences, session state | Only explicit parameters |
| **Injection** | Full content → Claude's prompt | Schema only → Claude's prompt |
| **Execution** | Claude orchestrates native tools | External process executes |
| **Separation** | No separation (in Claude's context) | True separation (external process) |
| **Determinism** | Non-deterministic (context-dependent) | Can be deterministic (parameter-only) |
| **Parallelization** | Limited (shared context) | Excellent (isolated execution) |
| **Performance** | Depends on orchestration complexity | Fast atomic operations |
| **Development** | Write Markdown (SKILL.md) | Write Node.js MCP server |
| **State** | Stateless (reloaded each time) | Can maintain state in server process |
| **Best For** | Context-dependent tasks | Context-independent tasks |
| **Best For** | Workflows, guidance, adaptation | Atomic ops, specialized execution |
| **Complexity** | Low (Markdown) | Medium-High (MCP protocol) |
| **Language** | Markdown | Node.js/Python/any |

---

## Decision Tree

```
Need to extend Claude?
│
├─ PRIMARY TEST: Can you write a clean function signature?
│  │  (No 'context', 'conversation', 'preferences' parameters)
│  │
│  ├─ YES → Does it need specialized execution?
│  │  │
│  │  ├─ YES (external services, libraries, performance)
│  │  │  └─→ Plugin ✅
│  │  │
│  │  └─ NO (just orchestrate existing tools)
│  │     └─→ Skill ✅
│  │
│  └─ NO (needs conversation/session context)
│     │
│     ├─ Example: "Generate commit message"
│     │  (needs: repo style, user intent, conventions)
│     │  └─→ Skill ✅
│     │
│     └─ Example: "Review code for project patterns"
│        (needs: project conventions, feedback history)
│        └─→ Skill ✅
│
└─ ADVANCED: Want both flexibility AND speed?
   └─→ Both! Skill for context-aware guidance + Plugin for execution
```

### Quick Decision Tests

**Test 1: The Delete Test**
> "If I delete the conversation history, can this task still work?"
- YES → Plugin candidate
- NO → Skill

**Test 2: The Function Signature Test**
> "Can I write: `function doTask(coreInputs): output` without a context parameter?"
- YES → Plugin candidate
- NO → Skill

**Test 3: The Parallel Test**
> "Can I run 100 of these in parallel without them needing to share context?"
- YES → Plugin (excellent parallelization)
- NO → Skill (shared context matters)

---

## Common Misconceptions

### ❌ Myth: "Plugins are just faster skills"
**Reality**: Plugins provide true separation of concern and external execution, not just speed.

### ❌ Myth: "Plugin implementation is in Claude's prompt"
**Reality**: Only the tool schema is in the prompt. Implementation runs externally.

### ❌ Myth: "Skills are always non-deterministic"
**Reality**: Skills guide Claude's orchestration, which involves LLM decisions, making them non-deterministic. But the *workflow* can be deterministic.

### ❌ Myth: "Plugins are always deterministic"
**Reality**: Plugins can spawn LLM agents internally, making them non-deterministic.

### ❌ Myth: "You must choose: skill OR plugin"
**Reality**: Best practice is often both - skill provides guidance, plugin provides execution.

---

## Conclusion

**The Decision Comes Down to Context**:

Skills and plugins aren't about "workflows vs execution" or "complexity vs simplicity" — they're about **context dependency**:

- **Skills** = Context-dependent tasks (need conversation, preferences, session state)
- **Plugins** = Context-independent tasks (clean function signature possible)

**The simple test**: Can you write `function doTask(coreInputs): output` without a context parameter?
- **YES** → Plugin (clean isolation, excellent parallelization)
- **NO** → Skill (rich context access, adaptive orchestration)

**Pro/Con trade-off**:
- **Plugin isolation** = Pro (no context pollution, deterministic, parallel-friendly) + Con (must explicitly pass everything)
- **Skill context** = Pro (access to conversation/session) + Con (context dilution, harder to parallelize)

**Best practice**: Start with the context test. If the task needs conversation/session context to work correctly, use a skill. If it can be fully parameterized, use a plugin. Combine both when you want context-aware strategy with optimized execution.
