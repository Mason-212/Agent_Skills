# Updating Work Items

All write operations use `--target-org <username>@gus.com`. Always confirm the action with the user before executing.

---

## Escaping User-Provided Text

User-provided text (comments, descriptions, subjects) can contain quotes, backticks, `$`, and other characters that are dangerous in shell context. Use single-quoted outer strings to prevent shell interpolation:

**Safe pattern — single-quoted outer shell string:**

```bash
sf data update record --sobject ADM_Work__c \
  --where "Name='W-12345678'" \
  --values 'Subject__c='"'"'User can'"'"'t log in with $pecial chars'"'"'' \
  --target-org <username>@gus.com
```

This is awkward for complex text. For anything beyond simple values, prefer a **heredoc approach**:

```bash
sf data update record --sobject ADM_Work__c \
  --where "Name='W-12345678'" \
  --values "$(cat <<'VALS'
Subject__c='User can\'t log in with $pecial chars'
Body__c='<p>Line 1</p><p>Line 2</p>'
VALS
)" \
  --target-org <username>@gus.com
```

The `<<'VALS'` (quoted heredoc) prevents all shell expansion inside the block.

**Rules:**
- **Always use a quoted heredoc (`<<'EOF'`)** for text containing `$`, backticks, or double quotes
- Inside the `--values` string, field values are single-quoted: `Field__c='value'`
- Escape single quotes within field values as `\'`
- Rich text fields (`Details__c`, `Details_and_Steps_to_Reproduce__c`, `Body__c`) accept HTML — use `<p>`, `<br>`, `<ol>/<li>`, etc. instead of `\n` for formatting
- Never pass raw user text into a double-quoted `--values` string without a heredoc — `$VAR` and `` `cmd` `` will be expanded by the shell

---

## Update Fields on a Work Item

```bash
sf data update record --sobject ADM_Work__c \
  --where "Name='W-12345678'" \
  --values "Status__c='In Progress'" \
  --target-org <username>@gus.com
```

Multiple fields at once:

```bash
sf data update record --sobject ADM_Work__c \
  --where "Name='W-12345678'" \
  --values "Status__c='In Progress' Priority__c='P2' Assignee__c='<user_id>'" \
  --target-org <username>@gus.com
```

## Common Update Operations

### Change Status

```bash
sf data update record --sobject ADM_Work__c \
  --where "Name='W-12345678'" \
  --values "Status__c='Fixed'" \
  --target-org <username>@gus.com
```

Open statuses: `New`, `Acknowledged`, `Triaged`, `In Progress`, `Investigating`, `More Info Reqd from Support`, `Waiting On Customer`, `Waiting On 3rd Party`, `Ready for Review`, `Fixed`, `QA In Progress`, `Waiting`, `Integrate`, `Pending Release`

Closed statuses: `Closed`, `Closed - Defunct`, `Closed - Duplicate`, `Closed - Eng Internal`, `Closed - Known Bug Exists`, `Closed - New Bug Logged`, `Closed - Resolved With Internal Tools`, `Closed - Resolved Without Code Change`, `Closed - Doc/Usability`, `Closed - Resolved with DB Script`, `Closed - No Fix - Working as Documented`, `Closed - No Fix - Working as Designed`, `Closed - No Fix - Feature Request`, `Closed - No Fix - Will Not Fix`, `Closed - Transitioned to Incident`, `Closed - Resolved by 3rd Party`, `Completed`, `Deferred`, `Duplicate`, `Inactive`, `Never`, `Not a bug`, `Not Reproducible`, `Rejected`, `Eng Internal`

### Reassign

```bash
sf data update record --sobject ADM_Work__c \
  --where "Name='W-12345678'" \
  --values "Assignee__c='<user_id>'" \
  --target-org <username>@gus.com
```

### Move to a Different Sprint

```bash
sf data update record --sobject ADM_Work__c \
  --where "Name='W-12345678'" \
  --values "Sprint__c='<sprint_id>'" \
  --target-org <username>@gus.com
```

Look up the target sprint first (see [Sprints and Teams](sprints-and-teams.md)).

### Update Story Points

```bash
sf data update record --sobject ADM_Work__c \
  --where "Name='W-12345678'" \
  --values "Story_Points__c=5" \
  --target-org <username>@gus.com
```

### Clear / Null a Field

To remove a value from a field (e.g., remove from an epic, clear a sprint, or unassign), set the field to an empty string:

```bash
sf data update record --sobject ADM_Work__c \
  --where "Name='W-12345678'" \
  --values "Epic__c=''" \
  --target-org <username>@gus.com
```

Multiple fields can be cleared at once:

```bash
sf data update record --sobject ADM_Work__c \
  --where "Name='W-12345678'" \
  --values "Epic__c='' Sprint__c=''" \
  --target-org <username>@gus.com
```

---

## Closing a Bug

Bugs have additional requirements before they can be closed. The `ftest__c` (Test) field **must** be populated.

### Test Field (`ftest__c`)

`ftest__c` is a free-text string field (max 255 chars) that documents the automated test covering this bug.

**How to populate:**

- **Fix includes a new or modified test** → set to the test class/method name (e.g., `LoginPageTest.testSafari17Crash`)
- **Manually tested** → set to `Manual Testing` or `Manual: UI`
- **Not applicable** → set to `NA` or `N/A`

### Close with Test Field

```bash
sf data update record --sobject ADM_Work__c \
  --where "Name='W-12345678'" \
  --values "Status__c='Closed' ftest__c='MyTestClass.testFixVerification'" \
  --target-org <username>@gus.com
```

### Common Closed Statuses

Pick the most specific closed status:

| Status | When to Use |
|--------|-------------|
| `Closed` | General closure after fix is verified |
| `Closed - Duplicate` | Duplicate of another work item (also set `Related_Work__c`) |
| `Closed - No Fix - Working as Designed` | Behavior is intentional |
| `Closed - No Fix - Will Not Fix` | Won't be addressed |
| `Closed - No Fix - Feature Request` | Not a bug, it's a feature request |
| `Closed - Resolved Without Code Change` | Fixed by config, data, or environment change |
| `Completed` | For user stories and to-dos |
| `Never` | Will never be fixed |
| `Not a bug` | Reported behavior is not a defect |
| `Not Reproducible` | Cannot reproduce the reported issue |
| `Deferred` | Postponed indefinitely |

---

## Adding Comments

Comments are separate records (`ADM_Comment__c`) linked to a work item.

**Note:** You need the Work record's `Id` (not the W- number) to create comments. Query the work item first to get the Id.

```bash
sf data create record --sobject ADM_Comment__c \
  --values "Work__c='<work_id>' Body__c='<p>Your comment here</p>'" \
  --target-org <username>@gus.com
```

---

## Managing Theme Assignments

Themes are linked to work items via the `ADM_Theme_Assignment__c` junction object. You need the work item's `Id` (not W- number) and the theme's `Id` for both operations.

### Assign a Theme to a Work Item

1. Look up the theme's `Id` (see [Querying](querying-work-items.md#query-themes)).
2. Look up the work item's `Id` (query by W- number).
3. Create the junction record:

```bash
sf data create record --sobject ADM_Theme_Assignment__c \
  --values "Work__c='<work_id>' Theme__c='<theme_id>'" \
  --target-org <username>@gus.com
```

**Note:** Do not set `Theme_Work_Key__c` — it is managed by the system and auto-populated. If a duplicate assignment already exists (same work + theme), the system will reject the create due to the unique constraint on `Theme_Work_Key__c`.

### Check Existing Theme Assignments Before Assigning

To avoid duplicate errors, query the exact work/theme pair first:

```bash
sf data query --query "
  SELECT Id, Name
  FROM ADM_Theme_Assignment__c
  WHERE Work__c = '<work_id>'
    AND Theme__c = '<theme_id>'
" --target-org <username>@gus.com
```

If this returns a record, the theme is already assigned and no action is needed.

### Remove a Theme from a Work Item

Theme assignments **can** be deleted (unlike work items). First find the assignment `Id`, then delete it:

```bash
# Step 1: Find the assignment record ID
sf data query --query "
  SELECT Id, Name
  FROM ADM_Theme_Assignment__c
  WHERE Work__c = '<work_id>'
    AND Theme__c = '<theme_id>'
  LIMIT 1
" --target-org <username>@gus.com

# Step 2: Delete it
sf data delete record --sobject ADM_Theme_Assignment__c \
  --record-id '<assignment_id>' \
  --target-org <username>@gus.com
```

After creating or deleting an assignment, re-query the work item's theme assignments to confirm the final state.

---

## Updating Subtasks

### Change Task Status

```bash
sf data update record --sobject ADM_Task__c \
  --where "Id='<task_id>'" \
  --values "Status__c='Completed'" \
  --target-org <username>@gus.com
```

**Task Status values:** `Not Started`, `In Progress`, `Completed`, `Waiting on someone else`, `Deferred`

### Log Hours on a Task

```bash
sf data update record --sobject ADM_Task__c \
  --where "Id='<task_id>'" \
  --values "Actual_Hours__c=6 Hours_Remaining__c=0 Status__c='Completed'" \
  --target-org <username>@gus.com
```
