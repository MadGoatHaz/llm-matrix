"""Test suite for The Local AI Stack.

Stdlib :mod:`unittest` — no test dependencies (see ``pyproject.toml``,
``[tool.unittest]``).

Run from the repo root:

    python -m unittest discover -s tests -v

The same tests run under pytest (``python -m pytest tests/``) because pytest
executes ``unittest`` classes natively; ``conftest.py`` only makes the repo
root importable for pytest's rootdir handling.

Modules:
    test_smoke     — pipeline scripts import; data files are valid JSON
    test_schema    — tools/schema.json structure (the data contract)
    test_data      — data/submissions.json invariants
    test_generate  — generator runs clean into a temp dir (structure checks)
    util           — shared helpers (path-based tool import, JSON loading)
"""
