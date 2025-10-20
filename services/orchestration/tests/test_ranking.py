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
