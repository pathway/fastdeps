.PHONY: help install install-dev test test-cov lint format type-check clean build docs

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install package in production mode
	pip install .

install-dev:  ## Install package in development mode with dev dependencies
	pip install -e ".[dev]"
	pre-commit install

test:  ## Run tests
	pytest

test-cov:  ## Run tests with coverage report
	pytest --cov=fastdeps --cov-report=html --cov-report=term

lint:  ## Run linting with ruff
	ruff check fastdeps tests

format:  ## Format code with black
	black fastdeps tests

type-check:  ## Run type checking with mypy
	mypy fastdeps

clean:  ## Clean build artifacts
	rm -rf build dist *.egg-info
	rm -rf .coverage htmlcov .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.py[co]" -delete

build:  ## Build distribution packages
	python -m build

docs:  ## Build documentation
	cd docs && make html

check:  ## Run all checks (lint, type-check, test)
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) test

release:  ## Prepare for release (run all checks and build)
	$(MAKE) check
	$(MAKE) clean
	$(MAKE) build

demo:  ## Run demo analysis on fastdeps itself
	fastdeps fastdeps -o demo.png --show