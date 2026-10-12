"""One-off: capture golden baselines from the CURRENT monolith.

Mirrors tests/test_generate.py's temp-workspace approach: copy the required
inputs into a temp dir, point the monolith's path constants there, run main(),
then copy the 5 generated pages + data.json into tests/golden/.

Run BEFORE refactoring so the golden files lock the pre-refactor bytes.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from tests.util import load_tool  # noqa: E402

REQUIRED_INPUTS = (
    "data/submissions.json",
    "tools/schema.json",
    "css/style.css",
    "js/main.js",
)
OUTPUTS = ("index.html", "matrix.html", "community.html", "guides.html", "about.html", "data.json")


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="las_golden_"))
    for rel in REQUIRED_INPUTS:
        src = ROOT / rel
        dst = tmp / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    module = load_tool("tools/generate_site.py")
    module.WORKSPACE = tmp
    module.DATA_DIR = tmp / "data"
    module.SUBMISSIONS = tmp / "data" / "submissions.json"
    module.SCHEMA = tmp / "tools" / "schema.json"
    module.main()

    golden = ROOT / "tests" / "golden"
    golden.mkdir(parents=True, exist_ok=True)
    for name in OUTPUTS:
        shutil.copy2(tmp / name, golden / name)
        print(f"captured golden/{name} ({(golden / name).stat().st_size} bytes)")

    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
