# Reference

## Repository Layout

- `knowledge/concepts/`: shared Splunk conventions and field groups
- `knowledge/indexes/`: index-specific notes and field inventories
- `knowledge/services/`: canonical service records, aliases, and pivots
- `knowledge/queries/examples/`: runnable SPL with reference output

## Working Method

1. Read the service file first if a service is named.
2. Read the index file if the query depends on extracted fields or sourcetype details.
3. Read example query files if the user wants something similar to an existing search.
4. Reuse documented names exactly unless the user provides stronger evidence.

## Default Query Patterns

### Recent Raw Logs

```spl
index=<index> k8s_container_name=<service> earliest=-30m
```

### Count By Pod

```spl
index=<index> k8s_container_name=<service> earliest=-30m
| stats count by falcon_instance, functional_domain, k8s_pod_name
```

### Count By Logger And Level

```spl
index=<index> k8s_container_name=<service> earliest=-30m
| stats count by logger, level
| sort - count
```

### Trace A Request

```spl
index=<index> k8s_container_name=<service> earliest=-30m mdc.requestId="<request-id>"
```

## Heuristics

- Start with the smallest query that answers the question.
- Prefer field filters over free-text filters when both are available.
- Add `table` when the output is too wide.
- Add `sort - count` after `stats count` when ranking is the goal.
- Keep note of fields that vary by environment, especially `functional_domain` and `falcon_instance`.

## Documentation Expectations

- Store durable facts, not one-off guesses.
- Keep reference output short and representative.
- Preserve sample ids only when they are useful pivots for future debugging.
