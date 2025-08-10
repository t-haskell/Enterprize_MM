# Operations

## Current Status

This is a **development scaffold** with minimal operational infrastructure. Most operational concerns (monitoring, alerting, SLOs) are not yet implemented.

## What's Actually Running

### Local Development Environment
- **Postgres**: Market data storage (port 5432)
- **Kafka**: Streaming infrastructure (port 9092) - not yet utilized
- **MLflow**: Model registry and tracking (port 5000)
- **Services**: API (8000), Serving (8080), Modeling, Ingestion

### Current Limitations
- No production deployment
- No monitoring or alerting
- No SLOs or performance metrics
- No automated scaling
- No backup or disaster recovery

## Development Operations

### Starting the System
```bash
make up          # Start all services
make seed        # Initialize database schema
make train       # Train initial model
```

### Health Checks
- **API**: `curl http://localhost:8000/docs` (FastAPI docs)
- **Serving**: `curl http://localhost:8080/docs` (FastAPI docs)
- **MLflow**: `curl http://localhost:5000` (MLflow UI)
- **Postgres**: `docker compose exec db pg_isready`

### Logs and Debugging
```bash
# View all service logs
docker compose logs

# View specific service logs
docker compose logs api
docker compose logs serving
docker compose logs modeling
docker compose logs ingestion

# Follow logs in real-time
docker compose logs -f api
```

### Common Issues

#### Model Not Available
**Symptoms**: API returns "model not available" error
**Diagnosis**: 
- Check if `make train` was run successfully
- Verify MLflow has a registered model
- Check serving service logs for model loading errors
**Resolution**: Run `make train` to create a model

#### Database Connection Issues
**Symptoms**: Services fail to start or can't connect to database
**Diagnosis**:
- Check if Postgres container is running
- Verify database schema is initialized
- Check connection strings in `.env` files
**Resolution**: Run `make seed` and restart services

#### High Memory/CPU Usage
**Symptoms**: System becomes slow or unresponsive
**Diagnosis**: Check resource usage with `docker stats`
**Resolution**: Restart containers or check for memory leaks

## Planned Operational Infrastructure

### Monitoring & Observability
- **Metrics**: Prometheus + Grafana dashboards
- **Logs**: Centralized logging with Loki
- **Tracing**: OpenTelemetry for distributed tracing
- **Health Checks**: Kubernetes readiness/liveness probes

### SLOs (When Implemented)
- **API Availability**: 99.9% uptime
- **Latency**: p50 < 150ms, p95 < 300ms
- **Model Freshness**: Daily retraining at 23:00 UTC
- **Data Freshness**: Market data < 5 minutes old

### Alerting (When Implemented)
- **Critical**: Service down, database unavailable
- **Warning**: High latency, model performance degradation
- **Info**: Training completion, deployment success

### Scaling & Deployment
- **Kubernetes**: Full K8s deployment with Helm charts
- **Auto-scaling**: HPA based on CPU/memory usage
- **Rolling Updates**: Zero-downtime deployments
- **Canary Deployments**: Gradual rollout of new models

## Current Runbooks

### Service Restart
```bash
# Restart specific service
docker compose restart api

# Restart all services
docker compose down
docker compose up -d
```

### Database Reset
```bash
# Complete reset (WARNING: loses all data)
docker compose down -v
docker compose up -d
make seed
make train
```

### Model Retraining
```bash
# Retrain current model
make train

# Check new model in MLflow
open http://localhost:5000
```

## Security Considerations

### Current State
- **No Authentication**: API endpoints are publicly accessible
- **Basic Rate Limiting**: 30 requests/minute on `/predict`
- **No Encryption**: All communication is unencrypted
- **No Secrets Management**: Credentials in plain text

### Planned Improvements
- **API Authentication**: JWT tokens or API keys
- **TLS Encryption**: HTTPS for all endpoints
- **Secrets Management**: HashiCorp Vault or AWS Secrets Manager
- **Network Security**: VPC isolation, security groups

## Backup & Recovery

### Current State
- **No Automated Backups**: Data persistence only via Docker volumes
- **No Disaster Recovery**: Single point of failure in local setup

### Planned Improvements
- **Database Backups**: Automated PostgreSQL backups
- **Model Artifacts**: S3 backup of MLflow models
- **Configuration**: GitOps for infrastructure as code
- **Multi-Region**: Cross-region redundancy

## Next Operational Priorities

1. **Basic Monitoring**: Add health checks and basic metrics
2. **Logging**: Centralized log collection and analysis
3. **Security**: Implement authentication and encryption
4. **Backup**: Automated backup and recovery procedures
5. **Kubernetes**: Move from Docker Compose to K8s
6. **CI/CD**: Automated testing and deployment pipelines
