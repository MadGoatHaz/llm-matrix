# ============================================================================
# The Local AI Stack — developer convenience commands (PLAN.md P3-2)
#
# Common pipeline + quality tasks so you don't have to remember the exact
# python invocations. Everything runs from the repo root with Python 3.14
# (override with `make PYTHON=python3.14 ...`).
#
#   make test     run the full stdlib unittest suite (the CI quality gate)
#   make build    regenerate the site (all pages + data.json)
#   make lint     byte-compile every .py file + validate every JSON file
#   make clean    remove __pycache__ dirs and other build artifacts
#   make golden   regenerate the tests/golden/ baselines (deliberate only)
#   make check    lint + test — the same gates CI enforces
# ============================================================================

# Prefer the project virtualenv (it carries the `markdown` content dep, so
# `make build` generates every page locally, matching CI). Fall back to the
# system interpreter when no `.venv` is present.
ifeq ($(wildcard .venv/bin/python),)
PYTHON ?= python3
else
PYTHON ?= .venv/bin/python
endif

.PHONY: help test build lint validate clean golden check

help:
	@echo "Local AI Stack — common commands"
	@echo ""
	@echo "  make test      Run the full unittest suite (the CI quality gate)"
	@echo "  make build     Regenerate the site (all pages + data.json)"
	@echo "  make lint      Byte-compile all .py files + validate all JSON"
	@echo "  make validate  Run the data-quality validator (tools/validate.py)"
	@echo "  make clean     Remove __pycache__ dirs and build artifacts"
	@echo "  make golden    Regenerate tests/golden/ baselines (deliberate!)"
	@echo "  make check     Lint + validate + test (the gates CI enforces)"

# --- Quality gates (mirror .github/workflows/ci.yml) ------------------------

test:
	$(PYTHON) -m unittest discover -s tests -v

lint:
	@echo "==> Byte-compiling all Python files (tools/ + tests/)"
	$(PYTHON) -m compileall -q tools tests
	@echo "==> Validating JSON files (data/**/*.json, tools/*.json)"
	@for f in data/*.json data/api/v1/*.json tools/*.json; do $(PYTHON) -m json.tool "$$f" >/dev/null || { echo "INVALID JSON: $$f"; exit 1; }; done
	@echo "OK: all JSON files valid"

# Data-quality gate (mirrors the CI lint job): the committed data must conform
# to schema.json. A hard failure exits non-zero; informational gaps don't.
validate:
	@echo "==> Validating data quality (tools/validate.py)"
	$(PYTHON) tools/validate.py

check: lint validate test

# --- Site generation --------------------------------------------------------

build:
	$(PYTHON) -m tools.site

# --- Cleanup ----------------------------------------------------------------

clean:
	@echo "==> Removing __pycache__ directories and build artifacts"
	@find . -type d -name __pycache__ -not -path "./.venv/*" -not -path "./.git/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -not -path "./.venv/*" -not -path "./.git/*" -delete 2>/dev/null || true
	@rm -rf ./*.egg-info 2>/dev/null || true
	@echo "Clean complete."

# --- Golden baselines (deliberate — review the diff before committing) ------

golden:
	@echo "==> Regenerating tests/golden/ baselines from the current generator"
	$(PYTHON) tests/capture_golden.py
	@echo "Done. Review the golden diff before committing."
