"""Trend and relative strength scenario."""
from __future__ import annotations

import random
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from .base import Scenario, ScenarioSpec


def _synthetic_prices(ticker: str, periods: int = 252) -> pd.Series:
    random.seed(f"price-{ticker}")
    price = 100.0 + random.uniform(-5, 5)
    data = []
    for _ in range(periods):
        price *= 1 + random.uniform(-0.02, 0.03)
        data.append(price)
    return pd.Series(data)


class TrendStrengthScenario(Scenario):
    spec = ScenarioSpec(
        scenario_id="trend_strength",
        title="Trend & Relative Strength",
        summary="Blend moving-average trend filters with RS percentiles.",
        inputs=["universe"],
        methodology=[
            "Simulate price history to evaluate moving-average crossovers",
            "Compute relative strength percentile vs the provided universe",
            "Derive position sizing guidance based on volatility",
        ],
        deliverables=["Trend-qualified candidates", "RS table", "Volatility scaled sizing"],
        keywords=["trend", "relative strength"],
    )

    def run(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_required_inputs(parameters)
        universe = parameters["universe"]
        if not isinstance(universe, list) or len(universe) < 3:
            raise ValueError("Universe must contain at least three tickers")
        ma_fast, ma_slow = (50, 200)
        rs_window = 63
        prices: Dict[str, pd.Series] = {ticker: _synthetic_prices(ticker) for ticker in universe}
        rs_scores: Dict[str, float] = {}
        rows: List[Dict[str, Any]] = []
        for ticker, series in prices.items():
            df = pd.DataFrame({"close": series})
            df["sma_fast"] = df["close"].rolling(ma_fast).mean()
            df["sma_slow"] = df["close"].rolling(ma_slow).mean()
            trend_ok = bool(df["sma_fast"].iloc[-1] > df["sma_slow"].iloc[-1])
            rs_scores[ticker] = series.pct_change(rs_window).iloc[-1]
            vol = df["close"].pct_change().std() * np.sqrt(252)
            position = min(max(0.5, 1.5 - vol), 1.5)
            rows.append(
                {
                    "ticker": ticker,
                    "trend_confirmed": trend_ok,
                    "sma_fast": round(df["sma_fast"].iloc[-1], 2),
                    "sma_slow": round(df["sma_slow"].iloc[-1], 2),
                    "volatility": round(vol, 3),
                    "suggested_position": round(position, 2),
                }
            )
        rs_rank = pd.Series(rs_scores).rank(pct=True)
        for row in rows:
            row["relative_strength_percentile"] = round(rs_rank[row["ticker"]], 3)
        qualified = [row for row in rows if row["trend_confirmed"] and row["relative_strength_percentile"] > 0.6]
        qualified.sort(key=lambda item: (item["relative_strength_percentile"], -item["volatility"]), reverse=True)
        return {
            "scenario_id": self.spec.scenario_id,
            "qualified_candidates": qualified[: parameters.get("top_n", 5)],
            "universe_summary": rows,
            "notes": "Synthetic price paths used; replace with real market data integration.",
        }
