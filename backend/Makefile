.PHONY: help install install-dev test lint format type-check pre-commit clean run

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	uv sync --no-dev

install-dev: ## Install all dependencies including dev dependencies
	uv sync --all-extras

test: ## Run tests with coverage
	uv run pytest

test-watch: ## Run tests in watch mode
	uv run pytest --watch

lint: ## Run ruff linter
	uv run ruff check .

lint-fix: ## Run ruff linter with auto-fix
	uv run ruff check --fix .

format: ## Format code with ruff
	uv run ruff format .

format-check: ## Check code formatting
	uv run ruff format --check .

type-check: ## Run type checking with ty
	uv run ty .

pre-commit-install: ## Install pre-commit hooks
	uv run pre-commit install

pre-commit-run: ## Run pre-commit on all files
	uv run pre-commit run --all-files

clean: ## Clean up cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

run: ## Run the FastAPI development server
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run the FastAPI production server
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

check-all: lint format-check type-check test ## Run all checks (lint, format, type-check, test)

ci: install-dev check-all ## Run CI pipeline locally