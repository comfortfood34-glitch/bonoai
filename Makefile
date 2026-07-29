.PHONY: setup test lint typecheck check run clean

PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

setup:
	$(PYTHON) -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -e ".[dev]"

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

lint:
	$(PYTHON) -m ruff check .

typecheck:
	$(PYTHON) -m mypy src tests

check:
	$(PYTHON) -m compileall -q src tests
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

run:
	PYTHONPATH=src $(PYTHON) -m bonoai info

clean:
	$(PYTHON) -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ('build', 'dist', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'htmlcov')]"
