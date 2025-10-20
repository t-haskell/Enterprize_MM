"""Settings for the orchestration service."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    """Runtime configuration derived from environment variables."""

    max_scenarios: int = int(os.getenv("MAX_SCENARIOS", "5"))
    default_timeout: float = float(os.getenv("MODEL_TIMEOUT", "30"))
    modeling_backend: str = os.getenv("MODELING_BACKEND", "local")
    modeling_endpoint: str = os.getenv("MODELING_ENDPOINT", "http://modeling:9000")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
