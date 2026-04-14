.PHONY: test lint coverage doctor clean install check

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

clean:
	rm -rf htmlcov/ .pytest_cache/ tests/__pycache__/
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

install:
	$(PYTHON) scripts/apply.py --project $(PROJECT) --platform claude --preset general
