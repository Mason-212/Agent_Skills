# Stable Lookup Tables

These are reference IDs for GUS objects that rarely or never change. Use them directly instead of querying each time.

---

## Work Record Types

| DeveloperName | Label | Id |
|---------------|-------|----|
| `Bug` | Bug | `012T00000004MUHIA2` |
| `User_Story` | User Story | `0129000000006gDAAQ` |
| `ToDo` | ToDo | `0129000000006ByAAI` |
| `Investigation` | Investigation | `0129000000006lWAAQ` |
| `Template` | Template - Bug | `012T00000004NOTIA2` |
| `User_Story_Template` | Template - User Story | `012EE00000018unYAA` |

To re-query if needed:

```bash
sf data query --query "
  SELECT Id, DeveloperName, Name
  FROM RecordType
  WHERE SobjectType = 'ADM_Work__c' AND IsActive = true
" --target-org <username>@gus.com
```

---

## Impact (`ADM_Impact__c`)

Referenced by `ADM_Work__c.Impact__c`. Required for bugs.

| Name | Id |
|------|----|
| Crash, Data Loss, Data Integrity, Corruption, Data Analysis (Critical) | `a0O900000004EExEAM` |
| Performance: Production | `a0OB000000LGc4VMAT` |
| Blitz | `a0OB000000LGc4QMAT` |
| Performance: Pre-Production | `a0O900000004EEvEAM` |
| Security: Production | `a0O900000004EEwEAM` |
| Security: Pre-Production | `a0OB0000000UXLyMAO` |
| Company Reputation, Data Analysis (Non-Critical) | `a0O900000004EEyEAM` |
| Malfunctioning | `a0O900000004EF2EAM` |
| Data Privacy Compliance: Production | `a0OB0000000BuOoMAK` |
| Data Privacy Compliance: Pre-Production | `a0OB0000000BuOtMAK` |
| Poor Usability | `a0O900000004EEzEAM` |
| Access, user creation, password reset | `a0OB0000000UXJ9MAO` |
| Incorrect Doc/UI Text | `a0O900000004EF3EAM` |
| Has Workaround | `a0O900000004EF0EAM` |
| Fit & Finish UI | `a0O900000004EF7EAM` |
| Cosmetic Doc/UI Text | `a0O900000004EF1EAM` |
| Major Feature | `a0O900000004EF6EAM` |
| Minor Feature | `a0O900000004EF4EAM` |
| Trivial | `a0O900000004EF5EAM` |
| Accessibility: Task Blocking | `a0OAH000000Cb0l2AC` |
| Accessibility: Difficult to Finish | `a0OAH000000Cb0q2AC` |
| Accessibility: Limited Impact | `a0OAH000000Cb0v2AC` |
| Cost to Serve | `a0OEE000001F3rR2AS` |
| Availability | `a0OEE000001YWXy2AO` |

**How to choose:** Match the impact to the bug description. For most code defects, common values are `Malfunctioning`, `Has Workaround`, or `Crash, Data Loss...` for severe issues. If the user doesn't specify, infer from the bug's severity and description. When in doubt, ask.

To re-query:

```bash
sf data query --query "SELECT Id, Name, Order__c FROM ADM_Impact__c ORDER BY Order__c" --target-org <username>@gus.com
```

---

## Frequency (`ADM_Frequency__c`)

Referenced by `ADM_Work__c.Frequency__c`. Required for bugs.

| Name | Id |
|------|----|
| Always | `a0L9000000000usEAA` |
| Often | `a0L9000000000utEAA` |
| Sometimes | `a0L9000000000urEAA` |
| Rarely | `a0L9000000000uuEAA` |

**How to choose:** Infer from the bug description and reproduction steps. If the steps are deterministic ("always crashes when..."), use `Always`. If the user says "intermittent" or "flaky", use `Sometimes` or `Rarely`. When in doubt, ask.

To re-query:

```bash
sf data query --query "SELECT Id, Name, Order__c FROM ADM_Frequency__c ORDER BY Order__c" --target-org <username>@gus.com
```
