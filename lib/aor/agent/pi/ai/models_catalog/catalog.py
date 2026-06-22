"""Hand-curated subset of pi-ai's models.generated.ts.

Covers only the four providers this port supports, with ~3-4 models each.
Prices are USD per million tokens (same unit as pi-ai). These are reference
values; production users should override or validate against the latest
provider pricing.
"""

from __future__ import annotations

from ..types import Model, ModelCost
from ._gateway_url import resolve_gateway_base_url


def _model(
    *,
    id: str,
    name: str,
    api: str,
    provider: str,
    base_url: str,
    context_window: int,
    max_tokens: int,
    input_cost: float,
    output_cost: float,
    cache_read: float = 0.0,
    cache_write: float = 0.0,
    reasoning: bool = False,
    inputs: tuple[str, ...] = ("text",),
) -> Model:
    return Model(
        id=id,
        name=name,
        api=api,
        provider=provider,
        base_url=base_url,
        reasoning=reasoning,
        input=list(inputs),  # type: ignore[arg-type]
        cost=ModelCost(
            input=input_cost,
            output=output_cost,
            cache_read=cache_read,
            cache_write=cache_write,
        ),
        context_window=context_window,
        max_tokens=max_tokens,
    )


# Resolved eagerly at import so every catalog `Model` sees the same URL.
# See `_gateway_url.py` for the precedence rules and the TODO(gateway-url)
# about adding real per-environment derivation.
_GATEWAY_BASE_URL = resolve_gateway_base_url()


_SALESFORCE_GATEWAY_MODELS: dict[str, Model] = {
    "gpt-4o-mini": _model(
        id="gpt-4o-mini",
        name="GPT-4o mini (Gateway)",
        api="openai-completions",
        provider="salesforce-gateway",
        base_url=_GATEWAY_BASE_URL,
        context_window=128_000,
        max_tokens=16_384,
        input_cost=0.15,
        output_cost=0.60,
    ),
    "gpt-4o": _model(
        id="gpt-4o",
        name="GPT-4o (Gateway)",
        api="openai-completions",
        provider="salesforce-gateway",
        base_url=_GATEWAY_BASE_URL,
        context_window=128_000,
        max_tokens=16_384,
        input_cost=2.50,
        output_cost=10.00,
    ),
    "gpt-5.1": _model(
        id="gpt-5.1",
        name="GPT-5.1 (Gateway)",
        api="openai-completions",
        provider="salesforce-gateway",
        base_url=_GATEWAY_BASE_URL,
        context_window=400_000,
        max_tokens=32_768,
        input_cost=2.00,
        output_cost=8.00,
        reasoning=True,
    ),
    "claude-sonnet-4-20250514": _model(
        id="claude-sonnet-4-20250514",
        name="Claude Sonnet 4 (Gateway)",
        api="openai-completions",
        provider="salesforce-gateway",
        base_url=_GATEWAY_BASE_URL,
        context_window=200_000,
        max_tokens=64_000,
        input_cost=3.00,
        output_cost=15.00,
        cache_read=0.30,
        cache_write=3.75,
    ),
    "claude-sonnet-4-5-20250929": _model(
        id="claude-sonnet-4-5-20250929",
        name="Claude Sonnet 4.5 (Gateway)",
        api="openai-completions",
        provider="salesforce-gateway",
        base_url=_GATEWAY_BASE_URL,
        context_window=200_000,
        max_tokens=64_000,
        input_cost=3.00,
        output_cost=15.00,
        cache_read=0.30,
        cache_write=3.75,
    ),
    "claude-haiku-4-5-20251001": _model(
        id="claude-haiku-4-5-20251001",
        name="Claude Haiku 4.5 (Gateway)",
        api="openai-completions",
        provider="salesforce-gateway",
        base_url=_GATEWAY_BASE_URL,
        context_window=200_000,
        max_tokens=32_000,
        input_cost=1.00,
        output_cost=5.00,
        cache_read=0.10,
        cache_write=1.25,
    ),
}


_OPENAI_MODELS: dict[str, Model] = {
    "gpt-5.1": _model(
        id="gpt-5.1",
        name="GPT-5.1",
        api="openai-responses",
        provider="openai",
        base_url="https://api.openai.com/v1",
        context_window=400_000,
        max_tokens=32_768,
        input_cost=2.00,
        output_cost=8.00,
        cache_read=0.20,
        reasoning=True,
    ),
    "gpt-5.2": _model(
        id="gpt-5.2",
        name="GPT-5.2",
        api="openai-responses",
        provider="openai",
        base_url="https://api.openai.com/v1",
        context_window=400_000,
        max_tokens=64_000,
        input_cost=3.00,
        output_cost=12.00,
        cache_read=0.30,
        reasoning=True,
    ),
    "gpt-5-codex": _model(
        id="gpt-5-codex",
        name="GPT-5 Codex",
        api="openai-responses",
        provider="openai",
        base_url="https://api.openai.com/v1",
        context_window=400_000,
        max_tokens=32_768,
        input_cost=1.50,
        output_cost=6.00,
        reasoning=True,
    ),
}


_ANTHROPIC_MODELS: dict[str, Model] = {
    "claude-sonnet-4-5": _model(
        id="claude-sonnet-4-5",
        name="Claude Sonnet 4.5",
        api="anthropic-messages",
        provider="anthropic",
        base_url="https://api.anthropic.com/v1",
        context_window=200_000,
        max_tokens=64_000,
        input_cost=3.00,
        output_cost=15.00,
        cache_read=0.30,
        cache_write=3.75,
        reasoning=True,
    ),
    "claude-opus-4-6": _model(
        id="claude-opus-4-6",
        name="Claude Opus 4.6",
        api="anthropic-messages",
        provider="anthropic",
        base_url="https://api.anthropic.com/v1",
        context_window=200_000,
        max_tokens=64_000,
        input_cost=15.00,
        output_cost=75.00,
        cache_read=1.50,
        cache_write=18.75,
        reasoning=True,
    ),
    "claude-haiku-4-5": _model(
        id="claude-haiku-4-5",
        name="Claude Haiku 4.5",
        api="anthropic-messages",
        provider="anthropic",
        base_url="https://api.anthropic.com/v1",
        context_window=200_000,
        max_tokens=32_000,
        input_cost=1.00,
        output_cost=5.00,
        cache_read=0.10,
        cache_write=1.25,
    ),
}


_GOOGLE_MODELS: dict[str, Model] = {
    "gemini-2.5-pro": _model(
        id="gemini-2.5-pro",
        name="Gemini 2.5 Pro",
        api="google-generative-ai",
        provider="google",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        context_window=1_000_000,
        max_tokens=65_536,
        input_cost=1.25,
        output_cost=10.00,
        reasoning=True,
    ),
    "gemini-2.5-flash": _model(
        id="gemini-2.5-flash",
        name="Gemini 2.5 Flash",
        api="google-generative-ai",
        provider="google",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        context_window=1_000_000,
        max_tokens=65_536,
        input_cost=0.30,
        output_cost=2.50,
        reasoning=True,
    ),
    "gemini-3-pro": _model(
        id="gemini-3-pro",
        name="Gemini 3 Pro",
        api="google-generative-ai",
        provider="google",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        context_window=2_000_000,
        max_tokens=128_000,
        input_cost=2.00,
        output_cost=15.00,
        reasoning=True,
    ),
}


MODELS: dict[str, dict[str, Model]] = {
    "salesforce-gateway": _SALESFORCE_GATEWAY_MODELS,
    "openai": _OPENAI_MODELS,
    "anthropic": _ANTHROPIC_MODELS,
    "google": _GOOGLE_MODELS,
}


def get_providers() -> list[str]:
    return list(MODELS.keys())


def get_models(provider: str) -> list[Model]:
    return list(MODELS.get(provider, {}).values())


def get_model(provider: str, model_id: str) -> Model | None:
    return MODELS.get(provider, {}).get(model_id)


def models_are_equal(a: Model | None, b: Model | None) -> bool:
    if a is None or b is None:
        return False
    return a.id == b.id and a.provider == b.provider


__all__ = [
    "MODELS",
    "get_model",
    "get_models",
    "get_providers",
    "models_are_equal",
]
