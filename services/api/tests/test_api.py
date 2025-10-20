"""Tests for the API layer."""
from __future__ import annotations

from fastapi.testclient import TestClient

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.api.app.main import app


def test_healthcheck():
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analysis_suggest(monkeypatch):
    from services.api.app.routers import analysis

    expected = {
        "prompt": "test",
        "options": [
            {
                "scenario_id": "quant_factor",
                "title": "Quant Factor Screen",
                "short_description": "Value/quality/momentum composite",
                "rationale": "Matches factors",
                "inputs": ["universe"],
                "methodology": ["z-scores"],
                "deliverables": ["top tickers"],
                "score": 0.9,
            }
        ],
        "metadata": {"model": "stub"},
    }

    async def fake_post(path, payload):
        assert path == "/suggest"
        return expected

    monkeypatch.setattr(analysis, "_post_to_orchestrator", fake_post)

    client = TestClient(app)
    resp = client.post("/analysis/suggest", json={"prompt": "test"})
    assert resp.status_code == 200
    assert resp.json() == expected


def test_analysis_run(monkeypatch):
    from services.api.app.routers import analysis

    expected = {
        "run_id": "123",
        "status": "queued",
        "message": "scheduled",
        "scenario_id": "quant_factor",
        "parameters": {"universe": ["AAPL", "MSFT"]},
    }

    async def fake_post(path, payload):
        assert path == "/execute"
        return expected

    monkeypatch.setattr(analysis, "_post_to_orchestrator", fake_post)

    client = TestClient(app)
    resp = client.post("/analysis/run", json={"scenario_id": "quant_factor", "parameters": {}})
    assert resp.status_code == 200
    assert resp.json() == expected


def test_legacy_predict(monkeypatch):
    from services.api.app.routers import legacy

    expected = {"symbol": "AAPL", "prediction": 101.0}

    async def fake_post(path, payload):
        assert path == "/predict"
        return expected

    monkeypatch.setattr(legacy, "_post", fake_post)

    client = TestClient(app)
    resp = client.post("/predict", json={"symbol": "AAPL"})
    assert resp.status_code == 200
    assert resp.json() == expected
