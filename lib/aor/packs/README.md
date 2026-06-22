# Multi-Agent Workflow Experiments

The goal of this directory is to stress-test promising multi-agent workflow patterns.

Traditional multi-agent approaches — fully autonomous agent swarms, ad-hoc orchestration — are hard to adopt in practice because they are:

- **Non-deterministic**: the same input can produce wildly different agent interaction sequences
- **Hard to observe**: it is difficult to know which agent said what, when, and why a decision was made
- **Hard to tune**: changing one agent's prompt can have unpredictable ripple effects on others

## Our approach

Each pack here defines a **DAG with named, observable nodes**. Each node runs a fresh LLM call with an explicit role definition. This gives us:

- **Deterministic structure**: the workflow topology is fixed; only content varies
- **Observability**: every node's input and output is recorded in the run directory
- **Tunability**: each node's behavior is controlled by a single `roles/*.md` file — editable without touching the DAG

## Design intent

These packs are intentionally **simple**: no agentic loop, no tools, no `AgentSession`. Each node is a single LLM call with a defined role. The DAG topology itself is the orchestration mechanism — that is what makes these patterns deterministic and observable.

The `roles/` files define **what each node is** (its persona and responsibility), not what it can do. The graph is designed to be user-configurable: the user controls the topology and role definitions, not the pack.

Future packs will showcase the full capacity of the `aor` framework — including `AgentSession`, tools, and more complex node executors — once these simpler patterns are validated.

## Packs

| Pack | Pattern | Use case |
|---|---|---|
| `multiagent_adversarial` | Generator → Verifier loop | Stress-test output quality via a user-defined executable verification gate |
| `multiagent_roles` | Role-based message passing | Structured collaboration: product manager → engineer → reviewer |
| `multiagent_solution_space` | Fan-out / fan-in | Explore N independent sub-domains in parallel, synthesize the best answer |

## Pack layout

```
my_pack/
  __init__.py           ← create_pack() factory, run dir setup
  _workflow.py          ← WorkflowSpec DAG definition and node logic
  agents/
    <agent_name>/
      ROLE.md           ← role definition fed into this agent's LLM system prompt
      _tools.py         ← tools this agent can call (optional, add when needed)
```

Each subdirectory under `agents/` is a first-class agent in the DAG. `ROLE.md` defines its persona and responsibility — it is fed directly into the LLM as the system prompt for that node.

`_tools.py` is optional. Add it when an agent needs to call functions (e.g. fetch data, run a script, call an API). Leave it absent until there is actual content — no empty stubs.

These are **not** `SKILL.md` files. `SKILL.md` lives in `skills/` and guides the outer Claude/Cursor agent. `ROLE.md` is inner, node-level — editable independently of the DAG structure.
