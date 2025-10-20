"""FastAPI application for the orchestration service."""
from __future__ import annotations

import json
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from .config import get_settings
from .llm import PromptEngine, TokenBudgetExceeded
from .models import (
    PromptRequest,
    ScenarioExecutionRequest,
    ScenarioExecutionResponse,
    ScenarioSuggestionResponse,
)
from .ranking import rank_scenarios
from .runner import RunNotFoundError, get_run, schedule_execution, subscribe_run

settings = get_settings()
app = FastAPI(title="Market Magic Orchestrator", version="0.2.0")
prompt_engine = PromptEngine()

allow_origins = ["*"] if settings.cors_allow_origins == ("*",) else list(settings.cors_allow_origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["system"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/suggest", response_model=ScenarioSuggestionResponse, tags=["analysis"])
async def suggest(request: PromptRequest) -> ScenarioSuggestionResponse:
    response = rank_scenarios(request)
    try:
        llm_metadata = prompt_engine.complete(request.prompt)
    except TokenBudgetExceeded as exc:
        llm_metadata = {"error": str(exc)}
    finally:
        prompt_engine.reset_budget()
    response.metadata["llm"] = llm_metadata
    response.metadata.setdefault("max_scenarios", settings.max_scenarios)
    return response


@app.post("/execute", response_model=ScenarioExecutionResponse, tags=["analysis"])
async def execute(
    request: ScenarioExecutionRequest, background_tasks: BackgroundTasks
) -> ScenarioExecutionResponse:
    return schedule_execution(request, background_tasks)


@app.get("/runs/{run_id}", tags=["analysis"])
async def get_run_status(run_id: str):
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run


@app.get("/runs/{run_id}/stream", tags=["analysis"])
async def stream_run(run_id: str) -> EventSourceResponse:
    try:
        generator: AsyncGenerator[dict, None] = subscribe_run(run_id)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found") from exc

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        async for event in generator:
            yield {"event": "message", "data": json.dumps(event)}

    return EventSourceResponse(event_generator())
