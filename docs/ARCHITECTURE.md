# Architecture Overview

## Platform Snapshot

The system now pivots around a **prompt-first analysis workflow** while keeping
its heritage as a **multi-modal financial market prediction** stack. Users
submit natural-language intents to the API which relays them to an orchestration
service. The orchestrator evaluates the prompt, ranks relevant research
scenarios, and schedules the selected analytics jobs across the modeling
service. Supporting services (ingestion, serving, MLflow, Postgres, Kafka)
provide market, fundamental, textual, and macro data so the generated insights
blend quantitative signals with language-driven guidance. Legacy prediction
capabilities remain available for direct model scoring.

## Component Topology

```
┌──────────────────────┐        ┌──────────────────────┐        ┌──────────────────────┐
│ FastAPI Gateway      │──────▶ │ Orchestration (LLM)  │──────▶ │ Modeling Scenarios   │
│ /analysis/suggest    │        │ /suggest, /execute   │        │ Quant, Trend, etc.   │
│ /analysis/run        │        │ Prompt ranking + run │        │ Scenario registry     │
└─────────┬────────────┘        └─────────┬────────────┘        └─────────┬────────────┘
          │                                 │                               │
          │ legacy predict                  │ run metadata                   │ ML artifacts
          ▼                                 ▼                               ▼
┌──────────────────────┐        ┌──────────────────────┐        ┌──────────────────────┐
│ Model Serving (FastAPI)│      │ Postgres + Kafka     │        │ MLflow Registry      │
│ /predict               │      │ Market data + events │        │ Experiments + models │
└─────────┬──────────────┘      └──────────────────────┘        └──────────────────────┘
          │
          ▼
┌──────────────────────┐
│ Frontend (Next.js)   │
│ Prompt + scenario UI │
└──────────────────────┘
```

### Key Responsibilities

- **API Gateway (`services/api`)**
  - Exposes `/analysis/suggest` and `/analysis/run` for the prompt-first UX.
  - Maintains the legacy `/predict` endpoint for backwards compatibility.
  - Applies global rate-limiting via SlowAPI.

- **Orchestration Service (`services/orchestration`)**
  - Stores the canonical scenario catalog and keyword metadata.
  - Ranks scenarios deterministically (keyword similarity) and
    attaches LLM stub metadata for observability.
  - Schedules scenario execution and tracks run status in-memory (TODO: persist).

- **Modeling Service (`services/modeling`)**
  - Provides a scenario registry with concrete implementations for
    quant factor, trend/RS, and earnings momentum analyses.
  - Hosts placeholders for the remaining scenarios with TODO markers.
  - Dispatches analytics via `run_scenario` for synchronous or orchestrated use.

- **Ingestion (`services/ingestion`)**
  - Prefect flows for OHLCV, fundamentals, macro indicators, and sentiment.
  - Currently uses deterministic stubs; ready for vendor SDK integration.

- **Serving (`services/serving`)**
  - Continues to expose the MLflow-backed `/predict` endpoint for legacy flows.

- **Multi-Modal Data Backbone**
  - Market structure: minute/daily OHLCV bars, factor composites, and volatility regimes.
  - Fundamentals: income statement, balance sheet, and cash-flow snapshots with revision history.
  - Textual + sentiment: earnings-call summaries, news sentiment, and social-signal scores.
  - Macro + alternative: rates, inflation, employment, and optional alternative datasets (shipping, mobility, etc.).
  - Each modality is wired through ingestion to scenario modules so prompt-driven analyses surface blended evidence.

- **Shared Infrastructure**
  - Postgres for market/fundamental data, Kafka for future streaming workloads.
  - MLflow registry for experiment tracking and model versioning.

## Prompt-First Workflow

1. User enters an intent in the UI (e.g. "long-term dividend compounders").
2. API validates request and forwards it to the orchestration service.
3. Orchestrator ranks the scenario catalog and returns the top-N options with
   rationale and deliverables.
4. User selects a scenario; API relays execution request to orchestrator.
5. Orchestrator schedules the run and (when modeling integration is available)
   executes the appropriate scenario module.
6. Results are streamed back to the UI once completed (TODO: SSE/WebSockets).

## Data & Analytics Flow

```
[Ingestion] ──▶ Postgres ─┐
                         │
                         ├─▶ [Modeling Scenarios] ──▶ MLflow artifacts/results
                         │
[External APIs] ─▶ Kafka ┘
```

- **Data ingestion** produces normalized tables for prices (`ohlcv`),
  fundamentals, macro signals, and sentiment. These feed the scenario modules.
- **Scenario modules** load/pull data (currently synthetic) to generate
  deliverables such as factor ranks or earnings watchlists.
- **Modeling outputs** are designed to be persisted (TODO) and surfaced to the UI.

## Outstanding TODOs

- Persist orchestrator run metadata to Postgres/Redis instead of in-memory.
- Replace deterministic data generators with vendor integrations (Polygon,
  FactSet, RavenPack, etc.).
- Extend scenario implementations for all catalog entries.
- Wire WebSockets or Kafka streams for real-time progress updates to the UI.
- Harden orchestration with retry/backoff, tracing, and authn/z.
