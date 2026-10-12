#!/usr/bin/env python3
"""
generate_site.py — thin entry point for the site generator.

The real implementation now lives in the modular ``tools/site`` package. This
file stays so the established command keeps working unchanged:

    python tools/generate_site.py

It is equivalent to:

    python -m tools.site

The module also re-exports a few helpers (``normalize_backend``,
``is_template_submission``, …) that other tools and the test suite import from
this file, and defines the module-level path constants the tests override
before calling ``main()``. The single source of truth for all of these is
``tools/site/utils.py``.
"""

import sys
from pathlib import Path

# Make the repo root importable so ``tools.site`` resolves from any cwd.
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from tools.site import main as _site_main  # noqa: E402
from tools.site import utils as _utils  # noqa: E402

# Module-level path constants (the test suite rebinds these before main()).
WORKSPACE = _utils.WORKSPACE
DATA_DIR = _utils.DATA_DIR
SUBMISSIONS = _utils.SUBMISSIONS
SCHEMA = _utils.SCHEMA

# Re-exported helpers (delegated to tools.site.utils — no duplicated logic).
normalize_backend = _utils.normalize_backend
is_template_submission = _utils.is_template_submission
is_placeholder = _utils.is_placeholder
clean_value = _utils.clean_value
real_submissions = _utils.real_submissions
load_json = _utils.load_json
html_escape = _utils.html_escape


def main() -> None:
    """Generate all site pages + data.json (delegates to ``tools.site``)."""
    _site_main(
        workspace=WORKSPACE,
        data_dir=DATA_DIR,
        submissions=SUBMISSIONS,
        schema=SCHEMA,
    )


if __name__ == "__main__":
    main()
