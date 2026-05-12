---
name: idea-to-specs
description: Transform ideas into implementation-ready specs using flexible superpowers plugin patterns
---

# Idea to Specs

## When to Use

- User starts new feature/project with vague requirements or rough ideas
- User asks to create epic, stories, or spec documents
- User wants to refine existing spec or story
- User requests structured spec creation workflow
- User invokes `/idea-to-specs` or similar spec generation commands

## When NOT to Use

- Code review or PR critique → use `git-review` or `pr-review-remote`
- Design critique of existing branch → use `code-design-critique`
- Quick bug fixes or straightforward implementation tasks
- User has complete, detailed spec already written

## Prerequisites Check

**CRITICAL**: Before proceeding, verify the environment and dependencies.

### 1. Check AI Platform

Verify you are running on Claude Code or another Claude-based platform:
- Check system context for Claude indicators
- If not Claude, inform user this skill is optimized for Claude and superpowers plugin integration

### 2. Check Superpowers Plugin

The superpowers plugin provides critical tools (`superpowers:brainstorming`, `/critique-me`, `/sc:spec-panel`).

**Check availability**:
```
Look for skills in system context:
- superpowers:brainstorming
- critique-me
- (Optional) sc:spec-panel
```

**If superpowers plugin NOT installed**:
```
⚠️ SUPERPOWERS PLUGIN NOT DETECTED

This skill relies on superpowers plugin tools:
- superpowers:brainstorming (requirements discovery)
- /critique-me (spec validation)
- /sc:spec-panel (expert review)

FALLBACK OPTIONS:

1. INSTALL PLUGIN (Recommended):
   - Claude Code: Install from official plugin marketplace
   - Cursor: Check ~/.cursor/skills/ for superpowers plugins
   
2. USE DEGRADED MODE:
   We can proceed with reduced functionality:
   - Replace brainstorming with manual Q&A
   - Replace critique-me with manual review prompts
   - Skip spec-panel (no automated expert review)
   
   This will work but lose structured workflows and rubrics.

3. USE DIFFERENT SKILL:
   If you don't have superpowers installed, consider:
   - Manual spec creation (no skill)
   - Basic requirements gathering workflows

Would you like to: (a) Install plugin, (b) Proceed in degraded mode, or (c) Skip this skill?
```

**If superpowers plugin IS installed**:
```
✅ Prerequisites met - proceeding with full functionality
```

### 3. Environment Detection

After checks, set internal mode flag:
- **FULL_MODE**: Superpowers plugin available, all features enabled
- **DEGRADED_MODE**: No superpowers, fallback to manual workflows
- **BLOCKED_MODE**: Prerequisites not met, cannot proceed

## Philosophy

**Flexible, not linear.** This skill provides a toolkit for cherry-picking steps from superpowers plugin based on what your specific situation needs. Most workflows are chaotic, not sequential. Epic structure is optional. Start where it makes sense for your context.

## Quick Reference

See [resources/quick-reference.md](resources/quick-reference.md) for the complete discovery, validation, and review toolkit showing which superpowers tools to use for different situations.

## Common Workflow Patterns

### Pattern 1: Idea → Spec
**Start**: Vague idea  
**Use**: `superpowers:brainstorming` → manual spec → `/critique-me` rubrics 1,2,3  
**Output**: Implementation-ready story

### Pattern 2: Problem → Investigation → Spec
**Start**: Known problem, unclear solution  
**Use**: `superpowers:brainstorming` (questions) → spike/prototype → spec → `/critique-me` rubrics 1,2  
**Output**: Evidence-based design

### Pattern 3: Spec → Validation → Refine
**Start**: Draft spec exists  
**Use**: `/critique-me` rubrics 1,2,3 → refine → `/sc:spec-panel` (if needed)  
**Output**: Validated, detailed spec

### Pattern 4: Direct Implementation
**Start**: Clear, simple feature  
**Use**: Write story directly → `/critique-me` rubric 3 (anti-slop check)  
**Output**: Story ready for implementation

## Operating Procedure

### 1. Assess Starting Point

**If user has**:
- Vague idea → Start with brainstorming
- Clear requirements → Skip to spec writing
- Draft spec → Jump to validation
- Simple task → Write story, validate with critique-me 3

**Epic structure decision**:
- Use epics when: 10+ stories, multiple teams, phased rollout
- Skip epics when: <5 stories, single feature, clear linear path

### 2. Discovery (When Needed)

**FULL_MODE** - Use `superpowers:brainstorming` when requirements are unclear:
```
[Invoke brainstorming skill via Skill tool]
Ask probing questions to uncover:
- Problem space and user needs
- Constraints and assumptions
- Success criteria
- Technical requirements
```

**DEGRADED_MODE** - Manual discovery without brainstorming skill:
```
Ask probing questions directly:
1. What problem does this solve?
2. Who are the users and what are their needs?
3. What are the constraints (technical, business, time)?
4. What does success look like?
5. What are the non-goals?

Document answers, then proceed to spec writing.
```

**Skip discovery when**: Requirements already clear, working from PRD, simple enhancement

### 3. Spec Creation

**Choose format based on scope**:
- **Epic** (10+ stories): Foundation → features → optimization phases
- **Multi-story** (3-10 stories): Group by component/layer
- **Single story**: Definition of done, acceptance criteria, examples
- **Spike**: Investigation goals, questions to answer, decision criteria

**Write for implementers**: Include examples, edge cases, verification criteria

### 4. Validation (Select Rubrics)

**FULL_MODE** - Use `/critique-me` with selected rubrics based on needs:

**Always validate with rubric 3** (anti-AI-slop):
- Catches generic advice, missing verification, padding
- Ensures actionable detail for implementers

**Add rubric 1** (stress-test) when:
- Making architectural decisions
- Choosing between approaches
- Risk-sensitive areas (performance, security, scale)

**Add rubric 2** (blind spots) when:
- Complex multi-component systems
- Integration points with external systems
- Spec feels complete but unsure what's missing

**Add rubrics 4+5** (code-quality, ml-design) when:
- Implementation-focused stories (not high-level epics)
- Technical design decisions already made

**Validation commands**:
```
[Invoke critique-me skill via Skill tool]
/critique-me on [path/to/spec.md] rubrics: 3
/critique-me on [path/to/spec.md] rubrics: 1,2,3
/critique-me on [path/to/epic.md] rubrics: 1,2
```

**DEGRADED_MODE** - Manual validation without critique-me skill:
```
Review spec manually for:

Anti-Slop Check (Always do this):
- Are requirements specific or generic?
- Does it have concrete examples?
- Are acceptance criteria verifiable?
- Is there filler/padding content?

Stress-Test (For architectural decisions):
- What assumptions are untested?
- What could go wrong?
- Are there performance/security risks?

Blind Spots (For complex systems):
- What edge cases are missing?
- What integration points are unclear?
- What failure modes are unhandled?

Document findings and refine spec accordingly.
```

### 5. Expert Review (Optional)

**FULL_MODE** - Use `/sc:spec-panel` when:
- Complex technical decisions needing multiple perspectives
- Architecture choices with long-term implications
- Team disagreement on approach

**DEGRADED_MODE** - Expert review not available:
```
⚠️ /sc:spec-panel requires superpowers plugin

Alternative: Manually review from multiple perspectives:
1. Technical perspective: Is this architecturally sound?
2. User perspective: Does this solve the real problem?
3. Operational perspective: Can we maintain this?
4. Security perspective: Are there vulnerabilities?
5. Performance perspective: Will this scale?

Document concerns from each perspective.
```

**Skip when**: Straightforward implementation, consensus exists, time-constrained

### 6. Refinement Loop

Based on validation feedback:
1. Fix must-fix items immediately
2. Incorporate high-value suggestions
3. Re-validate if major changes made
4. Stop when critique shows no critical issues

**Don't over-iterate**: 2-3 refinement passes max. Perfect is enemy of shipped.

## Integration with Superpowers Plugin

**FULL_MODE** - This skill **cherry-picks from** superpowers plugin tools:

| Tool | Use For | Skip When |
|------|---------|-----------|
| `superpowers:brainstorming` | Requirements discovery | Requirements clear |
| `/critique-me` rubric 1 | Stress-test decisions | Early brainstorming |
| `/critique-me` rubric 2 | Find blind spots | Simple features |
| `/critique-me` rubric 3 | Ensure substance | Never skip (always validate) |
| `/critique-me` rubrics 4,5 | Code/ML quality | High-level epics |
| `/sc:spec-panel` | Expert perspectives | Consensus exists |

**The plugin has structure; you cherry-pick steps based on your needs.**

**DEGRADED_MODE** - Manual fallbacks without plugin:

| Original Tool | Fallback Approach |
|---------------|------------------|
| `superpowers:brainstorming` | Direct Q&A with structured questions |
| `/critique-me` rubrics | Manual review checklists |
| `/sc:spec-panel` | Manual multi-perspective review |

**Performance impact**: DEGRADED_MODE works but loses structured workflows, rubrics, and automated validation.

## Examples

See [resources/examples.md](resources/examples.md) for real workflow examples showing:
- Single story creation (5 min workflow)
- Multi-story feature (20 min workflow)
- Epic with foundation stories (45 min workflow)
- Investigation spike (15 min workflow)

## Output Guidelines

**Specs should include**:
- **Context**: Why this matters, what problem it solves
- **Scope**: What's in/out, boundaries clear
- **Definition of Done**: Concrete acceptance criteria
- **Examples**: Happy path, edge cases, error scenarios
- **Verification**: How implementer proves it works
- **Non-goals**: What explicitly NOT to build

**Specs should NOT include**:
- Generic advice that could apply to any project
- Template language without specifics
- Unverifiable requirements ("good performance")
- Implementation details unless architecturally significant
- Padding or filler content

## Deep Dive

For extended philosophy, superpowers plugin architecture, and advanced patterns, see [resources/deep-dive.md](resources/deep-dive.md).

## Success Metrics

A good spec:
- ✅ Implementer knows exactly what to build
- ✅ Implementer can verify when done
- ✅ Passes `/critique-me` rubric 3 (anti-slop) with no major issues
- ✅ Contains real examples, not just descriptions
- ✅ Took appropriate time for complexity (don't over-invest)

A good workflow:
- ✅ Started at right point (didn't brainstorm when requirements clear)
- ✅ Used validation tools that added value (didn't over-validate)
- ✅ Produced actionable output (not just documentation)
- ✅ Balanced quality with velocity (shipped, not perfect)
