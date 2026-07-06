# Section 1.4 Update for appendix-concepts.md

Replace the existing section 1.4 with this:

---

### 1.4. Worktrees

A **worktree** is an isolated git workspace. By default, the daemon creates a separate git worktree for each session at `~/.claude-unleashed/worktrees/<session-id>/`. 

**Why worktrees?**

This isolation allows multiple Claude workers to modify git-backed code concurrently without:
- Overwriting each other's uncommitted changes
- Conflicting on branch checkouts
- Racing on git operations like staging/committing

Each worktree has its own branch (`claude-unleashed/<session-id>`), providing complete independence between sessions.

**Without worktrees:**

```bash
# Session A and B both editing the same repo
Session A: editing ~/my-app/auth.py (uncommitted)
Session B: editing ~/my-app/auth.py (uncommitted)
# CONFLICT! They overwrite each other's changes

Session A: git checkout main
Session B: git checkout feature-branch
# CONFLICT! Both trying to change HEAD
```

**With worktrees:**

```bash
# Each session gets its own directory
Session A (plucky-lynx):
  Directory: ~/.claude-unleashed/worktrees/abc123/
  Branch: claude-unleashed/abc123
  Editing: ~/.claude-unleashed/worktrees/abc123/auth.py

Session B (brave-fox):
  Directory: ~/.claude-unleashed/worktrees/def456/
  Branch: claude-unleashed/def456
  Editing: ~/.claude-unleashed/worktrees/def456/auth.py

# NO CONFLICTS! Completely isolated
```

**Worktree lifecycle:**

1. **Created** when session starts: `~/.claude-unleashed/worktrees/<session-id>/`
2. **Used** by the worker for all file operations
3. **Auto-pruned** when session completes (configurable grace period, default 24h)

**Manual cleanup:**

```bash
cu diagnostics worktree-prune --confirm
```

**Example: Three concurrent sessions**

```bash
# Terminal 1
cu run --repo ~/my-app --agent planner --prompt "Design auth system"
# Creates: ~/.claude-unleashed/worktrees/abc123/
# Branch: claude-unleashed/abc123

# Terminal 2
cu run --repo ~/my-app --agent executor --prompt "Implement logging"
# Creates: ~/.claude-unleashed/worktrees/def456/
# Branch: claude-unleashed/def456

# Terminal 3
cu run --repo ~/my-app --agent reviewer --prompt "Review tests"
# Creates: ~/.claude-unleashed/worktrees/ghi789/
# Branch: claude-unleashed/ghi789

# All three run simultaneously without conflicts
cu sessions ls
# plucky-lynx (planner)  - running
# brave-fox (executor)   - running
# clever-owl (reviewer)  - running
```

**Note:** Worktrees are only used in **worktree mode** (the default). Sessions running in **branch mode** (`--run-mode in-place`) work directly on your current branch without creating worktrees, but serialize per-repo to avoid conflicts. See [section 1.5 Branch Mode](#15-branch-mode) for details.

---
