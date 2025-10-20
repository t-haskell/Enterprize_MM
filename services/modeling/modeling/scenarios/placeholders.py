"""Placeholder scenarios for templates not yet implemented."""
from __future__ import annotations

from typing import Any, Dict, List

from .base import Scenario, ScenarioSpec


class StaticPlaceholderScenario(Scenario):
    def __init__(self, spec: ScenarioSpec) -> None:
        self.spec = spec

    def run(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_required_inputs(parameters)
        return {
            "scenario_id": self.spec.scenario_id,
            "status": "todo",
            "message": "Analytics pipeline pending full data integration.",
            "requested_parameters": parameters,
        }


PLACEHOLDER_SCENARIOS: List[Scenario] = [
    StaticPlaceholderScenario(
        ScenarioSpec(
            scenario_id="lightweight_dcf",
            title="Lightweight DCF & Margin-of-Safety",
            summary="Monte Carlo valuation bands based on growth/WACC assumptions.",
            inputs=["revenue_growth", "fcf_growth", "wacc", "terminal"],
            methodology=["TODO"],
            deliverables=["TODO"],
            keywords=["dcf"],
        )
    ),
    StaticPlaceholderScenario(
        ScenarioSpec(
            scenario_id="dividend_growth",
            title="Dividend-Growth Defensives",
            summary="Screen for dividend growth consistency and balance sheet strength.",
            inputs=["min_years", "payout_cap", "leverage_cap"],
            methodology=["TODO"],
            deliverables=["TODO"],
            keywords=["dividend"],
        )
    ),
    StaticPlaceholderScenario(
        ScenarioSpec(
            scenario_id="macro_regime",
            title="Macro-Regime Tilt",
            summary="Regime-aware sector and ETF tilts.",
            inputs=["macro_views", "risk_budget"],
            methodology=["TODO"],
            deliverables=["TODO"],
            keywords=["macro"],
        )
    ),
    StaticPlaceholderScenario(
        ScenarioSpec(
            scenario_id="nlp_sentiment",
            title="News & Social Sentiment",
            summary="FinBERT-driven sentiment overlay.",
            inputs=["sources", "decay"],
            methodology=["TODO"],
            deliverables=["TODO"],
            keywords=["sentiment"],
        )
    ),
    StaticPlaceholderScenario(
        ScenarioSpec(
            scenario_id="insider_buybacks",
            title="Insider Buying & Buybacks",
            summary="Blend insider transactions with buyback yield screens.",
            inputs=["net_buys", "buyback_yield"],
            methodology=["TODO"],
            deliverables=["TODO"],
            keywords=["insider"],
        )
    ),
    StaticPlaceholderScenario(
        ScenarioSpec(
            scenario_id="theme_basket",
            title="Secular Theme Basket",
            summary="Construct thematic baskets with HRP weighting.",
            inputs=["theme_keywords", "exposure_threshold", "moat_filters"],
            methodology=["TODO"],
            deliverables=["TODO"],
            keywords=["theme"],
        )
    ),
    StaticPlaceholderScenario(
        ScenarioSpec(
            scenario_id="pair_trade",
            title="Hedged Single-Name",
            summary="Construct long/short pair trades.",
            inputs=["target", "hedge_universe", "beta_window"],
            methodology=["TODO"],
            deliverables=["TODO"],
            keywords=["pairs"],
        )
    ),
    StaticPlaceholderScenario(
        ScenarioSpec(
            scenario_id="smart_beta",
            title="Core Index + Smart-Beta Tilt",
            summary="Blend core ETFs with factor tilts.",
            inputs=["core_etf", "factor_tilt", "max_tracking_error"],
            methodology=["TODO"],
            deliverables=["TODO"],
            keywords=["smart beta"],
        )
    ),
    StaticPlaceholderScenario(
        ScenarioSpec(
            scenario_id="dca_planner",
            title="DCA Planner with Regime-Aware Overlays",
            summary="Systematic investment plan with valuation overlays.",
            inputs=["cadence", "cashflows", "drawdown_triggers"],
            methodology=["TODO"],
            deliverables=["TODO"],
            keywords=["dca"],
        )
    ),
]
