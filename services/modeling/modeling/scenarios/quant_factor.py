"""Implementation of the quant factor screen scenario."""
from __future__ import annotations

import random
from typing import Any, Dict, List

import pandas as pd

from .base import Scenario, ScenarioSpec


def _deterministic_metric(ticker: str, field: str) -> float:
    random.seed(f"{ticker}-{field}")
    return random.uniform(0.5, 1.5)


class QuantFactorScenario(Scenario):
    spec = ScenarioSpec(
        scenario_id="quant_factor",
        title="Quant Factor Screen",
        summary="Composite ranking across value, quality, and momentum factors.",
        inputs=["universe"],
        methodology=[
            "Compute deterministic pseudo factor data for illustration",
            "Z-score each factor across the universe",
            "Combine factors using configurable weights to generate a composite rank",
        ],
        deliverables=["Top candidates", "Factor breakdown", "Backtest-style summary"],
        keywords=["quant", "factor", "zscore"],
    )

    FACTOR_FIELDS = {
        "value": "ev_to_ebitda",
        "quality": "roic",
        "momentum": "momentum_12m",
    }

    DEFAULT_WEIGHTS = {"value": 0.4, "quality": 0.3, "momentum": 0.3}

    def run(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_required_inputs(parameters)
        universe = parameters["universe"]
        if not isinstance(universe, list) or len(universe) < 3:
            raise ValueError("Universe must contain at least three tickers")

        weights = parameters.get("weights", self.DEFAULT_WEIGHTS)
        weight_total = sum(weights.values())
        if weight_total <= 0:
            raise ValueError("Weights must sum to a positive value")
        weights = {k: v / weight_total for k, v in weights.items() if k in self.FACTOR_FIELDS}

        rows: List[Dict[str, Any]] = []
        for ticker in universe:
            row = {"ticker": ticker}
            for factor, field in self.FACTOR_FIELDS.items():
                row[field] = _deterministic_metric(ticker, field)
            rows.append(row)
        df = pd.DataFrame(rows)

        z_cols = []
        for factor, field in self.FACTOR_FIELDS.items():
            mean = df[field].mean()
            std = df[field].std(ddof=0) or 1.0
            z_col = f"{field}_z"
            df[z_col] = (df[field] - mean) / std
            z_cols.append((factor, z_col))

        df["composite"] = 0.0
        for factor, z_col in z_cols:
            weight = weights.get(factor, 0.0)
            df["composite"] += df[z_col] * weight

        df.sort_values("composite", ascending=False, inplace=True)
        top_n = min(parameters.get("top_n", 5), len(df))
        top_candidates = df.head(top_n)

        summary = {
            "cagr": round(0.08 + 0.01 * top_candidates["composite"].mean(), 4),
            "sharpe": round(1.2 + 0.05 * top_candidates["composite"].std(ddof=0), 3),
            "max_drawdown": round(-0.18 + -0.02 * top_candidates["composite"].min(), 3),
        }

        breakdown = [
            {
                "ticker": row["ticker"],
                "score": round(row["composite"], 4),
                "factors": {
                    factor: round(row[f"{field}_z"], 3)
                    for factor, field in self.FACTOR_FIELDS.items()
                },
            }
            for row in top_candidates.to_dict("records")
        ]

        return {
            "scenario_id": self.spec.scenario_id,
            "summary": summary,
            "top_candidates": breakdown,
            "weights": weights,
            "notes": "Synthetic factor data used for demonstration; integrate real data providers.",
        }
