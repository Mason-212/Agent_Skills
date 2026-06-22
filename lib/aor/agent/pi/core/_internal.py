"""Internal helpers shared across `agent.pi.core` modules.

Kept private (single leading underscore on the module) so consumers go
through the public re-exports in `__init__.py`.
"""

from __future__ import annotations

import time


def now_ms() -> int:
    """Millisecond Unix timestamp, matching TS `Date.now()`.

    Centralized so `agent.py` and `agent_loop.py` stamp messages with a
    consistent epoch (and so a future swap to a monotonic or injectable
    clock only touches one file).
    """
    return int(time.time() * 1000)


__all__ = ["now_ms"]
