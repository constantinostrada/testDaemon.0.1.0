# =============================================================================
# Mini-Library API — Makefile
# =============================================================================

.PHONY: help install install-dev run lint format typecheck test test-cov \
        web-install web-dev web-build web-lint web-format clean

# Default target
help:
	@echo ""
	@echo "Mini-Library API — available commands:"
	@echo ""
	@echo "  Backend (Python / FastAPI)"
	@echo "  ──────────────────────────"
	@echo "  make install       Install production dependencies"
	@echo "  make install-dev   Install dev + test dependencies"
	@echo "  make run           Start the FastAPI dev server (port 8000)"
	@echo "  make lint          Run Ruff linter"
	@echo "  make format        Format with Black"
	@echo "  make typecheck     Run MyPy type checker"
	@echo "  make test          Run all Python tests"
	@echo "  make test-cov      Run tests with coverage report"
	@echo ""
	@echo "  Frontend (Next.js / TypeScript)"
	@echo "  ────────────────────────────────"
	@echo "  make web-install   npm install (frontend)"
	@echo "  make web-dev       Start Next.js dev server (port 3000)"
	@echo "  make web-build     Production build"
	@echo "  make web-lint      ESLint check"
	@echo "  make web-format    Prettier format"
	@echo ""
	@echo "  Misc"
	@echo "  ────"
	@echo "  make clean         Remove build artifacts"
	@echo ""

# ---------------------------------------------------------------------------
# Backend
# ---------------------------------------------------------------------------

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

run:
	uvicorn src.interfaces.api.main:app --reload --port 8000

lint:
	ruff check src/ tests/

format:
	black src/ tests/

typecheck:
	mypy src/

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

WEB_DIR = src/interfaces/web

web-install:
	cd $(WEB_DIR) && npm install

web-dev:
	cd $(WEB_DIR) && npm run dev

web-build:
	cd $(WEB_DIR) && npm run build

web-lint:
	cd $(WEB_DIR) && npm run lint

web-format:
	cd $(WEB_DIR) && npm run format

# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	cd $(WEB_DIR) && rm -rf .next out 2>/dev/null || true
	@echo "✓ Cleaned"
