# Creating Work Items

Work items are created with `sf data create record --sobject ADM_Work__c`. The record type determines whether the item is a Bug, User Story, ToDo, or Investigation.

---

## Record Types

| DeveloperName   | Label         | When to Use                                                         |
|-----------------|---------------|---------------------------------------------------------------------|
| `Bug`           | Bug           | Defects, gacks, test failures — anything broken                     |
| `User_Story`    | User Story    | Feature requests, enhancements — can have code checked in against them |
| `Investigation` | Investigation | R&D triage/diagnosis for customer support escalations               |
| `ToDo`          | ToDo          | Tasks that don't need source control check-in                       |

### Looking Up Record Type IDs

See [Stable Lookups](stable-lookups.md) for the full table of Record Type IDs. Key ones:

- **Bug:** `012T00000004MUHIA2`
- **User Story:** `0129000000006gDAAQ`
- **ToDo:** `0129000000006ByAAI`
- **Investigation:** `0129000000006lWAAQ`

---

## Recommended Fields by Record Type

There are no strictly required fields beyond auto-defaulted booleans, but these are the practical minimums for a useful work item.

> **Note:** GUS enforces `Assignee__c` as required via a custom validation rule on all record types. Always include it when creating work items — use the current user's ID if no assignee is specified.

### Bug

| Field | Purpose | Required? |
|-------|---------|-----------|
| `RecordTypeId` | Set to Bug record type ID | Yes |
| `Subject__c` | Bug title | Yes |
| `Product_Tag__c` | Product area (ID) | Yes |
| `Priority__c` | P0–P4 | Yes |
| `Found_in_Build__c` | Build where bug was found (ID) | Yes |
| `Impact__c` | Impact category (ID) | Yes |
| `Frequency__c` | How often it occurs (ID) | Yes |
| `ftest__c` | Name of automated test covering this bug | Required before closing (see [Updating Work Items](updating-work-items.md)) |
| `Details_and_Steps_to_Reproduce__c` | Reproduction steps | Strongly recommended |
| `Severity__c` | Crash, Bug - no workaround, etc. | Recommended |
| `Status__c` | Defaults to New if omitted | Optional |
| `Assignee__c` | User ID | Yes |
| `Scrum_Team__c` | Team ID | Optional (derived from Product Tag) |

### User Story

| Field | Purpose | Required? |
|-------|---------|-----------|
| `RecordTypeId` | Set to User_Story record type ID | Yes |
| `Subject__c` | Story title | Yes |
| `Product_Tag__c` | Product area (ID) | Yes |
| `Details__c` | Description / acceptance criteria | Strongly recommended |
| `Scrum_Team__c` | Team ID | Recommended |
| `Priority__c` | P0–P4 | Recommended |
| `Sprint__c` | Sprint ID | Optional |
| `Epic__c` | Epic ID | Optional |
| `Story_Points__c` | Estimation | Optional |
| `Assignee__c` | User ID | Yes |

### ToDo

| Field | Purpose | Required? |
|-------|---------|-----------|
| `RecordTypeId` | Set to ToDo record type ID | Yes |
| `Subject__c` | Title | Yes |
| `Assignee__c` | User ID | Yes |
| `Product_Tag__c` | Product area (ID) | Recommended |
| `Details__c` | Description | Optional |
| `Priority__c` | P0–P4 | Optional |
| `Epic__c` | Epic ID | Optional |

### Investigation

| Field | Purpose | Required? |
|-------|---------|-----------|
| `RecordTypeId` | Set to Investigation record type ID | Yes |
| `Subject__c` | Title | Yes |
| `Assignee__c` | User ID | Yes |
| `Product_Tag__c` | Product area (ID) | Recommended |
| `Priority__c` | P0–P4 | Recommended |
| `Details__c` | Description of the issue | Recommended |

---

## Determining the Product Tag

Product Tag is the most important field when creating work items — it controls routing, reporting, and team ownership. Users will rarely specify a tag explicitly, so you must determine it automatically.

Once resolved, the Product Tag also serves as an anchor for other lookups. Its `Team__c` field identifies the owning team, which you should use to scope searches for epics, sprints, and other team-owned objects. This is more reliable than guessing which of the user's teams to query.

### Inference Precedence

Use the **first match** from this list:

1. **User-specified tag** — the user names a tag or product area directly.
2. **Context from the request** — the user names a team, sprint, epic, or related work item that implies a specific tag or team. A cross-team bug should get the *target* team's tag, not the filing user's default.
3. **Discovery flow** (below) — fall back to the user's team membership and recent work history only when the request gives no team/product context.

### Discovery Flow (Fallback)

**Step 1 — Get the user's teams:**

```bash
sf org display user --target-org <username>@gus.com --json
# Extract the user ID from the "id" field in the response

sf data query --query "
  SELECT Scrum_Team__c, Scrum_Team_Name__c
  FROM ADM_Scrum_Team_Member__c
  WHERE Member_Name__c = '<user_id>'
    AND Active__c = true
    AND Scrum_Team__r.Active__c = true
" --target-org <username>@gus.com
```

The query filters out defunct/inactive teams via `Scrum_Team__r.Active__c = true`.

**Step 2 — Get Product Tags for the user's teams:**

```bash
sf data query --query "
  SELECT Id, Name, Team__c
  FROM ADM_Product_Tag__c
  WHERE Team__c IN ('<team_id_1>', '<team_id_2>') AND Active__c = true
  ORDER BY Name
" --target-org <username>@gus.com
```

**Step 3 — Filter out auto-assign tags:**

Many Product Tags are routing rules, not tags a human would set. Exclude tags whose names contain:
- `Autoassign`
- `Gacks`
- `violation`

These are automated bug-routing rules, not general-purpose tags.

**Step 4 — Disambiguate if needed:**

- **One candidate tag remaining** → use it.
- **Multiple candidates across different teams** → determine which team the work relates to (from sprint context, subject matter, or the user's recent work), then pick the tag for that team.
- **Multiple candidates on the same team** → check the user's recent work items, scoped to the candidate tags, to see which they use most:
  ```bash
  sf data query --query "
    SELECT Product_Tag__c, COUNT(Id) ct
    FROM ADM_Work__c
    WHERE Assignee__c = '<user_id>'
      AND Product_Tag__c IN ('<candidate_tag_id_1>', '<candidate_tag_id_2>')
      AND CreatedDate = LAST_N_DAYS:90
    GROUP BY Product_Tag__c
    ORDER BY COUNT(Id) DESC
    LIMIT 5
  " --target-org <username>@gus.com
  ```
- **Still ambiguous** → ask the user which product area the work falls under, presenting the filtered list of tags.

### Direct Lookup by Name

If the user does specify a tag name or you know the name from context:

```bash
sf data query --query "
  SELECT Id, Name, Team__c
  FROM ADM_Product_Tag__c
  WHERE Name LIKE '%search term%' AND Active__c = true
  LIMIT 10
" --target-org <username>@gus.com
```

### Impact and Frequency

Both are required for bugs. See [Stable Lookups](stable-lookups.md) for the full ID tables and selection guidance.

Common Impact values for code defects:
- **Malfunctioning** (`a0O900000004EF2EAM`) — most general code bugs
- **Has Workaround** (`a0O900000004EF0EAM`) — bug with a known workaround
- **Crash, Data Loss...** (`a0O900000004EExEAM`) — severe / data-affecting issues

Frequency values: `Always`, `Often`, `Sometimes`, `Rarely` — infer from reproduction steps.

### Found in Build

`Found_in_Build__c` is a reference to `ADM_Build__c`. Unlike Impact and Frequency, build values change over time.

**How to determine the build:** Check what the user's team has been using recently.

This is a **2-step lookup**: first aggregate recent work by `Found_in_Build__c`, then resolve those build IDs to names on `ADM_Build__c`.

```bash
# Step 1: Find the most commonly referenced build IDs in recent team work
sf data query --query "
  SELECT Found_in_Build__c, COUNT(Id) ct
  FROM ADM_Work__c
  WHERE Scrum_Team__c = '<team_id>'
    AND Found_in_Build__c <> null
    AND CreatedDate = LAST_N_DAYS:90
  GROUP BY Found_in_Build__c
  ORDER BY COUNT(Id) DESC
  LIMIT 5
" --target-org <username>@gus.com --json

# Step 2: Resolve the returned build IDs to build names
sf data query --query "
  SELECT Id, Name
  FROM ADM_Build__c
  WHERE Id IN ('<build_id_1>', '<build_id_2>', '<build_id_3>')
" --target-org <username>@gus.com
```

Use the most frequently referenced build after resolving the IDs to names. Common patterns include `main`, numbered releases (e.g., `262`, `264`), and named builds (e.g., `Off Core Build`).

If the user specifies a build name, look it up directly:

```bash
sf data query --query "
  SELECT Id, Name
  FROM ADM_Build__c
  WHERE Name LIKE '%search term%'
  LIMIT 10
" --target-org <username>@gus.com
```

### Epics

Users often refer to epics with vague or partial names (e.g., "the AI Gateway trust epic") rather than exact titles. Epic names in GUS frequently include release numbers, months, or date prefixes, so there are often many similarly-named epics spanning different time periods. The goal is to reliably translate loose user input into the correct, current epic.

#### Finding the Right Epic

**Step 1 — Scope to the right team via Product Tag.**

Don't guess which team owns the epic. Use the Product Tag you already resolved (see [Determining the Product Tag](#determining-the-product-tag)) — its `Team__c` field gives you the owning team. This is more reliable than using the user's team membership directly, since users may be on multiple teams or the epic may belong to a team the user contributes to but isn't their primary membership.

**Step 2 — Search by keywords from the user's request.**

Extract the meaningful terms from what the user said (ignoring generic words like "the", "epic", "current") and search with `LIKE`:

```bash
sf data query --query "
  SELECT Id, Name
  FROM ADM_Epic__c
  WHERE Team__c = '<product_tag_team_id>'
    AND Name LIKE '%keyword1%'
    AND Name LIKE '%keyword2%'
  ORDER BY Name
  LIMIT 20
" --target-org <username>@gus.com
```

Use multiple `AND Name LIKE` clauses to narrow results when the user provides several terms. If this returns no results, try relaxing to fewer keywords.

**Step 3 — Pick the most current epic.**

Multiple matches are common because teams create new epics each month or release cycle. To find the current one:

- **Month-prefixed epics** (e.g., `[April][AI Gateway][Trust] ...`, `[May][AI Gateway][Trust] ...`): pick the one whose month is closest to today without being in the past. If today is late in the month, the next month's epic may already exist and be the right choice.
- **Release-numbered epics** (e.g., `[252] [AI Gateway] Trust`, `[254] [AI Gateway] Trust`): pick the highest release number, which is the most current.
- **No date/release signal**: ask the user which one they mean, presenting the list.

**Step 4 — Confirm with the user** if multiple plausible current epics remain after filtering.

#### Listing All Epics for a Team

If you need to browse rather than search:

```bash
sf data query --query "
  SELECT Id, Name
  FROM ADM_Epic__c
  WHERE Team__c = '<team_id>'
  ORDER BY Name
  LIMIT 20
" --target-org <username>@gus.com
```

---

## Create Examples

### Create a Bug

```bash
sf data create record --sobject ADM_Work__c \
  --values "
    RecordTypeId='<bug_record_type_id>'
    Subject__c='Login page crashes on Safari 17'
    Product_Tag__c='<product_tag_id>'
    Priority__c='P2'
    Found_in_Build__c='<build_id>'
    Impact__c='a0O900000004EF2EAM'
    Frequency__c='a0L9000000000usEAA'
    Severity__c='Bug - no workaround'
    Details_and_Steps_to_Reproduce__c='<ol><li>Open Safari 17</li><li>Navigate to login page</li><li>Click Sign In</li><li>Page crashes</li></ol>'
  " \
  --target-org <username>@gus.com
```

### Create a User Story

```bash
sf data create record --sobject ADM_Work__c \
  --values "
    RecordTypeId='<user_story_record_type_id>'
    Subject__c='Add dark mode support to settings page'
    Product_Tag__c='<product_tag_id>'
    Scrum_Team__c='<team_id>'
    Priority__c='P3'
    Details__c='<p>As a user, I want to toggle dark mode in settings so that I can reduce eye strain.</p>'
    Story_Points__c=3
  " \
  --target-org <username>@gus.com
```

### Create a ToDo

```bash
sf data create record --sobject ADM_Work__c \
  --values "
    RecordTypeId='<todo_record_type_id>'
    Subject__c='Review Q3 security audit findings'
    Details__c='Go through the audit report and flag items for the team.'
    Priority__c='P3'
    Assignee__c='<user_id>'
  " \
  --target-org <username>@gus.com
```

---

## Create a Subtask (ADM_Task__c)

Tasks are subtasks within a work item:

```bash
sf data create record --sobject ADM_Task__c \
  --values "
    Work__c='<work_id>'
    Name='Write unit tests'
    Assigned_To__c='<user_id>'
    Status__c='Not Started'
    Starting_Hours__c=4
    Order__c=1
  " \
  --target-org <username>@gus.com
```

**Task Status values:** `Not Started`, `In Progress`, `Completed`, `Waiting on someone else`, `Deferred`

---

## Tips

- **Get the record ID back** after creation by adding `--json` — the response includes the new record's `id`.
- **Product Tag is the most important reference field** — it determines routing, reporting, and often auto-assigns the team. Always look it up first.
- **Status defaults to `New`** if not specified on creation.
- **Use formula name fields** (`Scrum_Team_Name__c`, `Product_Tag_Name__c`) when querying for display, but use the reference ID fields when creating or filtering.
- **Rich text fields use HTML** — `Details__c`, `Details_and_Steps_to_Reproduce__c`, and `Body__c` (on comments) are rich text fields that accept HTML. Use tags like `<p>`, `<br>`, `<ol>`, `<ul>`, `<li>`, `<b>`, and `<a href="...">` instead of `\n` for formatting. Plain `\n` will render as literal text, not line breaks.
