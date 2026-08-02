"""Built-in provider adapters.

Importing this subpackage registers each provider with the api registry (see
agent.pi.ai/registry.py). Providers are added here in the same order
as pi-ai providers/register-builtins.ts.
"""

from __future__ import annotations

# Provider modules each call register_api_provider(...) at import time.
# We import them here so `import agent.pi.ai` triggers registration of
# every built-in provider (matching pi-ai's side-effect import pattern).
from . import (  # noqa: F401
    anthropic,
    gateway,
    google_gemini,
    openai_responses,
)

__all__: list[str] = []
