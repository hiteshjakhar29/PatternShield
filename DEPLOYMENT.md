# Deployment Guide

## Prerequisites
- Docker and Docker Compose
- Python 3.12
- Access to PostgreSQL and Redis services

## Local Development
1. Copy `.env.example` to `.env` and adjust values.
2. Run `make install`.
3. Start the API: `python -m backend.app`.

## Docker Deployment
1. Build the image: `make docker-build`.
2. Start stack: `docker-compose --profile development up --build`.

## Cloud Deployment
- Push the built image to your registry.
- Provision PostgreSQL and Redis.
- Deploy using the provided `docker-compose.yml` or translate to your orchestration platform.

## Kubernetes (Optional)
- Convert services to deployments and apply ingress with TLS termination.

## Environment Variables
See `.env.example` for full list of supported options.

## Troubleshooting
- Check `/health/ready` endpoint for dependency status.
- Inspect logs with `make logs`.
- Verify database connectivity and credentials.

## Rollback
- Redeploy previous stable image tag.
- Restore database from backups if schema changes were applied.
