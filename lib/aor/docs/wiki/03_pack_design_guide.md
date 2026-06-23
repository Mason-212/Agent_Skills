# 3. Pack Design Guide

> **TLDR:** This section answers the three design decisions every pack author faces:
> which pack type fits your use case, which executor to use inside a node, and when to
> add an `AgentSession` for multi-turn LLM reasoning.

---

## 3.1 Which Pack Type?

**First question: does your pack own execution, or does it expose tools for others to drive?**

```
Does the pack own its execution pipeline?
├── No  → ToolPack
│         (caller picks which tools to call, in what order)
└── Yes → Workflow pack
           Does it always run to completion in one shot?
           ├── Yes → Are stage boundaries meaningful to observe or test?
           │         ├── Yes → PackWorkflowOrchestrator
           │         └── No  → PackWorkflowWrapper
           └── No  → PackWorkflowOrchestrator  (needs pause/resume)
```

**`ToolPack`** — your pack contributes independent operations; the caller decides
when and how to use them. No pipeline, no sequencing. Example: `ts_stats`.

**`PackWorkflowWrapper`** — the flow is linear and always runs to completion. No
meaningful stage boundaries. Example: `ctx_forecast`.

**`PackWorkflowOrchestrator`** — stage boundaries are meaningful, or the workflow
may pause for human approval. Examples: `anomaly_intel` (5-node statistical pipeline),
`deep_insights` (4-node: validate → plan → reason → format).

---

## 3.2 Which Executor?

Inside a `PackWorkflowOrchestrator`, every node needs an executor. The default choice
is always `CallableExecutor`.

Use `LLMSingleShotExecutor` only when a single prompt → response is sufficient and
you have no need for tools or multi-turn reasoning.

Never use `AgentLoopExecutor` in production — it stores the agent as an instance
variable on the executor, which is a singleton, so conversation history leaks across
requests. See Appendix A3 for the full explanation.

---

## 3.3 When to Add an AgentSession Inside a Node

Add an `AgentSession` inside a `CallableExecutor` node when:

- The node needs LLM reasoning across multiple turns (tool calls, error recovery,
  synthesis).
- The number of turns is not fixed in advance — the LLM decides when it's done.

Do **not** add an `AgentSession` when:

- The node is deterministic computation (statistics, validation, formatting). Use a
  plain callable.
- A single LLM call is sufficient. Use `LLMSingleShotExecutor` instead.

**Key rule:** Encode LLM reasoning as a conversation inside one `AgentSession`, not
as separate workflow nodes. The `deep_insights` `agent_reasoning` node handles
decomposition, code generation, execution, error recovery, and synthesis — all inside
one session's ReAct loop. Splitting those steps into separate nodes is a category
error (see Appendix A3).

The correct pattern:

```python
async def _run_agent(ctx: WorkflowNodeExecutionContext) -> StepResult:
    session = AgentSession(AgentSessionOptions(
        model=ctx.request.metadata["model"],
        tools=self.get_tools(session_id=ctx.request.session_id),
        include_pi_tools=False,
        include_default_skills=False,
        include_global_context=False,
    ))
    try:
        last = await session.run(ctx.request.text)
        return StepResult(status=StepStatus.SUCCESS, output=last)
    finally:
        await session.shutdown()  # state discarded; next request starts clean

node = WorkflowNode("agent_reasoning", CallableExecutor(self._run_agent))
```

Each request gets a fresh `AgentSession` with no history from prior requests.
