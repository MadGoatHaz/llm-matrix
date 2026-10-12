#!/usr/bin/env python3
"""Regenerate the ``tests/golden/`` baselines from the current generator.

The golden files (``tests/golden/{index,matrix,community,guides,about}.html``
+ ``data.json``) are the byte-for-byte regression baselines that
``tests/test_generate.py::TestGoldenRegression`` compares against. They are
committed to the repo so CI can detect accidental drift in the generated
pages without a network or a manual run.

Run this ONLY when you deliberately change the generator's output and want to
re-baseline (for example, after an intentional template change). It overwrites
the committed golden files — review the resulting diff before committing:

    make golden                 # recommended
    python tests/capture_golden.py    # equivalent

The capture mirrors the test's setup: it copies the generator's required
inputs into a throwaway workspace, runs ``tools.site.main()`` there, and
copies the canonical outputs (5 core pages + data.json + the /api/ docs
page) back into ``tests/golden/``. The committed site is never touched.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

# Repo root = parent of this tests/ directory (path-robust, any cwd).
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Inputs the generator requires at runtime (authored, not generated). The four
# core files plus the ``content/`` dir, so the full site — including the
# markdown-based recommend/guides pages — renders without "skipped" warnings,
# exactly like a real build.
REQUIRED_FILES = (
    "data/submissions.json",
    "tools/schema.json",
    "css/style.css",
    "js/main.js",
)
REQUIRED_DIRS = ("content",)

# The canonical outputs captured as golden baselines (the /api/ page is
# included from P4-4).
GOLDEN_FILES = (
    "index.html",
    "matrix.html",
    "community.html",
    "guides.html",
    "about.html",
    "data.json",
    "api/index.html",
)


def main() -> None:
    # Deferred import: the guide layer needs the `markdown` content dep, which
    # `pip install -e .` provides. The five core pages are stdlib-only.
    from tools.site import main as site_main

    tmp = Path(tempfile.mkdtemp(prefix="las_golden_capture_"))
    try:
        for rel in REQUIRED_FILES:
            src = ROOT / rel
            dst = tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        for rel in REQUIRED_DIRS:
            src = ROOT / rel
            if src.exists():
                shutil.copytree(src, tmp / rel, dirs_exist_ok=True)

        site_main(
            workspace=tmp,
            data_dir=tmp / "data",
            submissions=tmp / "data" / "submissions.json",
            schema=tmp / "tools" / "schema.json",
        )

        golden_dir = ROOT / "tests" / "golden"
        golden_dir.mkdir(parents=True, exist_ok=True)
        for rel in GOLDEN_FILES:
            dst = golden_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)  # e.g. golden/api/
            shutil.copy2(tmp / rel, dst)
            print(f"  updated tests/golden/{rel}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\nGolden baselines regenerated. Review the diff before committing.")


if __name__ == "__main__":
    main()
