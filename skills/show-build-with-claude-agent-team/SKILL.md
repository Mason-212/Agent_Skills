---
name: show-build-with-claude-agent-team
description: Show how to use Claude Code's agent teams feature with examples
---

# How to Build with Claude Agent Teams

A quick reference guide for using Claude Code's native agent teams feature to coordinate multiple Claude agents working in parallel on a project.

## Quick Start

### 1. Enable Agent Teams (One-Time Setup)

Add to `~/.claude/settings.json`:
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

**Optional**: Enable split-panes for iTerm2 visualization:
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "teammateMode": "tmux"
}
```

**Note**: Despite the name "tmux", this auto-detects iTerm2 and works for both.

For iTerm2, also:
- Install `it2` CLI: `brew install mkusaka/it2/it2`
- Enable Python API: iTerm2 → Settings → General → Magic → Enable Python API

### 2. Create a Plan File

Write a markdown plan with:
- **Goal**: What you're building and why
- **Components**: Major parts (frontend, backend, tests, etc.)
- **File ownership**: Which files/directories each component touches
- **Tasks**: List of specific work items
- **Acceptance criteria**: Definition of done

See the example plans in `resources/examples/` for templates.

### 3. Tell Claude to Create the Team

Use natural language - just describe what you want:

**Basic Format**:
```
Create an agent team called "[name]-team" with [N] teammates based on the plan at [/absolute/path/to/plan.md].

Spawn [N] teammates ([role1], [role2], [role3]). Each teammate owns [file/directory ownership].
```

**With Plan Approval**:
```
Create an agent team called "[name]-team" with [N] teammates based on the plan at [/path/to/plan.md].

Spawn [N] teammates ([roles]). Enable plan approval for [which teammates]. Each teammate owns [ownership].
```

**With Skills**:
```
Create an agent team called "[name]-team" with [N] teammates based on the plan at [/path/to/plan.md].

Spawn [N] teammates ([roles]). All teammates should use [skill-name:params, skill2] skills. Each teammate owns [ownership].
```

## Real Examples

### Example 1: Simple Feature (2 Teammates)

**Plan**: User profile page with view and edit functionality

**Prompt**:
```
Create an agent team called "user-profile-team" with 2 teammates based on the plan at /Users/myname/project/plans/profile-feature.md.

Spawn 2 teammates (Frontend Dev for Profile UI components, Backend Dev for profile API and tests). Frontend owns src/components/Profile/, Backend owns src/routes/profile.js and src/models/User.js.
```

### Example 2: Complex System (6 Teammates with Skills)

**Plan**: NRR workflow integration with multiple components

**Prompt**:
```
Create an agent team called "nrr-workflow-integration-team" with 6 teammates based on the plan at /Users/thomaschang/Documents/dev/git/a360/edc-python/agents/specs/nrr-workflow-integration-plan.md.

Spawn 3 implementors (Deep Insight, Forecast, Causal RCA) and 3 critics (stress-test, code-quality, anti-ai-slop using /critique-me skill). Enable plan approval for implementors. Each implementor owns their specific Act page file.
```

### Example 3: Full-Stack Chat System (4 Teammates with Plan Approval)

**Plan**: Real-time chat with WebSocket, persistence, and presence

**Prompt**:
```
Create an agent team called "chat-system-team" with 4 teammates based on the plan at /Users/myname/projects/chat/plan.md.

Spawn 4 teammates (Frontend Dev for UI, Backend Dev for API/WebSocket, Infrastructure Dev for Docker setup, Testing Dev for all tests). Enable plan approval for Frontend and Backend teammates. All teammates should use git-commit and critique-me:1,2,3 skills. Frontend owns src/components/Chat/, Backend owns src/websocket/ and src/routes/chat.js, Infrastructure owns docker/ and Dockerfile, Testing owns tests/.
```

## Monitoring Your Team

### View Teammates
- **Split-panes mode**: Each teammate in separate pane, click to interact
- **In-process mode**: Press `Shift+Down` to cycle through teammates

### View Task List
- Press `Ctrl+T` to toggle task list view
- Shows pending, in-progress, and completed tasks
- Task dependencies managed automatically

### Interact with Teammates
- Click into a pane (split-panes) or cycle to them (in-process)
- Type to send them direct messages
- Redirect their approach or provide guidance

### Common Issues to Watch For
- **Lead implementing instead of delegating**: Tell it "Wait for your teammates"
- **File conflicts**: If multiple teammates edit same file, intervene and redirect
- **Stuck teammates**: Send direct guidance or ask lead to spawn replacement
- **Plan approval delays**: Check lead is reviewing plans, nudge if needed

## Cleanup

When work is done:

1. **Shut down teammates**: Ask lead to shut down each teammate gracefully
2. **Clean up team**: After all teammates exit, ask lead to clean up the team
3. **Verify**: Check `~/.claude/teams/` and `~/.claude/tasks/` are empty

**Important**: Must shut down teammates BEFORE cleanup. Lead will fail cleanup if teammates still running.

## Tips for Success

### Plan Structure
- **Clear components**: Separate frontend, backend, tests, docs
- **File ownership**: Specify which files/directories each component owns
- **10-30 tasks total**: Aim for 5-6 tasks per teammate
- **Dependencies**: Note what blocks what

### Team Sizing
- **2 teammates**: Simple features, ~10-12 tasks
- **3 teammates**: Medium complexity, ~15-18 tasks
- **4 teammates**: Complex systems, ~20-25 tasks
- **5 teammates**: Very complex, ~25-30 tasks (diminishing returns after this)

### Skills Usage
- Specify skills inline: `using /critique-me:1,2,3 skill`
- All teammates get access to specified skills
- Skills are from `~/.claude/skills/`

### Plan Approval
- Enable for risky or complex changes
- Lead reviews each teammate's plan before they implement
- Lead can approve or reject with feedback
- Add safety gate before code changes

### File Conflicts
- **Prevention**: Clear file ownership in plan and prompt
- **Detection**: Monitor for multiple teammates on same files
- **Resolution**: Pause one, redirect to different files

## Troubleshooting

### Team not creating
- Check: `echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` outputs `1`
- If not set, add to settings.json and restart Claude Code
- Verify plan file path is absolute and exists

### Teammates not visible
- **In-process mode**: Press `Shift+Down` to cycle
- **Split-panes**: Check iTerm2 Python API enabled and `it2` installed
- Verify teammateMode in settings.json

### Cleanup fails
- Check: Are all teammates shut down? `ls ~/.claude/teams/`
- Shut down each teammate individually first
- Only lead should run cleanup, never teammates

## Example Plans

See `resources/examples/` for template plans:
- **simple-plan.md**: 2-teammate user profile feature
- **complex-plan.md**: 4-teammate real-time chat system

Both show the structure, components, file ownership, and tasks format that works well with agent teams.

## Related Resources

- **Claude Code Docs**: https://code.claude.com/docs/en/agent-teams
- **Subagents**: For focused tasks without inter-agent coordination
- **Plan Mode**: Use `/plan` before creating teams to design the work structure
