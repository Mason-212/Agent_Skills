---
name: edc-pr-tracker
description: Manage the edc-python PR tracker — update tracked people, change repo or run frequency, and trigger manual runs. Writes per-person Obsidian notes to sfVault.
---

# EDP PR Tracker

## When to Use

Activate this skill when the user wants to:
- Add or remove a person from the tracked PR list
- Change the GitHub repo being tracked
- Adjust how often the tracker runs (schedule times)
- Trigger a manual run right now
- See the current tracker configuration
- Understand what files are being written and where

## Key Paths

| Resource | Path |
|---|---|
| Config | `~/Documents/dev/git/a360/edc-python/agents/apps/data/pr_tracker/config.yaml` |
| Script | `~/Documents/dev/git/a360/edc-python/agents/apps/data/pr_tracker/pr_tracker.py` |
| Shell entry point | `~/Documents/dev/git/a360/edc-python/agents/apps/data/pr_tracker/run_pr_tracker.sh` |
| launchd plist | `~/Library/LaunchAgents/com.edc.pr-tracker.plist` |
| Output vault | `~/Documents/dev/sfVault/1_orgs/0_edc/PRs/<person>/YYYYMMDD-<pr_number>-<slug>.md` |
| Logs | `~/Library/Logs/pr-tracker.log` |

## Operating Procedure

### 0. Summarize PRs (on-demand synthesis by the agent)

When the user says "summarize today's PRs", "what's happening in the repo", "catch me up", or similar:

1. List today's vault files: `ls -t ~/Documents/dev/sfVault/1_orgs/0_edc/PRs/*/*.md`
   Filter to files with today's date prefix (YYYYMMDD).
2. Read each file — focus on **Technical Insights** and **Key Code Snippets** sections.
3. Synthesize across all files grouped by **component** (from the `components:` frontmatter field):

**Output format:**
```
## PR Activity — YYYY-MM-DD

### agents/
- **nguyen-tuan** [#1195](URL): One sentence — what design decision was made and why it matters.
- **thomaschang** [#1142](URL): One sentence.

### services/
- **peiyu-li** [#1194](URL): One sentence.

### Coordination flags
- PRs #X and #Y both touch `agents/packs/` — potential conflict or dependency.
- PR #Z introduces an architectural pivot: <what changed>.
```

**Synthesis rules:**
- One sentence per PR: "X introduces Y to solve Z" or "X trades A for B"
- Name the abstraction, not just the file path
- Surface coordination flags: two PRs touching the same component or abstraction
- Highlight architectural pivots (new components, boundary changes, deliberate removals)
- Do NOT summarize test-only PRs as design decisions

### 1. Show current config

Read `config.yaml` and display:
- `repo` and `gh_host`
- `people` list (GitHub logins)
- `schedule.times`
- `pr_limit`, `pr_state`

### 2. Add a person

Edit `config.yaml`, append the GitHub login to the `people` list. Show the user the updated list for confirmation before writing.

### 3. Remove a person

Edit `config.yaml`, remove the login from `people`. Confirm with user first.

### 4. Change repo

Edit `config.yaml`, update `repo` (format: `org/repo`) and optionally `gh_host`. Confirm before writing.

### 5. Change schedule

Two-step change — both files must stay in sync:

**Step A — update `config.yaml`** `schedule.times` list (24h `HH:MM` strings).

**Step B — update the launchd plist** `~/Library/LaunchAgents/com.edc.pr-tracker.plist`:
- Each time becomes one `<dict>` inside `<array>` under `StartCalendarInterval`
- Example for 08:00 and 17:00:
  ```xml
  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Hour</key><integer>17</integer><key>Minute</key><integer>0</integer></dict>
  </array>
  ```

**Step C — reload launchd**:
```bash
launchctl unload ~/Library/LaunchAgents/com.edc.pr-tracker.plist
launchctl load   ~/Library/LaunchAgents/com.edc.pr-tracker.plist
```

Verify with `launchctl list | grep pr-tracker`.

### 6. Trigger a manual run

```bash
bash ~/Documents/dev/git/a360/edc-python/agents/apps/data/pr_tracker/run_pr_tracker.sh
```

To preview without writing files:
```bash
bash ~/Documents/dev/git/a360/edc-python/agents/apps/data/pr_tracker/run_pr_tracker.sh --dry-run
```

Tail the log during or after a run:
```bash
tail -f ~/Library/Logs/pr-tracker.log
```

### 7. Check launchd status

```bash
launchctl list | grep pr-tracker
```

A non-zero PID means it is currently running. Exit code `0` in the last column means the last run succeeded.

## Output Format

Each run writes one file per open PR per tracked person:

```
sfVault/1_orgs/0_edc/PRs/
  nguyen-tuan/
    20260814-1195-W-23866152-Honor-modelApiName.md
  thomaschang/
    20260814-1142-W-23664450-DMO-retrieval.md
```

Files are **overwritten** on each run (same date + PR number = same filename), so re-running is idempotent. Closed/merged PR files are not auto-deleted — they remain as history.

## Safety Notes

- Always confirm people additions/removals with the user before editing `config.yaml`
- Never remove the `gh_host` key — `gh` CLI requires it to target the internal GitHub
- The plist must be unloaded before editing and reloaded after, or launchd ignores changes
- Do not run this skill on non-macOS systems (launchd is macOS-only)
