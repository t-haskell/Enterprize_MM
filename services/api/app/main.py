import os
from fastapi import FastAPI
from pydantic import BaseModel
import httpx
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Market Magic API")
app.state.limiter = limiter

SERVING_URL = os.getenv("SERVING_URL", "http://localhost:8080")

class PredictRequest(BaseModel):
    symbol: str
    last5: list[float] | None = None

@app.post("/predict")
@limiter.limit("30/minute")
async def predict(req: PredictRequest):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{SERVING_URL}/predict", json=req.model_dump())
        return r.json()
