# Spec Creation Examples

Real workflow examples showing how to cherry-pick from the toolkit.

---

## Example 1: Simple Feature (5 min)

**Context**: Add password visibility toggle to login form

**Workflow**:
```
1. Skip brainstorming (requirement clear)
2. Write story directly (3 min):
   - Feature: Toggle button in password field
   - Acceptance: Click shows/hides password
   - Example: Eye icon, click → plaintext, click → masked
   - Verification: Manual test + unit test for toggle logic

3. Validate with anti-slop (2 min):
   /critique-me on stories/password-toggle.md rubrics: 3
   
   Result: Passes - has concrete examples and verification
```

**Output**: Implementation-ready story, 5 min total

**Why this workflow**:
- ✅ Skipped brainstorming (feature well-understood)
- ✅ Skipped epic (single story)
- ✅ Used only rubric 3 (simple feature, no architecture decisions)
- ✅ Skipped spec-panel (no debate needed)

---

## Example 2: Medium Feature (35 min)

**Context**: Add rate limiting to public API endpoints

**Workflow**:
```
1. Light brainstorming (10 min):
   - What rate? (100 req/min per user)
   - What happens when exceeded? (429 response)
   - How to identify users? (API key)
   - Storage? (Redis)

2. Write spec (15 min):
   - Epic: NO (only 3 stories, single component)
   - Story 1: Redis rate limiter module
   - Story 2: Middleware integration
   - Story 3: Error handling and headers
   
   Each story has:
   - Examples of requests hitting limit
   - Acceptance criteria with specific numbers
   - Edge cases (no key, invalid key, burst traffic)

3. Validate with stress-test + blind spots + anti-slop (10 min):
   /critique-me on specs/rate-limiting.md rubrics: 1,2,3
   
   Findings:
   - Rubric 1: Didn't specify limit reset strategy (must-fix)
   - Rubric 2: Missing distributed rate limiting (multi-instance)
   - Rubric 3: Passes - concrete examples
   
4. Refine spec (5 min):
   - Added: Reset strategy = sliding window
   - Added: Story 2.1 = Redis shared state for multi-instance
```

**Output**: 4 implementation-ready stories, 40 min total (includes refinement)

**Why this workflow**:
- ✅ Used brainstorming to clarify storage and limits
- ✅ Skipped epic (only 4 stories, single team)
- ✅ Used rubrics 1,2 (architectural decision on rate strategy)
- ✅ Used rubric 3 (always validate)
- ✅ Skipped spec-panel (no team disagreement)

---

## Example 3: Complex Epic (95 min)

**Context**: Domain Pack Extension System for ML model integration

**Workflow**:
```
1. Brainstorming session (30 min):
   Invoked: superpowers:brainstorming
   
   Questions explored:
   - What's a domain pack? (Plugin for ML capability)
   - How do packs integrate? (Abstract base class)
   - Lifecycle? (open → use → close)
   - Tool exposure? (Optional get_tools method)
   - Validation? (PackTestHarness)
   
   Output: Clear requirements for foundation

2. Write epic structure (45 min):
   Epic: Domain Pack System
   
   Phase 1 - Foundation (3 stories):
   - Story 1.1: BoundDomainPack interface
   - Story 1.2: PackRegistry (discovery & loading)
   - Story 1.3: PackExecutionContext (multi-turn state)
   
   Phase 2 - First Packs (2 stories):
   - Story 2.1: Moirai Forecast Pack
   - Story 2.2: TabICL Scoring Pack
   
   Each story has:
   - Definition of Done (concrete deliverables)
   - Code examples showing usage
   - Test coverage requirements (21 tests for 1.1)
   - Files to create/modify
   - Integration points with existing system

3. Validate epic with stress-test + blind spots (15 min):
   /critique-me on specs/epic-foundations.md rubrics: 1,2
   
   Findings:
   - Rubric 1: How to handle pack version conflicts? (must-fix)
   - Rubric 2: Missing pack health checks (high-value)
   - Rubric 2: No pack upgrade/rollback strategy (later)
   
4. Validate Story 1.1 with all rubrics (10 min):
   /critique-me on specs/story-1.1-foundation.md rubrics: 1,2,3,4,5
   
   Findings:
   - Rubric 3: Good - concrete examples, no padding
   - Rubric 4: Suggest async context manager pattern (incorporated)
   - Rubric 5: ML-specific: How to handle model caching? (added to story)
   
5. Refine epic (10 min):
   - Added: Story 1.1 includes check_health method
   - Added: PackDescriptor includes version field
   - Added: Note about version conflict resolution (defer to 1.2)

6. Spec panel review (20 min):
   /sc:spec-panel on specs/epic-foundations.md
   
   Expert feedback:
   - Architecture: Concern about tight coupling with orchestrator
   - ML Expert: Recommend workspace isolation per pack
   - Systems: Suggest resource limits (memory, CPU)
   
   Refinement:
   - Decoupled: PackWorkflowWrapper separate from Orchestrator
   - Added: workspace_dir per pack instance
   - Defer: Resource limits to Story 1.3 (ExecutionContext)
```

**Output**: Epic with 5 detailed stories, 115 min total (includes panel)

**Why this workflow**:
- ✅ Used brainstorming (complex system, many unknowns)
- ✅ Created epic (10+ stories across 2 phases)
- ✅ Used rubrics 1,2 on epic (architectural decisions)
- ✅ Used all 5 rubrics on first story (foundation is critical)
- ✅ Used spec-panel (architectural choices with long-term impact)
- ✅ Two refinement passes (epic + first story)

---

## Example 4: Investigation Spike (20 min)

**Context**: Evaluate three approaches for async workflow orchestration

**Workflow**:
```
1. Skip brainstorming (investigation goal clear)

2. Write spike story (10 min):
   - Goal: Choose between Temporal, Celery, custom async
   - Questions to answer:
     * Which handles Pi agent interrupts?
     * What's deployment complexity?
     * License compatibility?
   - Success criteria:
     * Written comparison doc
     * Recommendation with rationale
     * POC for recommended approach
   - Time box: 4 hours
   
3. Validate with stress-test + blind spots (10 min):
   /critique-me on spikes/workflow-orchestration.md rubrics: 1,2
   
   Findings:
   - Rubric 1: Good - questions are concrete
   - Rubric 2: Missing evaluation criteria (must-fix)
   
4. Refine spike (5 min):
   - Added: Evaluation criteria (latency <100ms, Python 3.11 support)
   - Added: Decision due date (end of week)
```

**Output**: Spike story with clear investigation plan, 25 min total

**Why this workflow**:
- ✅ Skipped brainstorming (investigation scope clear)
- ✅ Skipped epic (single spike)
- ✅ Used rubrics 1,2 (decision will impact architecture)
- ✅ Skipped rubric 3 (spike is meta, not implementation)
- ✅ Skipped spec-panel (no team to coordinate yet)

---

## Example 5: Refining Existing Spec (15 min)

**Context**: Draft spec written, needs quality check before implementation

**Workflow**:
```
1. Skip brainstorming (spec already exists)
2. Skip writing (spec exists)

3. Validate draft with anti-slop only (5 min):
   /critique-me on specs/user-authentication.md rubrics: 3
   
   Findings:
   - Generic advice: "implement secure authentication" (must-fix)
   - Missing verification: "ensure performance is good" (must-fix)
   - Good examples: Login flow with error scenarios (keep)
   
4. Refine spec (8 min):
   - Removed: Generic security advice
   - Added: Specific security requirements (bcrypt, 12 rounds)
   - Fixed: "Response time <200ms on p95" (measurable)
   - Added: Verification commands (curl examples)
   
5. Re-validate (2 min):
   /critique-me on specs/user-authentication.md rubrics: 3
   
   Result: Passes - actionable, specific, verifiable
```

**Output**: Implementation-ready spec, 15 min total

**Why this workflow**:
- ✅ Skipped brainstorming (spec drafted)
- ✅ Used only rubric 3 (quality check for specificity)
- ✅ Skipped rubrics 1,2 (no architectural decisions to stress-test)
- ✅ Skipped spec-panel (straightforward auth, well-trodden)
- ✅ Single refinement pass (targeted fixes)

---

## Workflow Pattern Summary

| Example | Discovery | Structure | Validation | Expert Review | Time |
|---------|-----------|-----------|------------|---------------|------|
| Simple feature | None | Story only | Rubric 3 | None | 5 min |
| Medium feature | Light (10 min) | 4 stories | Rubrics 1,2,3 | None | 40 min |
| Complex epic | Full (30 min) | Epic + phases | All rubrics | Spec-panel | 115 min |
| Investigation spike | None | Spike story | Rubrics 1,2 | None | 25 min |
| Refine existing | None | N/A | Rubric 3 | None | 15 min |

**Key Insight**: Time investment scales with complexity, not linearly with features. Don't over-invest in simple tasks.

---

## Anti-Pattern Examples

### ❌ Example: Over-Brainstorming Simple Feature

```
Task: Add search bar to existing page
User: "Create spec for search bar"

WRONG:
1. Launch brainstorming (30 min asking about user needs)
2. Create epic with 3 phases
3. Validate with all 5 rubrics + spec-panel
4. 2 hours later: Still no implementation

RIGHT:
1. Write story directly (3 min):
   - Add search input to navbar
   - Filter on keypress
   - Example: Type "user" → show user entities
2. Validate with rubric 3 (2 min)
3. 5 min later: Ready to implement
```

### ❌ Example: Skipping Anti-Slop Validation

```
Task: Add caching layer
User: "Write spec for caching"

WRONG:
Spec contains:
- "Implement efficient caching for better performance"
- "Choose appropriate cache strategy"
- "Ensure cache invalidation is handled properly"

Result: Implementer doesn't know what to build

RIGHT:
After /critique-me rubric 3:
- "Cache user profiles in Redis with 5-minute TTL"
- "Invalidate on profile update via pub/sub"
- "Verification: Profile API latency <50ms p95"

Result: Implementer knows exactly what to build and how to verify
```

### ❌ Example: Epic for Small Scope

```
Task: 3 related stories for pagination feature
User: "Create epic for pagination"

WRONG:
Epic: Pagination System
Phase 1: Foundation (1 story)
Phase 2: Implementation (2 stories)
Result: Over-structured, slows velocity

RIGHT:
No epic, just 3 stories:
- Story 1: Backend pagination API
- Story 2: Frontend pagination component
- Story 3: Tests and edge cases
Result: Clear, simple, fast to implement
```

---

## Lessons from Real Workflows

### Lesson 1: Most Features Don't Need Brainstorming
**From Example 1**: If you can write concrete examples immediately, skip brainstorming. Save 10-30 minutes.

### Lesson 2: Always Use Rubric 3 (Anti-Slop)
**From Example 5**: Generic advice like "implement secure auth" wastes implementer time. Rubric 3 catches this every time.

### Lesson 3: Epics Are Optional
**From Example 2**: 3-4 stories don't need epic overhead. Only use for 10+ stories or multi-team coordination.

### Lesson 4: Validation Effort Scales with Risk
**From Examples 1 vs 3**: Simple feature = rubric 3 only. Architectural foundation = all rubrics + panel.

### Lesson 5: Time Box Your Spec Work
**From all examples**: If spending >2x the guideline times, you're over-speccing. Ship and iterate.
