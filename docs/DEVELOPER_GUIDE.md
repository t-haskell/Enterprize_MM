# Developer Guide

## Overview

The project now delivers a prompt-first analytics flow on top of a
**multi-modal financial market prediction** backbone. The API service proxies
natural-language prompts to a dedicated orchestration layer that ranks research
scenarios and dispatches modeling workloads. Ingestion, modeling, and serving
continue to provide the market, fundamental, textual, sentiment, macro, and
alternative data foundation alongside the legacy prediction path. Scenario
implementations consume these modalities explicitly so contributors can reason
about how each data feed influences prompt-driven outputs.

## Local Development

### Prerequisites

- Docker + Docker Compose
- Python 3.11+ (optional for running services locally without containers)
- `make` for convenience commands

### Quickstart

```bash
make bootstrap          # install hooks + copy env templates
make up                 # build & launch Postgres, Kafka, MLflow, services
make seed               # initialise database schema
make train              # run example training job
make predict            # call the legacy prediction endpoint
```

### Prompt Workflow Smoke Test

```bash
curl -s http://localhost:8000/analysis/suggest \
  -H "Content-Type: application/json" \
  -d '{"prompt": "I want a long-term dividend strategy", "max_scenarios": 4}' | jq

curl -s http://localhost:8000/analysis/run \
  -H "Content-Type: application/json" \
  -d '{"scenario_id": "quant_factor", "parameters": {"universe": ["AAPL", "MSFT", "GOOG"]}}' | jq
```

### Service Directory Highlights

- `services/api`
  - `app/routers/analysis.py` – prompt ingestion + orchestration proxy
  - `app/routers/legacy.py` – `/predict` compatibility route
  - `app/schemas.py` – shared Pydantic contracts
- `services/orchestration`
  - `app/catalog.py` – canonical scenario definitions (12 entries)
  - `app/ranking.py` – deterministic keyword scoring
  - `app/runner.py` – background execution + run tracking (TODO: persistence)
- `services/modeling`
  - `modeling/scenarios/` – scenario registry and concrete implementations
  - `modeling/scenarios/quant_factor.py` – factor composite example
  - `modeling/scenarios/trend_strength.py` – SMA + RS signal example
  - `modeling/scenarios/earnings_momentum.py` – earnings/revision signals
- `services/ingestion`
  - `src/ingestion/flows.py` – Prefect flows for prices, fundamentals, macro, sentiment

### Testing

The repository contains unit tests for API, orchestration, and modeling
scenarios. Run them directly (requires dependencies) or inside Docker:

```bash
pytest services/api/tests -q
pytest services/orchestration/tests -q
pytest services/modeling/tests -q
```

### Configuration Notes

- API relies on `ORCHESTRATION_URL` and `SERVING_URL` environment variables.
- Orchestrator exposes port `8100` and can be tuned via `MAX_SCENARIOS`.
- Scenario implementations expect structured `parameters` dictionaries (see
  `schemas.py` and scenario docstrings for required keys).
- TODOs are embedded where production integrations (LLM provider, data vendors,
  persistent run store) are still pending.

## Contribution Guidelines

- Prefer small, well-scoped PRs with tests.
- Use TODO comments sparingly and include context/links when possible.
- Follow Ruff formatting (run `ruff format` and `ruff check`) and MyPy for
  modeling service contributions.
- Document new scenarios or API changes in `docs/ARCHITECTURE.md` + README.
