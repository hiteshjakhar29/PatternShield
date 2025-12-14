#!/usr/bin/env bash
set -euo pipefail

env_target=${1:-staging}
read -rp "Deploy to ${env_target}? (y/n): " confirm
[[ ${confirm,,} == "y" ]] || { echo "Deployment cancelled"; exit 1; }

echo "Running pre-deployment checks..."
docker-compose config >/dev/null

echo "Building image..."
docker build -t patternshield/app:${env_target} .

echo "Starting services..."
docker-compose --profile production up -d --build

echo "Running smoke test..."
curl -f http://localhost:5000/health || { echo "Health check failed"; exit 1; }

echo "Deployment complete"
