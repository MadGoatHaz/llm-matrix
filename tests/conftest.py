"""pytest configuration for the Local AI Stack test suite.

The suite itself is stdlib :mod:`unittest` (see ``pyproject.toml``); this
file exists so that ``python -m pytest tests/`` works from any working
directory: it puts the repo root on ``sys.path`` so ``tests.util`` and the
path-based tool imports resolve identically to
``python -m unittest discover -s tests``.

No fixtures are defined — every test is deterministic and self-contained
(no network, no clock, no environment dependence).
"""

import sys
from pathlib import Path

# Repo root = parent of this tests/ directory.
ROOT = str(Path(__file__).resolve().parent.parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
