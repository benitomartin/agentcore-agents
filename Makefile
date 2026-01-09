# Makefile

# Check if .env exists
ifeq (,$(wildcard .env))
$(error .env file is missing at .env. Please create one based on .env.example)
endif

# Load environment variables from .env
include .env

.PHONY: mypy clean help ruff-check ruff-check-fix ruff-format ruff-format-fix all-check all-fix

#################################################################################
## Agentcore Commands
#################################################################################

agentcore-s3-setup: ## Create S3 bucket for documents
	@echo "Setting up S3 bucket..."
	uv run scripts/setup_s3.py
	@echo "S3 bucket setup completed."

agentcore-lambda-deploy: ## Deploy Lambda function for Gateway tools
	@echo "Deploying Lambda function..."
	uv run scripts/deploy_lambda.py
	@echo "Lambda deployment completed."

agentcore-gateway: ## Run the Agentcore gateway
	@echo "Running the Agentcore gateway..."
	uv run scripts/setup_gateway.py
	@echo "Agentcore gateway completed."

agentcore-user-auth: ## Setup user authentication
	@echo "Setting up user authentication..."
	uv run scripts/setup_user_auth.py
	@echo "User authentication setup completed."

agentcore-runtime-permissions: ## Setup runtime permissions
	@echo "Setting up runtime permissions..."
	uv run scripts/setup_runtime_permissions.py
	@echo "Runtime permissions setup completed."

################################################################################
## Prek Commands
################################################################################

prek-run: ## Run prek hooks
	@echo "Running prek hooks..."
	prek run --all-files
	@echo "Prek checks complete."

################################################################################
## Linting
################################################################################

# Linting (just checks)
ruff-check: ## Check code lint violations (--diff to show possible changes)
	@echo "Checking Ruff formatting..."
	uv run ruff check .
	@echo "Ruff lint checks complete."

ruff-check-fix: ## Auto-format code using Ruff
	@echo "Formatting code with Ruff..."
	uv run ruff check . --fix --exit-non-zero-on-fix
	@echo "Formatting complete."

################################################################################
## Formatting
################################################################################

# Formatting (just checks)
ruff-format: ## Check code format violations (--diff to show possible changes)
	@echo "Checking Ruff formatting..."
	uv run ruff format . --check
	@echo "Ruff format checks complete."

ruff-format-fix: ## Auto-format code using Ruff
	@echo "Formatting code with Ruff..."
	uv run ruff format .
	@echo "Formatting complete."

#################################################################################
## Static Type Checking
#################################################################################

mypy: ## Run MyPy static type checker
	@echo "Running MyPy static type checker..."
	uv run mypy
	@echo "MyPy static type checker complete."

################################################################################
## Cleanup
################################################################################

clean: ## Clean up cached generated files
	@echo "Cleaning up generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete."

################################################################################
## Composite Commands
################################################################################

all-check: ruff-format ruff-check clean ## Run all: linting, formatting and type checking

all-fix: ruff-format-fix ruff-check-fix mypy clean ## Run all fix: auto-formatting and linting fixes

################################################################################
## Help
################################################################################

help: ## Display this help message
	@echo "Default target: $(.DEFAULT_GOAL)"
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help