"""Load lib/aor configuration from .env.

Resolution order for each setting:
  1. lib/aor/.env  (file on disk)
  2. Environment variables already set in the shell
  3. Hardcoded fallback (LLM_PROVIDER=sfdc_gateway, no API key)

Call load() once at startup. After that, read settings via the module-level
attributes: PROVIDER, MODEL, API_KEY, MAX_COST_USD.

Note: MAX_RETRIES is pack-specific (currently only used by multiagent_adversarial)
and is NOT stored here. It is collected from the user at runtime and passed via
WorkflowRequest.metadata.
"""

from __future__ import annotations

import os
from pathlib import Path

_ENV_PATH = Path(__file__).parent.parent / ".env"

# Module-level settings (populated by load())
PROVIDER: str = "sfdc_gateway"
MODEL: str = "claude-sonnet-4-5-20250929"
API_KEY: str = ""
MAX_COST_USD: float | None = None

# Tracing settings
PHOENIX_TRACING: bool = False
PHOENIX_COLLECTOR_ENDPOINT: str = "http://localhost:6006/v1/traces"

_loaded = False


def load(env_path: Path | None = None) -> None:
    """Load settings from .env file. Safe to call multiple times."""
    global PROVIDER, MODEL, API_KEY, MAX_COST_USD, PHOENIX_TRACING, PHOENIX_COLLECTOR_ENDPOINT, _loaded

    path = env_path or _ENV_PATH
    if path.exists():
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=path, override=False)  # shell env vars win
    elif not _loaded:
        import warnings
        warnings.warn(
            f"lib/aor config not found at {path}. "
            "Copy lib/aor/.env.example to lib/aor/.env and fill in your API key.",
            stacklevel=2,
        )

    PROVIDER = os.environ.get("LLM_PROVIDER", "sfdc_gateway")
    MODEL = os.environ.get("LLM_MODEL", "claude-sonnet-4-5-20250929")
    API_KEY = os.environ.get("LLM_API_KEY", "")

    if not API_KEY and PROVIDER != "local":
        raise EnvironmentError(
            "LLM_API_KEY is not set in lib/aor/.env. "
            f"Set it to your {PROVIDER} API key "
            "(sfdc_gateway → EDC_GATEWAY_API_KEY value, "
            "anthropic → Anthropic key, openai → OpenAI key, local → leave blank)."
        )

    raw_cost = os.environ.get("MAX_COST_USD", "")
    try:
        MAX_COST_USD = float(raw_cost) if raw_cost else None
    except ValueError:
        MAX_COST_USD = None

    PHOENIX_TRACING = os.environ.get("PHOENIX_TRACING", "false").lower() == "true"
    PHOENIX_COLLECTOR_ENDPOINT = os.environ.get(
        "PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces"
    )

    _loaded = True

    if PHOENIX_TRACING:
        from agent import tracing as aor_tracing
        aor_tracing.setup(PHOENIX_COLLECTOR_ENDPOINT)


def as_metadata() -> dict:
    """Return config as a metadata dict suitable for WorkflowRequest.metadata."""
    if not _loaded:
        load()
    return {
        "provider": PROVIDER,
        "model": MODEL,
        "api_key": API_KEY,
        "max_cost_usd": MAX_COST_USD,
    }
