# Makefile for PatternShield Backend
# Provides convenient commands for development and deployment

.PHONY: help install dev prod build run test test-cov test-fast test-local test-docker test-deployed clean deploy lint format security

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip3
DOCKER := docker
DOCKER_COMPOSE := docker-compose
IMAGE_NAME := patternshield-api
CONTAINER_NAME := patternshield-container

help: ## Show this help message
	@echo "PatternShield Backend - Available Commands"
	@echo "==========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# LOCAL DEVELOPMENT
# ============================================================================

install: ## Install dependencies for local development
	$(PIP) install -r requirements-prod.txt
	$(PYTHON) -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt')"
	@echo "✅ Dependencies installed"

dev: ## Run development server (Flask built-in)
	$(PYTHON) app.py

prod-local: ## Run production server locally (gunicorn)
	gunicorn --config gunicorn_config.py app_production:app

# ============================================================================
# DOCKER OPERATIONS
# ============================================================================

build: ## Build Docker image
	$(DOCKER) build -t $(IMAGE_NAME):latest .
	@echo "✅ Docker image built: $(IMAGE_NAME):latest"

build-no-cache: ## Build Docker image without cache
	$(DOCKER) build --no-cache -t $(IMAGE_NAME):latest .
	@echo "✅ Docker image built (no cache): $(IMAGE_NAME):latest"

run: ## Run Docker container
	$(DOCKER) run -d \
		--name $(CONTAINER_NAME) \
		-p 5000:5000 \
		-e FLASK_ENV=production \
		-e CORS_ORIGINS=* \
		$(IMAGE_NAME):latest
	@echo "✅ Container started: $(CONTAINER_NAME)"
	@echo "   URL: http://localhost:5000"
	@echo "   Logs: make logs"
	@echo "   Stop: make stop"

run-dev: ## Run Docker container with dev settings
	$(DOCKER) run -d \
		--name $(CONTAINER_NAME) \
		-p 5000:5000 \
		-e FLASK_ENV=development \
		-e FLASK_DEBUG=True \
		-v $(PWD):/app \
		$(IMAGE_NAME):latest
	@echo "✅ Dev container started with volume mount"

compose-up: ## Start services with docker-compose
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Services started with docker-compose"

compose-down: ## Stop services with docker-compose
	$(DOCKER_COMPOSE) down
	@echo "✅ Services stopped"

compose-build: ## Build services with docker-compose
	$(DOCKER_COMPOSE) build
	@echo "✅ Services built"

compose-logs: ## Show logs from docker-compose
	$(DOCKER_COMPOSE) logs -f

# ============================================================================
# CONTAINER MANAGEMENT
# ============================================================================

stop: ## Stop running container
	$(DOCKER) stop $(CONTAINER_NAME) 2>/dev/null || true
	@echo "✅ Container stopped"

remove: ## Remove container
	$(DOCKER) rm -f $(CONTAINER_NAME) 2>/dev/null || true
	@echo "✅ Container removed"

restart: stop remove run ## Restart container

logs: ## Show container logs
	$(DOCKER) logs -f $(CONTAINER_NAME)

shell: ## Open shell in running container
	$(DOCKER) exec -it $(CONTAINER_NAME) /bin/bash

inspect: ## Inspect container
	$(DOCKER) inspect $(CONTAINER_NAME)

# ============================================================================
# TESTING
# ============================================================================

test: ## Run all tests with pytest
	cd $(shell pwd) && RATE_LIMIT_ENABLED=false API_KEY_REQUIRED=false \
		FEEDBACK_FILE=/tmp/test_feedback.jsonl TEMPORAL_FILE=/tmp/test_temporal.json \
		pytest tests/ -v --tb=short

test-cov: ## Run tests with HTML coverage report
	cd $(shell pwd) && RATE_LIMIT_ENABLED=false API_KEY_REQUIRED=false \
		FEEDBACK_FILE=/tmp/test_feedback.jsonl TEMPORAL_FILE=/tmp/test_temporal.json \
		pytest tests/ --cov=. --cov-report=html --cov-report=term-missing -v --tb=short
	@echo "✅ Coverage report: htmlcov/index.html"

test-fast: ## Run tests, stop on first failure
	cd $(shell pwd) && RATE_LIMIT_ENABLED=false API_KEY_REQUIRED=false \
		FEEDBACK_FILE=/tmp/test_feedback.jsonl TEMPORAL_FILE=/tmp/test_temporal.json \
		pytest tests/ -x --tb=short -q

test-local: ## Smoke-test a locally running server
	@curl -sf http://localhost:5000/health | $(PYTHON) -m json.tool || echo "❌ Server not responding"

test-docker: ## Build image, run container, smoke-test, then stop
	@echo "Starting container for testing..."
	@make run > /dev/null 2>&1
	@sleep 6
	@curl -sf http://localhost:5000/health | $(PYTHON) -c \
		"import sys,json; d=json.load(sys.stdin); assert d['status']=='healthy', d; print('✅ Smoke test passed')"
	@make stop > /dev/null 2>&1

test-deployed: ## Smoke-test deployed server (prompts for URL)
	@read -p "Enter deployed URL: " url; \
	curl -sf $$url/health | $(PYTHON) -m json.tool

health: ## Check health endpoint
	@curl -f http://localhost:5000/health | python3 -m json.tool || echo "❌ Server not responding"

# ============================================================================
# CODE QUALITY
# ============================================================================

lint: ## Run flake8, black check, and isort check across backend/
	@echo "--- flake8 (errors) ---"
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics \
		--exclude=venv,.venv,__pycache__,tests
	@echo "--- flake8 (style) ---"
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics \
		--exclude=venv,.venv,__pycache__,tests
	@echo "--- black (check) ---"
	black --check --diff . --exclude="/(venv|\.venv|__pycache__|tests)/" || true
	@echo "--- isort (check) ---"
	isort --check-only --diff . --skip venv --skip .venv || true
	@echo "✅ Linting complete"

format: ## Auto-format code with black and isort
	black . --exclude="/(venv|\.venv|__pycache__|tests)/"
	isort . --skip venv --skip .venv
	@echo "✅ Code formatted"

security: ## Run bandit security scan across backend/
	bandit -r . -ll -f json -o bandit-report.json \
		--exclude ./venv,./\.venv,./tests || true
	@echo "✅ Security scan complete (see bandit-report.json)"

# ============================================================================
# DEPLOYMENT
# ============================================================================

deploy-render: ## Deploy to Render (requires RENDER_DEPLOY_HOOK env var)
	@if [ -z "$$RENDER_DEPLOY_HOOK" ]; then \
		echo "❌ RENDER_DEPLOY_HOOK not set"; \
		echo "   Get it from: Render Dashboard → Your Service → Settings → Deploy Hook"; \
		exit 1; \
	fi
	@curl -X POST $$RENDER_DEPLOY_HOOK
	@echo "✅ Deployment triggered on Render"

deploy-railway: ## Deploy to Railway
	railway up
	@echo "✅ Deployed to Railway"

push-ecr: ## Push image to AWS ECR (requires AWS_ACCOUNT_ID and AWS_REGION)
	@if [ -z "$$AWS_ACCOUNT_ID" ] || [ -z "$$AWS_REGION" ]; then \
		echo "❌ AWS_ACCOUNT_ID and AWS_REGION must be set"; \
		exit 1; \
	fi
	aws ecr get-login-password --region $$AWS_REGION | \
		docker login --username AWS --password-stdin $$AWS_ACCOUNT_ID.dkr.ecr.$$AWS_REGION.amazonaws.com
	docker tag $(IMAGE_NAME):latest $$AWS_ACCOUNT_ID.dkr.ecr.$$AWS_REGION.amazonaws.com/$(IMAGE_NAME):latest
	docker push $$AWS_ACCOUNT_ID.dkr.ecr.$$AWS_REGION.amazonaws.com/$(IMAGE_NAME):latest
	@echo "✅ Image pushed to ECR"

# ============================================================================
# UTILITY
# ============================================================================

clean: ## Clean up containers, images, and cache
	@echo "Cleaning up..."
	$(DOCKER) stop $(CONTAINER_NAME) 2>/dev/null || true
	$(DOCKER) rm $(CONTAINER_NAME) 2>/dev/null || true
	$(DOCKER) rmi $(IMAGE_NAME):latest 2>/dev/null || true
	$(DOCKER) system prune -f
	rm -rf __pycache__ *.pyc logs/*.log
	@echo "✅ Cleanup complete"

clean-all: clean ## Clean everything including volumes
	$(DOCKER) volume prune -f
	@echo "✅ Full cleanup complete"

env: ## Create .env file from example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file from .env.example"; \
		echo "⚠️  Remember to update SECRET_KEY and other values"; \
	else \
		echo "⚠️  .env file already exists"; \
	fi

generate-keys: ## Generate secure keys for SECRET_KEY and API_KEY
	@echo "SECRET_KEY=$$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
	@echo "API_KEY=$$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"

stats: ## Show Docker image and container stats
	@echo "=== Docker Images ==="
	@$(DOCKER) images | grep $(IMAGE_NAME) || echo "No images found"
	@echo ""
	@echo "=== Running Containers ==="
	@$(DOCKER) ps | grep $(IMAGE_NAME) || echo "No containers running"
	@echo ""
	@echo "=== Container Stats ==="
	@$(DOCKER) stats --no-stream $(CONTAINER_NAME) 2>/dev/null || echo "Container not running"

size: ## Show Docker image size
	@$(DOCKER) images $(IMAGE_NAME):latest --format "{{.Size}}"

version: ## Show version info
	@echo "Python: $$(python3 --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$(docker-compose --version)"

# ============================================================================
# QUICK COMMANDS
# ============================================================================

quick-start: build run ## Quick start: build and run
	@echo "✅ Quick start complete!"
	@echo "   Access at: http://localhost:5000"
	@make health

quick-test: test ## Run pytest suite (fast, no Docker needed)
	@echo "✅ Quick test complete!"

full-check: lint test security build test-docker ## Full pre-deployment check: lint → pytest → bandit → Docker build → smoke test
	@echo "✅ All checks passed!"
	@echo "   Ready for deployment"
