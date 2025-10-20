"""Legacy routes maintained for backwards compatibility."""
from __future__ import annotations

import os
from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException, Request, status

from ..dependencies import limiter
from ..schemas import PredictRequest

router = APIRouter(tags=["legacy"])

SERVING_URL = os.getenv("SERVING_URL", "http://localhost:8080")
DEFAULT_TIMEOUT = float(os.getenv("SERVING_TIMEOUT", "10"))


async def _post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{SERVING_URL.rstrip('/')}{path}"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:  # pragma: no cover - safety net
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:  # pragma: no cover - network errors
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/predict")
@limiter.limit("30/minute")
async def predict(request: Request) -> Dict[str, Any]:
    """Proxy the legacy predict workflow through to the serving service."""

    try:
        payload_data = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload") from exc
    payload = PredictRequest.model_validate(payload_data)
    return await _post("/predict", payload.model_dump())
