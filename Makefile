.PHONY: test lint coverage doctor clean install check release-check

PYTHON ?= python3
PROJECT ?= .

test:
	$(PYTHON) -m pytest tests/ -v

lint:
	$(PYTHON) -m ruff check scripts/ tests/
	$(PYTHON) -m ruff format --check scripts/ tests/

format:
	$(PYTHON) -m ruff format scripts/ tests/
	$(PYTHON) -m ruff check --fix scripts/ tests/

coverage:
	$(PYTHON) -m pytest tests/ -v --cov=scripts --cov-report=term-missing --cov-report=html

doctor:
	$(PYTHON) scripts/doctor.py --project $(PROJECT)

check: lint test

release-check:
	@command -v $(PYTHON) >/dev/null || (echo "$(PYTHON) not found" && exit 1)
	@$(PYTHON) -m build --version >/dev/null 2>&1 || (echo "$(PYTHON) -m build not available. Install package 'build' first." && exit 1)
	@$(PYTHON) -m venv --help >/dev/null 2>&1 || (echo "$(PYTHON) venv support not available. Install python3-venv first." && exit 1)
	@rm -rf .release-check-venv dist build
	@set -e; \
	trap 'rm -rf .release-check-venv' EXIT; \
	$(PYTHON) -m venv .release-check-venv; \
	. .release-check-venv/bin/activate; \
	pip install --upgrade pip build; \
	python -m build; \
	pip install dist/*.whl; \
	test "$$(so2x-cli --version)" = "so2x-cli $$(cat VERSION)"

clean:
	rm -rf htmlcov/ .pytest_cache/ tests/__pycache__/
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

install:
	$(PYTHON) scripts/apply.py --project $(PROJECT) --platform claude --preset general
