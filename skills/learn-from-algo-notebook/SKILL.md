---
name: learn-from-algo-notebook
description: Generate a Bloom's Taxonomy study guide from an algorithm Jupyter notebook
---

# Learn from Algorithm Notebook

## When to Use

- The user asks you to study, review, or create a study guide from an algorithm notebook
- The user provides a `.ipynb` file and wants to learn or prepare for interviews from it
- The user says "learn from", "study", or "review" in reference to a Jupyter notebook containing algorithm problems
- The user invokes this skill with `@learn-from-algo-notebook`

## Operating Procedure

1. **Identify the source notebook.** The user must provide a `.ipynb` file path. If they haven't, ask for one.

2. **Read the notebook thoroughly.** Read every cell — markdown, code, and comments. Understand every problem, every complexity analysis, every code annotation.

3. **Determine the output path.** Write the study guide to the same directory as the source notebook, using the same base name with a `.md` extension.
   - Example: `notebooks/algos/Algo-Recursion-BackTracking.ipynb` → `notebooks/algos/Algo-Recursion-BackTracking.md`

4. **Generate the study guide** following the Document Structure below.

5. **Run verification checks** (see Verification section) and report results.

6. **Report.** Tell the user: source notebook path, output path, problem count, and the verification summary.

## Document Structure

Generate these sections in order:

### Section 1: Level 6 — Create ("Synthesize and Transfer")

This section goes first to establish the big picture before diving into individual problems.

- **Meta-template:** Synthesize one pseudocode template that unifies all problems in the notebook. Show how each problem is a parameterization of: `candidates` (choices), `constraint` (pruning), `goal` (completion), `state` (modify/restore).
- **Pattern transfer heuristic:** Build a decision tree or checklist: given a new unseen problem, which pattern from this notebook applies? Use problem characteristics as decision criteria.
- **Compose patterns:** Show one example of combining two patterns from the notebook to solve a harder problem.
- **Design a variant:** Create one novel problem variant by modifying constraints of an existing problem. Describe what changes in the solution.

### Section 2: Cross-Problem Pattern Summary

For each problem in the notebook, list:

- Pattern family (e.g., subset, permutation, constraint-backtracking, mathematical, greedy)
- Branching factor and depth
- Key pruning mechanism
- Time and space complexity
- One-sentence insight (the single most important thing to remember)

### Section 3: Per-Problem Deep Dives

For each problem in the notebook, create a subsection (`###`) containing:

- **Key insights:** 2-3 bullet points distilling the core algorithmic idea and why it works.
- **Pattern code:** Short pseudocode (5-10 lines) showing how the problem instantiates the meta-template from Section 1. Identify the four key slots: initialization, expansion/neighbor generation, termination condition, and result extraction.
- **Level 3 — Apply:**
  - *Dry-run trace:* Pick a small concrete input. Walk through the algorithm step-by-step showing state at each iteration or recursive call. Keep traces compact — show enough steps to reveal the algorithm's rhythm, then summarize the rest.
  - *Edge-case inventory:* List 2-3 edge cases and predict the algorithm's behavior on each. Note whether the notebook's code handles them correctly.
- **Level 4 — Analyze:**
  - *Structural decomposition:* Map the solution to the paradigm template. Identify what each part of the code corresponds to.
  - *Complexity anatomy:* Derive time and space complexity step-by-step:
    1. Identify the input variables that drive complexity.
    2. Count the work using the appropriate method for the algorithm type:
       - *Graph traversal:* "each node visited at most once" + "each edge inspected at most once"
       - *Recursive with memoization:* unique subproblems × work per subproblem
       - *Recursive without memoization:* recurrence relation → recursion tree (branching factor, depth, pruning)
       - *BFS with level-flushing:* total nodes enqueued × work per node
       - *Nested loops with neighbor generation:* outer × inner × work per step
    3. State the final time complexity with a one-sentence justification.
    4. Space complexity: list each contributor separately (stack depth, auxiliary structures, input mutation). Sum for total.
  - *Cross-problem comparison:* Compare to others in the notebook on at least two structural dimensions.
- **Level 5 — Evaluate:**
  - *When this approach fails:* At least one scenario where the approach is suboptimal; name the better alternative.
  - *Pruning effectiveness:* Quantify how much pruning reduces the search space versus brute force.
  - *Code critique:* Flag bugs, naming issues, correctness pitfalls, or subtle errors. These mirror real interview mistakes.
  - *Defend-your-analysis drill:* 2-3 sentence script for defending the runtime complexity if an interviewer challenged it.

After all per-problem subsections, include one synthesis paragraph identifying the deepest structural insight connecting multiple problems.

### Section 4: Gaps — What's Missing

Identify 3-5 related problem types or techniques the notebook does not cover but that a complete understanding of the topic requires. For each gap, name one canonical LeetCode-style problem.

### Section 5: Interview Extras

- **Follow-up questions:** For each problem, list 2-3 follow-up questions an interviewer would ask after you solve it.
- **Mistake log template:** Include a blank template section where the user can record their own bugs and misunderstandings during practice.
- **Spaced repetition triggers:** For each problem, write one trigger question suitable for Anki that forces recall of the key structural insight.

## Style Rules

- **Pattern code per problem.** Each problem gets a short pseudocode snippet (5-10 lines max) showing how it instantiates the meta-template. The notebook already has the full code.
- **Dense and direct.** No filler, no "in this section we will discuss." Every sentence should teach or test.
- **Preserve the notebook's analysis.** When the notebook has a good insight, reference and build on it rather than replacing it.
- **Flag, don't fix.** When noting code bugs, describe the bug and why it matters. Do not rewrite the corrected code.

## Verification

After generating the guide, perform these checks:

1. **Coverage:** Every problem in the notebook has entries in all five sections. List any gaps.
2. **Accuracy:** Complexity claims match the notebook's analysis, or explicitly note disagreements and why.
3. **No fabrication:** Every insight traces to notebook content or well-known algorithm theory.

Report: total problem count, total insight count per Bloom level, and any verification flags.

## Important Constraints

- Write the study guide to the output path (same directory, `.md` extension) — do not print it inline.
- Do not invent problem properties that aren't in the notebook.
- Do not skip problems — every problem in the notebook must appear in every section.
