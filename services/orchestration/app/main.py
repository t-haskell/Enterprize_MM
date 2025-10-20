"""FastAPI application for the orchestration service."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, status

from .config import get_settings
from .llm import PromptEngine
from .models import (
    PromptRequest,
    ScenarioExecutionRequest,
    ScenarioExecutionResponse,
    ScenarioSuggestionResponse,
)
from .ranking import rank_scenarios
from .runner import get_run, schedule_execution

app = FastAPI(title="Market Magic Orchestrator", version="0.1.0")
settings = get_settings()
prompt_engine = PromptEngine()


@app.get("/healthz", tags=["system"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/suggest", response_model=ScenarioSuggestionResponse, tags=["analysis"])
async def suggest(request: PromptRequest) -> ScenarioSuggestionResponse:
    response = rank_scenarios(request)
    response.metadata["llm"] = prompt_engine.complete(request.prompt)
    response.metadata.setdefault("max_scenarios", settings.max_scenarios)
    return response


@app.post("/execute", response_model=ScenarioExecutionResponse, tags=["analysis"])
async def execute(request: ScenarioExecutionRequest) -> ScenarioExecutionResponse:
    return schedule_execution(request)


@app.get("/runs/{run_id}", tags=["analysis"])
async def get_run_status(run_id: str):
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run
