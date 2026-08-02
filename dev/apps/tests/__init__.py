"""Test helpers for running app tests from the repository root."""

from __future__ import annotations

import sys
from pathlib import Path

APPS_DIR = Path(__file__).resolve().parents[1]
apps_dir = str(APPS_DIR)
if apps_dir not in sys.path:
    sys.path.insert(0, apps_dir)
