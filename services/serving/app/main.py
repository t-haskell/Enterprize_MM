import os
import mlflow
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Market Magic Serving")


class PredictRequest(BaseModel):
    symbol: str = "AAPL"
    last5: list[float] | None = None


def load_model():
    name = os.getenv("MODEL_NAME", "market-magic-model")
    stage = os.getenv("MODEL_STAGE", "Production")
    uri = f"models:/{name}/{stage}"
    return mlflow.pyfunc.load_model(uri)


_model = None


@app.on_event("startup")
def _startup():
    global _model
    try:
        _model = load_model()
    except Exception as e:
        _model = None
        print("Model load failed:", e)


@app.post("/predict")
def predict(req: PredictRequest):
    if _model is None:
        return {"error": "model not available"}
    x = np.array(req.last5 or [100, 101, 102, 103, 104]).reshape(1, -1)
    pred = _model.predict(x).item()
    return {"symbol": req.symbol, "prediction": pred}
