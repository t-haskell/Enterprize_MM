"""Scenario execution utilities."""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict

from .models import ScenarioExecutionRequest, ScenarioExecutionResponse

_RUN_STORE: Dict[str, Dict[str, Any]] = {}


async def _execute(run_id: str, scenario_id: str, parameters: Dict[str, Any]) -> None:
    try:
        from modeling.scenarios.runner import run_scenario  # type: ignore
    except Exception as exc:  # pragma: no cover - runtime dependency guard
        _RUN_STORE[run_id] = {
            "status": "failed",
            "message": f"Modeling backend unavailable: {exc}",
            "scenario_id": scenario_id,
            "parameters": parameters,
        }
        return

    try:
        result = await asyncio.to_thread(run_scenario, scenario_id, parameters)
        _RUN_STORE[run_id] = {
            "status": "succeeded",
            "message": "Completed",
            "scenario_id": scenario_id,
            "parameters": parameters,
            "result": result,
        }
    except Exception as exc:  # pragma: no cover - actual execution path
        _RUN_STORE[run_id] = {
            "status": "failed",
            "message": str(exc),
            "scenario_id": scenario_id,
            "parameters": parameters,
        }


def schedule_execution(payload: ScenarioExecutionRequest) -> ScenarioExecutionResponse:
    run_id = str(uuid.uuid4())
    _RUN_STORE[run_id] = {
        "status": "running",
        "message": "Scheduled",
        "scenario_id": payload.scenario_id,
        "parameters": payload.parameters,
    }
    asyncio.create_task(_execute(run_id, payload.scenario_id, payload.parameters))
    return ScenarioExecutionResponse(
        run_id=run_id,
        status="running",
        message="Scenario execution scheduled",
        scenario_id=payload.scenario_id,
        parameters=payload.parameters,
    )


def get_run(run_id: str) -> Dict[str, Any] | None:
    return _RUN_STORE.get(run_id)
