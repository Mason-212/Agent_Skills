# Spec Creation Toolkit - Quick Reference

Cherry-pick what you need for your specific situation. No prescribed sequence.

## Discovery Tools

### Use `superpowers:brainstorming` when:
- Starting with vague requirements ("I want to build...")
- Need to understand problem space through dialogue
- Multiple stakeholders with different perspectives
- Requirements buried in assumptions

### Skip when:
- Requirements already clear
- Writing from existing spec/PRD
- Simple, well-understood features

---

## Validation Tools

### Use `/critique-me` rubric 1 (stress-test) when:
- Making architectural decisions
- Choosing between approaches
- Risk-sensitive decisions (performance, security, scale)

### Use `/critique-me` rubric 2 (blind spots) when:
- Spec feels complete but you're unsure what's missing
- Complex multi-component systems
- Integration points with external systems

### Use `/critique-me` rubric 3 (anti-slop) when:
- Document feels wordy or generic
- Want to ensure actionable detail
- Before sharing with implementers
- **ALWAYS validate before implementation** (critical quality gate)

### Use `/critique-me` rubrics 4+5 (code-quality, ml-design) when:
- Implementation-focused stories (not high-level epics)
- Technical design decisions already made

### Skip when:
- Early brainstorming (too early to validate)
- Simple well-understood features

---

## Expert Review Tools

### Use `/sc:spec-panel` when:
- Complex technical decisions needing multiple perspectives
- Architecture choices with long-term implications
- Disagreement among team members

### Skip when:
- Straightforward feature implementation
- Already have consensus
- Time-constrained

---

## Structure Tools

### Use Epic structure when:
- 10+ stories in scope
- Multiple sub-projects/teams involved
- Need phased rollout (foundation → features → optimization)

### Skip when:
- Single feature
- <5 stories
- Clear linear implementation path

---

## Cherry-Picking Patterns

### Pattern 1: Idea → Spec
**Start**: Vague idea  
**Use**: `superpowers:brainstorming` → manual spec → `/critique-me` rubrics 1,2,3  
**Output**: Implementation-ready story  
**Time**: 15-30 min

### Pattern 2: Problem → Investigation → Spec
**Start**: Known problem, unclear solution  
**Use**: `superpowers:brainstorming` (questions) → spike/prototype → spec → `/critique-me` rubrics 1,2  
**Output**: Evidence-based design  
**Time**: 20-45 min (includes spike)

### Pattern 3: Spec → Validation → Refine
**Start**: Draft spec exists  
**Use**: `/critique-me` rubrics 1,2,3 → refine → `/sc:spec-panel` (if needed)  
**Output**: Validated, detailed spec  
**Time**: 10-20 min

### Pattern 4: Direct Implementation
**Start**: Clear, simple feature  
**Use**: Write story directly → `/critique-me` rubric 3 (anti-slop check)  
**Output**: Story ready for implementation  
**Time**: 5-10 min

---

## Decision Trees

### Should I start with brainstorming?
```
Requirements clear? → No → Use brainstorming
                   → Yes → Skip to spec writing

Multiple stakeholders? → Yes → Use brainstorming
                       → No → Assess clarity

User stories unclear? → Yes → Use brainstorming
                      → No → Write directly
```

### Should I create an epic?
```
Story count? → 10+ → Create epic with phases
            → 5-9 → Consider epic if multiple teams
            → <5 → Skip epic, write stories directly

Multiple teams? → Yes → Create epic for coordination
               → No → Only if phased rollout needed

Phased rollout? → Yes (foundation → features → optimization) → Epic
                → No → Stories sufficient
```

### Which critique-me rubrics?
```
Always use: Rubric 3 (anti-slop) - quality gate

Add Rubric 1 (stress-test) if:
- Architectural decisions
- Performance/security critical
- Multiple approach options

Add Rubric 2 (blind spots) if:
- Complex system
- Integration points
- Feels complete but unsure

Add Rubrics 4,5 (code/ML) if:
- Implementation story (not epic)
- Technical design included
```

### Should I use spec-panel?
```
Consensus exists? → Yes → Skip panel
                 → No → Consider panel

Architecture impact? → High → Use panel
                    → Low → Skip panel

Time pressure? → Yes → Skip panel
              → No → Panel if valuable

Team disagreement? → Yes → Use panel to resolve
                  → No → Skip panel
```

---

## Anti-Patterns to Avoid

❌ **Brainstorming when requirements clear**  
→ Wastes time, delays implementation

❌ **Creating epic for <5 stories**  
→ Over-structure, slows velocity

❌ **Skipping anti-slop validation (rubric 3)**  
→ Ships generic, unactionable specs

❌ **Over-validating simple features**  
→ All 5 rubrics on "add button" - overkill

❌ **Using spec-panel without architectural impact**  
→ Multiple experts debating trivial UI change

❌ **Writing specs without examples**  
→ Implementers guess at requirements

❌ **Over-iterating on refinement**  
→ 5+ passes seeking perfection, never ships

---

## Quality Gates

### Before Writing Spec
- ✅ Requirements clear enough to write concrete examples
- ✅ Success criteria can be verified
- ✅ Scope boundaries defined (what's out of scope)

### Before Validation
- ✅ Spec includes real examples, not just descriptions
- ✅ Edge cases and error scenarios covered
- ✅ Acceptance criteria concrete and verifiable

### Before Implementation
- ✅ Passed `/critique-me` rubric 3 (anti-slop) with no major issues
- ✅ Must-fix items from validation addressed
- ✅ Implementer can answer "how do I verify this works?"

### Before Shipping (from spec)
- ✅ All Definition of Done items met
- ✅ Examples from spec implemented and tested
- ✅ Edge cases handled per spec

---

## Time Investment Guidelines

**Don't over-invest in specs.** Balance quality with velocity.

| Complexity | Discovery | Writing | Validation | Total |
|-----------|-----------|---------|------------|-------|
| Simple feature | 0 min | 5 min | 5 min (rubric 3) | 10 min |
| Medium feature | 10 min | 15 min | 10 min (rubrics 1,2,3) | 35 min |
| Complex system | 20 min | 30 min | 15 min + panel | 65 min |
| Epic (10+ stories) | 30 min | 45 min | 20 min + panel | 95 min |

**If spending >2x these times**: You're over-speccing. Ship and iterate.

---

## Superpowers Plugin Tool Map

| Superpowers Tool | What It Does | When to Use | When to Skip |
|-----------------|--------------|-------------|--------------|
| `superpowers:brainstorming` | Interactive requirements discovery via questions | Vague requirements, multiple stakeholders | Clear requirements, time pressure |
| `/critique-me` rubric 1 | Stress-test decisions and assumptions | Architectural choices, risk-sensitive | Early exploration, consensus exists |
| `/critique-me` rubric 2 | Find blind spots in coverage | Complex systems, integration heavy | Simple features, well-trodden path |
| `/critique-me` rubric 3 | Ensure substance and actionability | **Always before implementation** | Never skip (critical gate) |
| `/critique-me` rubrics 4,5 | Code quality and ML design checks | Implementation stories with code | High-level epics, conceptual specs |
| `/sc:spec-panel` | Multi-expert perspective | Architecture debates, team disagreement | Consensus exists, straightforward |

**Key insight**: The plugin has structure; you cherry-pick based on your specific needs and constraints.
