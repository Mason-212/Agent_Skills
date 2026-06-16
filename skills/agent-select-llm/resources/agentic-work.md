## Agentic Work

Use this overlay for repo-aware agent loops, multi-step tool use, cross-file changes, long-running implementation sessions, and tasks where the model must maintain state over time.

## Domain Signals

- the user wants the model to work across a repo, not just answer once
- the task includes planning, edits, verification, and recovery
- tools, terminals, tests, or staged workflows are involved
- the model must preserve intent across multiple steps

## Decision Lenses

| Agentic lens | What to evaluate | Critical failure state | Model tendency |
|---|---|---|---|
| `dependency-mapping` | how well the model can track cross-file and cross-step dependencies | the model edits one subsystem and forgets related updates elsewhere | strong dependency tracking pushes toward top agentic models |
| `state-retention` | whether the model must keep a long-horizon plan in mind | the model loses track of earlier decisions or repeats work | long-horizon tasks push toward stronger reasoning models |
| `tool-orchestration` | how much the task depends on shells, tests, logs, and iteration | the model uses tools in the wrong order or misses key verification steps | tool-heavy work favors disciplined agentic models |
| `recovery-tolerance` | how costly partial failure is | the model makes progress but cannot recover cleanly from errors or drift | low recovery tolerance favors more reliable models |
| `session-volume` | how much repeated back-and-forth the task will involve | the best model is too slow or expensive to sustain across a long session | high-volume sessions favor balanced workhorse models |

## Good Follow-up Questions

- "Will this be a long multi-step session with tools and verification, or mostly one-shot guidance?"
- "Does the task cross many files or subsystems?"
- "How expensive would it be if the model misses a dependency or loses context halfway through?"
- "Do you want the strongest agentic model, or a cheaper workhorse for a long session?"

## Recommendation Tendencies

- For large repo changes, long sessions, and dependency-heavy work, prioritize agentic reliability over raw speed.
- For long execution loops, prefer models that stay consistent across planning, implementation, and recovery.
- For medium-stakes repo tasks done frequently, favor a balanced workhorse model to keep throughput high.
- If the task is really just coding in one or two files, the coding overlay may be a better primary lens than this one.

## Provider-Specific Hints

Treat these as tendencies, not absolute rankings:

- `Claude Fable 5`: strong fit when long-horizon reasoning and repo-wide coordination dominate
- `Claude Opus 4.8`: strong fit for heavy multi-file implementation and agentic collaboration
- `Claude Sonnet 4.6`: good workhorse default when you want speed without giving up too much coding quality
- `GPT-5.5`: useful when the agentic workflow contains strict structured handoffs or schema-heavy steps
