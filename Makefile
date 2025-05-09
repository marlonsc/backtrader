# Copyright (c) 2025 backtrader contributors
# Makefile for the backtrader project

PYTHON=python3
PIP=$(VENV)/bin/pip
SRC=backtrader tests contrib tools
REQ=requirements.txt
REQ_DEV=requirements-dev.txt
VENV=.venv
TYPINGS=typings

.PHONY: help venv install install-dev editable stubgen stubs lint format test check build clean distclean fix

help:
	@echo "Available targets:"
	@echo "  stubs        - Generate/update type stubs in $(TYPINGS) (full setup)"
	@echo "  lint         - Check code style and types (ruff, pyright, mypy)"
	@echo "  fix          - Auto-fix code style issues (ruff, autopep8, black)"
	@echo "  format       - Format code with black"
	@echo "  test         - Run all tests with pytest"
	@echo "  check        - Run stubs, lint, format, and test in sequence"
	@echo "  build        - Build distribution wheel"
	@echo "  clean        - Remove temporary files and caches"
	@echo "  distclean    - Remove all build/test artifacts and .venv"

# Step 1: Ensure venv exists
$(VENV):
	@echo "[venv] Creating virtual environment ..."
	@$(PYTHON) -m venv $(VENV)

# Step 2: Install runtime dependencies
install: $(VENV)
	@echo "[install] Installing runtime dependencies ..."
	@$(PIP) install -r $(REQ)

# Step 3: Install dev dependencies
install-dev: install
	@echo "[install-dev] Installing development dependencies ..."
	@$(PIP) install -r $(REQ_DEV)

# Step 4: Install package in editable mode
editable: install-dev
	@echo "[editable] Installing package in editable mode ..."
	@$(PIP) install -e .

# Step 5: Generate stubs
stubgen: editable
	@echo "[stubgen] Checking for stubgen ..."
	@if ! $(VENV)/bin/stubgen --help >/dev/null 2>&1; then \
	  echo 'Error: stubgen is not installed. Check requirements-dev.txt.'; \
	  exit 1; \
	fi
	@echo "[stubgen] Generating type stubs for $(SRC) into $(TYPINGS)/ ..."
	PYTHONPATH=. $(VENV)/bin/stubgen backtrader -o $(TYPINGS)

# User-facing target
stubs: stubgen

# Lint the codebase using ruff, flake8, pylint, mypy, bandit, vulture
lint:
	@echo "Running all linters (ruff, flake8, pylint, mypy, bandit, vulture)..."
	ruff check backtrader tests contrib tools
	flake8 backtrader/ tests/ contrib/ tools/
	pylint backtrader/ tests/ contrib/ tools/
	mypy backtrader/ tests/ contrib/ tools/
	bandit -r backtrader/ contrib/ tools/
	vulture backtrader/ contrib/ tools/

# Format code using black, isort, autoflake, docformatter, pyupgrade
format:
	@echo "Auto-formatting code (black, isort, autoflake, docformatter, pyupgrade)..."
	isort backtrader/ tests/ contrib/ tools/
	autoflake --in-place --remove-unused-variables --remove-all-unused-imports -r backtrader/ tests/ contrib/ tools/
	black backtrader/ tests/ contrib/ tools/
	docformatter --in-place --wrap-summaries 90 --wrap-descriptions 90 --style google -r backtrader/ tests/ contrib/ tools/
	find backtrader tests contrib tools -name '*.py' -print0 | xargs -0 -n 1 $(VENV)/bin/pyupgrade --py311-plus

# Check code style and types (no changes)
check:
	@echo "Checking code style and types (ruff, black, isort, mypy, flake8, pylint, bandit, vulture)..."
	ruff check backtrader tests contrib tools --check
	black backtrader/ tests/ contrib/ tools/ --check
	isort backtrader/ tests/ contrib/ tools/ --check-only
	mypy backtrader/ tests/ contrib/ tools/
	flake8 backtrader/ tests/ contrib/ tools/
	pylint backtrader/ tests/ contrib/ tools/
	bandit -r backtrader/ contrib/ tools/
	vulture backtrader/ contrib/ tools/

# Individual tool targets
flake8:
	flake8 backtrader/ tests/ contrib/ tools/

isort:
	isort backtrader/ tests/ contrib/ tools/

mypy:
	mypy backtrader/ tests/ contrib/ tools/

bandit:
	bandit -r backtrader/ contrib/ tools/

autoflake:
	autoflake --in-place --remove-unused-variables --remove-all-unused-imports -r backtrader/ tests/ contrib/ tools/

docformatter:
	docformatter --in-place --wrap-summaries 90 --wrap-descriptions 90 --style google -r backtrader/ tests/ contrib/ tools/

vulture:
	vulture backtrader/ contrib/ tools/

pyupgrade:
	@echo "[fix] Upgrading syntax with pyupgrade ..."
	find backtrader tests contrib tools -name '*.py' -print0 | xargs -0 -n 1 $(VENV)/bin/pyupgrade --py311-plus

test:
	pytest

check: stubs lint format test

build:
	$(PYTHON) -m build

clean:
	rm -rf build dist .pytest_cache .ruff_cache .mypy_cache .coverage .tox *.egg-info
	find . -type d -name '__pycache__' -exec rm -rf {} +

# DANGEROUS: removes .venv and all build/test artifacts
# Use with caution!
distclean: clean
	rm -rf $(VENV) $(TYPINGS)

fix:
	@echo "[fix] Removing unused imports and variables with autoflake ..."
	$(VENV)/bin/autoflake --in-place --remove-unused-variables --remove-all-unused-imports -r backtrader tests contrib tools
	@echo "[fix] Upgrading syntax with pyupgrade ..."
	find backtrader tests contrib tools -name '*.py' -print0 | xargs -0 -n 1 $(VENV)/bin/pyupgrade --py311-plus
	@echo "[fix] Sorting imports with isort ..."
	$(VENV)/bin/isort backtrader tests contrib tools
	@echo "[fix] Auto-fixing with Ruff ..."
	$(VENV)/bin/ruff check --fix --unsafe-fixes backtrader tests contrib tools || true
	@echo "[fix] Auto-fixing with autopep8 ..."
	$(VENV)/bin/autopep8 --in-place --aggressive --aggressive --recursive backtrader tests contrib tools
	@echo "[fix] Formatting docstrings with docformatter ..."
	$(VENV)/bin/docformatter --in-place --wrap-summaries 90 --wrap-descriptions 90 --style google -r backtrader tests contrib tools
	@echo "[fix] Formatting with Black ..."
	$(VENV)/bin/black backtrader tests contrib tools
