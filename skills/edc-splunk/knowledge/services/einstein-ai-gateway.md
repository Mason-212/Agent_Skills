# `einstein-ai-gateway`

## Identity

- primary service name: `einstein-ai-gateway`
- common alias: `ai-gateway`
- best base filter: `k8s_container_name=einstein-ai-gateway`
- cross-check fields: `service=einstein-ai-gateway` and `service_name=einstein-ai-gateway`

## Known Placement

- `index=distapps`
- `k8s_namespace=einstein-edc`
- `service_group=einstein-edc`
- `sourcetype=einstein-edc`
- observed raw sample environment: `environment=aws-prod21`, `falcon_instance=aws-prod21-useast2`, `functional_domain=einstein`
- observed aggregate sample rows: `falcon_instance=aws-prod0-uswest2`, `functional_domain=cdp1`

## Log Shape

Events are JSON logs with:

- top-level fields: `timestamp`, `level`, `thread`, `logger`, `message`, and `service`
- nested context: `mdc.*`
- request correlation: `mdc.requestId`, `mdc.trace_id`, `mdc.span_id`, and `mdc.clientTraceId`

## Useful Pivots

- request tracing: `mdc.requestId`, `mdc.trace_id`, `mdc.clientTraceId`
- caller and app context: `mdc.callerService`, `mdc.clientAppName`, `mdc.clientFeatureId`, `mdc.appContext`
- org context: `mdc.ctx-user-org-id`, `mdc.coreTenantId`, `mdc.cdpTenantId`
- user context: `mdc.ctxUserId`, `mdc.userId`, `mdc.ctx-user-role-id`
- runtime behavior: `level`, `logger`, `message`, `thread`

## Known Example Queries

### Recent Raw Logs

```spl
index=distapps k8s_container_name=einstein-ai-gateway earliest=-30m
```

### Event Counts By Pod

```spl
index=distapps k8s_container_name=einstein-ai-gateway earliest=-30m
| stats count by falcon_instance, functional_domain, k8s_pod_name
| sort 0 - count
```

### Peak 5-Minute Usage By Cluster

```spl
index=distapps k8s_container_name=einstein-ai-gateway earliest=-15d latest=now
| bin _time span=5m
| stats count as usage by _time falcon_instance functional_domain
| stats max(usage) as max_5m_usage by falcon_instance functional_domain
| sort 0 - max_5m_usage
```

### Peak Hourly Average Of 5-Minute Usage By Cluster

```spl
index=distapps k8s_container_name=einstein-ai-gateway earliest=-15d latest=now
| bin _time span=5m
| stats count as usage_5m by _time falcon_instance functional_domain
| bin _time span=1h
| stats avg(usage_5m) as hourly_avg_5m_usage by _time falcon_instance functional_domain
| stats max(hourly_avg_5m_usage) as max_hourly_avg_5m_usage by falcon_instance functional_domain
| sort 0 - max_hourly_avg_5m_usage
```

### P95 5-Minute Usage By Cluster

```spl
index=distapps k8s_container_name=einstein-ai-gateway earliest=-15d latest=now
| bin _time span=5m
| stats count as usage_5m by _time falcon_instance functional_domain
| stats perc95(usage_5m) as p95_5m_usage by falcon_instance functional_domain
| sort 0 - p95_5m_usage
```

### Total Usage By Cluster

```spl
index=distapps k8s_container_name=einstein-ai-gateway earliest=-15d latest=now
| stats count as total_usage by falcon_instance functional_domain
| sort 0 - total_usage
```

## Observed Sample Log Lines

### Cache Metrics Event

```json
{"timestamp":"1774374659225","level":"DEBUG","thread":"lettuce-epollEventLoop-9-2","logger":"com.salesforce.sconems.smartcache.common.MetricsRecorder","message":"Recording L1 cache hit for cache orgSettings","service":"einstein-ai-gateway"}
```

### SpEL Evaluation Event

```json
{"timestamp":"1774374659223","level":"INFO","thread":"parallel-2","logger":"com.salesforce.sconems.smartcache.common.AnnotationExpressionParser","message":"Evaluated SpEL [false] to [false]","service":"einstein-ai-gateway"}
```

## Notes

- Normalize user references like `ai-gateway` to `einstein-ai-gateway` unless a more precise service name is later confirmed.
- Do not assume one fixed `functional_domain`; current samples show more than one.
- Current examples suggest Splunk is already extracting nested `mdc.*` fields from the JSON payload.
- The usage-oriented queries above treat event count as a proxy for service usage; switch to `dc('mdc.requestId')` when request-level counting is preferred and the field is well populated.
- A related dashboard spec is available at `knowledge/dashboards/einstein-ai-gateway/usage-by-fi-fd.xml`, and it uses distinct-count usage based on `mdc.trace_id`.
- For the dashboard use case, `mdc.trace_id` was preferred over `mdc.requestId` because observed trace-id coverage was higher.
