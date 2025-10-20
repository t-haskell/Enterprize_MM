"""Tests for orchestration runner lifecycle compatibility."""

from __future__ import annotations

import asyncio
from pathlib import Path

from services.orchestration.app import runner
from services.orchestration.app.models import ScenarioExecutionRequest


def test_schedule_execution_emits_full_lifecycle(monkeypatch):
    """Ensure queued -> running -> succeeded lifecycle events remain intact."""

    runner._RUN_STORE.clear()
    runner._RUN_SUBSCRIBERS.clear()

    async def fake_to_thread(func, *args, **kwargs):  # type: ignore[override]
        return func(*args, **kwargs)

    def fake_run_scenario(scenario_id: str, parameters: dict):
        return {"scenario": scenario_id, "parameters": parameters}

    modeling_path = Path(__file__).resolve().parents[2] / "modeling"
    monkeypatch.syspath_prepend(str(modeling_path))

    monkeypatch.setattr(runner.asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr("modeling.scenarios.runner.run_scenario", fake_run_scenario)

    async def exercise() -> None:
        request = ScenarioExecutionRequest(scenario_id="quant_factor", parameters={"universe": ["AAPL"]})
        response = runner.schedule_execution(request)

        assert response.status == "queued"
        assert response.message == "Scenario execution queued"

        events = []
        async for update in runner.subscribe_run(response.run_id):
            events.append(update)
            if update["status"] == "succeeded":
                break

        statuses = [event["status"] for event in events]
        assert statuses[0] == "queued"
        assert statuses[-1] == "succeeded"
        assert "running" in statuses
        assert events[-1]["result"] == {"scenario": "quant_factor", "parameters": {"universe": ["AAPL"]}}

        await asyncio.sleep(0)  # allow background tasks to settle

    asyncio.run(exercise())
