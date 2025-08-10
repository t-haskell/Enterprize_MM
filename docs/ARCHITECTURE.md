# Architecture

- Batch + streaming ingestion writes to Postgres and Kafka topics.
- Training jobs read features via SQL and emit runs to MLflow. Hydra manages configs.
- Serving loads the latest *Production* model from MLflow and exposes `/predict`.
- API gateway composes features + predictions with basic auth and rate limiting.
- CI runs lint/test, builds images, pushes to registry; CD uses Helm + Argo CD.
- Terraform defines S3/ECR/RDS/VPC as a reference for AWS.

See `docs/OPERATIONS.md` for SLOs, runbooks, and on-call playbooks.
