"""The versioned data API (P4-4).

The site's dataset *is* the API. This module publishes it as stable,
versioned JSON files that scripts, other sites, and research tools can
consume:

* ``data.json``                    — the canonical dataset at the site root
  (what the client-side tools fetch), now carrying a ``version`` field.
* ``data/api/v1/submissions.json`` — the same payload at its versioned path.
* ``data/api/v1/benchmarks.json``  — the Crucible benchmark-thread dataset.
* ``data/api/v1/hardware.json``    — the "Show Off Your AI Rig" dataset.
* ``data/api/v1/schema.json``      — the JSON Schema for the submissions
  payload. **Authored, not generated** — the generator never overwrites it.

**Versioning policy.** ``API_VERSION`` is ``major.minor``. A *breaking*
change to any published shape bumps the major and moves the files to a new
``data/api/vN/`` path (old versions stay frozen); an *additive* change
bumps the minor in place. The full contract — fields, CORS behavior,
update cadence, changelog — lives in ``data/api/README.md``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from . import utils

#: The current data API version (major.minor).
API_VERSION = "1.0"

#: The published, versioned data directory (relative to the repo root).
API_DIR = "data/api"
API_V1_DIR = f"{API_DIR}/v1"

#: The secondary-thread datasets that get a versioned copy under v1/
#: (the canonical submissions dataset is handled separately).
_SECONDARY_DATASETS = ("benchmarks.json", "hardware.json")


def api_payload(data: dict, version: str = API_VERSION) -> dict:
    """The versioned submissions payload (``data.json`` / ``v1/submissions.json``).

    The dataset parsed by ``tools/parse.py`` plus the API ``version`` field,
    which is placed first so consumers see the contract generation up front.

    Args:
        data: The parsed dataset (``data/submissions.json``: header fields +
            the ``submissions`` list).
        version: The API version stamp.

    Returns:
        A new dict — ``data`` is not mutated.
    """
    out = {"version": version}
    out.update(data)
    return out


def write_api(ws: Path, data: dict, version: str = API_VERSION) -> list[str]:
    """Write the versioned data API files into ``ws`` (the repo root).

    Writes ``data.json`` and ``data/api/v1/submissions.json`` (always — they
    are the canonical payload), then versioned copies of the secondary
    datasets (``benchmarks.json``, ``hardware.json``) when present. Missing
    secondary datasets are reported as warnings, never silently dropped —
    a test workspace that only carries the core inputs simply publishes the
    canonical payload.

    The authored ``data/api/v1/schema.json`` is **not** touched.

    Args:
        ws: The repo root / output directory.
        data: The parsed dataset (``data/submissions.json``).
        version: The API version stamp for every payload written.

    Returns:
        The list of relative paths written (for logging/tests).
    """
    written: list[str] = []

    # --- Canonical payload: data.json + data/api/v1/submissions.json ---
    payload = api_payload(data, version)
    for rel in ("data.json", f"{API_V1_DIR}/submissions.json"):
        path = ws / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        written.append(rel)
        print(f"  wrote {rel} ({path.stat().st_size} bytes)")

    # --- Secondary datasets (versioned copies when present) ---
    for name in _SECONDARY_DATASETS:
        src = ws / "data" / name
        if not src.exists():
            print(f"WARNING: data/{name} not found — "
                  f"{API_V1_DIR}/{name} not published.", file=sys.stderr)
            continue
        sec = utils.load_json(src)
        sec = {"version": version, **sec}
        rel = f"{API_V1_DIR}/{name}"
        path = ws / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(sec, f, indent=2)
        written.append(rel)
        print(f"  wrote {rel} ({path.stat().st_size} bytes)")

    return written
