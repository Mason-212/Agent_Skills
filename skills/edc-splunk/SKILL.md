---
name: edc-splunk
description: Write, refine, and explain Splunk SPL using this repository's knowledge base of indexes, services, fields, example queries, and reference outputs. Use when the user asks for a Splunk query, wants help debugging filters or stats, or needs help interpreting Splunk results for documented services.
---

# Splunk Query Writer

## Quick Start

When working on a Splunk request in this project:

1. Read the most relevant files in `knowledge/` before answering.
2. Identify the canonical service name, aliases, index, and key fields.
3. Return runnable SPL first, then a short explanation and any useful variants.
4. Prefer narrow, composable queries with explicit time bounds.
5. Ground explanations in fields that are documented in this repository.

## Default Workflow

### 1. Read Project Context

Start with the service file:

- `knowledge/services/<service>.md`

### 2. Normalize The Service Identity

- If the user uses an alias, map it to the documented canonical service name.
- Prefer `k8s_container_name` for container-level filtering when it is documented.
- Cross-check `service` and `service_name` if naming may differ.

### 3. Build The Query

- Always include a time window unless the user explicitly says otherwise.
- Start with the base search first.
- Add one goal-driven transformation at a time: `stats`, `timechart`, `table`, `top`, `sort`, or a field filter.
- Keep raw-log and aggregate forms separate.

### 4. Respond In This Format

- `Goal`: what the query answers
- `Query`: runnable SPL
- `Why it works`: fields and assumptions used
- `Variants`: optional narrower or wider forms

### 5. Interpret Carefully

- Do not assume a field is universal just because it appears in one sample.
- If a field is inferred rather than confirmed in the knowledge base, say so.
- If the user provides new facts and asks to preserve them, update the project docs.

## Query Guidelines

- Prefer documented extracted fields over re-parsing raw JSON.
- Use `logger`, `level`, `message`, and `thread` for fast log slicing.
- Use `mdc.requestId`, `mdc.trace_id`, `mdc.span_id`, and `mdc.clientTraceId` for request tracing.
- Include `falcon_instance`, `functional_domain`, and `k8s_pod_name` when comparing deployments or pods.
- If a query returns no results, progressively loosen filters instead of rewriting the whole search.

## Additional Resources

- For repository layout and query heuristics, see [resources/reference.md](resources/reference.md)
- For answer patterns, see [resources/examples.md](resources/examples.md)
