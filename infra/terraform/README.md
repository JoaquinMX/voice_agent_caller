# Terraform Infrastructure Modules (Placeholder)

This directory will contain Terraform modules for provisioning the core cloud infrastructure required by the voice agent platform, including:

- Networking (VPC, subnets, security groups, NAT gateways)
- Kubernetes cluster (EKS/GKE) and node groups
- Managed data services (RDS for PostgreSQL, ElastiCache/MemoryStore for Redis, Qdrant)
- Observability stack (OpenTelemetry Collector, Prometheus, Grafana, Loki)
- Secrets management (AWS Secrets Manager / GCP Secret Manager)
- Telephony provider webhooks (API Gateway + Lambda or Cloud Run)

Modules will be structured for reuse across staging and production environments with environment-specific variable files.
