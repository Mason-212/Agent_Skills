# Spec Creation Deep Dive

Extended guide for transforming ideas into implementation-ready specs using flexible patterns.

## Philosophy

### The Problem with Linear Workflows

Traditional spec creation assumes:
- Everyone starts with vague requirements → FALSE (some start with clear PRDs)
- All projects need epics → FALSE (most features are <5 stories)
- More process = better quality → FALSE (over-process kills velocity)
- AI assistants need prescriptive steps → FALSE (cherry-picking based on context is better)

**Reality**: Spec creation is chaotic, context-dependent, and should be optimized for value delivery, not process adherence.

### The Cherry-Picking Principle

Instead of "follow these 8 phases", think:

> "Here's a toolkit. Pick the tools that add value for your specific situation. Skip the rest."

**Benefits**:
- ⚡ Faster - no mandatory steps that don't add value
- 🎯 Targeted - tools applied where they matter most
- 🧠 Context-aware - adapt to your specific needs
- 🚢 Shipping-focused - balance quality with velocity

---

## The Toolkit Architecture

### Discovery Layer

**Tools**:
- `superpowers:brainstorming` - Interactive requirements discovery

**When valuable**:
- Vague initial requirements
- Multiple stakeholders with different perspectives
- Domain you're unfamiliar with
- Requirements buried in assumptions

**When skip**:
- Clear requirements from PRD or user story
- Well-understood domain
- Time pressure

**Output**: Requirements clarity sufficient to write concrete examples

---

### Structure Layer

**Tools**:
- Epic format (phases, foundation → features → optimization)
- Multi-story grouping (by component/layer)
- Single story format (acceptance criteria, examples)
- Investigation spike format (questions, success criteria)

**Decision tree**:
```
10+ stories? → Epic with phases
5-9 stories + multiple teams? → Consider epic
3-5 stories, single team? → Story group
1-2 stories? → Individual stories
Unclear solution? → Investigation spike
```

**Output**: Structured documents ready for validation

---

### Validation Layer

**Tools**:
- `/critique-me` rubric 1 (stress-test decisions)
- `/critique-me` rubric 2 (blind spots and coverage)
- `/critique-me` rubric 3 (anti-AI-slop / substance)
- `/critique-me` rubric 4 (code quality)
- `/critique-me` rubric 5 (ML design)

**Selection matrix**:
```
Always use: Rubric 3 (critical quality gate)

Add Rubric 1 if: Architectural decisions, multiple approaches, risk-sensitive
Add Rubric 2 if: Complex system, integration-heavy, feels complete but unsure
Add Rubrics 4,5 if: Implementation story (not conceptual), includes code/ML design
```

**Output**: Concrete issues (must-fix, high-value, later) for refinement

---

### Expert Review Layer

**Tools**:
- `/sc:spec-panel` - Multi-expert perspective

**When valuable**:
- Architecture choices with long-term implications
- Team disagreement on approach
- Complex technical decisions needing multiple lenses

**When skip**:
- Consensus already exists
- Straightforward implementation
- Time-constrained

**Output**: Expert feedback, alternative approaches, consensus building

---

## Integration with Superpowers Plugin

### Plugin Structure (What It Provides)

The superpowers plugin has its own structured flows:

**`superpowers:brainstorming`**:
1. Context exploration
2. Clarifying questions
3. Approach proposals
4. Design presentation
5. Spec writing

**`/critique-me`**:
1. Artifact inference
2. Rubric selection
3. Rubric reading
4. Artifact analysis
5. Structured critique

**`/sc:spec-panel`**:
1. Expert selection
2. Framework application
3. Multi-perspective analysis
4. Synthesis across experts

### Cherry-Picking Strategy

You **don't** follow the plugin's internal flow linearly. You invoke tools at appropriate points in **your** workflow.

**Example - Plugin has 5 brainstorming phases; you might**:
- Use only phase 1-2 (questions) then write spec yourself
- Skip brainstorming entirely if requirements clear
- Use phase 3 (approaches) without preceding questions

**Example - critique-me has artifact inference; you might**:
- Provide explicit paths instead of letting it infer
- Use only rubric 3 for quick validation
- Use all 5 rubrics for critical foundation stories

**The plugin is a library, not a script. You compose calls based on your needs.**

---

## Real-World Workflow Patterns

### Pattern 1: Greenfield Feature (Unknown → Known)

**Context**: Building new feature with unclear requirements

**Workflow**:
```
1. Discovery (20-30 min):
   - Invoke superpowers:brainstorming
   - Explore problem space through questions
   - Identify constraints and assumptions
   
2. Structure (15 min):
   - Decide epic vs stories based on scope
   - Write first pass with examples
   
3. Validation (10 min):
   - /critique-me rubrics 1,2,3
   - Find architectural issues and blind spots
   
4. Refinement (10 min):
   - Address must-fix items
   - Incorporate high-value suggestions
   
5. Optional Expert Review (20 min):
   - /sc:spec-panel if architectural choices uncertain
   - Get multi-perspective validation

Total: 55-85 min depending on complexity
```

### Pattern 2: Brownfield Enhancement (Known → Specific)

**Context**: Adding feature to existing system with clear requirements

**Workflow**:
```
1. Skip Discovery (requirements clear)

2. Structure (10 min):
   - Write stories with concrete examples
   - Reference existing system patterns
   
3. Validation (5 min):
   - /critique-me rubric 3 only (substance check)
   - Ensure actionable detail
   
4. Quick Refinement (5 min):
   - Fix any generic advice
   - Add verification criteria

Total: 20 min (80% faster than full discovery)
```

### Pattern 3: Architectural Spike (Exploration → Decision)

**Context**: Evaluating multiple approaches before committing

**Workflow**:
```
1. Light Discovery (10 min):
   - superpowers:brainstorming for evaluation criteria
   - What matters for this decision?
   
2. Investigation Spike (time-boxed):
   - POC each approach
   - Document findings
   
3. Validation (10 min):
   - /critique-me rubrics 1,2 (stress-test decision)
   - Find risks in recommended approach
   
4. Expert Review (20 min):
   - /sc:spec-panel for architectural validation
   - Multiple perspectives on long-term implications

Total: 40 min + spike time
```

### Pattern 4: Quality Gate (Draft → Ready)

**Context**: Existing spec needs quality check before implementation

**Workflow**:
```
1. Skip Discovery & Structure (already exists)

2. Validation (5 min):
   - /critique-me rubric 3 only
   - Quick substance check
   
3. Targeted Refinement (5-10 min):
   - Fix generic advice
   - Add missing verification
   - Ensure concrete examples

Total: 10-15 min (minimum viable validation)
```

---

## Quality Standards

### What Makes a Good Spec?

**Must have**:
- ✅ Concrete examples (happy path, edge cases, errors)
- ✅ Verifiable acceptance criteria (how to prove it works)
- ✅ Clear scope boundaries (what's in/out)
- ✅ Passes critique-me rubric 3 (substance over fluff)

**Should have** (complexity-dependent):
- Context explaining why this matters
- Non-goals (what explicitly NOT to build)
- Integration points with existing system
- Performance/security requirements (when relevant)

**Don't over-invest in**:
- Exhaustive documentation (README can evolve)
- Perfect formatting and polish
- Speculative future features (YAGNI)
- Implementation details (unless architecturally significant)

### Validation Depth Guidelines

| Spec Type | Minimum Validation | Maximum Validation |
|-----------|-------------------|-------------------|
| Simple feature | Rubric 3 | Rubrics 1,2,3 |
| Medium feature | Rubrics 2,3 | Rubrics 1,2,3 |
| Complex feature | Rubrics 1,2,3 | Rubrics 1,2,3 + panel |
| Foundation/Architecture | Rubrics 1,2,3,4 | All rubrics + panel |
| Epic (conceptual) | Rubrics 1,2 | Rubrics 1,2 + panel |
| Implementation story | Rubrics 3,4 | Rubrics 1,2,3,4,5 |
| Investigation spike | Rubrics 1,2 | Rubrics 1,2 |

**Rule**: Validation effort should scale with architectural impact, not line count.

---

## Time Investment Guidelines

### How Much Time to Spend?

**General principle**: Spec time should be 10-20% of implementation time.

If implementation takes:
- 1 hour → Spend 5-10 min on spec (lean story with examples)
- 4 hours → Spend 20-40 min on spec (story with validation)
- 1 day → Spend 1-2 hours on spec (detailed story or small epic)
- 1 week → Spend 4-8 hours on spec (epic with multiple stories)

**If spending more**: You're over-speccing. Ship and iterate based on feedback.

### Breakdown by Activity

**Typical 40-minute medium feature spec**:
- Discovery (optional): 10 min
- Writing: 15 min
- Validation: 10 min
- Refinement: 5 min

**Atypical but valid variations**:
- 0 min discovery, 5 min writing, 5 min validation = 10 min (clear requirements)
- 30 min discovery, 30 min writing, 20 min validation + panel = 80 min (complex, high-impact)

**Key**: Adapt investment to value delivered, not process adherence.

---

## Anti-Patterns and How to Avoid Them

### Anti-Pattern 1: Over-Brainstorming

**Symptom**: 30-minute brainstorming session for "add button to navbar"

**Why it happens**: Treating brainstorming as mandatory first step

**Fix**: Ask "Can I write concrete examples right now?" If yes, skip brainstorming.

**Example**:
```
WRONG: "Let's brainstorm what this button should do..."
RIGHT: "Button labeled 'New User' in top-right nav, opens modal form"
```

### Anti-Pattern 2: Epic Bloat

**Symptom**: Epic with 3 phases for 4 stories

**Why it happens**: Assuming all multi-story work needs epic structure

**Fix**: Only create epics for 10+ stories or multi-team coordination.

**Example**:
```
WRONG: Epic "Pagination System" with Foundation → Implementation phases
RIGHT: 3 stories (API, UI component, tests) grouped by feature
```

### Anti-Pattern 3: Skipping Anti-Slop Validation

**Symptom**: Spec with "implement efficient caching" and "ensure good performance"

**Why it happens**: Not validating for substance before implementation

**Fix**: Always run critique-me rubric 3 before sharing with implementers.

**Example**:
```
WRONG: "Add secure authentication with proper error handling"
RIGHT: "bcrypt with 12 rounds, return 401 with specific error codes"
```

### Anti-Pattern 4: Over-Validation

**Symptom**: Running all 5 rubrics + spec-panel on "change button color"

**Why it happens**: Treating validation as checklist vs. risk-based activity

**Fix**: Match validation effort to architectural impact.

**Example**:
```
WRONG: All rubrics for trivial UI change (30 min validation)
RIGHT: Rubric 3 only for trivial change (2 min validation)
```

### Anti-Pattern 5: Perfection Before Shipping

**Symptom**: 5 refinement passes, still finding "one more thing to improve"

**Why it happens**: Treating spec as final artifact vs. living document

**Fix**: Stop after 2-3 passes when critique shows no critical issues.

**Example**:
```
WRONG: Pass 5 - "Should I add more examples for edge case X?"
RIGHT: Pass 2 - No must-fix items, ship and iterate based on implementation feedback
```

---

## Advanced Techniques

### Technique 1: Validation Layering

Instead of one big validation pass, layer validations based on development stage:

**Layer 1** (epic level): Rubrics 1,2 - stress-test architecture, find blind spots  
**Layer 2** (story level): Rubric 3 - ensure each story is actionable  
**Layer 3** (implementation): Rubrics 4,5 - validate code and ML design

**Benefit**: Catch architectural issues early, detail issues late.

### Technique 2: Parallel Validation

For multi-story work, validate stories in parallel:

```
Story 1.1 → critique-me rubric 3
Story 1.2 → critique-me rubric 3    } Parallel
Story 1.3 → critique-me rubric 3

Aggregate findings → Refine all three
```

**Benefit**: Faster validation, consistent quality across stories.

### Technique 3: Incremental Spec Evolution

Don't write the complete spec upfront. Evolve it:

**Phase 1**: Lean story (examples, acceptance criteria) → Implement  
**Phase 2**: During implementation, update spec with learnings  
**Phase 3**: After implementation, spec becomes documentation

**Benefit**: Spec stays accurate, reflects reality vs. speculation.

### Technique 4: Tool Combination

Combine tools creatively for your situation:

**Example 1**: Brainstorming for evaluation criteria → Skip to spike (no spec writing)  
**Example 2**: Write spec → Validate with rubric 3 → Refine → Validate with rubrics 1,2  
**Example 3**: Brainstorm approaches → Pick one → Spec-panel for validation → Write spec

**Benefit**: Custom workflows that fit your exact needs.

---

## Superpowers Plugin Deep Dive

### How the Plugin Works

The superpowers plugin provides structured workflows as skills that AI can invoke:

**Skill Structure**:
```
skills/superpowers-brainstorming/
├── SKILL.md                          # Main instructions
└── resources/                        # Supporting content
```

When you invoke a skill (e.g., `/brainstorm` or `superpowers:brainstorming`), the AI:
1. Loads the skill content into context
2. Follows the workflow defined in SKILL.md
3. Uses resources/ content for rubrics, patterns, examples
4. Returns structured output per skill guidelines

### Key Plugin Skills

**`superpowers:brainstorming`**:
- Interactive requirements discovery
- Clarifying questions in rounds
- Approach proposals with trade-offs
- Design presentation with approval gates
- Spec document generation

**`/critique-me`**:
- Multi-rubric validation system
- 5 specialized rubrics (stress-test, blind spots, anti-slop, code-quality, ml-design)
- Artifact inference (paths, conversation, mixed)
- Structured critique output
- Recommendations prioritization

**`/sc:spec-panel`**:
- Multi-expert perspective simulation
- Domain expert selection
- Framework application
- Synthesis across expert views
- Consensus building

### Cherry-Picking vs. Following

**The plugin provides flows, but you control invocation:**

**Full Flow** (plugin structure):
```
superpowers:brainstorming
  → Questions (Round 1, 2, 3...)
  → Approaches (2-3 options)
  → Design presentation
  → User approval
  → Spec writing
  → Commit
```

**Cherry-Picked** (your control):
```
You: "Help me understand requirements for X"
AI: [Invokes brainstorming → Questions only]

You: "I'll write the spec myself"
AI: [Skips remaining brainstorming phases]

You: "Now validate my spec"
AI: [Invokes critique-me rubric 3]

You: "Good, let's implement"
AI: [Skips spec-panel, moves to implementation]
```

**Key Insight**: You're not following the plugin's internal flow end-to-end. You're invoking specific plugin capabilities when they add value to **your** flow.

---

## Relationship to Other Skills

This skill (`idea-to-specs`) integrates with other skills in your repo:

### Related Skills

**`critique-me`**: Core validation tool used by idea-to-specs
- idea-to-specs tells you WHEN to use critique-me
- critique-me tells you HOW to run validation

**`code-design-critique`**: Branch-scoped design review
- Use BEFORE implementation for design validation
- Complements idea-to-specs (which focuses on spec creation)

**`git-commit`**: Committing spec documents
- Use AFTER spec creation to save work

**`git-review` / `pr-review-remote`**: PR review
- Use AFTER implementation for code review
- Different from spec validation (critique-me)

### Skill Invocation Flow

```
idea-to-specs (this skill)
  → Guides spec creation workflow
  → Invokes superpowers:brainstorming when needed
  → Invokes critique-me for validation
  → Outputs: Implementation-ready spec

code-design-critique
  → Reviews design on branch
  → Can work with spec from idea-to-specs
  → Outputs: Design feedback

git-commit
  → Commits spec documents
  → Standard git workflow
  → Outputs: Committed spec

[Implementation happens]

git-review / pr-review-remote
  → Reviews implementation PR
  → Validates against spec
  → Outputs: PR feedback
```

---

## Troubleshooting Common Issues

### Issue 1: "I don't know where to start"

**Symptoms**: Staring at blank page, unclear what to write

**Diagnosis**: Need discovery, requirements unclear

**Solution**: Invoke `superpowers:brainstorming` to clarify through questions

---

### Issue 2: "Spec feels generic and unhelpful"

**Symptoms**: Implementer says "I don't know what to build" after reading spec

**Diagnosis**: Spec lacks substance, has generic advice

**Solution**: Run `/critique-me rubric 3` to find and fix generic content

---

### Issue 3: "Validation taking too long"

**Symptoms**: 30+ minutes validating simple feature

**Diagnosis**: Over-validating based on process vs. risk

**Solution**: Use only rubric 3 for simple features, reserve full validation for complex/risky work

---

### Issue 4: "Spec doesn't match implementation"

**Symptoms**: Code diverged from spec during implementation

**Diagnosis**: Spec too detailed upfront, couldn't adapt

**Solution**: Write lean spec with examples, let it evolve during implementation

---

### Issue 5: "Taking too long to create specs"

**Symptoms**: Spending 2+ hours on spec for 4-hour implementation

**Diagnosis**: Over-speccing, treating spec as final artifact

**Solution**: Time-box spec work to 10-20% of implementation time, ship and iterate

---

## Success Stories

### Story 1: Domain Pack Foundation (Complex Epic)

**Challenge**: Design extensible plugin system for ML capabilities

**Approach**:
- 30 min brainstorming → Clear requirements
- 45 min epic writing → 10 stories across 2 phases
- 15 min validation (rubrics 1,2) → Found version conflict issue
- 20 min spec-panel → Decoupling recommendation
- Result: 5 detailed, validated stories ready for implementation

**Time**: 110 min total  
**Value**: Foundation prevented major refactoring later  
**ROI**: 2 weeks saved by getting architecture right upfront

### Story 2: Rate Limiting (Medium Feature)

**Challenge**: Add rate limiting to public API

**Approach**:
- 10 min brainstorming → Storage and limits clarified
- 15 min spec writing → 3 stories with examples
- 10 min validation (rubrics 1,2,3) → Found distributed case
- Result: 4 stories (added multi-instance story)

**Time**: 35 min total  
**Value**: Prevented production incident (missing distributed handling)  
**ROI**: 1 day saved debugging production issue

### Story 3: Password Toggle (Simple Feature)

**Challenge**: Add show/hide toggle to password field

**Approach**:
- 0 min brainstorming (feature clear)
- 3 min spec writing → Story with examples
- 2 min validation (rubric 3 only) → Passed
- Result: Implementation-ready story

**Time**: 5 min total  
**Value**: Clear guidance for implementer, no back-and-forth  
**ROI**: 30 min saved from implementation confusion

---

## Further Reading

### Superpowers Plugin Documentation

- Skills directory: `~/.claude/skills/superpowers-*/`
- Official plugin: Check for superpowers plugin in skill marketplace

### Related Skills in This Repo

- `skills/critique-me/` - Multi-rubric validation
- `skills/code-design-critique/` - Branch-scoped design review
- `skills/git-commit/` - Commit workflow
- `skills/git-review/` - PR review workflow

### External Resources

- [Shape Up by Basecamp](https://basecamp.com/shapeup) - Appetite-based scoping
- [Working Backwards (Amazon)](https://www.amazon.jobs/en/principles) - Start with customer, work backwards
- [YAGNI Principle](https://martinfowler.com/bliki/Yagni.html) - You Aren't Gonna Need It

---

## Conclusion

**Remember the core principle**: This is a toolkit, not a script. Cherry-pick tools that add value for your specific situation. Balance quality with velocity. Ship and iterate.

**The best spec is the one that**:
- ✅ Gives implementers clarity
- ✅ Took appropriate time for complexity
- ✅ Prevents rework from ambiguity
- ✅ Ships, doesn't sit in refinement limbo

**Now go create specs that help teams ship great software faster.**
