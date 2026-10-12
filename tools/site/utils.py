"""Shared helpers for the site generator.

Data loading, template/placeholder detection, field accessors, display
formatting, and the aggregation functions (stats, trending, backends,
fastest) that the page renderers build on.

This module is deliberately dependency-free (stdlib only) so the five
core pages can be generated without the optional ``markdown`` package.
"""

from __future__ import annotations

import html as html_module
import json
import re
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path constants (defaults = the real repo root). Tests may override the
# module-level copies in the thin entry point; the generator's ``main()``
# accepts explicit path arguments so it never depends on these at runtime.
# ---------------------------------------------------------------------------

#: Repo root (this file lives at ``<root>/tools/site/utils.py``).
WORKSPACE: Path = Path(__file__).resolve().parent.parent.parent
DATA_DIR: Path = WORKSPACE / "data"
SUBMISSIONS: Path = DATA_DIR / "submissions.json"
SCHEMA: Path = WORKSPACE / "tools" / "schema.json"

# ---------------------------------------------------------------------------
# Canonical URLs
# ---------------------------------------------------------------------------

SITE_URL = "https://madgoathaz.github.io/llm-matrix"
FORUM_THREAD = "https://forum.level1techs.com/t/256443"
FORUM_CATEGORY = ("https://forum.level1techs.com/"
                  "c/high-performance-computing/deep-machine-learning-ai/155")
GITHUB_REPO = "https://github.com/MadGoatHaz/llm-matrix"


# ---------------------------------------------------------------------------
# Data loading + template / placeholder detection
# ---------------------------------------------------------------------------

def load_json(path: str | Path) -> Any:
    """Load and parse a JSON file from ``path``."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def html_escape(s: Any) -> str:
    """HTML-escape a value; ``''`` for falsy input (XSS-safe interpolation)."""
    if not s:
        return ""
    return html_module.escape(str(s))


# Unfilled template values look like "[e.g., ...]" — i.e. the whole value is
# wrapped in brackets.
PLACEHOLDER_RE = re.compile(r"^\[.*\]$", re.DOTALL)


def is_placeholder(value: Any) -> bool:
    """True if value is empty/None or an unfilled template placeholder."""
    if value is None:
        return True
    s = str(value).strip()
    if not s:
        return True
    return bool(PLACEHOLDER_RE.match(s))


def clean_value(value: Any) -> str:
    """Display string for a field: '' if placeholder, else the stripped value."""
    if is_placeholder(value):
        return ""
    return str(value).strip()


def is_template_submission(s: dict) -> bool:
    """True if a submission carries no real data (unfilled/empty template)."""
    key_fields = [
        (s.get("hardware") or {}).get("description"),
        (s.get("model") or {}).get("name"),
        s.get("backend"),
        s.get("quant"),
        (s.get("performance") or {}).get("decode_tps"),
        (s.get("context") or {}).get("stable"),
        s.get("use_cases"),
    ]
    return all(is_placeholder(v) for v in key_fields)


def real_submissions(data: dict) -> list[dict]:
    """Submissions with real data (templates filtered out)."""
    return [s for s in data.get("submissions", []) if not is_template_submission(s)]


# ---------------------------------------------------------------------------
# Field accessors + display helpers
# ---------------------------------------------------------------------------

def hw(s: dict) -> dict:
    """The submission's hardware object (``{}`` if absent)."""
    return s.get("hardware") or {}


def model_name(s: dict) -> str:
    """The submission's model name (``''`` if absent)."""
    return (s.get("model") or {}).get("name", "")


def perf(s: dict) -> dict:
    """The submission's performance object (``{}`` if absent)."""
    return s.get("performance") or {}


def ctx(s: dict) -> dict:
    """The submission's context object (``{}`` if absent)."""
    return s.get("context") or {}


def short_model(name: Any) -> str:
    """Compact model label for cards: first model only, no repo prefix."""
    if not name:
        return ""
    s = str(name).strip()
    s = s.split(",")[0].strip()
    if "/" in s and not s.lower().startswith(("http", "www")):
        s = s.split("/", 1)[1]
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s).strip(" ,")
    if len(s) > 55:
        s = s[:52] + "…"
    return s


BACKEND_ALIASES = {
    "llamacpp": "llama.cpp",
    "llama-cpp": "llama.cpp",
    "llama cpp": "llama.cpp",
}


def normalize_backend(raw: Any, schema: dict) -> str:
    """Canonical backend name for filter attributes.

    'vLLM (magiccodingman/vllm-radiance, adaptive MTP=8)' -> 'vLLM'
    'Strata 0.1.42' -> 'Strata'
    'llamacpp' -> 'llama.cpp'
    """
    if not raw:
        return ""
    s = str(raw).strip()
    s = re.sub(r"\(.*$", "", s).strip()              # drop trailing parenthetical
    s = re.sub(r"\s+\d[\w.]*$", "", s).strip()       # drop trailing version
    if not s:
        return ""
    alias = BACKEND_ALIASES.get(s.lower())
    if alias:
        return alias
    for sb in schema.get("backends", []):
        if sb.lower() == s.lower():
            return sb
    return s


def compute_stats(subs: list[dict], schema: dict) -> dict:
    """Headline counts: submissions, contributors, vendors, backends."""
    vendor_set = set()
    backend_set = set()
    for s in subs:
        v = hw(s).get("vendor", "")
        if v and not is_placeholder(v):
            # Exclude "Mixed" when it comes only from empty/template entries
            if v == "Mixed" and is_placeholder(hw(s).get("description")):
                continue
            vendor_set.add(v)
        b = normalize_backend(s.get("backend", ""), schema)
        if b:
            backend_set.add(b)
    contributors = {s["source"]["username"] for s in subs}
    return {
        "submissions": len(subs),
        "contributors": len(contributors),
        "vendors": len(vendor_set),
        "backends": len(backend_set),
    }


def group_by_tier(subs: list[dict], tiers: list[dict]) -> list[tuple[str, str, list[dict]]]:
    """Ordered [(tier_id, tier_label, [subs...])] for tiers that have rows."""
    labels = {t["id"]: t["label"] for t in tiers}
    out = []
    for t in tiers:
        tier_subs = [s for s in subs if s.get("tier") == t["id"]]
        if tier_subs:
            out.append((t["id"], labels[t["id"]], tier_subs))
    return out


def group_by_contributor(subs: list[dict]) -> list[tuple[str, list[dict]]]:
    """[(username, [subs...])] sorted by submission count desc, then name."""
    by_user = {}
    for s in subs:
        by_user.setdefault(s["source"]["username"], []).append(s)
    return sorted(by_user.items(), key=lambda kv: (-len(kv[1]), kv[0].lower()))


# Quant/format/author tokens used to reduce a raw (messy, repo-prefixed,
# comma-separated) model name down to a clean "family" label for trend
# grouping — e.g. "Swift-Qwen3.8-27B-Uncensored-FP8" -> "Qwen3.8-27B".
FAMILY_AUTHOR_PREFIX = re.compile(
    r"^(?:swift|carnice|unsloth|bartowski|deadbydawn101|d0xin|"
    r"maziyarpanahi|samuelcardillo|kwaipilot)[-_]?", re.I)
FAMILY_TAIL_TOKEN = re.compile(
    r"[-_](?:gguf|sft|fp16|fp8|bf16|nvfp4|mxfp4|iq\d[\w.]*|q\d[\w.]*|"
    r"i-nano|uncensored|w\d+a\d+|exl2[\w.]*|the-defiant[\w-]*|"
    r"heretic[\w-]*|neo-max[\w-]*|mtp[\w-]*|agentic[\w-]*|opus[\w-]*|"
    r"reasoning[\w-]*|gemini-?cli[\w-]*|dev)\b[\w.-]*$", re.I)


def model_family(name: Any) -> str:
    """Reduce a raw model name to a clean family label (first model only)."""
    if not name:
        return ""
    s = str(name).split(",")[0].strip()
    if "/" in s and not s.lower().startswith(("http", "www")):
        s = s.split("/", 1)[1].strip()
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s).strip()   # drop trailing parenthetical
    s = FAMILY_AUTHOR_PREFIX.sub("", s).strip()
    for _ in range(6):  # peel trailing quant/format tokens one at a time
        new = FAMILY_TAIL_TOKEN.sub("", s).strip(" -_")
        if new == s:
            break
        s = new
    return s


def parse_speed(value: Any) -> float | None:
    """First numeric token in a decode_tps string, as float (or None)."""
    m = re.search(r"(\d+(?:\.\d+)?)", clean_value(value))
    return float(m.group(1)) if m else None


def trending_models(subs: list[dict], n: int = 3) -> list[tuple[str, int, str]]:
    """Top-n model families by submission count: [(family, count, note)]."""
    counts = {}
    best_speed = {}
    for s in subs:
        fam = model_family(model_name(s))
        if not fam:
            continue
        counts[fam] = counts.get(fam, 0) + 1
        sp = parse_speed(perf(s).get("decode_tps"))
        if sp is not None:
            best_speed[fam] = max(best_speed.get(fam, 0.0), sp)
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))[:n]
    out = []
    for fam, c in ranked:
        sp = best_speed.get(fam)
        note = f"Up to {sp:g} t/s decode" if sp else "Community favorite"
        out.append((fam, c, note))
    return out


def popular_backends(subs: list[dict], schema: dict, n: int = 3) -> list[tuple[str, int]]:
    """Top-n backends by usage: [(backend, count)]."""
    counts = {}
    for s in subs:
        b = normalize_backend(s.get("backend", ""), schema)
        if b:
            counts[b] = counts.get(b, 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))[:n]


def fastest_setups(subs: list[dict], n: int = 3) -> list[tuple[str, str, float, Any]]:
    """Top-n submissions by decode speed: [(username, model, speed, hardware)]."""
    rows = []
    for s in subs:
        sp = parse_speed(perf(s).get("decode_tps"))
        if sp is None:
            continue
        rows.append((sp, s["source"]["username"], model_name(s),
                     hw(s).get("description")))
    rows.sort(key=lambda r: -r[0])
    return [(u, m, sp, h) for sp, u, m, h in rows[:n]]
