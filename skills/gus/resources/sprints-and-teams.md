# Sprints and Teams

How to discover user context — who you are, what team(s) you're on, and what sprint is current.

---

## Find the Current User's Salesforce ID

```bash
sf org display user --target-org <username>@gus.com --json
```

The response includes:
- `id` — the User record ID (e.g., `005B0000006evUqIAI`)
- `username` — the login username
- `orgId` — the GUS org ID

---

## Look Up a User by Name or Email

When the user says "assign to Jane Doe" or "who is jdoe@salesforce.com", look them up on the `User` object:

```bash
# By name (supports partial match)
sf data query --query "
  SELECT Id, Name, Email, Username
  FROM User
  WHERE Name LIKE '%Doe%' AND IsActive = true
" --target-org <username>@gus.com
```

```bash
# By email
sf data query --query "
  SELECT Id, Name, Email, Username
  FROM User
  WHERE Email = 'jdoe@salesforce.com' AND IsActive = true
" --target-org <username>@gus.com
```

```bash
# By GUS username
sf data query --query "
  SELECT Id, Name, Email, Username
  FROM User
  WHERE Username = 'jdoe@gus.com' AND IsActive = true
" --target-org <username>@gus.com
```

**Note:** GUS usernames follow the pattern `<alias>@gus.com`. If the user provides a Salesforce email like `jdoe@salesforce.com`, try both `Email` and `Username` fields. If multiple results are returned, present the matches and ask the user to confirm.

---

## Find a User's Team(s)

Team membership is stored in `ADM_Scrum_Team_Member__c`. Query by the user's Salesforce ID:

```bash
sf data query --query "
  SELECT Scrum_Team__c, Scrum_Team_Name__c, Role__c
  FROM ADM_Scrum_Team_Member__c
  WHERE Member_Name__c = '<user_id>'
    AND Active__c = true
    AND Scrum_Team__r.Active__c = true
" --target-org <username>@gus.com
```

This returns all active teams the user belongs to (filtering out defunct/inactive teams), along with their role on each team.

---

## Find the Current Sprint for a Team

Sprints have `Start_Date__c` and `End_Date__c`. Query for the sprint where today falls within the range:

```bash
sf data query --query "
  SELECT Id, Name, Start_Date__c, End_Date__c, Days_Remaining__c,
         Completed_Story_Points__c
  FROM ADM_Sprint__c
  WHERE Scrum_Team__c = '<team_id>'
    AND Start_Date__c <= TODAY
    AND End_Date__c >= TODAY
" --target-org <username>@gus.com
```

### Sprint Naming Convention

Sprints typically follow the pattern: `YYYY.MMx-Team Name`

Examples:
- `2026.03b-Commerce Cloud Database Engineering (CCDE)`
- `2026.03b-Platform Encryption & Keys`

Where `MM` is the month and the letter suffix (`a`, `b`, `c`) indicates the sprint within that month.

---

## List Recent Sprints for a Team

```bash
sf data query --query "
  SELECT Id, Name, Start_Date__c, End_Date__c, Completed_Story_Points__c
  FROM ADM_Sprint__c
  WHERE Scrum_Team__c = '<team_id>'
  ORDER BY Start_Date__c DESC
  LIMIT 10
" --target-org <username>@gus.com
```

---

## Get Team Details

```bash
sf data query --query "
  SELECT Id, Name, Active__c, Product_Owner__c, Scrum_Master__c,
         Engineering_Manager__c, Supporting_Architect__c
  FROM ADM_Scrum_Team__c
  WHERE Id = '<team_id>'
" --target-org <username>@gus.com
```

Or search by name:

```bash
sf data query --query "
  SELECT Id, Name, Active__c
  FROM ADM_Scrum_Team__c
  WHERE Name LIKE '%team name%' AND Active__c = true
" --target-org <username>@gus.com
```

---

## List Team Members

```bash
sf data query --query "
  SELECT Member_Name__c, Member_Name_Formula__c, Role__c
  FROM ADM_Scrum_Team_Member__c
  WHERE Scrum_Team__c = '<team_id>' AND Active__c = true
  ORDER BY Role__c
" --target-org <username>@gus.com
```

---

## Find Product Tags for a Team

Product Tags define the product areas a team owns:

```bash
sf data query --query "
  SELECT Id, Name
  FROM ADM_Product_Tag__c
  WHERE Team__c = '<team_id>' AND Active__c = true
  ORDER BY Name
" --target-org <username>@gus.com
```

---

## Find Epics for a Team

```bash
sf data query --query "
  SELECT Id, Name, Priority__c, Development_Lead__c
  FROM ADM_Epic__c
  WHERE Team__c = '<team_id>'
  ORDER BY Priority__c
  LIMIT 20
" --target-org <username>@gus.com
```

---

## Full Context Discovery Workflow

To go from "who am I?" to "what should I work on?", follow these steps:

1. **Get your user ID:**
   ```bash
   sf org display user --target-org <username>@gus.com --json
   ```

2. **Find your team(s):**
   ```bash
   sf data query --query "SELECT Scrum_Team__c, Scrum_Team_Name__c FROM ADM_Scrum_Team_Member__c WHERE Member_Name__c = '<user_id>' AND Active__c = true AND Scrum_Team__r.Active__c = true" --target-org <username>@gus.com
   ```

3. **Find the current sprint:**
   ```bash
   sf data query --query "SELECT Id, Name FROM ADM_Sprint__c WHERE Scrum_Team__c = '<team_id>' AND Start_Date__c <= TODAY AND End_Date__c >= TODAY" --target-org <username>@gus.com
   ```

4. **List your work in the sprint:**
   ```bash
   sf data query --query "SELECT Name, Subject__c, Status__c, Priority__c, Record_Type__c, Assignee__r.Name, Story_Points__c FROM ADM_Work__c WHERE Assignee__c = '<user_id>' AND Sprint__c = '<sprint_id>' ORDER BY Priority__c" --target-org <username>@gus.com
   ```

---

## Optimized: Current Sprint Work (Fewer Queries)

The full workflow above requires 4 sequential queries. You can reduce this to 3 queries by skipping the explicit sprint lookup. Instead, filter work items directly using sprint date fields via relationship traversal. This returns **all work for the team** in the current sprint:

1. **Get your user ID:**
   ```bash
   sf org display user --target-org <username>@gus.com --json
   ```

2. **Find your team(s):**
   ```bash
   sf data query --query "SELECT Scrum_Team__c, Scrum_Team_Name__c FROM ADM_Scrum_Team_Member__c WHERE Member_Name__c = '<user_id>' AND Active__c = true AND Scrum_Team__r.Active__c = true" --target-org <username>@gus.com
   ```

3. **Get the team's work in the current sprint (no sprint ID needed):**
   ```bash
   sf data query --query "
     SELECT Name, Subject__c, Status__c, Priority__c, Record_Type__c,
            Assignee__c, Assignee__r.Name, Story_Points__c, Sprint_Name__c
     FROM ADM_Work__c
     WHERE Scrum_Team__c = '<team_id>'
       AND Sprint__r.Start_Date__c <= TODAY
       AND Sprint__r.End_Date__c >= TODAY
     ORDER BY Priority__c, Status__c
   " --target-org <username>@gus.com
   ```

This uses `Sprint__r.Start_Date__c` and `Sprint__r.End_Date__c` to find work items whose sprint is currently active, eliminating the need to query `ADM_Sprint__c` separately.

To scope to a single user's work, add `AND Assignee__c = '<user_id>'` to the WHERE clause.

**When to use:** This is ideal for team sprint board queries. If you also need sprint metadata (days remaining, velocity), use the full workflow above instead.
