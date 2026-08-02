"""Static model catalog + cost calculation + capability flags.

Python port of vendor/pi-mono-upstream/packages/ai/src/models.ts (minus the
auto-generated catalog, which we replace with a hand-curated small table).
"""

from __future__ import annotations

from .capabilities import (
    supports_thinking,
    supports_xhigh,
)
from .catalog import (
    MODELS,
    get_model,
    get_models,
    get_providers,
    models_are_equal,
)
from .cost import calculate_cost

__all__ = [
    "MODELS",
    "calculate_cost",
    "get_model",
    "get_models",
    "get_providers",
    "models_are_equal",
    "supports_thinking",
    "supports_xhigh",
]
