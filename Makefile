.PHONY: help install install-dev lint format check test serve build clean pre-commit

help:
	@echo "Available commands:"
	@echo "  install       - Install the package in development mode"
	@echo "  install-dev   - Install with dev + mcp dependencies"
	@echo "  lint          - Run ruff linting with auto-fix"
	@echo "  format        - Format code with ruff"
	@echo "  check         - Run all checks (lint + format check + tests)"
	@echo "  test          - Run pytest"
	@echo "  pre-commit    - Install pre-commit hooks"
	@echo "  serve         - Serve test documentation locally"
	@echo "  build         - Build test documentation"
	@echo "  clean         - Clean build artifacts"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev,mcp]"
	pre-commit install

lint:
	ruff check --fix src/ tests/

format:
	ruff format src/ tests/

check: lint
	ruff format --check src/ tests/
	pytest tests/ -v

test:
	pytest tests/ -v

pre-commit:
	pre-commit install

serve:
	cd test-site && mkdocs serve

build:
	cd test-site && mkdocs build

clean:
	rm -rf test-site/site/ build/ dist/ src/*.egg-info .pytest_cache
