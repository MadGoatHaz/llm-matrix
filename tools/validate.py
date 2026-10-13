#!/usr/bin/env python3
"""
validate.py — data-quality validation for The Local AI Stack (PLAN.md P3-5).

Runs a battery of checks over the committed data files against
``tools/schema.json`` and prints a clear pass/fail report:

  1. valid-json            — every committed ``.json`` file parses.
  2. required-fields       — each submission carries the full canonical key set.
  3. enum-conformance      — tier / vendor / backend / confidence / lifecycle /
                            engine_mode are all schema-legal (backend via the
                            generator's single-source-of-truth normalizer).
                            Empty values are missing data, not violations —
                            they surface in the data-gap check.
  4. duplicates            — no duplicate submission ids; repeated post+model
                            pairs are flagged (informational).
  5. vram-reasonable       — VRAM is sensible: a tier's ceiling is > 0 and
                            <= 1000 GB, and no explicit "N GB" hardware figure
                            is 0 or > 1000 GB (figures in system-memory
                            context, e.g. "Xeon CPU (1024 GB)", are skipped).
  6. referential-integrity — post ids are integers and the schema still
                             references the ``main`` thread that ``parse.py``
                             depends on.
  7. data-gaps (info)      — surfaces known gaps (e.g. 0 Apple submissions,
                             empty engine_mode, un-normalizable use cases).

A check that fails is a hard **error** (exit code 1); the data-gap check is
informational (a **warning**) and never affects the exit code. This is stdlib-
only, consistent with the rest of the data pipeline.

Run:
    python tools/validate.py
"""

import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (defaults = the real repo). Tests may point these elsewhere.
# ---------------------------------------------------------------------------
WORKSPACE = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSPACE / "data"
SCHEMA = WORKSPACE / "tools" / "schema.json"

# Make the repo root importable so we can reuse the generator's normalizer
# (the single source of truth for backend canonicalization) without
# duplicating its logic.
_REPO_ROOT = str(WORKSPACE)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from tools.site.utils import normalize_backend, match_use_cases  # noqa: E402

# Every JSON file the pipeline reads/writes that must stay valid.
DATA_FILES = (
    "data/submissions.json",
    "data/benchmarks.json",
    "data/hardware.json",
    "data/category_threads.json",
    "data/last_seen.json",
    "tools/schema.json",
    "tools/tags.json",
)

# The canonical key contract every parsed submission carries (schema v2.1).
# Mirrors tests/test_data.py so the validator and the test suite agree.
REQUIRED_KEYS = (
    "id", "source", "type", "raw", "tier", "hardware", "backend", "model",
    "quant", "weight_precision", "use_cases", "context", "performance",
    "engine_mode", "notes", "confidence", "lifecycle", "highlight", "tags",
)

# No real accelerator (or system) has this much memory; it bounds "reasonable".
MAX_VRAM_GB = 1000

# "N GB" / "NGB" / "N GiB" in a hardware description.
_GB_RE = re.compile(r"(\d+)\s*(?:GB|GiB|GiB|gib|GIB)\b", re.IGNORECASE)
_URL_RE = re.compile(r"^https?://")

# Words that mark a "N GB" figure as *system* memory (not VRAM) when they
# appear in the short context immediately before the figure.
_SYSTEM_MEM_CONTEXT_RE = re.compile(
    r"(?i)\b(cpu|ram|memory|mem|ddr|epyc|xeon|ryzen|apu)\b"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path):
    """Load and parse a JSON file from ``path``."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _check(name, status, detail=""):
    """A single named result: ``status`` is ``pass`` / ``fail`` / ``warn``."""
    return {"name": name, "status": status, "detail": detail}


# ---------------------------------------------------------------------------
# Individual checks (each returns a list of _check dicts)
# ---------------------------------------------------------------------------

def check_json_files(workspace=WORKSPACE):
    """Every committed ``.json`` file must parse (check 1)."""
    results = []
    for rel in DATA_FILES:
        path = workspace / rel
        if not path.exists():
            results.append(_check(f"valid-json: {rel}", "fail", "file is missing"))
            continue
        try:
            load_json(path)
            results.append(_check(f"valid-json: {rel}", "pass"))
        except Exception as exc:  # noqa: BLE001 - report any parse failure
            results.append(_check(f"valid-json: {rel}", "fail", str(exc)))
    return results


def check_required_fields(subs):
    """Each submission carries the full canonical key set (check 2)."""
    bad = []
    for s in subs:
        missing = [k for k in REQUIRED_KEYS if k not in s]
        if missing:
            bad.append(f"{s.get('id', '?')} (missing {', '.join(missing)})")
    if bad:
        return [_check("required-fields", "fail",
                       f"{len(bad)}/{len(subs)} missing keys: " + "; ".join(bad[:5]))]
    return [_check("required-fields", "pass",
                   f"{len(subs)} submissions carry all {len(REQUIRED_KEYS)} keys")]


def check_enum_conformance(subs, schema):
    """tier / vendor / backend / confidence / lifecycle / engine_mode (check 3).

    The raw ``backend`` string is canonicalized with the generator's
    ``normalize_backend`` before being checked against the schema set — the
    same rule the test suite applies, so a free-text backend is only a problem
    if it genuinely names an unknown engine.

    Empty values are *missing data*, not contract breaks: an absent backend or
    an un-normalizable tier (``None``) is surfaced by the data-gap check and
    never hard-fails the gate, so one unusual community entry can't stall the
    weekly push. A *non-empty* invalid value (e.g. tier ``t9``) still fails.
    """
    valid_tiers = {t["id"] for t in schema["tiers"]}
    valid_vendors = set(schema["hardware_vendors"])
    valid_backends = set(schema["backends"])
    valid_confidence = set(schema["confidence_levels"])
    valid_lifecycle = set(schema["lifecycle_statuses"])
    valid_modes = set(schema["engine_modes"])

    violations = []
    for s in subs:
        sid = s.get("id", "?")
        tier = s.get("tier")
        if tier is not None and tier not in valid_tiers:
            violations.append(f"{sid}: tier {tier!r}")
        vendor = (s.get("hardware") or {}).get("vendor")
        if vendor not in valid_vendors:
            violations.append(f"{sid}: vendor {vendor!r}")
        backend_raw = (s.get("backend") or "").strip()
        if backend_raw:
            backend = normalize_backend(backend_raw, schema)
            if backend not in valid_backends:
                violations.append(f"{sid}: backend {backend_raw!r} -> {backend!r}")
        if s.get("confidence") not in valid_confidence:
            violations.append(f"{sid}: confidence {s.get('confidence')!r}")
        if s.get("lifecycle") not in valid_lifecycle:
            violations.append(f"{sid}: lifecycle {s.get('lifecycle')!r}")
        mode = (s.get("engine_mode") or "").strip()
        if mode and mode not in valid_modes:
            violations.append(f"{sid}: engine_mode {mode!r}")

    if violations:
        return [_check("enum-conformance", "fail",
                       f"{len(violations)} violation(s): " + "; ".join(violations[:6]))]
    return [_check("enum-conformance", "pass", "all enum values are schema-legal")]


def check_duplicates(subs):
    """No duplicate submission ids; repeated post+model flagged (check 4)."""
    ids = [s.get("id") for s in subs]
    dup_ids = sorted({i for i in ids if ids.count(i) > 1})
    if dup_ids:
        return [_check("duplicates", "fail",
                       f"{len(dup_ids)} duplicate id(s): " + ", ".join(dup_ids[:5]))]

    # Near-duplicates: the same forum post reporting the same model name twice.
    seen = {}
    near = []
    for s in subs:
        src = s.get("source") or {}
        model = (s.get("model") or {}).get("name", "")
        key = (src.get("post_id"), model)
        if key in seen:
            near.append(f"{seen[key]} & {s.get('id')} (same post+model)")
        else:
            seen[key] = s.get("id")
    if near:
        return [_check("duplicates", "warn",
                       f"{len(near)} repeated post+model: " + "; ".join(near[:3]))]
    return [_check("duplicates", "pass", f"{len(subs)} unique submission ids")]


def check_vram_reasonable(subs, schema):
    """VRAM is never 0 and never > 1000 GB (check 5).

    Two sources: the submission's tier (whose *upper* bound must be a real,
    finite amount of memory) and any explicit ``N GB`` figure in the hardware
    string. A tier like ``t1`` is ``≤16GB`` = ``[0, 16]`` — a 0 *floor* is
    legitimate (small cards live there), so only the ceiling is bounded: it
    must be ``> 0`` and ``<= MAX_VRAM_GB``. An explicit ``0GB`` or ``5000GB``
    in the hardware text is a genuine error.

    System memory is not VRAM: a ``N GB`` figure whose immediate context
    names a CPU/RAM component ("Xeon CPU (1024 GB)", "128GB DDR4") is
    skipped — hosts with a terabyte of system RAM (model spill-out rigs)
    are legitimate and must not trip the VRAM ceiling.
    """
    tier_ranges = {t["id"]: t["range"] for t in schema["tiers"]}
    problems = []
    for s in subs:
        sid = s.get("id", "?")
        rng = tier_ranges.get(s.get("tier"))
        if rng is not None:
            if rng[1] <= 0:
                problems.append(f"{sid}: tier {s.get('tier')} has no VRAM (max {rng[1]}GB)")
            elif rng[1] > MAX_VRAM_GB:
                problems.append(f"{sid}: tier {s.get('tier')} max {rng[1]}GB exceeds {MAX_VRAM_GB}GB")
        hw = (s.get("hardware") or {}).get("description", "")
        for m in _GB_RE.finditer(hw):
            n = int(m.group(1))
            lookback = hw[max(0, m.start() - 25):m.start()]
            if _SYSTEM_MEM_CONTEXT_RE.search(lookback):
                continue  # system memory / CPU figure, not VRAM
            if n == 0:
                problems.append(f"{sid}: hardware lists 0GB")
            elif n > MAX_VRAM_GB:
                problems.append(f"{sid}: hardware lists {n}GB (> {MAX_VRAM_GB}GB)")
    if problems:
        return [_check("vram-reasonable", "fail",
                       f"{len(problems)} issue(s): " + "; ".join(problems[:6]))]
    return [_check("vram-reasonable", "pass",
                   f"all {len(subs)} VRAM values within (0, {MAX_VRAM_GB}GB]")]


def check_referential_integrity(subs, schema):
    """Hard referential contract (check 6): post ids are integers and the
    schema still references the ``main`` thread ``parse.py`` depends on.

    (A ``model.url`` that is not an ``http(s)`` link is a *data gap*, not a
    contract break — it is reported by :func:`check_data_gaps`.)
    """
    problems = []
    for s in subs:
        sid = s.get("id", "?")
        src = s.get("source") or {}
        pid = src.get("post_id")
        if pid is not None and not isinstance(pid, int):
            problems.append(f"{sid}: post_id {pid!r} is not an integer")
    thread_ids = {t.get("id") for t in schema.get("monitored_threads", [])}
    if "main" not in thread_ids:
        problems.append("schema: 'main' monitored thread missing (parse.py depends on it)")
    if problems:
        return [_check("referential-integrity", "fail",
                       f"{len(problems)} issue(s): " + "; ".join(problems[:6]))]
    return [_check("referential-integrity", "pass",
                   "post ids and the schema's thread references are sound")]


def check_data_gaps(subs, schema):
    """Informational gaps for the maintainer (check 7; never a hard fail)."""
    notes = []
    vendors = [(s.get("hardware") or {}).get("vendor") for s in subs]
    apple = sum(1 for v in vendors if v == "Apple")
    notes.append(f"{apple} Apple/MLX submissions (biggest demographic gap)")
    empty_mode = sum(1 for s in subs if not (s.get("engine_mode") or "").strip())
    notes.append(f"{empty_mode}/{len(subs)} engine_mode empty")
    empty_backend = sum(1 for s in subs if not (s.get("backend") or "").strip())
    none_tier = sum(1 for s in subs if s.get("tier") is None)
    if empty_backend:
        notes.append(f"{empty_backend}/{len(subs)} backend empty")
    if none_tier:
        notes.append(f"{none_tier}/{len(subs)} tier un-normalizable")
    unnormalized = sum(
        1 for s in subs
        if (s.get("use_cases") or "").strip() and not match_use_cases(s.get("use_cases"), schema)
    )
    notes.append(f"{unnormalized} use_cases strings map to no schema category")
    bad_urls = sum(
        1 for s in subs
        if (s.get("model") or {}).get("url") and not _URL_RE.match((s.get("model") or {}).get("url", ""))
    )
    notes.append(f"{bad_urls} model urls are not http(s) links")
    return [_check("data-gaps (info)", "warn", " | ".join(notes))]


# ---------------------------------------------------------------------------
# Orchestration + report
# ---------------------------------------------------------------------------

def validate(data_dir=DATA_DIR, workspace=WORKSPACE, schema_path=SCHEMA):
    """Run every check.

    Args:
        data_dir: Directory holding the data ``.json`` files.
        workspace: Repo root (resolves the full set of ``DATA_FILES``).
        schema_path: Path to ``schema.json``.

    Returns:
        ``(results, valid)`` — ``results`` is the list of per-check dicts and
        ``valid`` is True only when no check has status ``fail``.
    """
    results = check_json_files(workspace=workspace)

    schema = load_json(schema_path)
    data = load_json(Path(data_dir) / "submissions.json")
    subs = data.get("submissions", [])

    results += check_required_fields(subs)
    results += check_enum_conformance(subs, schema)
    results += check_duplicates(subs)
    results += check_vram_reasonable(subs, schema)
    results += check_referential_integrity(subs, schema)
    results += check_data_gaps(subs, schema)

    valid = all(r["status"] != "fail" for r in results)
    return results, valid


def render_report(results):
    """Format the per-check results as a readable report string."""
    icon = {"pass": "✓", "fail": "✗", "warn": "⚠"}
    lines = [
        "=" * 64,
        "DATA QUALITY REPORT — The Local AI Stack",
        "=" * 64,
    ]
    for r in results:
        line = f" {icon.get(r['status'], '?')} [{r['status'].upper():4}] {r['name']}"
        if r["detail"]:
            line += f" — {r['detail']}"
        lines.append(line)
    n_pass = sum(1 for r in results if r["status"] == "pass")
    n_fail = sum(1 for r in results if r["status"] == "fail")
    n_warn = sum(1 for r in results if r["status"] == "warn")
    lines += [
        "-" * 64,
        f"SUMMARY: {n_pass} passed, {n_fail} failed, {n_warn} warning(s)",
        "=" * 64,
    ]
    return "\n".join(lines)


def main():
    """Run the validator on the committed data; return the exit code."""
    results, valid = validate()
    print(render_report(results))
    if valid:
        print("\nRESULT: VALID — the data passes all hard checks.")
        return 0
    print("\nRESULT: INVALID — fix the failing checks above before merging.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
