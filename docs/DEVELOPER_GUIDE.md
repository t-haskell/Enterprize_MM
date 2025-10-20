# Developer Guide

## Overview

Enterprize MM now operates as an **LLM-assisted orchestration platform** layered
on the original multi-modal analytics stack. The FastAPI gateway exposes a
prompt-first API, the orchestration service ranks the scenario catalogue and
streams run updates, and the revamped Next.js frontend visualises the full job
lifecycle. Modeling, ingestion, and serving services remain unchanged, providing
quantitative depth for the scenarios recommended by the orchestration layer.

## Local Development

### Prerequisites

- Docker + Docker Compose (core services)
- Node.js 18+ and npm (Next.js frontend)
- Python 3.11+ if you want to run services outside containers
- `make` for convenience scripts

### Quickstart Workflow

```bash
make bootstrap            # install hooks + copy env templates
make up                   # build and start Postgres, Kafka, MLflow, API, orchestrator, etc.
make orchestrator         # hot-rebuild just the orchestration service container when iterating
make api                  # refresh the FastAPI gateway after modifying routers
make seed                 # initialise database schema + seed data
```

Once the stack is up:

- **Frontend** –
  ```bash
  cd frontend
  npm install
  npm run dev              # http://localhost:3000
  ```
  Configure the API origin via `NEXT_PUBLIC_API_BASE_URL` (defaults to
  `http://localhost:8000`).
- **Smoke test the orchestration API** –
  ```bash
  curl -s http://localhost:8000/analysis/suggest \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Find breakout momentum in semiconductors", "max_scenarios": 5}' | jq

  curl -s http://localhost:8000/analysis/run \
    -H "Content-Type: application/json" \
    -d '{"scenario_id": "trend_strength", "parameters": {"universe": ["AMD","NVDA","AVGO"]}}' | jq
  ```
- **Follow a live run** – open `http://localhost:3000/runs/<run_id>` in the
  browser or stream the SSE feed directly:
  ```bash
  curl -N http://localhost:8000/analysis/runs/<run_id>/stream
  ```

### Service Directory Cheatsheet

- `frontend/`
  - `app/page.tsx` – landing page (prompt form, ranked scenarios, FAQ/tooltips).
  - `app/runs/[id]/page.tsx` – run dashboard consuming SSE updates.
  - `hooks/useRunStream.ts` – EventSource wrapper for orchestration streams.
  - `app/api/analytics/route.ts` – lightweight analytics logger for prompt usage.
- `services/api`
  - `app/main.py` – FastAPI entrypoint with CORS configuration.
  - `app/routers/analysis.py` – proxies `/analysis/*` endpoints & SSE stream.
- `services/orchestration`
  - `app/main.py` – SSE endpoint + prompt ranking entrypoints.
  - `app/runner.py` – asyncio-based run store and publisher.
  - `app/catalog.py` – canonical scenario definitions and metadata.
- `services/modeling`
  - `modeling/scenarios/` – concrete implementations for factor, trend, and
    earnings momentum pipelines.
- `services/ingestion`
  - `src/ingestion/flows.py` – Prefect flows seeding price, fundamental,
    macro, and sentiment data.

### Configuration Notes

- **CORS** – Both API and orchestration services honour `CORS_ALLOW_ORIGINS`
  (comma-delimited, `*` by default) so the frontend can connect during local dev
  or when deployed separately.
- **Orchestration** – `MAX_SCENARIOS` controls ranking breadth; additional
  settings live in `app/config.py`.
- **Frontend** – set `NEXT_PUBLIC_API_BASE_URL` when proxying through gateways or
  staging environments.
- **Analytics logging** – prompt usage posts land in the Next.js server logs via
  `/api/analytics` and can be wired to a real warehouse later.

### Testing & Quality

- Python unit tests (run inside containers or directly):
  ```bash
  pytest services/api/tests -q
  pytest services/orchestration/tests -q
  pytest services/modeling/tests -q
  ```
- Frontend linting/build:
  ```bash
  cd frontend
  npm run lint
  npm run build
  ```
- Formatting – modeling service ships with Ruff + MyPy targets under `make fmt`.

### Debugging SSE Streams

The orchestration runner uses in-memory queues to multiplex SSE subscribers. A
few tips when diagnosing issues:

- Each run sends an initial `queued` event immediately after scheduling. A
  follow-up `running` update fires as soon as the worker thread begins
  executing. If you do not see these, confirm the API proxy (`/analysis/runs/{id}`)
  returns the same state as the orchestrator (`/runs/{id}`).
- The frontend will fall back to periodic polling when the SSE proxy returns an
  error (e.g., older orchestrator builds). Watch the network tab to ensure the
  `/analysis/runs/{id}` endpoint is reachable when troubleshooting.
- SSE connections are long-lived. Ensure reverse proxies (or local dev tools)
  do not buffer or compress the stream.
- Event payloads are JSON dictionaries; the UI renders them verbatim. Use
  `curl -N` to validate structure before debugging frontend rendering.

### Contributing

- Prefer focused PRs with accompanying updates to docs/README when behaviour
  changes.
- Document new scenarios by updating `app/catalog.py`, `docs/ARCHITECTURE.md`,
  and the frontend copy if surfaced to users.
- Avoid wrapping imports in try/except unless guarding optional dependencies.
- Coordinate with operations for infra changes (see `docs/OPERATIONS.md`).
