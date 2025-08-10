# Operations

## SLOs
- API availability: 99.9%
- p50 latency: < 150ms local; < 300ms prod
- Freshness: model retrained daily at 23:00 UTC

## Runbooks
- **Model not found**: Check MLflow UI; ensure a model is in "Production" stage.
- **DB errors**: Verify `db` is up; run `make seed`; check connection strings.
- **High latency**: Inspect Grafana dashboards; scale `serving` via HPA (K8s).

## Alerts
- 5xx rate, latency SLO breach, missing daily training run.
