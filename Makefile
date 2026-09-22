# ============================================================
# Makefile — Automated Data Pipeline & BI Architecture
# ============================================================

.PHONY: help setup install run test lint clean docker-up docker-down db-setup validate

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Environment Setup ---

setup: ## Create virtual environment and install dependencies
	python -m venv .venv
	.venv/Scripts/activate && pip install -r requirements.txt

install: ## Install dependencies into current environment
	pip install -r requirements.txt

install-dev: ## Install with dev dependencies
	pip install -r requirements.txt
	pip install -e ".[dev]"

install-snowflake: ## Install optional Snowflake dependencies
	pip install -e ".[snowflake]"

# --- Configuration ---

env: ## Create .env from template
	copy .env.example .env

validate: ## Validate environment setup
	python scripts/validate_environment.py

# --- Database ---

docker-up: ## Start PostgreSQL via Docker Compose
	docker-compose up -d

docker-down: ## Stop Docker Compose services
	docker-compose down

db-setup: ## Initialize database schemas and tables
	python scripts/setup_database.py

# --- Pipeline ---

run: ## Run the pipeline
	python scripts/run_pipeline.py

run-manual: ## Run pipeline manually
	python orchestration/jobs/manual_pipeline.py

# --- API ---

api: ## Start the monitoring API server
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# --- Testing ---

test: ## Run all tests
	pytest tests/ -v

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

test-cov: ## Run tests with coverage report
	pytest tests/ --cov=src --cov-report=html

# --- Cleanup ---

clean: ## Remove caches and temporary files
	if exist __pycache__ rd /s /q __pycache__
	if exist .pytest_cache rd /s /q .pytest_cache
	if exist htmlcov rd /s /q htmlcov
	if exist .coverage del .coverage
	for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
