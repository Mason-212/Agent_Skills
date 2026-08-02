"""Capability flags (port of pi-ai `supportsXhigh` and related).

The xhigh logic matches pi-ai models.ts exactly so the
supports-xhigh.test.ts port asserts the same behavior.
"""

from __future__ import annotations

from ..types import Model


def supports_xhigh(model: Model) -> bool:
    """Port of pi-ai supportsXhigh (models.ts line 55)."""
    if any(tag in model.id for tag in ("gpt-5.2", "gpt-5.3", "gpt-5.4")):
        return True
    if model.api == "anthropic-messages":
        return "opus-4-6" in model.id or "opus-4.6" in model.id
    return False


def supports_thinking(model: Model) -> bool:
    """True if the model exposes a `thinking` / reasoning channel.

    Not a pi-ai primitive, but useful for the notebook's side-by-side section.
    Derived from the catalog's `reasoning` flag plus provider-known families.
    """
    if model.reasoning:
        return True
    if model.api == "anthropic-messages" and "opus" in model.id:
        return True
    if model.api == "google-generative-ai" and "2.5" in model.id:
        return True
    return False


__all__ = ["supports_thinking", "supports_xhigh"]
