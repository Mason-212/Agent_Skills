"""Environment-variable API key discovery.

Narrowed port of vendor/pi-mono-upstream/packages/ai/src/env-api-keys.ts:
covers only the four providers this package supports. OAuth, Vertex ADC, and
Bedrock credential chains are intentionally not ported.
"""

from __future__ import annotations

import os

_PROVIDER_ENV_VARS: dict[str, tuple[str, ...]] = {
    # Gateway uses the repo's existing env var, not OPENAI_API_KEY.
    "salesforce-gateway": ("ENG_AI_MODEL_GW_KEY",),
    "openai": ("OPENAI_API_KEY",),
    # ANTHROPIC_OAUTH_TOKEN takes precedence over ANTHROPIC_API_KEY per pi-ai.
    "anthropic": ("ANTHROPIC_OAUTH_TOKEN", "ANTHROPIC_API_KEY"),
    "google": ("GEMINI_API_KEY",),
}


def get_env_api_key(provider: str) -> str | None:
    """Return the first non-empty env var configured for the provider, or None."""
    for var in _PROVIDER_ENV_VARS.get(provider, ()):
        value = os.environ.get(var)
        if value:
            return value
    return None


__all__ = ["get_env_api_key"]
