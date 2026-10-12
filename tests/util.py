"""Shared helpers for the Local AI Stack test suite.

Stdlib only. ``tools/`` is a directory of entry-point scripts (no
``__init__.py``, no package), so tests import them by file path via
:func:`load_tool` rather than ``import tools.pull``.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

# Repo root = parent of this tests/ directory. Every path in the suite is
# resolved from here, so tests work from any working directory.
ROOT = Path(__file__).resolve().parent.parent

#: The five pipeline scripts (the "5-tool pipeline").
PIPELINE_SCRIPTS = (
    "tools/pull.py",
    "tools/diff.py",
    "tools/parse.py",
    "tools/parse_thread.py",
    "tools/generate_site.py",
)

#: Every JSON file the pipeline reads or writes that must stay valid.
DATA_FILES = (
    "data/submissions.json",
    "data/benchmarks.json",
    "data/hardware.json",
    "data/category_threads.json",
    "data/last_seen.json",
    "data/api/v1/submissions.json",
    "data/api/v1/schema.json",
    "data/api/v1/benchmarks.json",
    "data/api/v1/hardware.json",
    "tools/schema.json",
    "tools/tags.json",
)


def load_tool(relpath: str, module_name: str | None = None) -> ModuleType:
    """Import a ``tools/*.py`` script as a module from its file path.

    Args:
        relpath: Path relative to the repo root (e.g. ``"tools/pull.py"``).
        module_name: Optional module name; defaults to the file stem.

    Returns:
        The executed module. Scripts here only define constants and
        functions at import time (no side effects), so importing is safe.
    """
    path = ROOT / relpath
    name = module_name or path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot build import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(relpath: str):
    """Load a JSON file from the repo (path relative to the repo root)."""
    with open(ROOT / relpath, encoding="utf-8") as f:
        return json.load(f)
