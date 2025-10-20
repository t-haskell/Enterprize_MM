import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.orchestration.app.models import PromptRequest
from services.orchestration.app.ranking import rank_scenarios


def test_rank_scenarios_returns_results():
    request = PromptRequest(prompt="long-term value investment with dividends", max_scenarios=3)
    response = rank_scenarios(request)
    assert response.options
    assert response.options[0].scenario_id in {"quant_factor", "dividend_growth"}
    assert response.metadata["total_available"] == 12


def test_rank_scenarios_respects_limit():
    request = PromptRequest(prompt="macro regime tilt with etf", max_scenarios=2)
    response = rank_scenarios(request)
    assert len(response.options) <= 2


def test_rank_scenarios_filters_ineligible():
    request = PromptRequest(
        prompt="pair trading strategy with hedging",
        max_scenarios=5,
        user_profile={
            "jurisdiction": "SG",
            "accredited_investor": False,
            "excluded_tags": ["hedging"],
        },
    )
    response = rank_scenarios(request)
    scenario_ids = {option.scenario_id for option in response.options}
    assert "pair_trade" not in scenario_ids
    assert "dca_planner" not in scenario_ids  # restricted region
