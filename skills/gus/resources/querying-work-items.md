# Querying Work Items

All queries use `sf data query` with `--target-org <username>@gus.com`. Add `--json` for machine-readable output.

## Escaping in SOQL

- Single quotes must be escaped as `\'` inside SOQL string literals (e.g., `WHERE Subject__c LIKE '%can\'t log in%'`)
- Newlines are not allowed in SOQL string literals — use single-line search terms
- The `!` character triggers bash history expansion inside double-quoted strings. Use `<>` instead of `!=` for not-equal comparisons (e.g., `Field__c <> null` instead of `Field__c != null`)

For escaping in write operations (`--values`), see [Updating Work Items](updating-work-items.md).

---

## Look Up a Work Item by W- Number

```bash
sf data query --query "
  SELECT Id, Name, Subject__c, Status__c, Priority__c, Record_Type__c,
         Assignee__c, Scrum_Team_Name__c, Sprint_Name__c, Epic_Name__c,
         Product_Tag_Name__c, Story_Points__c, Details__c,
         Details_and_Steps_to_Reproduce__c, Due_Date__c, Closed_On__c
  FROM ADM_Work__c
  WHERE Name = 'W-12345678'
" --target-org <username>@gus.com
```

## List Work Assigned to a User

First get the user's Salesforce ID (see [Sprints and Teams](sprints-and-teams.md)), then:

```bash
sf data query --query "
  SELECT Name, Subject__c, Status__c, Priority__c, Record_Type__c,
         Story_Points__c, Sprint_Name__c
  FROM ADM_Work__c
  WHERE Assignee__c = '<user_id>'
    AND Status__c IN (
      'New','Acknowledged','Triaged','In Progress','Investigating',
      'More Info Reqd from Support','Waiting On Customer','Waiting On 3rd Party',
      'Ready for Review','Fixed','QA In Progress',
      'Waiting','Integrate','Pending Release'
    )
  ORDER BY Priority__c, Status__c
" --target-org <username>@gus.com
```

**Note:** This query uses an allowlist of open statuses rather than excluding closed ones, so newly added closed statuses won't leak through.

## Filter by Status

```bash
# All in-progress work for a team
sf data query --query "
  SELECT Name, Subject__c, Record_Type__c, Assignee__c, Assignee__r.Name,
         Priority__c, Story_Points__c
  FROM ADM_Work__c
  WHERE Scrum_Team__c = '<team_id>'
    AND Status__c = 'In Progress'
" --target-org <username>@gus.com
```

Common open statuses to filter on: `New`, `Triaged`, `In Progress`, `Fixed`, `QA In Progress`, `Ready for Review`.

## Filter by Sprint

```bash
sf data query --query "
  SELECT Name, Subject__c, Status__c, Priority__c, Record_Type__c,
         Assignee__c, Assignee__r.Name, Story_Points__c
  FROM ADM_Work__c
  WHERE Sprint__c = '<sprint_id>'
  ORDER BY Priority__c
" --target-org <username>@gus.com
```

## Filter by Epic

```bash
sf data query --query "
  SELECT Name, Subject__c, Status__c, Priority__c, Record_Type__c,
         Assignee__c, Assignee__r.Name
  FROM ADM_Work__c
  WHERE Epic__c = '<epic_id>'
  ORDER BY Priority__c
" --target-org <username>@gus.com
```

## Filter by Product Tag

```bash
sf data query --query "
  SELECT Name, Subject__c, Status__c, Priority__c
  FROM ADM_Work__c
  WHERE Product_Tag__c = '<product_tag_id>'
    AND Status__c IN (
      'New','Acknowledged','Triaged','In Progress','Investigating',
      'More Info Reqd from Support','Waiting On Customer','Waiting On 3rd Party',
      'Ready for Review','Fixed','QA In Progress',
      'Waiting','Integrate','Pending Release'
    )
  ORDER BY Priority__c
" --target-org <username>@gus.com
```

## Search by Subject

```bash
sf data query --query "
  SELECT Name, Subject__c, Status__c, Priority__c, Record_Type__c
  FROM ADM_Work__c
  WHERE Subject__c LIKE '%search term%'
  LIMIT 20
" --target-org <username>@gus.com
```

**Note:** SOQL `LIKE` is case-insensitive for most fields.

## Get Comments on a Work Item

```bash
sf data query --query "
  SELECT Body__c, Comment_Created_By__c, Comment_Created_Date__c
  FROM ADM_Comment__c
  WHERE Work__c = '<work_id>'
  ORDER BY Comment_Created_Date__c DESC
" --target-org <username>@gus.com
```

## Get Tasks (Subtasks) for a Work Item

```bash
sf data query --query "
  SELECT Name, Status__c, Assigned_To__c, Hours_Remaining__c,
         Actual_Hours__c, Order__c, Completed_On__c
  FROM ADM_Task__c
  WHERE Work__c = '<work_id>'
  ORDER BY Order__c
" --target-org <username>@gus.com
```

## Get Change Lists (Perforce) for a Work Item

```bash
sf data query --query "
  SELECT Name, Perforce_Changelist__c, Branch__c, Check_In_By__c, Check_In_Date__c
  FROM ADM_Change_List__c
  WHERE Work__c = '<work_id>'
  ORDER BY Check_In_Date__c DESC
" --target-org <username>@gus.com
```

## Get Child Work Items

Work items can have children via the `ADM_Parent_Work__c` junction object:

```bash
sf data query --query "
  SELECT Child_Work__c, Child_Subject__c, Child_Status__c, Child_Sprint__c
  FROM ADM_Parent_Work__c
  WHERE Parent_Work__c = '<work_id>'
" --target-org <username>@gus.com
```

Or via the simple `Parent__c` self-reference:

```bash
sf data query --query "
  SELECT Name, Subject__c, Status__c
  FROM ADM_Work__c
  WHERE Parent__c = '<work_id>'
" --target-org <username>@gus.com
```

## Get Parent Work Item

Check **both** paths — a work item may use the direct self-reference, the junction object, or both:

```bash
# Direct parent (Parent__c self-reference on ADM_Work__c)
sf data query --query "
  SELECT Parent__c, Parent__r.Name, Parent__r.Subject__c, Parent__r.Status__c
  FROM ADM_Work__c
  WHERE Id = '<work_id>' AND Parent__c <> null
" --target-org <username>@gus.com
```

```bash
# Junction-object parents (ADM_Parent_Work__c)
sf data query --query "
  SELECT Parent_Work__c, Parent_Work_Subject__c, Parent_Status__c
  FROM ADM_Parent_Work__c
  WHERE Child_Work__c = '<work_id>'
" --target-org <username>@gus.com
```

**Note:** Always query both. Reporting "no parent" requires that both return empty results.

## Query Releases

```bash
# Search by name
sf data query --query "
  SELECT Id, Name, Status__c, Release_Date__c
  FROM ADM_Release__c
  WHERE Name LIKE '%262%'
  ORDER BY Release_Date__c DESC
  LIMIT 10
" --target-org <username>@gus.com
```

```bash
# Get releases a work item was released in
sf data query --query "
  SELECT Release__c, Release_Name__c
  FROM ADM_Released_In__c
  WHERE Work__c = '<work_id>'
" --target-org <username>@gus.com
```

## Query Builds

```bash
# Search by name
sf data query --query "
  SELECT Id, Name
  FROM ADM_Build__c
  WHERE Name LIKE '%main%'
  LIMIT 10
" --target-org <username>@gus.com
```

```bash
# Recent builds
sf data query --query "
  SELECT Id, Name
  FROM ADM_Build__c
  ORDER BY CreatedDate DESC
  LIMIT 10
" --target-org <username>@gus.com
```

## Query Themes

### List Active Themes for a Team

First get the team ID (see [Sprints and Teams](sprints-and-teams.md)), then:

```bash
sf data query --query "
  SELECT Id, Name, Description__c, Theme_Rank__c, Color__c
  FROM ADM_Theme__c
  WHERE Scrum_Team__c = '<team_id>'
    AND Active__c = true
  ORDER BY Theme_Rank__c
" --target-org <username>@gus.com
```

Many themes are associated with a team via `Scrum_Team__c`. Remove `AND Active__c = true` if you need inactive or historical themes too, or use the name search below to find themes with no team set.

### Search Themes by Name

```bash
sf data query --query "
  SELECT Id, Name, Description__c, Scrum_Team__c, Scrum_Team__r.Name, Active__c
  FROM ADM_Theme__c
  WHERE Name LIKE '%search term%'
    AND Active__c = true
  ORDER BY Name
" --target-org <username>@gus.com
```

Add `AND Scrum_Team__c = '<team_id>'` if you want to scope the search to one team.

### Get Themes Assigned to a Work Item

First get the work item's `Id` (not the W- number), then query the junction object:

```bash
sf data query --query "
  SELECT Id, Theme__c, Theme__r.Name, Theme__r.Description__c
  FROM ADM_Theme_Assignment__c
  WHERE Work__c = '<work_id>'
" --target-org <username>@gus.com
```

The returned `Id` is the theme-assignment record ID; keep it if you plan to remove the theme later.

### Get Work Items Assigned to a Theme

First get the theme's `Id` from one of the queries above, then:

```bash
sf data query --query "
  SELECT Work__c, Work__r.Name, Work__r.Subject__c, Work__r.Status__c
  FROM ADM_Theme_Assignment__c
  WHERE Theme__c = '<theme_id>'
  ORDER BY Work__r.Name
" --target-org <username>@gus.com
```

---

## Useful Formula Fields for Queries

These denormalized fields on `ADM_Work__c` let you avoid joins:

| Field | Contains |
|-------|----------|
| `Scrum_Team_Name__c` | Team name string |
| `Sprint_Name__c` | Sprint name string |
| `Epic_Name__c` | Epic name string |
| `Product_Tag_Name__c` | Product tag name string |
| `Record_Type__c` | Record type name (Bug, User Story, etc.) |

Use these for display purposes. Use the `__c` reference fields (e.g., `Scrum_Team__c`) for filtering by ID.

**Resolving names for User reference fields:**

There are no formula/denormalized name fields for user references like `Assignee__c`, `Product_Owner__c`, or `QA_Engineer__c`. Use the `__r` relationship syntax to get the user's name inline:

| Instead of | Use |
|------------|-----|
| `Assignee__c` (returns User ID) | `Assignee__c, Assignee__r.Name` (returns ID + name) |
| `Product_Owner__c` | `Product_Owner__c, Product_Owner__r.Name` |
| `QA_Engineer__c` | `QA_Engineer__c, QA_Engineer__r.Name` |

This works for any reference field pointing to `User`. The `__r` syntax traverses the relationship and returns fields from the related record.
