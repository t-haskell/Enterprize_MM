import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.modeling.modeling.scenarios import SCENARIO_REGISTRY
from services.modeling.modeling.scenarios.runner import run_scenario


def test_registry_contains_expected_scenarios():
    assert "quant_factor" in SCENARIO_REGISTRY
    assert "trend_strength" in SCENARIO_REGISTRY
    assert "earnings_momentum" in SCENARIO_REGISTRY


def test_quant_factor_executes():
    result = run_scenario(
        "quant_factor",
        {"universe": ["AAPL", "MSFT", "GOOG", "AMZN"], "top_n": 3},
    )
    assert len(result["top_candidates"]) == 3
    assert all("score" in entry for entry in result["top_candidates"])


def test_trend_strength_executes():
    result = run_scenario(
        "trend_strength",
        {"universe": ["AAPL", "MSFT", "GOOG", "AMZN"]},
    )
    assert "universe_summary" in result
    assert isinstance(result["universe_summary"], list)


def test_earnings_momentum_executes():
    result = run_scenario(
        "earnings_momentum",
        {"universe": ["AAPL", "MSFT", "GOOG"], "earnings_window": 6},
    )
    assert result["metadata"]["window"] == 6
    assert result["watchlist"]
