# 2. Runtime Model

> **TLDR:** A pack runs inside the EDC runtime through three layers: the pack type
> determines the overall execution shape, the executor determines what runs inside each
> node, and WorkflowPolicy determines how the graph advances after each node completes.

---

## 2.1 Pack Types

There are two fundamental pack types. The distinction is **who owns execution**:

| Pack Type | Who owns execution | Entry point |
|---|---|---|
| **Tools-only** (`ToolPack`) | The caller — picks which tools to call, in what order, how many times | `get_tools(session_id)` |
| **Workflow pack** | The pack — defines the pipeline; caller just says run | `run_direct(request)` |

### 2.1.1 ToolPack — Caller Owns Execution

A `ToolPack` exposes the pack's tools directly with no workflow and no orchestration.
The caller invokes tools individually on demand.

**Use when:** your pack contributes independent, reusable operations with no fixed
execution order. The caller decides when and how many times to invoke each tool.

**Example — `ts_stats`:** provides `compute_features` and `segment_time_series` as
standalone tools. The outer agent calls whichever it needs, in whatever order the
problem requires. Forcing them into a pipeline would impose artificial sequencing.

### 2.1.2 Workflow Pack — Pack Owns Execution

A workflow pack defines its own execution pipeline. The caller triggers it and the
pack runs from start to finish. There are two variants:

**`PackWorkflowWrapper`** — a single callable. No named stages, no observable
checkpoints, no pause/resume.

**Use when:** the flow is linear, always runs to completion, and has no meaningful
stage boundaries worth observing independently.

**Example — `ctx_forecast`:** validate inputs → run forecast model → return result.
All steps are one logical operation; splitting them into nodes adds boilerplate with
no observability benefit.

---

**`PackWorkflowOrchestrator`** — a DAG of named nodes. Records execution history per
node. Can pause mid-graph for human approval and resume from a checkpoint. Does
**not** require an LLM.

**Use when:** stage boundaries are meaningful (each node is a distinct concern worth
inspecting or testing independently), or the workflow may need to pause for human
approval.

**Example — `anomaly_intel`:** five deterministic stages (`open_session → profile →
fit_world_model → run_discovery → export_findings`), each a distinct computational
concern. The execution history lets you inspect what each stage produced independently.

**Example — `deep_insights`:** four stages (`validate_input → plan_task →
agent_reasoning → format_output`). The structural boundaries — input validation,
LLM planning, LLM reasoning, output formatting — are meaningfully separate even
though only two nodes use an LLM.

---

## 2.2 Executors

An **executor** is what each workflow node delegates to. Every node has one executor
that is constructed once at pack init and reused across all requests — executors must
be stateless.

| Executor | LLM? | Use for |
|---|---|---|
| `CallableExecutor` | Either | **Default** — any Python callable, including ones that construct an `AgentSession` |
| `LLMSingleShotExecutor` | Yes (1 turn) | Single prompt → response: classify, summarise, extract |
| `AgentLoopExecutor` | Yes (many turns) | **Avoid** — leaks conversation history across requests |

`CallableExecutor` is the correct choice in almost all cases.

---

## 2.3 How a Node Invokes an LLM

A node can invoke an LLM in one of two ways, or not at all:

1. **`LLMSingleShotExecutor`** — one prompt, one response. No tools, no loop. Use for
   classification, summarization, or structured extraction.

2. **`AgentSession`** inside a `CallableExecutor` — a harness around Pi's agent that
   assembles the system prompt, tools, and skills, then drives a multi-turn ReAct loop
   until the LLM reaches a final answer. **Pi is EDC's internal LLM runtime.** As a
   pack author you never interact with Pi directly — `AgentSession` handles all setup
   and exposes a single `run(prompt)` interface.

3. **Plain `CallableExecutor`** — no LLM. Pure Python. Used for deterministic nodes
   like input validation or statistical computation.

When `AgentSession` is used, Pi drives a **ReAct** (Reason + Act) loop — the LLM
reasons, calls tools, reads results, and reasons again until it stops emitting tool
calls. See Appendix A1 for the full wire format.

---

## 2.4 WorkflowPolicy and Graph Transitions

`WorkflowPolicy` is a property of each workflow node. After every node execution it
decides what happens next.

| Decision | Meaning |
|---|---|
| `NEXT` | Advance to the next node |
| `RETRY` | Re-execute the same node |
| `COMPLETE` | Terminal success — workflow ends |
| `FAIL` | Terminal failure — workflow raises an error |
| `INTERRUPT` | Pause execution and return a checkpoint for human approval |

**`DefaultWorkflowPolicy`** covers all partner packs — it advances on success and
fails on failure. Replace it only when the next node must be chosen dynamically from
a node's output, or you need a human-in-the-loop approval step.

A paused workflow (`INTERRUPT`) can be resumed by passing the checkpoint back to
`resume_direct()`. See section 4 (Building a Pack) for the code pattern.
