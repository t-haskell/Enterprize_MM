# Developer Guide

## Current Status

This is a **scaffold/prototype** project that demonstrates the basic structure for a multi-modal ML system. Most components are minimal implementations that need to be expanded for production use.

## Local Development

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Make (optional, for convenience commands)

### Getting Started
```bash
make bootstrap        # Install pre-commit hooks, create local env files
make up               # Launch all services via Docker Compose
make seed             # Load base schema and seed data
make train            # Run example training flow (creates dummy model)
make predict          # Test the prediction API with dummy data
make test             # Run unit tests (basic coverage)
make down             # Stop all containers
```

### What Actually Works Right Now
- **Basic Services**: All services start and communicate with each other
- **Dummy Data**: Ingestion generates fake OHLCV data for testing
- **Simple ML**: Basic LinearRegression model trained on dummy features
- **API Testing**: `/predict` endpoint responds with mock predictions
- **MLflow**: Model registration and basic tracking

### What's Not Production Ready
- **Data Sources**: Currently generates fake data instead of real market data
- **ML Models**: Very basic sklearn model, no proper feature engineering
- **Error Handling**: Minimal error handling and validation
- **Testing**: Basic test coverage, no integration tests
- **Security**: No authentication, basic rate limiting only

## Development Workflow

### Adding Real Data Sources
The ingestion service has TODO markers for real data providers:
```python
# In services/ingestion/src/ingestion/flows.py
@task
def fetch_ohlcv(symbol: str, days: int = 5) -> pd.DataFrame:
    # TODO: replace with real provider call (e.g., Yahoo/Polygon)
    # Currently generates dummy data
```

### Improving ML Models
The modeling service uses a basic LinearRegression:
```python
# In services/modeling/modeling/train.py
# Replace with proper feature engineering and model selection
model = LinearRegression().fit(X, Y)
```

### Adding New Services
Follow the existing pattern:
1. Create service directory in `services/`
2. Add Dockerfile and requirements.txt
3. Update `docker-compose.yml`
4. Add to Makefile targets

## Conventions

### Code Quality
- **Python**: Ruff for formatting/linting, MyPy for type checking
- **Testing**: pytest for unit tests
- **Dependencies**: Poetry for modeling service, pip for others
- **Formatting**: Pre-commit hooks for consistent code style

### Configuration
- **Environment**: Use `.env.example` files as templates
- **Service Config**: Each service manages its own config
- **MLflow**: Centralized model registry and experiment tracking

### Versioning
- **Git**: GitHub flow with protected `main` branch
- **Models**: MLflow handles model versioning
- **Data**: Basic schema versioning via SQL scripts

## Environment Structure

```
dev/          # Local development (Docker Compose)
├── Postgres  # Market data storage
├── Kafka     # Streaming data (not yet used)
├── MLflow    # Model registry
└── Services  # All microservices

stage/        # Not yet implemented
prod/         # Not yet implemented
```

## Common Issues & Solutions

### Model Not Found
- Ensure `make train` has been run
- Check MLflow UI at http://localhost:5000
- Verify model is in "Production" stage

### Database Connection Issues
- Run `make seed` to initialize schema
- Check if Postgres container is running
- Verify connection strings in `.env` files

### Service Communication
- All services must be running (`make up`)
- Check service logs: `docker compose logs <service>`
- Verify network connectivity between containers

## Next Development Priorities

1. **Real Data Integration**: Replace dummy data with actual market data providers
2. **Feature Engineering**: Implement proper technical indicators and features
3. **Model Validation**: Add cross-validation, backtesting, and performance metrics
4. **Error Handling**: Comprehensive error handling and logging
5. **Testing**: Expand test coverage and add integration tests
6. **Monitoring**: Add proper observability and alerting
