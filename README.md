# Market Magic — Multi‑Modal Financial Market Prediction (Scaffold)

A production‑minded, extendable scaffold for a **multi‑modal** ML system that ingests market data,
news/social sentiment, and (optionally) satellite/alt data; trains models; serves predictions; and
ships with CI/CD, Terraform, Helm, and observability hooks.

> This is a *starter* repo: it runs locally via `docker compose` and is structured to scale to K8s.
> Replace placeholders marked with `TODO:` as you implement real logic and credentials.

## Fast Start

```bash
make bootstrap        # install pre-commit hooks, create local env files
make up               # launch Postgres, Kafka, MLflow, services (dev)
make seed             # load base schema and seed data
make train            # run example training flow (dummy model)
make predict          # call model-serving API
make test             # run unit tests
make down             # stop containers
```

## High-Level Architecture

- **services/ingestion** – Prefect flows for OHLCV, news, social; writers to Postgres/Kafka
- **services/modeling** – Hydra-configured training, MLflow tracking, modular pipelines
- **services/serving** – FastAPI model server loading the latest "Production" model from MLflow
- **services/api** – FastAPI gateway for clients; rate-limits, auth, joins features + predictions
- **frontend/** – Next.js dashboard (placeholder)
- **infra/** – Terraform (AWS reference), Helm charts, Argo CD app manifests
- **ops/** – Observability: Prometheus/Grafana, Loki, OpenTelemetry collector configs
- **.github/workflows/** – CI (lint, test, build), CD (charts + images) or use Jenkinsfile

See `docs/ARCHITECTURE.md` and `docs/DEVELOPER_GUIDE.md` for details.
