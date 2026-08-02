# 1. What Is a Pack?

> **TLDR:** An EDC domain pack is a self-contained Python package that registers domain
> capabilities into the EDC agent runtime. It contributes up to three building blocks —
> skills, tools, and a workflow — each with a distinct role.

---

## 1.0 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Domain Pack                                                            │
│                                                                         │
│  Skills  (SKILL.md)  ──────────────────────────────────────────┐       │
│  Tools   (_tools.py) ──────────────────────────────────────┐   │       │
│  Workflow (_workflow.py) ──────────────────────────────┐   │   │       │
│                                                        │   │   │       │
└────────────────────────────────────────────────────────┼───┼───┼───────┘
                                                         │   │   │
                                                         ▼   │   │
┌────────────────────────────────────────────────────────────┼───┼───────┐
│  PackWorkflowOrchestrator                              │   │   │       │
│                                                        │   │   │       │
│  WorkflowRuntime  (DAG)                                │   │   │       │
│                                                        │   │   │       │
│  ┌─────────────────────────┐   ┌──────────────────────────────┐        │
│  │  WfNode: validate_input │──►│  WfNode: reasoning_task      │        │
│  │                         │   │                              │        │
│  │  CallableExecutor       │   │  CallableExecutor            │        │
│  │    (python fn)          │   │  ┌────────────────────────┐  │        │
│  │                         │   │  │  AgentSession          │◄─┼────────┼──┐
│  │  WorkflowPolicy         │   │  │  System Prompt  ◄──────┼──┼────────┼──┤
│  │  (next/retry/fail)      │   │  │  Agent Loop            │  │        │  │
│  └─────────────────────────┘   │  │  Providers ◄───────────┼──┼────────┼──┘
│                                │  └────────────────────────┘  │        │
│                                │  WorkflowPolicy              │        │
│                                └──────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
```

The `PackWorkflowOrchestrator` is the primary execution container — it runs a DAG of
named nodes, each with a `CallableExecutor` and a `WorkflowPolicy`. Skills, tools, and
the workflow shape flow in from the pack. Nodes that need LLM reasoning create an
`AgentSession` internally; nodes that do not (validation, statistics, formatting) are
plain Python callables.

---

## 1.1 The Three Pack Contributions

A pack can contribute any combination of three things:

| Contribution | File | What it does |
|---|---|---|
| **Skills** | `skills/<name>/SKILL.md` | Prose injected into the system prompt — tells the LLM *when and why* to call a tool |
| **Tools** | `_tools.py` | Python functions with JSON Schema — what the LLM can actually *call* |
| **Workflow** | `_workflow.py` | A DAG of `WorkflowNode`s — orchestrates multi-step logic |

Not every pack needs all three. `ts_stats` has only tools. `anomaly_intel` has a workflow
with no LLM and no skills. `deep_insights` has all three.

---

## 1.2 Skills vs Tools — What Triggers Function Dispatch

| | Skills | Tools |
|---|---|---|
| **Format sent to LLM** | Plain text inside `system` string | JSON schema in `tools[]` array |
| **Purpose** | Tell LLM *when and why* to use a tool | Give the LLM callable Python functions — the mechanism by which the LLM crosses from reasoning into action |
| **Triggers invocation?** | **No** — prose only, no execute binding | **Yes** — LLM emits `toolCall` block; loop dispatches to Python |
| **Sent how often** | Every turn (embedded in system prompt) | Every turn (re-serialized in `tools[]`) |

**Skills are guidance. Tools are capability.** A tool with a sharp `description` is more
effective than a verbose skill — the description is what the vendor uses to decide when to
call the tool.
