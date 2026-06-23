# 0. Start Here

> **TLDR:** An EDC domain pack is how partner teams contribute domain-specific tools, skills, and workflows to the shared EDC agent runtime. Four reference implementations are
> available to learn from.

---

## 0.1 Overview

The EDC agent framework lets partner teams plug domain capabilities into a shared LLM
agent runtime. A **partner pack** is the unit of contribution: a self-contained Python
package that registers tools the LLM can call, prose skills that guide when to call them,
and optionally a workflow DAG that orchestrates multi-step logic.

For a one-page visual overview of the full architecture, see
`docs/wiki/resources/Packs-Archtecture.pdf`. Section 1.0 of the wiki reproduces it as
a text diagram.

Four reference implementations ship in `agents/packs/partners/`:

| Pack | What it does | EDC abstraction used |
|---|---|---|
| `anomaly_intel` | Statistical anomaly detection on time series | `PackWorkflowOrchestrator` + 5 `CallableExecutor` nodes |
| `ctx_forecast` | Short-horizon numeric forecasting | `PackWorkflowWrapper` (single callable) |
| `ts_stats` | Reusable statistical analysis tools | `ToolPack` (tools only, no workflow) |
| `deep_insights` | LLM-driven natural language Q&A over tabular data | `PackWorkflowOrchestrator` + flat Moirai pattern |

---

## 0.2 Quickstart: Build Your First Pack in 30 Minutes

### 0.2.1 Prerequisites

- Python 3.11+
- `uv` package manager (`uv sync --all-packages` to install workspace deps)
- Familiarity with async Python and Pydantic v2

### 0.2.2 Minimal Pack Layout

```
agents/packs/partners/my_pack/
├── __init__.py          ← exposes create_pack()
├── _tools.py            ← tool definitions
└── skills/
    └── my-pack/
        └── SKILL.md     ← prose guidance for the LLM
```

### 0.2.3 Step 1 — Define a Tool

```python
# _tools.py
from edc_agent.packs.tool import pack_tool, ToolResult, ToolExecutionContext

@pack_tool(
    name="greet",
    description="Return a greeting for the given name. Call this when the user asks to be greeted.",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Name to greet"}
        },
        "required": ["name"],
    },
)
async def greet(args: dict, ctx: ToolExecutionContext) -> ToolResult:
    return ToolResult(content=f"Hello, {args['name']}!")
```

### 0.2.4 Step 2 — Write a Skill

```markdown
<!-- skills/my-pack/SKILL.md -->
# My Pack

Use the `greet` tool when the user asks to be greeted by name.
Always pass the user's first name only.
```

### 0.2.5 Step 3 — Expose create_pack()

```python
# __init__.py
from pathlib import Path
from edc_agent.packs.tool_pack import ToolPack
from edc_agent.packs.descriptor import PackDescriptor

class MyPack(ToolPack):
    pass

def create_pack(workspace_dir: Path) -> MyPack:
    return MyPack(
        descriptor=PackDescriptor(id="my_pack", name="My Pack", version="1.0.0"),
        workspace_dir=workspace_dir,
    )
```

### 0.2.6 Step 4 — Run It

```bash
uv run pytest agents/packs/partners/my_pack/tests/
```

---

## 0.3 Glossary

| Term | Meaning |
|---|---|
| **Pack** | A Python package under `agents/packs/` that contributes tools, skills, and/or a workflow |
| **Tool** | A Python function with a JSON Schema, callable by the LLM via function-calling protocol |
| **Skill** | A `SKILL.md` prose file injected into the system prompt — guidance only, no function dispatch |
| **Workflow** | A DAG of `WorkflowNode`s executed by `WorkflowRuntime` (LangGraph under the hood) |
| **WorkflowNode** | A singleton node in the DAG; holds an executor and a policy |
| **Executor** | The object a `WorkflowNode` delegates to (`CallableExecutor`, `LLMSingleShotExecutor`, etc.) |
| **WorkflowPolicy** | Decides the next transition after a node completes (`NEXT`, `RETRY`, `FAIL`, etc.) |
| **AgentSession** | A request-scoped object that assembles system prompt + tools and drives the pi ReAct loop |
| **PackWorkflowWrapper** | Single async callable — no graph, no checkpointing |
| **PackWorkflowOrchestrator** | Multi-node DAG with `step_history`, pause/resume, and `WorkflowRuntime` |
| **ToolPack** | Pack variant with tools only — `run_direct()` raises `NotImplementedError` |
| **ReAct** | Reason + Act loop: LLM reasons, calls a tool, receives result, reasons again |
| **Disk-first contract** | Tool writes full output to `ctx.workspace_dir`; returns only a compact preview to the LLM |
| **session_id** | Shared key that correlates workspace files with LLM conversation history |

