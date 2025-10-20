"""Earnings momentum and revisions scenario."""
from __future__ import annotations

import random
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from .base import Scenario, ScenarioSpec


def _synthetic_events(ticker: str, window: int) -> pd.DataFrame:
    random.seed(f"earnings-{ticker}")
    dates = pd.date_range(end=pd.Timestamp.today(), periods=window, freq="7D")
    surprises = np.clip(np.random.default_rng(abs(hash(ticker)) % (2**32)).normal(0.0, 0.05, len(dates)), -0.2, 0.2)
    revisions = [random.uniform(-0.05, 0.1) for _ in dates]
    return pd.DataFrame({"date": dates, "surprise": surprises, "revision": revisions})


def _logistic(x: float) -> float:
    return float(1 / (1 + np.exp(-x)))


class EarningsMomentumScenario(Scenario):
    spec = ScenarioSpec(
        scenario_id="earnings_momentum",
        title="Earnings Momentum & Revisions",
        summary="Identify earnings-related catalysts via surprise and revision data.",
        inputs=["universe"],
        methodology=[
            "Generate pseudo earnings surprise/revision data",
            "Score near-term catalysts via weighted signals",
            "Estimate beat probability using a logistic transform",
        ],
        deliverables=["Pre/post earnings watchlist", "Signal diagnostics", "Calendar"],
        keywords=["earnings", "revisions"],
    )

    def run(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_required_inputs(parameters)
        universe = parameters["universe"]
        if not isinstance(universe, list) or len(universe) < 2:
            raise ValueError("Universe must contain at least two tickers")
        window = parameters.get("earnings_window", 8)
        revision_threshold = parameters.get("revision_threshold", 0.02)

        candidates: List[Dict[str, Any]] = []
        for ticker in universe:
            df = _synthetic_events(ticker, window)
            recent = df.tail(3)
            surprise_score = recent["surprise"].mean()
            revision_score = recent["revision"].mean()
            logistic_input = 2.5 * surprise_score + 1.8 * revision_score
            probability = _logistic(logistic_input)
            catalysts = [
                {
                    "date": row.date.isoformat(),
                    "surprise": round(float(row.surprise), 3),
                    "revision": round(float(row.revision), 3),
                }
                for row in recent.itertuples()
            ]
            candidates.append(
                {
                    "ticker": ticker,
                    "surprise_score": round(float(surprise_score), 3),
                    "revision_score": round(float(revision_score), 3),
                    "beat_probability": round(probability, 3),
                    "revisions_trending_up": revision_score > revision_threshold,
                    "catalysts": catalysts,
                }
            )
        candidates.sort(key=lambda item: item["beat_probability"], reverse=True)
        return {
            "scenario_id": self.spec.scenario_id,
            "watchlist": candidates[: parameters.get("top_n", 5)],
            "metadata": {
                "window": window,
                "revision_threshold": revision_threshold,
                "note": "Synthetic signals provided; integrate broker/estimize feeds for production.",
            },
        }
