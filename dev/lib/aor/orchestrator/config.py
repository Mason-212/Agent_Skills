"""File-backed configuration helpers for orchestrator."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .policy import DSPyLMConfig


class OrchestratorConfig(BaseModel):
    """Top-level orchestrator configuration."""

    dspy_lm: DSPyLMConfig | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


def load_orchestrator_config(path: str | Path) -> OrchestratorConfig:
    """Load orchestrator configuration from a JSON file."""

    config_path = Path(path)
    return OrchestratorConfig.model_validate(json.loads(config_path.read_text()))
