# Developer Guide

## Local Dev
- `make up` boots core infra via Docker.
- Add symbols with `INSERT INTO symbols(symbol,name) VALUES ('AAPL','Apple');`.
- `make train` runs an example model to create a registered model in MLflow.

## Conventions
- Python: Ruff + MyPy + pytest.
- Config: Hydra with YAML (`services/modeling/conf`).
- Versioning: GitHub flow with protected `main` and `release/*` branches.
- Data versioning optional via DVC (hook points provided).

## Environments
- dev/stage/prod are mirrored; use `values-*.yaml` Helm overlays.
