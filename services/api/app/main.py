"""FastAPI entrypoint for the Market Magic API service."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .dependencies import limiter
from .routers import analysis, legacy

app = FastAPI(title="Market Magic API", version="2.0.0")
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
def _rate_limit_handler(request, exc):  # pragma: no cover - delegated to slowapi
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})


@app.get("/healthz", tags=["system"])
async def healthcheck() -> dict[str, str]:
    """Simple liveness endpoint."""

    return {"status": "ok"}


app.include_router(analysis.router)
app.include_router(legacy.router)
