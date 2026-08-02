"""Cost calculation (port of pi-ai `calculateCost`).

pi-ai mutates `usage.cost` in place and returns it. We do the same so that
downstream code (notebook section 9, provider adapters) sees the updated cost
without having to re-read the Usage reference.
"""

from __future__ import annotations

from ..types import Model, Usage, UsageCost


def calculate_cost(model: Model, usage: Usage) -> UsageCost:
    """Populate `usage.cost` using the model's per-million-token pricing.

    Matches pi-ai's formula exactly: cost = (rate / 1_000_000) * tokens.
    The `total` field sums all four categories.
    """
    rate = model.cost
    usage.cost.input = (rate.input / 1_000_000) * usage.input
    usage.cost.output = (rate.output / 1_000_000) * usage.output
    usage.cost.cache_read = (rate.cache_read / 1_000_000) * usage.cache_read
    usage.cost.cache_write = (rate.cache_write / 1_000_000) * usage.cache_write
    usage.cost.total = (
        usage.cost.input
        + usage.cost.output
        + usage.cost.cache_read
        + usage.cost.cache_write
    )
    return usage.cost


__all__ = ["calculate_cost"]
