---
name: gus
description: Query, create, and update GUS work items, sprints, and teams via the Salesforce CLI
---

# GUS

## When to Use

Activate this skill when:
- Looking up a GUS work item by W- number
- Listing work assigned to a user or team
- Checking sprint status or velocity
- Creating a bug, user story, or to-do
- Updating work item status, priority, or assignment
- Adding comments to a work item
- Finding a user's team, current sprint, or product tags
- Querying epics, releases, or builds
- Assigning or removing themes on a work item
- Listing or searching themes for a team
- Inspecting which themes are assigned to a work item or which work items are in a theme

## Operating Procedure

1. Identify the user's goal: query, create, update, or comment.
2. Before acting, read the relevant resource files (see Detailed Reference below).
3. If the task requires user context (team, sprint, assigned work), start with the context discovery workflow in `resources/sprints-and-teams.md`.
4. **Read-only queries** can be executed immediately using the Salesforce CLI. Always use `--target-org <username>@gus.com`. Add `--json` when you need to parse output programmatically.
5. When creating work items, always look up reference IDs (Product Tag, Record Type, Team, Sprint) first — do not guess IDs. If the user does not specify a Product Tag, follow the discovery flow in `resources/creating-work-items.md` to determine it automatically from the user's team membership and recent work.
6. **Work items cannot be deleted.** If a user asks to delete or remove a work item, change its status to `Never` instead.
7. **Before any write operation** (create, update, comment), present a summary of what will be written and get explicit user confirmation before executing. This includes:
   - **Create:** Show the record type, subject, and all fields that will be set.
   - **Update:** Show the work item being modified and the fields/values that will change.
   - **Comment:** Show the target work item and the comment body.
8. **After any write operation**, verify the result:
   - Use `--json` on the write command to capture the returned record ID.
   - Re-query the created or updated record and show the user the confirmed state (key fields like Name, Status, Subject, Assignee).
   - For comments, show the comment body and timestamp as confirmation.
9. When displaying results, use the denormalized name fields (`Scrum_Team_Name__c`, `Product_Tag_Name__c`, `Sprint_Name__c`, `Epic_Name__c`) for readability.

## Quick Reference

| Item | Value |
|------|-------|
| GUS Org ID | `00DT0000000DpvcMAC` |
| Target Org | `<username>@gus.com` (see below) |
| Instance URL | `https://gus.my.salesforce.com` |
| Work Item Object | `ADM_Work__c` |
| Work ID Format | `W-XXXXXXXX` (e.g., `W-12345678`) |

### Salesforce CLI (`sf`) setup

If `sf` is missing or outdated:

1. **Verify** — `sf --version` (expect the modern **sf** v2 CLI, not legacy `sfdx`-only workflows).
2. **Install** — Follow Salesforce’s guide: [Install Salesforce CLI](https://developer.salesforce.com/docs/atlas.en-us.sfdx_setup.meta/sfdx_setup/sfdx_setup_install_cli.htm). Common options: platform installer from [Salesforce CLI download](https://developer.salesforce.com/tools/salesforcecli), or `npm install -g @salesforce/cli` if your environment allows it.
3. **GUS authentication** — If `sf org list` does not show org id `00DT0000000DpvcMAC`, run the **GUS login** in [Determining Your Target Org](#determining-your-target-org) below.

### Determining Your Target Org

All commands require `--target-org <username>@gus.com`. To find the correct username, run:

```bash
sf org list
```

Look for the row with Org Id `00DT0000000DpvcMAC` — the Username column is your target org value. The pattern is typically `<alias>@gus.com` (e.g., `jdoe@gus.com`).

If the GUS org is not listed, the user needs to authenticate first:

```bash
sf org login web --instance-url https://gus.my.salesforce.com --alias gus
```

### Key CLI Commands

| Action | Command |
|--------|---------|
| Query | `sf data query --query "<SOQL>" --target-org <username>@gus.com` |
| Create | `sf data create record --sobject <Object> --values "<fields>" --target-org <username>@gus.com` |
| Update | `sf data update record --sobject <Object> --where "<filter>" --values "<fields>" --target-org <username>@gus.com` |
| Get user info | `sf org display user --target-org <username>@gus.com` |

### Core Objects

| API Name | Purpose |
|----------|---------|
| `ADM_Work__c` | Work items (Bugs, User Stories, ToDos, Investigations) |
| `ADM_Scrum_Team__c` | Engineering teams |
| `ADM_Sprint__c` | Time-boxed iterations |
| `ADM_Epic__c` | Larger initiatives grouping work items |
| `ADM_Product_Tag__c` | Product area categorization |
| `ADM_Release__c` | Release versions |
| `ADM_Build__c` | Software builds |
| `ADM_Task__c` | Subtasks within a work item |
| `ADM_Comment__c` | Comments on work items |
| `ADM_Change_List__c` | Perforce changelists linked to work items |
| `ADM_Scrum_Team_Member__c` | Team membership (links Users to Teams) |
| `ADM_Theme__c` | Themes for grouping related work items |
| `ADM_Theme_Assignment__c` | Junction: assigns a work item to a theme |

## Task → File Map

| I need to... | Read this |
|--------------|-----------|
| Look up a work item by W- number | [Querying](resources/querying-work-items.md) |
| List work assigned to a user or team | [Querying](resources/querying-work-items.md) |
| Search or filter work items | [Querying](resources/querying-work-items.md) |
| Get comments, tasks, or changelists for a work item | [Querying](resources/querying-work-items.md) |
| Query releases or builds | [Querying](resources/querying-work-items.md) |
| Create a bug | [Creating](resources/creating-work-items.md) + [Stable Lookups](resources/stable-lookups.md) + [Sprints and Teams](resources/sprints-and-teams.md) |
| Create a user story or to-do | [Creating](resources/creating-work-items.md) + [Sprints and Teams](resources/sprints-and-teams.md) |
| Create a subtask on a work item | [Creating](resources/creating-work-items.md) |
| Determine the right Product Tag | [Creating](resources/creating-work-items.md) + [Sprints and Teams](resources/sprints-and-teams.md) |
| Update status, reassign, or move sprints | [Updating](resources/updating-work-items.md) |
| Close a bug (including `ftest__c`) | [Updating](resources/updating-work-items.md) |
| Add a comment to a work item | [Updating](resources/updating-work-items.md) |
| Update or complete a subtask | [Updating](resources/updating-work-items.md) |
| Find a user by name or email | [Sprints and Teams](resources/sprints-and-teams.md) |
| Find my team, sprint, or product tags | [Sprints and Teams](resources/sprints-and-teams.md) |
| Look up Record Type, Impact, or Frequency IDs | [Stable Lookups](resources/stable-lookups.md) |
| Understand field types, picklists, or relationships | [Object Model](resources/object-model.md) |
| List or search themes for a team | [Querying](resources/querying-work-items.md) |
| Get themes assigned to a work item | [Querying](resources/querying-work-items.md) |
| Get work items assigned to a theme | [Querying](resources/querying-work-items.md) |
| Assign a theme to a work item | [Updating](resources/updating-work-items.md) |
| Remove a theme from a work item | [Updating](resources/updating-work-items.md) |
