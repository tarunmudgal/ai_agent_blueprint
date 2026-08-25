# ---------------------------------------------------------------------------
# ai_agent_blueprint — developer convenience commands
#
#   make install    install runtime + dev dependencies
#   make format     auto-fix formatting and import order (black, isort)
#   make lint       run every linter, read-only (flake8, pylint, mypy, bandit)
#   make check      format --check + lint, the combination CI should run
#   make hooks      install the pre-commit git hook, one-time
#   make clean      remove caches and build artefacts
#
# All tools point at PY_DIRS below. Add a directory here when a new chapter
# ships its own examples/ folder.
# ---------------------------------------------------------------------------

PY := python3
PY_DIRS := 01-smart-intern-prompt-engineering/examples

.PHONY: install format lint check hooks clean

install:
	$(PY) -m pip install -r requirements.txt -r requirements-dev.txt

format:
	$(PY) -m black $(PY_DIRS)
	$(PY) -m isort $(PY_DIRS)

lint:
	$(PY) -m flake8 $(PY_DIRS)
	$(PY) -m pylint $(PY_DIRS)
	$(PY) -m mypy $(PY_DIRS)
	$(PY) -m bandit -q -r $(PY_DIRS) -c pyproject.toml

check:
	$(PY) -m black --check --diff $(PY_DIRS)
	$(PY) -m isort --check --diff $(PY_DIRS)
	$(MAKE) lint

hooks:
	pre-commit install

clean:
	find . -type d -name "__pycache__" -not -path "*/.venv/*" -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache .ruff_cache htmlcov .coverage
