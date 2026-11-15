.PHONY: install install-dev lint format type-check test test-cov test-fast clean build publish help

help:
	@echo "Lakeforge Development Commands"
	@echo "=============================="
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install production dependencies"
	@echo "  make install-dev      Install dev + optional dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run ruff linter"
	@echo "  make format           Format code with black"
	@echo "  make type-check       Run mypy type checker"
	@echo "  make lint-fix         Fix linting issues automatically"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-cov         Run tests with coverage report"
	@echo "  make test-fast        Run tests in parallel (faster)"
	@echo "  make test-phase10     Run Phase 10 tests only"
	@echo "  make test-phase12     Run Phase 12 tests only"
	@echo ""
	@echo "Building:"
	@echo "  make build            Build distribution packages"
	@echo "  make clean            Clean build artifacts"
	@echo ""
	@echo "Development:"
	@echo "  make dev              Run in development mode (REPL)"
	@echo "  make ci               Run full CI pipeline locally"
	@echo ""

install:
	pip install -e .

install-dev:
	pip install -e ".[dev,databricks,postgres,pdf,semantic]"

lint:
	ruff check lakeforge/ tests/

lint-fix:
	ruff check --fix lakeforge/ tests/
	black lakeforge/ tests/

format:
	black lakeforge/ tests/

type-check:
	mypy lakeforge/ --ignore-missing-imports

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=lakeforge --cov-report=html --cov-report=term-missing

test-fast:
	pytest tests/ -v -n auto

test-phase10:
	pytest tests/test_phase10_cli.py -v

test-phase12:
	pytest tests/test_phase12_*.py -v

build:
	python -m build

clean:
	rm -rf build/ dist/ .eggs/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov/

dev:
	@echo "Starting Lakeforge REPL with sample data..."
	python -m lakeforge.cli inspect tests/data/customers.csv

ci: lint format type-check test-cov
	@echo "✅ All CI checks passed!"

.PHONY: help install install-dev lint lint-fix format type-check test test-cov test-fast test-phase10 test-phase12 build clean dev ci
