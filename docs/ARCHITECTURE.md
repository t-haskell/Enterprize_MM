# Architecture

## Current Implementation Status

### ✅ Implemented
- **Local Development**: Docker Compose setup with Postgres, Kafka, MLflow, and all services
- **Basic Services**: API, serving, modeling, and ingestion services with minimal implementations
- **Data Pipeline**: Simple dummy data generation and basic MLflow model registration
- **API Endpoints**: Basic `/predict` endpoint with rate limiting (30/minute)

### 🚧 Partially Implemented
- **Data Ingestion**: Prefect flows structure exists but uses dummy data (marked with TODO for real providers)
- **ML Pipeline**: Basic sklearn LinearRegression model with dummy features
- **Infrastructure**: Basic Terraform VPC setup, minimal Helm chart structure
#### Terraform and Helm
**Terraform**: Infrastructure as Code (IaC) tool for managing cloud and on-premises resources. It creates and manages infrastructure resources such as virtual machines, networks, and databases.
**Helm**: A package manager for Kubernetes that simplifies the process of installing and managing applications on a Kubernetes cluster. It provides a way to define, install, and upgrade applications using a templating engine and a set of best practices.


### 📋 Planned/Not Yet Implemented
- **Production Data**: Real market data ingestion from providers (Yahoo/Polygon)
- **Advanced ML**: Multi-modal models, proper feature engineering, model validation
- **Kubernetes**: Full K8s deployment with Argo CD
- **Monitoring**: Prometheus/Grafana, proper SLOs and alerting
- **CI/CD**: Automated testing, building, and deployment pipelines

## Current Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   API      │───▶│  Serving   │───▶│  MLflow    │
│ (FastAPI)  │    │ (FastAPI)  │    │ (Model     │
│ Port 8000  │    │ Port 8080  │    │  Registry) │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐    ┌─────────────┐
│  Ingestion │    │  Modeling   │
│ (Prefect)  │    │ (Training)  │
└─────────────┘    └─────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐    ┌─────────────┐
│  Postgres  │    │   Kafka     │
│   (Data)   │    │ (Streaming) │
└─────────────┘    └─────────────┘
```

## Data Flow

1. **Ingestion**: Currently generates dummy OHLCV data, writes to Postgres
2. **Training**: Reads from Postgres, trains simple linear model, registers with MLflow
3. **Serving**: Loads latest "Production" model from MLflow, serves predictions
4. **API**: Gateway that calls serving service with rate limiting

## Next Steps

- Replace dummy data with real market data providers
- Implement proper feature engineering and model validation
- Add monitoring and observability
- Deploy to Kubernetes with proper CI/CD
- Implement multi-modal data ingestion (news, sentiment, etc.)

See `docs/DEVELOPER_GUIDE.md` for local development setup and `docs/OPERATIONS.md` for operational considerations.
