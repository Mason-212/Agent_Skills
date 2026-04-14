# Examples

## Example 1: Recent Logs For A Service

### User Request

Write a query for recent `ai-gateway` logs.

### Good Response Shape

`Goal`: Show recent raw events for the `einstein-ai-gateway` container.

```spl
index=distapps k8s_container_name=einstein-ai-gateway earliest=-30m
```

`Why it works`: `ai-gateway` is documented as an alias of `einstein-ai-gateway`, and `k8s_container_name` is the best confirmed base filter.

## Example 2: Compare Pod Volume

### User Request

Which `einstein-ai-gateway` pods are generating the most logs?

### Good Response Shape

`Goal`: Compare event volume by pod over the last 30 minutes.

```spl
index=distapps k8s_container_name=einstein-ai-gateway earliest=-30m
| stats count by falcon_instance, functional_domain, k8s_pod_name
| sort - count
```

`Why it works`: the documented example already groups by `falcon_instance`, `functional_domain`, and `k8s_pod_name`, which are the key placement fields for this service.

## Example 3: Trace A Specific Request

### User Request

Show me everything tied to request `aec19faa-7721-bed9-aa2c-92d0d05ea7b8`.

### Good Response Shape

`Goal`: Follow one request through `einstein-ai-gateway` log lines.

```spl
index=distapps k8s_container_name=einstein-ai-gateway earliest=-30m mdc.requestId="aec19faa-7721-bed9-aa2c-92d0d05ea7b8"
```

`Why it works`: `mdc.requestId` is a documented extracted field and is better than raw text matching.
