"""Scenario dispatcher for the modeling service."""
from __future__ import annotations

from typing import Any, Dict

from . import SCENARIO_REGISTRY


def run_scenario(scenario_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    if scenario_id not in SCENARIO_REGISTRY:
        raise KeyError(f"Unknown scenario_id: {scenario_id}")
    scenario = SCENARIO_REGISTRY[scenario_id]
    return scenario.run(parameters)
