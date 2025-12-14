.PHONY: help install test lint security-scan docker-build docker-run docker-compose-up docker-compose-down migrate logs shell deploy-staging deploy-production health

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r backend/requirements.txt

test: ## Run tests
	FLASK_ENV=test pytest

lint: ## Run formatting and lint checks
	black --check backend
	flake8 backend

security-scan: ## Run security checks
	bandit -r backend || true
	pip-audit -r backend/requirements.txt || true

docker-build: ## Build Docker image
	docker build --build-arg APP_ENV=${FLASK_ENV:-production} -t patternshield/app:latest .

docker-run: ## Run Docker container
	docker run --env-file .env -p 5000:5000 patternshield/app:latest

docker-compose-up: ## Start all services
	docker-compose up --build -d

docker-compose-down: ## Stop all services
	docker-compose down

migrate: ## Run database migrations
	alembic upgrade head

logs: ## Tail application logs
	docker-compose logs -f app

shell: ## Open shell in container
	docker-compose exec app /bin/sh

deploy-staging: ## Deploy to staging
	./scripts/deploy.sh staging

deploy-production: ## Deploy to production
	./scripts/deploy.sh production

health: ## Check health endpoint
	curl -f http://localhost:5000/health
