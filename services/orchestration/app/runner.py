"""Scenario execution utilities."""
from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, Set

from fastapi import BackgroundTasks

from .events import get_event_emitter
from .models import ScenarioExecutionRequest, ScenarioExecutionResponse
from .persistence import get_run_store


class RunNotFoundError(Exception):
    """Raised when attempting to stream a run that does not exist."""


_RUN_STORE: Dict[str, Dict[str, Any]] = {}
_RUN_SUBSCRIBERS: Dict[str, Set[asyncio.Queue[Dict[str, Any]]]] = defaultdict(set)


def _persist_and_publish(run_id: str, state: Dict[str, Any]) -> None:
    """Persist the latest run state and broadcast it to subscribers."""

    payload = state.copy()
    payload.setdefault("run_id", run_id)
    payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())

    _RUN_STORE[run_id] = payload
    for queue in list(_RUN_SUBSCRIBERS.get(run_id, set())):
        queue.put_nowait(payload.copy())


async def _execute(run_id: str, scenario_id: str, parameters: Dict[str, Any]) -> None:
    _persist_and_publish(
        run_id,
        {
            "status": "running",
            "message": "Executing scenario",
            "scenario_id": scenario_id,
            "parameters": parameters,
        },
    )

    try:
        from modeling.scenarios.runner import run_scenario  # type: ignore
    except Exception as exc:  # pragma: no cover - runtime dependency guard
        _persist_and_publish(
            run_id,
            {
                "status": "failed",
                "message": f"Modeling backend unavailable: {exc}",
                "scenario_id": scenario_id,
                "parameters": parameters,
            },
        )
        return

    try:
        result = await asyncio.to_thread(run_scenario, scenario_id, parameters)
        _persist_and_publish(
            run_id,
            {
                "status": "succeeded",
                "message": "Completed",
                "scenario_id": scenario_id,
                "parameters": parameters,
                "result": result,
            },
        )
    except asyncio.CancelledError:  # pragma: no cover - cooperative cancellation
        _persist_and_publish(
            run_id,
            {
                "status": "cancelled",
                "message": "Execution cancelled",
                "scenario_id": scenario_id,
                "parameters": parameters,
            },
        )
        raise
    except Exception as exc:  # pragma: no cover - actual execution path
        _persist_and_publish(
            run_id,
            {
                "status": "failed",
                "message": str(exc),
                "scenario_id": scenario_id,
                "parameters": parameters,
            },
        )


def schedule_execution(
    payload: ScenarioExecutionRequest,
    background_tasks: Optional[BackgroundTasks] = None,
) -> ScenarioExecutionResponse:
    run_id = str(uuid.uuid4())
    _persist_and_publish(
        run_id,
        {
            "status": "queued",
            "message": "Queued",
            "scenario_id": payload.scenario_id,
            "parameters": payload.parameters,
        },
    )
    asyncio.create_task(_execute(run_id, payload.scenario_id, payload.parameters))
    return ScenarioExecutionResponse(
        run_id=run_id,
        status="queued",
        message="Scenario execution queued",
        scenario_id=payload.scenario_id,
        parameters=payload.parameters,
    )


def subscribe_run(run_id: str) -> AsyncGenerator[Dict[str, Any], None]:
    """Return an async generator streaming run state transitions."""

    if run_id not in _RUN_STORE:
        raise RunNotFoundError(run_id)

    queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
    queue.put_nowait(_RUN_STORE[run_id].copy())
    _RUN_SUBSCRIBERS[run_id].add(queue)

    async def _generator() -> AsyncGenerator[Dict[str, Any], None]:
        try:
            while True:
                event = await queue.get()
                yield event
                if event.get("status") in {"succeeded", "failed", "cancelled"}:
                    break
        finally:
            _RUN_SUBSCRIBERS[run_id].discard(queue)
            if not _RUN_SUBSCRIBERS[run_id]:
                _RUN_SUBSCRIBERS.pop(run_id, None)

    return _generator()


def get_run(run_id: str) -> Dict[str, Any] | None:
    state = _RUN_STORE.get(run_id)
    return state.copy() if state else None
