# GUS Object Model Reference

> GUS Org ID: `00DT0000000DpvcMAC`
> Target Org: `<username>@gus.com`

This document describes the Salesforce custom objects in GUS and how they relate to each other, for use by AI agents interacting with GUS via the Salesforce CLI (`sf`).

---

## Core Objects

### ADM_Work__c (Work Item)

The central object in GUS. Every bug, user story, investigation, and to-do is a Work record differentiated by **Record Type**.

**Record Types:**

| DeveloperName         | Label                 | Purpose                                                       |
|-----------------------|-----------------------|---------------------------------------------------------------|
| `Bug`                 | Bug                   | Track defects or problems                                     |
| `User_Story`          | User Story            | Feature requests; can have code checked in against them       |
| `Investigation`       | Investigation         | R&D triage/diagnosis for customer support escalations         |
| `ToDo`                | ToDo                  | Unit of work that doesn't require source control check-in     |
| `Template`            | Template - Bug        | Bug template for creating bugs from a template                |
| `User_Story_Template` | Template - User Story | User story template for creating stories from a template      |

**Key Fields:**

| API Name            | Label            | Type      | Notes                                      |
|---------------------|------------------|-----------|--------------------------------------------|
| `Name`              | Work ID          | string    | Auto-generated (e.g., `W-12345678`)        |
| `Subject__c`        | Subject          | string    | Title / summary of the work item           |
| `Details__c`        | Description      | rich text (HTML) | Full description; use HTML formatting (e.g., `<br>`, `<ol>`, `<p>`) |
| `Details_and_Steps_to_Reproduce__c` | Details and Steps to Reproduce | rich text (HTML) | Bug-specific reproduction steps; use HTML formatting |
| `Status__c`         | Status           | picklist  | See status values below                    |
| `Priority__c`       | Priority         | picklist  | `P0`, `P1`, `P2`, `P3`, `P4`              |
| `Severity__c`       | Severity         | picklist  | Bug severity (see values below)            |
| `Type__c`           | Type             | picklist  | Bug subtype (Bug, Gack, Test Failure, etc) |
| `Story_Points__c`   | Story Points     | double    | Estimation points                          |
| `RecordTypeId`      | Record Type      | reference | Determines Bug vs User Story vs ToDo etc   |
| `Record_Type__c`    | Record Type      | string    | Formula field with record type name        |
| `Assignee__c`       | Assigned To      | reference | -> `User`                                  |
| `Product_Owner__c`  | Product Owner    | reference | -> `User`                                  |
| `QA_Engineer__c`    | QA Engineer      | reference | -> `User`                                  |
| `UE_Engineer__c`    | Designer         | reference | -> `User`                                  |
| `Tech_Writer__c`    | Tech Writer      | reference | -> `User`                                  |
| `Scrum_Team__c`     | Team             | reference | -> `ADM_Scrum_Team__c`                     |
| `Product_Tag__c`    | Product Tag      | reference | -> `ADM_Product_Tag__c`                    |
| `Sprint__c`         | Sprint           | reference | -> `ADM_Sprint__c`                         |
| `Epic__c`           | Epic             | reference | -> `ADM_Epic__c`                           |
| `Release__c`        | Release          | reference | -> `ADM_Release__c`                        |
| `Scheduled_Build__c`| Scheduled Build  | reference | -> `ADM_Build__c`                          |
| `Found_in_Build__c` | Found in Build   | reference | -> `ADM_Build__c`                          |
| `Parent__c`         | Parent           | reference | -> `ADM_Work__c` (self-reference)          |
| `Related_Work__c`   | Duplicate Of     | reference | -> `ADM_Work__c` (duplicate linking)       |
| `Due_Date__c`       | Due Date         | datetime  | Target completion date                     |
| `Closed_On__c`      | Closed On        | datetime  | When the item was closed                   |
| `Perforce_Status__c`| Source Control Status | picklist | Check-in status                        |
| `Branch__c`         | Branch           | string    | Source control branch                      |

**Formula/Denormalized Name Fields** (read-only, useful for queries):

| API Name              | Value                          |
|-----------------------|--------------------------------|
| `Scrum_Team_Name__c`  | Team name                      |
| `Sprint_Name__c`      | Sprint name                    |
| `Epic_Name__c`        | Epic name                      |
| `Product_Tag_Name__c` | Product tag name               |

**Note:** There are no denormalized name fields for User references (`Assignee__c`, `Product_Owner__c`, etc.). Use `Assignee__r.Name` to get human-readable names in queries. See [Querying Work Items](querying-work-items.md#useful-formula-fields-for-queries) for details.

**Status Picklist Values:**

Open statuses:
- `New`, `Acknowledged`, `Triaged`, `In Progress`, `Investigating`
- `More Info Reqd from Support`, `Waiting On Customer`, `Waiting On 3rd Party`
- `Ready for Review`, `Fixed`, `QA In Progress`
- `Waiting`, `Integrate`, `Pending Release`

Closed statuses:
- `Closed`, `Closed - Defunct`, `Closed - Duplicate`, `Closed - Eng Internal`
- `Closed - Known Bug Exists`, `Closed - New Bug Logged`
- `Closed - Resolved With Internal Tools`, `Closed - Resolved Without Code Change`
- `Closed - Doc/Usability`, `Closed - Resolved with DB Script`
- `Closed - No Fix - Working as Documented`, `Closed - No Fix - Working as Designed`
- `Closed - No Fix - Feature Request`, `Closed - No Fix - Will Not Fix`
- `Closed - Transitioned to Incident`, `Closed - Resolved by 3rd Party`
- `Completed`, `Deferred`, `Duplicate`, `Inactive`, `Never`, `Not a bug`
- `Not Reproducible`, `Rejected`, `Eng Internal`

**Severity Picklist Values (Bugs):**
- `Crash`, `Bug - no workaround`, `Bug - workaround`, `Annoying`, `Cosmetic`
- `Major Feature`, `Minor Feature`, `Trivial`

**Type Picklist Values (Bugs):**
- `Bug`, `Gack`, `Help`, `Integrate`, `Test Change`, `Test Case`, `Test Failure`
- `Bug List`, `Translation`, `Non Deterministic Test`, `Test Tool`, `Skunkforce`

---

### ADM_Epic__c (Epic)

Groups related work items into a larger initiative.

**Key Fields:**

| API Name             | Label            | Type      | Notes                              |
|----------------------|------------------|-----------|------------------------------------|
| `Name`               | Epic Name        | string    | Name of the epic                   |
| `Team__c`            | Team             | reference | -> `ADM_Scrum_Team__c`            |
| `Planned_Release__c` | Planned Release  | reference | -> `ADM_Planned_Release__c`       |
| `Scheduled_Build__c` | Scheduled Build  | reference | -> `ADM_Build__c`                 |
| `Priority__c`        | Priority         | double    | Numeric priority                   |
| `Development_Lead__c`| Development Lead | reference | -> `User`                          |
| `Design_Lead__c`     | Design Lead      | reference | -> `User`                          |
| `Quality_Lead__c`    | Quality Lead     | reference | -> `User`                          |
| `Performance_Lead__c`| Performance Lead | reference | -> `User`                          |

**Category Picklist:**
- `Component`, `Feature`, `Trust`, `Engineering`, `Non-Engineering`, `Operations`

**Relationship to Work:** Work items link to epics via `ADM_Work__c.Epic__c`.

---

### ADM_Sprint__c (Sprint)

A time-boxed iteration for a scrum team.

**Key Fields:**

| API Name                    | Label          | Type      | Notes                    |
|-----------------------------|----------------|-----------|--------------------------|
| `Name`                      | Name           | string    | Sprint name              |
| `Scrum_Team__c`             | Scrum Team     | reference | -> `ADM_Scrum_Team__c`   |
| `Start_Date__c`             | Start Date     | date      | Sprint start             |
| `End_Date__c`               | End Date       | date      | Sprint end               |
| `Days_Remaining__c`         | Days Remaining | string    | Computed days left       |
| `Completed_Story_Points__c` | Velocity       | double    | Points completed         |

**Relationship to Work:** Work items link to sprints via `ADM_Work__c.Sprint__c`.

---

### ADM_Scrum_Team__c (Scrum Team)

An engineering team in GUS.

**Key Fields:**

| API Name              | Label               | Type      | Notes                    |
|-----------------------|----------------------|-----------|--------------------------|
| `Name`                | Team Name            | string    | Team name                |
| `Active__c`           | Active               | boolean   | Whether team is active   |
| `Product_Owner__c`    | Product Owner        | reference | -> `User`                |
| `Scrum_Master__c`     | Scrum Lead           | reference | -> `User`                |
| `Engineering_Manager__c` | Engineering Manager | reference | -> `User`               |
| `Security_Champion__c`| Security Champion    | reference | -> `User`                |
| `Supporting_Architect__c` | Supporting Architect | reference | -> `User`            |
| `Cloud_LU__c`         | Cloud                | reference | -> `ADM_Cloud__c`        |
| `Forwarding_Team__c`  | Forwarding Team      | reference | -> `ADM_Scrum_Team__c` (self-ref) |

---

### ADM_Product_Tag__c (Product Tag)

Categorizes work by product area. Used for routing, reporting, and ownership.

**Key Fields:**

| API Name         | Label            | Type      | Notes                    |
|------------------|------------------|-----------|--------------------------|
| `Name`           | Product Tag Name | string    | Tag name                 |
| `Active__c`      | Active           | boolean   | Whether tag is active    |
| `Team__c`        | Team             | reference | -> `ADM_Scrum_Team__c`   |

**Relationship to Work:** Work items link via `ADM_Work__c.Product_Tag__c`.

---

### ADM_Release__c (Release)

A release or patch version.

**Key Fields:**

| API Name            | Label          | Type      | Notes                      |
|---------------------|----------------|-----------|----------------------------|
| `Name`              | Release Name   | string    | Release name               |
| `Status__c`         | Status         | picklist  | Release status             |
| `Release_Date__c`   | Base Release Date | datetime | Target release date      |
| `Build__c`          | Build          | reference | -> `ADM_Build__c`          |
| `Major_Release__c`  | Major Release  | reference | -> `ADM_Release__c` (self-ref) |
| `Application__c`    | Application    | reference | -> `ADM_Application__c`    |
| `Release_Manager__c`| Release Manager | reference | -> `User`                 |

**Relationship to Work:** Work items link via `ADM_Work__c.Release__c`. The junction object `ADM_Released_In__c` tracks which releases a work item was actually released in.

---

### ADM_Build__c (Build)

A specific build of the software.

**Key Fields:**

| API Name         | Label       | Type      | Notes                      |
|------------------|-------------|-----------|----------------------------|
| `Name`           | Name        | string    | Build name/number          |
| `Application__c` | Application | reference | -> `ADM_Application__c`    |

**Relationship to Work:** Referenced by `ADM_Work__c.Scheduled_Build__c` (target build) and `ADM_Work__c.Found_in_Build__c` (build where bug was found).

---

### ADM_Theme__c (Theme)

A grouping mechanism for work items. Themes can be associated with a scrum team via `Scrum_Team__c`, and work items are linked to themes via the `ADM_Theme_Assignment__c` junction object.

**Key Fields:**

| API Name         | Label       | Type      | Notes                                |
|------------------|-------------|-----------|--------------------------------------|
| `Name`           | Theme Name  | string    | Theme name                           |
| `Active__c`      | Active      | boolean   | Whether theme is active              |
| `Scrum_Team__c`  | Scrum Team  | reference | -> `ADM_Scrum_Team__c`               |
| `Description__c` | Description | textarea  | Optional description of the theme    |
| `Theme_Rank__c`  | Theme Rank  | double    | Numeric priority/ordering rank       |
| `Color__c`       | Color       | string    | Display color for the theme          |

**Relationship to Work:** Via junction object `ADM_Theme_Assignment__c`.

---

## Child / Junction Objects

### ADM_Task__c (Task / Subtask)

Subtasks within a work item for tracking individual pieces of work.

| API Name           | Label          | Type      | Notes                    |
|--------------------|----------------|-----------|--------------------------|
| `Name`             | Task Name      | string    | Task title               |
| `Work__c`          | Work           | reference | -> `ADM_Work__c`         |
| `Assigned_To__c`   | Assigned To    | reference | -> `User`                |
| `Status__c`        | Status         | picklist  | See below                |
| `Starting_Hours__c`| Starting Hours | double    | Estimated hours          |
| `Hours_Remaining__c`| Hours Remaining | double  | Remaining hours          |
| `Actual_Hours__c`  | Actual Hours   | double    | Hours spent              |
| `Due_By__c`        | Due By         | date      | Task due date            |
| `Completed_On__c`  | Completed On   | datetime  | Completion timestamp     |
| `Order__c`         | Order          | double    | Sort order               |

**Task Status Picklist:**
- `Not Started`, `In Progress`, `Completed`, `Waiting on someone else`, `Deferred`

---

### ADM_Comment__c (Comment)

Comments/notes on a work item.

| API Name                | Label              | Type      | Notes                    |
|-------------------------|--------------------|-----------|--------------------------|
| `Name`                  | Story Comment Name | string    | Auto-generated           |
| `Work__c`               | Work               | reference | -> `ADM_Work__c`         |
| `Body__c`               | Comment            | rich text (HTML) | Comment text; use HTML formatting |
| `Comment_Created_By__c` | Comment Created By | reference | -> `User`                |
| `Comment_Created_Date__c`| Comment Created Date | datetime | When posted            |

---

### ADM_Change_List__c (Change List / Perforce Changelist)

Links source control changes to work items.

| API Name             | Label         | Type      | Notes                         |
|----------------------|---------------|-----------|-------------------------------|
| `Name`               | Changelist ID | string    | ID of the changelist          |
| `Work__c`            | Work          | reference | -> `ADM_Work__c`              |
| `Task__c`            | Task          | reference | -> `ADM_Task__c`              |
| `Perforce_Changelist__c` | Changelist # | string | Perforce CL number           |
| `Branch__c`          | Branch        | string    | Branch name                   |
| `Check_In_By__c`     | Check-in By   | reference | -> `User`                     |
| `Check_In_Date__c`   | Check-in Date | datetime  | When checked in               |

---

### ADM_Parent_Work__c (Parent-Child Work Relationship)

Junction object linking work items in a parent-child hierarchy (separate from `ADM_Work__c.Parent__c`).

| API Name          | Label        | Type      | Notes                    |
|-------------------|--------------|-----------|--------------------------|
| `Parent_Work__c`  | Parent Work  | reference | -> `ADM_Work__c`         |
| `Child_Work__c`   | Child Work   | reference | -> `ADM_Work__c`         |

---

### ADM_Released_In__c (Released In)

Junction object tracking which releases a work item was released in.

| API Name     | Label      | Type      | Notes                    |
|--------------|------------|-----------|--------------------------|
| `Work__c`    | Work ID    | reference | -> `ADM_Work__c`         |
| `Release__c` | Release    | reference | -> `ADM_Release__c`      |

---

### ADM_Theme_Assignment__c (Theme Assignment)

Junction object assigning work items to themes (many-to-many between `ADM_Work__c` and `ADM_Theme__c`).

| API Name           | Label            | Type      | Notes                                                   |
|--------------------|------------------|-----------|---------------------------------------------------------|
| `Name`             | Theme Assignment | string    | Auto-generated (format: `THA-NNNNNNN`)                  |
| `Work__c`          | Work             | reference | -> `ADM_Work__c`                                        |
| `Theme__c`         | Theme            | reference | -> `ADM_Theme__c`                                       |
| `Theme_Work_Key__c`| Theme Work Key   | string    | Unique composite key (`<WorkId>@<ThemeId>`); prevents duplicate assignments |

**Note:** `Theme_Work_Key__c` acts as a uniqueness guard. Do not set it manually — it is managed by the system. When assigning a theme, only set `Work__c` and `Theme__c`.

---

### ADM_Work_Subscriber__c (Work Subscriber)

Tracks users subscribed to work item notifications.

---

### ADM_Acceptance_Criterion__c (Acceptance Criteria)

Acceptance criteria linked to a work item via `Work__c`.

---

### ADM_Team_Dependency__c (Team Dependency)

Tracks dependencies between teams on work items.

| API Name                   | Notes                              |
|----------------------------|------------------------------------|
| `Dependent_User_Story__c`  | Work item that depends on another  |
| `Provider_User_Story__c`   | Work item being depended upon      |

---

## Entity Relationship Diagram (Text)

```
ADM_Scrum_Team__c ──────────────────────┐
  │                                      │
  ├── has many ADM_Sprint__c             │
  ├── has many ADM_Epic__c               │
  ├── has many ADM_Product_Tag__c        │
  └── has many ADM_Theme__c              │
                                         │
ADM_Work__c ─────────────────────────────┤
  │  (Bug | User Story | Investigation | ToDo)
  │                                      │
  ├── belongs to ADM_Scrum_Team__c ──────┘
  ├── belongs to ADM_Sprint__c
  ├── belongs to ADM_Epic__c
  ├── belongs to ADM_Product_Tag__c
  ├── belongs to ADM_Release__c
  ├── belongs to ADM_Build__c (Scheduled + Found In)
  ├── self-ref Parent__c (simple parent)
  │
  ├── has many ADM_Task__c (subtasks)
  ├── has many ADM_Comment__c (comments)
  ├── has many ADM_Change_List__c (source control changes)
  ├── has many ADM_Acceptance_Criterion__c
  ├── has many ADM_Work_Subscriber__c
  │
  ├── many-to-many ADM_Parent_Work__c (parent/child hierarchy)
  ├── many-to-many ADM_Released_In__c (released in which releases)
  ├── many-to-many ADM_Theme_Assignment__c (themes)
  └── many-to-many ADM_Team_Dependency__c (team dependencies)

ADM_Release__c
  ├── has ADM_Build__c
  └── self-ref Major_Release__c (major/minor hierarchy)
```

For CLI command examples, see the workflow guides: [Querying](querying-work-items.md), [Creating](creating-work-items.md), [Updating](updating-work-items.md).
