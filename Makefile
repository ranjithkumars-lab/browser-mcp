# Enterprise MCP Server Template - developer commands.

PYTHON       := uv run python
UV_RUN       := uv run
PYTEST       := $(UV_RUN) pytest
RUFF         := $(UV_RUN) ruff
PYRIGHT      := $(UV_RUN) pyright
MKDOCS       := $(UV_RUN) mkdocs

.DEFAULT_GOAL := help

.PHONY: help install sync
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Install the project and dev dependencies
	uv sync --all-extras

sync: ## Sync dependencies with the lockfile
	uv sync --all-extras

.PHONY: fmt lint typecheck test
fmt: ## Format code with Ruff
	$(RUFF) format .
	$(RUFF) check . --fix

lint: ## Lint with Ruff
	$(RUFF) check .

typecheck: ## Type check with Pyright
	$(PYRIGHT)

test: ## Run the test suite
	$(PYTEST)

test-coverage: ## Run tests with coverage
	$(PYTEST) --cov=enterprise_mcp --cov=browser_mcp --cov-report=html --cov-report=term

.PHONY: run doctor config
run: ## Run the server
	$(UV_RUN) enterprise-mcp serve

doctor: ## Run environment diagnostics
	$(UV_RUN) enterprise-mcp doctor

config: ## Show effective configuration
	$(UV_RUN) enterprise-mcp config --json

.PHONY: docs build docker clean
docs: ## Serve MkDocs documentation locally
	$(MKDOCS) serve

build: ## Build the Python package
	uv build

docker: ## Build the Docker image
	docker build -f deployments/docker/Dockerfile -t enterprise-mcp-server:latest .

clean: ## Remove build and cache artifacts
	rm -rf .venv build dist *.egg-info .pytest_cache .ruff_cache .pyright htmlcov docs/site
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

.PHONY: pre-commit
pre-commit: ## Run pre-commit on all files
	$(UV_RUN) pre-commit run --all-files
