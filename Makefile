.PHONY: test coverage lint format type-check check clean help

help:
	@echo "Available targets:"
	@echo "  make test          - Run pytest"
	@echo "  make coverage      - Run pytest with coverage (must be >85%)"
	@echo "  make lint          - Run ruff linter"
	@echo "  make format        - Auto-format code with black and ruff"
	@echo "  make type-check    - Run mypy type checking"
	@echo "  make security      - Run security audit with bandit"
	@echo "  make check         - Run all checks (lint, format, type-check, test)"
	@echo "  make clean         - Remove build artifacts and caches"

test:
	python -m pytest confluence_skill/tests/ -v

coverage:
	python -m pytest confluence_skill/tests/ --cov=confluence_skill --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	python -m ruff check confluence_skill/

format:
	python -m black confluence_skill/
	python -m ruff check --fix confluence_skill/

type-check:
	python -m mypy confluence_skill/ --strict

security:
	bandit -r confluence_skill/ -ll

check: lint type-check test coverage
	@echo "✅ All checks passed!"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name .coverage -delete
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned up build artifacts"
