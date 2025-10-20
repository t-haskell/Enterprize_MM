"""Routers implementing the prompt-first analysis workflow."""
from __future__ import annotations

import os
from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException, Request, status

from ..dependencies import limiter
from ..schemas import (
    PromptRequest,
    ScenarioExecutionRequest,
    ScenarioExecutionResponse,
    ScenarioSuggestionResponse,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])

ORCHESTRATION_URL = os.getenv("ORCHESTRATION_URL", "http://localhost:8100")
DEFAULT_TIMEOUT = float(os.getenv("ORCHESTRATION_TIMEOUT", "15"))


async def _post_to_orchestrator(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{ORCHESTRATION_URL.rstrip('/')}{path}"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:  # pragma: no cover - safety net
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:  # pragma: no cover - network errors
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/suggest", response_model=ScenarioSuggestionResponse)
@limiter.limit("20/minute")
async def suggest_analysis(request: Request) -> ScenarioSuggestionResponse:
    """Return the top-N scenario options for the provided user prompt."""

    try:
        payload_data = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload") from exc
    payload = PromptRequest.model_validate(payload_data)
    data = await _post_to_orchestrator("/suggest", payload.model_dump())
    return ScenarioSuggestionResponse.model_validate(data)


@router.post("/run", response_model=ScenarioExecutionResponse)
@limiter.limit("20/minute")
async def run_analysis(request: Request) -> ScenarioExecutionResponse:
    """Schedule execution for a selected scenario."""

    try:
        payload_data = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload") from exc
    payload = ScenarioExecutionRequest.model_validate(payload_data)
    data = await _post_to_orchestrator("/execute", payload.model_dump())
    return ScenarioExecutionResponse.model_validate(data)
