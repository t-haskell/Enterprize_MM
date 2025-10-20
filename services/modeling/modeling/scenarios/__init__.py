"""Scenario registry for analytics workflows."""
from __future__ import annotations

from typing import Dict

from .base import Scenario
from .quant_factor import QuantFactorScenario
from .trend_strength import TrendStrengthScenario
from .earnings_momentum import EarningsMomentumScenario
from .placeholders import PLACEHOLDER_SCENARIOS

SCENARIO_REGISTRY: Dict[str, Scenario] = {
    scenario.spec.scenario_id: scenario
    for scenario in [
        QuantFactorScenario(),
        TrendStrengthScenario(),
        EarningsMomentumScenario(),
        *PLACEHOLDER_SCENARIOS,
    ]
}

__all__ = ["SCENARIO_REGISTRY", "Scenario"]
