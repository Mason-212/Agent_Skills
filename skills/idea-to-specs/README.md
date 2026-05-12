# idea-to-specs

Transform ideas into implementation-ready specs using flexible superpowers plugin patterns.

## Overview

A cherry-picking toolkit for spec creation that adapts to your specific needs. Skip unnecessary steps, focus on what adds value.

**Core principle**: Flexible, not linear. Most workflows are chaotic. Epic structure is optional. Start where it makes sense for your context.

## Prerequisites

**Recommended**:
- ✅ Claude Code or Claude-based AI platform
- ✅ Superpowers plugin installed (provides brainstorming, critique-me, spec-panel)

**Graceful Degradation**:
- ⚠️ Works without superpowers plugin but with reduced functionality
- ⚠️ Manual fallbacks available (Q&A replaces brainstorming, checklists replace rubrics)
- ❌ Best experience requires full plugin integration

The skill will auto-detect prerequisites and inform you of available vs. degraded features.

## Quick Start

### For AI Assistants

**On invocation**:
1. Check prerequisites (Claude platform, superpowers plugin)
2. Set mode (FULL_MODE vs DEGRADED_MODE)
3. Inform user of available functionality
4. Proceed with appropriate workflow

**Invoke**: `/idea-to-specs` when user starts spec/story work

**Auto-activates** when user:
- Starts new feature with vague requirements
- Asks to create epic, stories, or spec documents
- Wants to refine existing spec
- Requests structured spec creation workflow

**Prerequisites check example**:
```
✅ Claude Code detected
✅ Superpowers plugin detected (brainstorming, critique-me, spec-panel)
✅ Full functionality available

Proceeding with idea-to-specs workflow...
```

**Degraded mode example**:
```
✅ Claude Code detected
⚠️ Superpowers plugin NOT detected

Available: Manual Q&A, manual validation checklists
Unavailable: Structured brainstorming, rubric validation, expert panel

Proceeding with DEGRADED_MODE (reduced functionality)...
```

### For Humans

**Read first**: [resources/quick-reference.md](resources/quick-reference.md) - Decision trees and tool selection guide

**Common patterns**:
1. **Idea → Spec**: Brainstorm → write → validate (15-30 min)
2. **Problem → Investigation → Spec**: Questions → spike → spec (20-45 min)
3. **Spec → Validation → Refine**: Critique → refine (10-20 min)
4. **Direct Implementation**: Write → anti-slop check (5-10 min)

**Deep dive**: [resources/deep-dive.md](resources/deep-dive.md) - Philosophy, advanced patterns, troubleshooting

## Structure

```
idea-to-specs/
├── SKILL.md                      # Main skill (AI instructions)
├── README.md                     # This file (human overview)
└── resources/
    ├── quick-reference.md        # Toolkit with decision trees
    ├── examples.md               # 5 real workflow examples
    └── deep-dive.md              # Extended guide and philosophy
```

## Toolkit Components

### Discovery Tools
- `superpowers:brainstorming` - Interactive requirements discovery
- **Use when**: Vague requirements, multiple stakeholders
- **Skip when**: Requirements clear, time pressure

### Validation Tools
- `/critique-me` rubric 1 (stress-test) - Architectural decisions
- `/critique-me` rubric 2 (blind spots) - Complex systems
- `/critique-me` rubric 3 (anti-slop) - **Always validate** before implementation
- `/critique-me` rubrics 4,5 (code/ML) - Implementation stories

### Expert Review
- `/sc:spec-panel` - Multi-expert perspective
- **Use when**: Architecture choices, team disagreement
- **Skip when**: Consensus exists, straightforward

### Structure
- Epic format - For 10+ stories, multi-team coordination
- Story group - For 3-9 stories, single team
- Single story - For 1-2 stories, simple features
- Investigation spike - For unclear solutions

## Integration with Superpowers Plugin

This skill **cherry-picks from** superpowers plugin tools:

| Tool | When to Use | When to Skip |
|------|-------------|--------------|
| `superpowers:brainstorming` | Requirements unclear | Requirements clear |
| `/critique-me` rubric 1 | Architectural decisions | Early brainstorming |
| `/critique-me` rubric 2 | Complex systems | Simple features |
| `/critique-me` rubric 3 | **Always (quality gate)** | Never skip |
| `/critique-me` rubrics 4,5 | Implementation stories | High-level epics |
| `/sc:spec-panel` | Complex decisions | Consensus exists |

**Key insight**: The plugin has structure; you cherry-pick based on your specific needs.

## Time Investment Guidelines

Spec time should be **10-20% of implementation time**:

| Complexity | Discovery | Writing | Validation | Total |
|-----------|-----------|---------|------------|-------|
| Simple | 0 min | 5 min | 5 min | 10 min |
| Medium | 10 min | 15 min | 10 min | 35 min |
| Complex | 20 min | 30 min | 15 min | 65 min |
| Epic | 30 min | 45 min | 20 min | 95 min |

**If spending >2x these times**: You're over-speccing. Ship and iterate.

## Success Metrics

A good spec:
- ✅ Implementer knows exactly what to build
- ✅ Implementer can verify when done
- ✅ Passes `/critique-me` rubric 3 with no major issues
- ✅ Contains real examples, not just descriptions
- ✅ Took appropriate time for complexity

A good workflow:
- ✅ Started at right point (didn't over-discover)
- ✅ Used validation that added value
- ✅ Produced actionable output
- ✅ Balanced quality with velocity

## Examples

See [resources/examples.md](resources/examples.md) for 5 detailed workflow examples:
1. Simple feature (5 min) - Password toggle
2. Medium feature (35 min) - Rate limiting
3. Complex epic (95 min) - Domain pack system
4. Investigation spike (20 min) - Workflow orchestration
5. Refining existing spec (15 min) - Quality gate

## Related Skills

- **critique-me** - Multi-rubric validation (used by this skill)
- **code-design-critique** - Branch-scoped design review
- **git-commit** - Committing spec documents
- **git-review / pr-review-remote** - PR review after implementation

## Installation

From the skills repo root:
```bash
./scripts/dev_refresh_skills_and_tools.sh
```

This installs to:
- `~/.claude/skills/idea-to-specs/`
- `~/.cursor/skills/idea-to-specs/`
- `~/.agents/skills/idea-to-specs/`

## Usage

**AI invocation**:
```
User: "Help me create a spec for user authentication"
AI: [Auto-invokes idea-to-specs skill]
AI: [Follows toolkit based on context]
```

**Manual invocation**:
```
User: "/idea-to-specs"
AI: [Loads skill and provides guidance]
```

**Reference during work**:
```
User: "Which critique-me rubrics should I use?"
AI: [References resources/quick-reference.md decision trees]
```

## Philosophy

From [resources/deep-dive.md](resources/deep-dive.md):

> **The Problem with Linear Workflows**: Traditional spec creation assumes everyone starts with vague requirements (false), all projects need epics (false), and more process equals better quality (false).
>
> **The Cherry-Picking Principle**: Here's a toolkit. Pick the tools that add value for your specific situation. Skip the rest.
>
> **Benefits**: Faster (no mandatory steps), targeted (tools where they matter), context-aware (adapt to needs), shipping-focused (balance quality with velocity).

## Anti-Patterns

❌ **Over-brainstorming** - 30 min session for "add button"  
✅ **Fix**: Can you write concrete examples now? If yes, skip brainstorming.

❌ **Epic bloat** - Epic with 3 phases for 4 stories  
✅ **Fix**: Only create epics for 10+ stories or multi-team coordination.

❌ **Skipping anti-slop** - Spec has "implement efficient caching"  
✅ **Fix**: Always run critique-me rubric 3 before implementation.

❌ **Over-validation** - All 5 rubrics for "change button color"  
✅ **Fix**: Match validation effort to architectural impact.

❌ **Perfection seeking** - 5 refinement passes, never ships  
✅ **Fix**: Stop after 2-3 passes when critique shows no critical issues.

## Contributing

When updating this skill:
1. Maintain the cherry-picking philosophy (toolkit, not script)
2. Keep examples concrete (real workflows with timings)
3. Update decision trees in quick-reference.md
4. Test skill invocation cross-project
5. Verify all resources/ paths are relative

## License

Part of the thomaschangsf/skills repository.
