"""Arize Phoenix tracing setup for the aor library.

Call setup() once at startup (done automatically by agent.config.load()
when PHOENIX_TRACING=true in lib/aor/.env).

Packs use the context manager helpers to add named spans:

    from agent.tracing import node_span, llm_span

    async def _node_generate(self, ctx):
        with node_span("generate", attempt=1):
            ...

    async def _call_llm(self, ...):
        with llm_span(provider="anthropic", model="claude-sonnet"):
            ...
"""

from __future__ import annotations

import contextlib
from typing import Any, Generator

from opentelemetry import trace
from opentelemetry.trace import NonRecordingSpan

_tracer: trace.Tracer = trace.get_tracer("aor")
_setup_done = False


def setup(collector_endpoint: str) -> None:
    """Configure OTel to export to Phoenix and auto-instrument LangChain/LangGraph."""
    global _tracer, _setup_done
    if _setup_done:
        return

    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    provider = TracerProvider()
    provider.add_span_processor(
        SimpleSpanProcessor(OTLPSpanExporter(endpoint=collector_endpoint))
    )
    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer("aor")

    try:
        from openinference.instrumentation.langchain import LangChainInstrumentor
        LangChainInstrumentor().instrument()
    except ImportError:
        pass  # instrumentation package not installed — spans still work

    _setup_done = True


def is_enabled() -> bool:
    return _setup_done


@contextlib.contextmanager
def node_span(node_name: str, **attributes: Any) -> Generator[trace.Span, None, None]:
    """Context manager that wraps a DAG node execution in an OTel span.

    Usage:
        with node_span("generate", attempt=1, prompt_length=300) as span:
            span.set_attribute("artifact_length", len(artifact))
    """
    if not _setup_done:
        yield _noop_span()
        return

    with _tracer.start_as_current_span(f"aor.node.{node_name}") as span:
        span.set_attribute("aor.node_name", node_name)
        for k, v in attributes.items():
            span.set_attribute(f"aor.{k}", _safe(v))
        yield span


@contextlib.contextmanager
def llm_span(provider: str, model: str, **attributes: Any) -> Generator[trace.Span, None, None]:
    """Context manager that wraps an LLM call in an OTel span.

    Usage:
        with llm_span(provider="anthropic", model="claude-sonnet") as span:
            response = await call_llm(...)
            span.set_attribute("aor.response_length", len(response))
    """
    if not _setup_done:
        yield _noop_span()
        return

    with _tracer.start_as_current_span("aor.llm_call") as span:
        span.set_attribute("aor.provider", provider)
        span.set_attribute("aor.model", model)
        for k, v in attributes.items():
            span.set_attribute(f"aor.{k}", _safe(v))
        yield span


@contextlib.contextmanager
def policy_span(policy_name: str, **attributes: Any) -> Generator[trace.Span, None, None]:
    """Context manager that wraps a policy decision in an OTel span.

    Usage:
        with policy_span("adversarial", attempt=2, max_retries=3) as span:
            decision = await policy.decide(...)
            span.set_attribute("aor.action", decision.action.value)
    """
    if not _setup_done:
        yield _noop_span()
        return

    with _tracer.start_as_current_span(f"aor.policy.{policy_name}") as span:
        span.set_attribute("aor.policy_name", policy_name)
        for k, v in attributes.items():
            span.set_attribute(f"aor.{k}", _safe(v))
        yield span


def _safe(value: Any) -> str | int | float | bool:
    """OTel attributes must be primitive types."""
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _noop_span() -> trace.Span:
    """Return a non-recording span when tracing is disabled."""
    return NonRecordingSpan(trace.INVALID_SPAN_CONTEXT)
