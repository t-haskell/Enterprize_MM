"""Routers implementing the prompt-first analysis workflow."""
from __future__ import annotations

import os
from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

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


async def _get_from_orchestrator(path: str) -> Dict[str, Any]:
    url = f"{ORCHESTRATION_URL.rstrip('/')}{path}"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(url)
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
    try:
        payload = PromptRequest.model_validate(payload_data)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        ) from exc
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
    try:
        payload = ScenarioExecutionRequest.model_validate(payload_data)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        ) from exc
    data = await _post_to_orchestrator("/execute", payload.model_dump())
    return ScenarioExecutionResponse.model_validate(data)


@router.get("/runs/{run_id}")
@limiter.limit("60/minute")
async def get_run(run_id: str) -> Dict[str, Any]:
    """Return the latest state for a scheduled run."""

    return await _get_from_orchestrator(f"/runs/{run_id}")


@router.get("/runs/{run_id}/stream")
@limiter.limit("60/minute")
async def stream_run(run_id: str) -> StreamingResponse:
    """Proxy Server-Sent Events from the orchestration service."""

    url = f"{ORCHESTRATION_URL.rstrip('/')}/runs/{run_id}/stream"

    async def event_iterator():
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "GET",
                    url,
                    headers={"Accept": "text/event-stream"},
                ) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_raw():
                        yield chunk
        except httpx.HTTPStatusError as exc:  # pragma: no cover - streaming status guard
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=exc.response.text,
            ) from exc
        except httpx.HTTPError as exc:  # pragma: no cover - streaming network errors
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return StreamingResponse(event_iterator(), media_type="text/event-stream")
