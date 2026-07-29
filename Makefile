.PHONY: setup test lint typecheck compile coverage check run clean

PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

setup:
	$(PYTHON) -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -e ".[dev]"

test:
	PYTHONPATH=src $(PYTHON) -m pytest tests

lint:
	$(PYTHON) -m ruff check .

typecheck:
	$(PYTHON) -m mypy src tests

coverage:
	PYTHONPATH=src $(PYTHON) -m pytest --cov=bonoai --cov-branch --cov-report=term-missing --cov-fail-under=95 tests

check: compile lint typecheck coverage

compile:
	$(PYTHON) -m compileall -q src tests

run:
	PYTHONPATH=src $(PYTHON) -m bonoai info

clean:
	$(PYTHON) -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ('build', 'dist', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'htmlcov')]"
