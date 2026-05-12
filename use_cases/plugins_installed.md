## 1 Claude Plugins
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