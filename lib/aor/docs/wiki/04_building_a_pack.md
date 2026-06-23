# 4. Building a Pack

> **TLDR:** A pack is a self-contained Python package that registers domain capabilities
> with the EDC runtime. It declares its identity, manages its lifecycle, and contributes
> tools, skills, and optionally a workflow — all isolated per session.

---

## 4.1 Pack Identity and Discovery

### 4.1.1 PackDescriptor

Every pack declares its identity with a `PackDescriptor`:

```python
PackDescriptor(id="ts_stats", name="Time Series Statistical Analysis", version="1.0.0")
```

- `id` is used as the workspace directory name, logger name (`edc.pack.<id>`), and
  `PackResult.pack_id`. Keep it stable across deployments.
- `version` follows semver. Bump minor for new tools, major for breaking changes.

### 4.1.2 The create_pack() Factory

Every pack `__init__.py` must expose a `create_pack(workspace_dir: Path)` function.
`PackRegistry` calls it at load time and validates the returned object is a
`BoundDomainPack`. No explicit registration or config file needed — the directory
structure is the registry.

```python
# __init__.py
from pathlib import Path
from .my_pack import MyPack
from edc_agent.packs.descriptor import PackDescriptor

def create_pack(workspace_dir: Path) -> MyPack:
    return MyPack(
        descriptor=PackDescriptor(id="my_pack", name="My Pack", version="1.0.0"),
        workspace_dir=workspace_dir,
    )
```

### 4.1.3 Pack Discovery

`PackRegistry` discovers packs by filesystem convention. Any directory under
`agents/packs/` with an `__init__.py` is a candidate. The directory name is the pack id.

```python
registry = PackRegistry(packs_root=Path("agents/packs"))
pack_ids = registry.discover()           # ["anomaly_intel", "ctx_forecast", ...]
pack     = await registry.load("ts_stats")
```

---

## 4.2 Pack Lifecycle

```
instantiate  →  open()  →  [serve requests]  →  close()
                               ↕ per session
                         evict_session(id)
                         cleanup_session_workspace(id)
```

### 4.2.1 open() and close()

Called once per process, not per request. Load shared resources (model weights, DB
connections) in `_open_impl()`; release them in `_close_impl()`. Both are idempotent.

### 4.2.2 check_health()

Called after `open()` to verify readiness. Returns `HealthStatus(healthy=bool,
message=str)`. Default returns `healthy=True`; override when the pack has external
dependencies that can fail.

### 4.2.3 evict_session()

Call when a conversation ends. Removes the cached `AgentTool` list for that session
so closures are garbage collected. Pair with `cleanup_session_workspace(session_id)`
to delete the workspace directory on disk. Without eviction, closed sessions accumulate
in memory indefinitely.

### 4.2.4 Two Execution Paths

Every pack exposes two independent entry points. They do not know about each other:

```
Stateless path  →  run_direct(request) / resume_direct(checkpoint, response)
                   Returns WorkflowCompleted | WorkflowPaused
                   Raises  WorkflowFailedError on terminal failure
                   Use for: REST endpoints, batch jobs, scheduled tasks

Stateful path   →  get_tools(session_id) → [AgentTool, ...]
                   Each tool exposes execute(call_id, args, signal, on_update)
                   Use for: multi-turn AgentSession conversations
```

A `ToolPack` only supports the stateful path (`run_direct()` raises
`NotImplementedError`). A `PackWorkflowWrapper` or `PackWorkflowOrchestrator`
supports the stateless path.

---

## 4.3 Writing Tools

### 4.3.1 Tool Definition

Use `@pack_tool` to define a tool in `_tools.py`:

```python
from edc_agent.packs.tool import pack_tool, ToolResult, ToolExecutionContext

@pack_tool(
    name="compute_features",
    description="Compute mean, std, linear trend, and autocorrelation for a numeric "
                "time series. Call this to characterise a series before forecasting or "
                "anomaly detection.",
    parameters={
        "type": "object",
        "properties": {
            "values": {
                "type": "array",
                "items": {"type": "number"},
                "description": "Numeric time series values in chronological order",
            },
        },
        "required": ["values"],
    },
)
async def compute_features(args: dict, ctx: ToolExecutionContext) -> ToolResult:
    values = args["values"]
    # ... computation ...
    return ToolResult(content=json.dumps({"mean": mean, "std": std}))
```

### 4.3.2 Writing a Sharp Description

The `description` field is what the vendor uses to decide when to call your tool.
It is the highest-leverage string you write. Make it specific:

- State what the tool does in one sentence.
- State *when* to call it (trigger condition).
- State any preconditions or constraints.

Avoid vague descriptions like "Analyzes data" — the LLM cannot decide from that alone.

### 4.3.3 JSON Schema Best Practices

- Use `"required"` to mark mandatory fields.
- Add `"description"` to every property — the LLM uses these to fill arguments correctly.
- Keep schemas flat where possible; deeply nested schemas confuse models.
- Use `"enum"` for fields with a fixed set of valid values.

---

## 4.4 Writing Skills

### 4.4.1 Skill File Layout

```
agents/packs/partners/my_pack/
└── skills/
    └── my-pack/
        └── SKILL.md
```

### 4.4.2 What to Put in a Skill

A skill teaches the LLM *when and why* to use your tools — context the JSON schema alone
cannot express:

```markdown
# My Pack

## When to use compute_features
Call `compute_features` before any forecasting or anomaly detection task to establish
a statistical baseline. Do not call it more than once per series unless the series
has been modified.

## When to use segment_time_series
Call `segment_time_series` when the user asks about change points, structural breaks,
or regime shifts in the data.
```

Keep skills concise. The LLM receives them as plain text on every turn — verbose skills
dilute the signal.

### 4.4.3 Skills Are Static

Skills are read from disk once at `AgentSession.__init__` and baked into the system
prompt string. They cannot be changed after session construction.

---

## 4.5 Writing a Workflow

### 4.5.1 WorkflowSpec and WorkflowNode

Define the workflow shape in `_workflow.py`:

```python
from edc_orchestrator.graph import WorkflowSpec, WorkflowBuilder
from edc_orchestrator.types import WorkflowNode
from edc_orchestrator.executors import CallableExecutor

def build_workflow(model, workspace, session_id) -> WorkflowSpec:
    return (
        WorkflowBuilder("my_pack")
        .add_node(WorkflowNode("validate", CallableExecutor(_validate), allowed_next_nodes=("run",)))
        .add_node(WorkflowNode("run",      CallableExecutor(_run),      allowed_next_nodes=()))
        .set_start("validate")
        .build()
    )
```

### 4.5.2 WorkflowNode is a Singleton

`WorkflowNode` and its executor are constructed once at pack init and reused for every
request. **Executors must be stateless.** Per-request state must be created inside the
callable body and discarded before it returns.

### 4.5.3 Node Callable Signature

Every callable passed to `CallableExecutor` receives a `WorkflowNodeExecutionContext`
and returns a `StepResult`:

```python
from edc_orchestrator.types import WorkflowNodeExecutionContext, StepResult, StepStatus

async def _validate(ctx: WorkflowNodeExecutionContext) -> StepResult:
    if not ctx.request.text:
        return StepResult(status=StepStatus.FAILURE, output={"error": "empty input"})
    return StepResult(status=StepStatus.SUCCESS, output={"validated": True})
```

---

## 4.6 Disk-First Tool Response Contract

Tool execute functions should use `build_tool_response()` to format their return value.
It writes full data to `ctx.workspace_dir` and returns a compact preview to the LLM:

```python
from edc_agent.packs.tool_response import build_tool_response

return build_tool_response(
    session_id=ctx.session_id,
    output_filename="forecast.json",
    preview={"type": "forecast", "q50_first": 148.2, "trend": "upward"},
    extra={"horizon": 12},
)
# → {"status": "success", "output_path": "<session_id>/forecast.json", "preview": {...}}
```

`build_tool_response` validates `session_id` characters, blocks absolute paths and `..`
traversal, and ensures JSON-serializability. Use it instead of assembling the dict
manually.

---

## 4.7 Workspace Isolation and session_id Keying

`ctx.workspace_dir` is `<workspace_root>/<session_id>/`. Each session gets its own
directory. Never write to a shared path — two concurrent sessions writing to the same
file will race silently.

The `session_id` passed to `get_tools()` must match the `session_id` used to key the pi
`SessionManager` JSONL. This shared key correlates workspace files with LLM conversation
history for debugging.

---

## 4.8 Agent Integration (Slim)

When your node constructs an `AgentSession`, always set these three flags:

```python
session = AgentSession(AgentSessionOptions(
    model=model,
    tools=pack.get_tools(session_id=session_id),
    include_pi_tools=False,          # no bash/read/write inside a pack node
    include_default_skills=False,    # developer's personal skills are noise
    include_global_context=False,    # developer's AGENTS.md is irrelevant
    api_key=api_key,
))
```

| Flag | Default | Why set False in pack nodes |
|---|---|---|
| `include_pi_tools` | `True` | Suppresses bash/read/write/edit — pack nodes should only expose their own tools |
| `include_default_skills` | `True` | Excludes the developer's personal `~/.pi/skills/` — irrelevant to pack logic |
| `include_global_context` | `True` | Excludes `AGENTS.md` workspace context — adds noise to the system prompt |

Wire skills from your pack using `collect_skill_paths_from_pack`:

```python
from edc_agent.packs.skill_provider import collect_skill_paths_from_pack

skill_paths = collect_skill_paths_from_pack(pack)
session = AgentSession(AgentSessionOptions(
    ...
    skill_paths=skill_paths,
))
```

For full details on how `AgentSession` assembles the system prompt and tool list, and
how the vendor wire format works, see **Appendix A1**.
