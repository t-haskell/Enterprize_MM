"""Scenario execution utilities."""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, Optional

from fastapi import BackgroundTasks

from .events import get_event_emitter
from .models import ScenarioExecutionRequest, ScenarioExecutionResponse
from .persistence import get_run_store

_STORE = get_run_store()
_EMITTER = get_event_emitter()


async def _execute(run_id: str, scenario_id: str, parameters: Dict[str, Any]) -> None:
    await _EMITTER.emit(
        "run.started",
        {"run_id": run_id, "scenario_id": scenario_id, "parameters": parameters},
    )
    try:
        from modeling.scenarios.runner import run_scenario  # type: ignore
    except Exception as exc:  # pragma: no cover - runtime dependency guard
        payload = {
            "status": "failed",
            "message": f"Modeling backend unavailable: {exc}",
            "scenario_id": scenario_id,
            "parameters": parameters,
        }
        _STORE.update(run_id, payload)
        await _EMITTER.emit("run.failed", {"run_id": run_id, **payload})
        return

    try:
        result = await asyncio.to_thread(run_scenario, scenario_id, parameters)
        payload = {
            "status": "succeeded",
            "message": "Completed",
            "scenario_id": scenario_id,
            "parameters": parameters,
            "result": result,
        }
        _STORE.update(run_id, payload)
        await _EMITTER.emit("run.succeeded", {"run_id": run_id, **payload})
    except Exception as exc:  # pragma: no cover - actual execution path
        payload = {
            "status": "failed",
            "message": str(exc),
            "scenario_id": scenario_id,
            "parameters": parameters,
        }
        _STORE.update(run_id, payload)
        await _EMITTER.emit("run.failed", {"run_id": run_id, **payload})


def _dispatch(run_id: str, scenario_id: str, parameters: Dict[str, Any]) -> None:
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_execute(run_id, scenario_id, parameters))
    except RuntimeError:
        asyncio.run(_execute(run_id, scenario_id, parameters))


def schedule_execution(
    payload: ScenarioExecutionRequest,
    background_tasks: Optional[BackgroundTasks] = None,
) -> ScenarioExecutionResponse:
    run_id = str(uuid.uuid4())
    run_payload = {
        "status": "running",
        "message": "Scheduled",
        "scenario_id": payload.scenario_id,
        "parameters": payload.parameters,
    }
    _STORE.create(run_id, run_payload)
    if background_tasks is not None:
        background_tasks.add_task(_dispatch, run_id, payload.scenario_id, payload.parameters)
    else:
        asyncio.create_task(_execute(run_id, payload.scenario_id, payload.parameters))
    return ScenarioExecutionResponse(
        run_id=run_id,
        status="running",
        message="Scenario execution scheduled",
        scenario_id=payload.scenario_id,
        parameters=payload.parameters,
    )


def get_run(run_id: str) -> Dict[str, Any] | None:
    return _STORE.get(run_id)
