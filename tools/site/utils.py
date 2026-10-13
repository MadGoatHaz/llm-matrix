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


def icon(glyph: str) -> str:
    """A decorative icon/emoji wrapped in an ``aria-hidden`` span (P2-6).

    Screen readers skip the glyph and read only the adjacent text label,
    which is the accessible pattern for decorative icons.
    """
    return f'<span class="icon" aria-hidden="true">{html_module.escape(glyph)}</span>'


def compact_json(obj: Any) -> str:
    """Serialize ``obj`` to compact JSON that can never leak ``{{``/``}}``.

    The template-leak check rejects any page containing the literal
    ``{{`` or ``}}`` sequences. ``indent=2`` was the original workaround
    (braces on their own lines), but it roughly doubles the size of the
    baked config islands. Compact JSON with tight separators is valid and,
    because a JSON object always opens with ``{"`` and closes its nesting
    as ``}}``, the only possible adjacent-brace run is ``}}`` at the end of
    nested objects — which is split into ``} }`` (legal JSON whitespace).
    ``{{`` cannot occur in valid JSON at all (an opening brace is always
    followed by a string key).
    """
    payload = json.dumps(obj, separators=(",", ":"))
    return payload.replace("}}", "} }")


# Unfilled template values look like "[e.g., ...]", "[vLLM | llama.cpp | ...]"
# or "[Full model name]" — the whole value is wrapped in brackets AND the
# content reads as a fill-in instruction: an option list (pipes), an example
# marker, or a template phrase. Contributors who simply wrap real values in
# brackets (e.g. "[llama-cpp]", "[8192]") are NOT placeholders.
PLACEHOLDER_RE = re.compile(r"^\[.*\]$", re.DOTALL)
TEMPLATE_CONTENT_RE = re.compile(
    r"\||e\.g\.|example|full model|your \w+|name here|insert", re.IGNORECASE
)


def is_placeholder(value: Any) -> bool:
    """True if value is empty/None or an unfilled template placeholder.

    Bracket styling is irrelevant to the check: the template *content*
    (option lists, example markers, fill-in phrases) is what identifies an
    unfilled field, so values that parse.py has already unbracketed are
    caught just as reliably as raw bracketed ones.
    """
    if value is None:
        return True
    s = str(value).strip()
    if not s:
        return True
    body = s[1:-1].strip() if (s.startswith("[") and s.endswith("]")) else s
    return bool(TEMPLATE_CONTENT_RE.search(body))


def clean_value(value: Any) -> str:
    """Display string for a field: '' if placeholder, else the stripped
    value (a user's surrounding-bracket styling is removed)."""
    if is_placeholder(value):
        return ""
    s = str(value).strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1].strip()
    return s


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


#: The fields the client-side tools (launch-command generator, comparison
#: view) actually need from a submission. The verbose ``raw`` block and the
#: ``source``/``confidence``/``lifecycle``/``highlight``/``tags`` metadata are
#: dropped to keep the baked JSON island small.
CLIENT_SUBMISSION_FIELDS = (
    "id", "tier", "hardware", "backend", "model", "quant",
    "weight_precision", "use_cases", "context", "performance",
    "engine_mode", "notes",
)


def trim_for_client(s: dict) -> dict:
    """A submission reduced to the fields the client tools consume.

    ``hardware`` / ``model`` / ``context`` / ``performance`` are kept whole
    (they are small structured objects); the flat scalar fields are copied
    verbatim. ``source`` is kept (post id + username + date) so the row
    detail panel can build the original forum deep link (``#post-N``).
    Missing keys default to empty so the JSON shape is stable.
    """
    out: dict[str, Any] = {}
    for key in CLIENT_SUBMISSION_FIELDS:
        val = s.get(key)
        out[key] = val if val is not None else (
            {} if key in ("hardware", "model", "context", "performance") else "")
    src = s.get("source") or {}
    out["source"] = {
        "post_number": src.get("post_number"),
        "post_id": src.get("post_id"),
        "username": src.get("username", ""),
        "submitted_at": src.get("submitted_at", ""),
    }
    out["username"] = out["source"]["username"]
    return out


# ---------------------------------------------------------------------------
# Use-case normalization (free text -> schema categories)
# ---------------------------------------------------------------------------

#: Keyword map for reducing a submission's free-text ``use_cases`` string to
#: the schema's canonical categories. Mirrors ``js/recommend.js`` (the
#: client-side recommendation engine) so the generation-time filter
#: attributes (``data-use-case``) and the recommend tooling agree.
USE_CASE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Agentic Coding": ("coding", "code", "agentic", "programming", "developer",
                      "software", "judge", "opencode"),
    "Repo Editing": ("repo", "repository", "codebase"),
    "Deep Reasoning": ("reasoning", "deep reason", "think", "analysis"),
    "Math/Logic": ("math", "logic", "arithmetic", "calculat"),
    "RAG": ("rag", "retrieval"),
    "Document Ingestion": ("document", "ingest", "q&a", "qa"),
    "Creative Writing": ("creative", "writing", "story", "fiction"),
    "Roleplay": ("roleplay", "character"),
    "General Chat": ("chat", "conversation", "general", "brainstorm", "planning"),
    "Translation": ("translation", "translate", "language"),
    "Security Research": ("security", "dos", "vulnerab", "exploit"),
    "Multimodal": ("multimodal", "vision", "image", "audio", "video"),
    "Production Serving": ("production", "serving", "api", "openai-compatible"),
    "Embeddings": ("embedding",),
}


def _keyword_in(text: str, kw: str) -> bool:
    """True if ``kw`` occurs in ``text`` (both lowercased).

    Single alphanumeric tokens require word boundaries (so ``rag`` never
    matches ``storage``); multi-word / punctuated tokens use a substring
    match — the same rule ``js/recommend.js`` applies.
    """
    if " " not in kw and re.fullmatch(r"[a-z0-9]+", kw):
        return re.search(r"\b" + re.escape(kw) + r"\b", text) is not None
    return kw in text


def match_use_cases(raw: Any, schema: dict | None = None) -> list[str]:
    """The canonical schema use-case categories a free-text string covers.

    Args:
        raw: The submission's free-text ``use_cases`` value.
        schema: ``schema.json`` — categories are returned in
            ``schema.use_cases`` order (minus ``Other``). Falls back to the
            keyword-map order when no schema is given.

    Returns:
        A (possibly empty) list of category names, e.g.
        ``"Coding, Security Research (DoS)" -> ["Agentic Coding",
        "Security Research"]``.
    """
    if is_placeholder(raw):
        return []
    text = str(raw).lower()
    categories = [c for c in (schema or {}).get("use_cases", []) if c != "Other"]
    if not categories:
        categories = list(USE_CASE_KEYWORDS)
    out = []
    for cat in categories:
        if any(_keyword_in(text, kw) for kw in USE_CASE_KEYWORDS.get(cat, ())):
            out.append(cat)
    return out


def commands_config_island(subs: list[dict], schema: dict) -> str:
    """Embed the trimmed submission set + schema pick-lists as a JSON island.

    The launch-command generator (``js/commands.js``) and the comparison
    view (``js/compare.js``) run entirely in the browser. Baking what they
    need — every submission's data (minus the verbose ``raw`` block) plus the
    schema's ``backends`` and ``tiers`` lists (for client-side normalization
    and VRAM labels) — into a ``<script type="application/json">`` island
    means these tools make **no network request**: the page works offline
    straight from disk and stays fast.

    The payload is compact (P2-7: halves the island size vs ``indent=2``)
    and brace-safe (no ``{{``/``}}`` for the template-leak check) via
    :func:`compact_json`.
    """
    config = {
        "backends": schema.get("backends", []),
        "tiers": schema.get("tiers", []),
        "submissions": [trim_for_client(s) for s in subs],
    }
    payload = compact_json(config)
    return (
        '  <script type="application/json" id="commands-config">\n'
        f"{payload}\n"
        "  </script>"
    )


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
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1].strip()
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
    if s.startswith("[") and s.endswith("]"):       # drop user's bracket styling
        s = s[1:-1].strip()
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


# ---------------------------------------------------------------------------
# P4-1 / P4-2: chart + advanced-filter data helpers
# ---------------------------------------------------------------------------

#: "27B", "35B-A3B" (MoE: total first), "125B" — case-insensitive.
_MODEL_SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*B(?:-A\s*\d+(?:\.\d+)?\s*B)?", re.I)
_GB_RE = re.compile(r"(\d+(?:\.\d+)?)\s*GB", re.I)


def parse_model_size(name: Any) -> float | None:
    """Total parameter count (billions) from a model name.

    Reads the *first* model in a comma-separated list and takes the total
    parameter count — for MoE names (``35B-A3B``) that is the first number,
    i.e. total weights, not the active subset. ``None`` when no size is
    stated (e.g. "Qwen3.8-Flash-Next" — the 125B is only in the notes).
    """
    if not name:
        return None
    first = str(name).split(",")[0].strip()
    m = _MODEL_SIZE_RE.search(first)
    return float(m.group(1)) if m else None


def estimate_vram_gb(s: dict, schema: dict) -> float | None:
    """Best-known VRAM footprint of a submission, in GB.

    Precedence: an explicit ``N GB`` in the submitter's notes (e.g. "fits
    12.7GB incl. KV"), then the hardware description ("16GB HBM2"), then the
    tier's range maximum (a documented fallback — the tier band's ceiling).
    ``None`` when none of the three yield a number.
    """
    m = _GB_RE.search(clean_value(s.get("notes")))
    if m:
        return float(m.group(1))
    m = _GB_RE.search(clean_value(hw(s).get("description")))
    if m:
        return float(m.group(1))
    for t in schema.get("tiers", []):
        if t.get("id") == s.get("tier") and t.get("range"):
            return float(t["range"][1])
    return None


def search_blob(s: dict) -> str:
    """Lowercase concatenation of every searchable field of a submission.

    Used for the P4-2 text search: the row carries this as ``data-search``
    so the client matches model name, hardware, backend, quant, use case,
    context, KV, performance, engine mode, notes, and submitter without
    DOM text crawling (notes are not a table column).
    """
    parts = [
        model_name(s),
        hw(s).get("description"),
        hw(s).get("vendor"),
        s.get("backend"),
        s.get("quant"),
        s.get("weight_precision"),
        s.get("use_cases"),
        s.get("engine_mode"),
        s.get("notes"),
        ctx(s).get("stable"),
        ctx(s).get("kv_cache"),
        perf(s).get("decode_tps"),
        perf(s).get("prefill_tps"),
        perf(s).get("power_w"),
        (s.get("source") or {}).get("username"),
    ]
    return " ".join(p for p in parts if p and not is_placeholder(p)).lower()


def row_sort_attrs(s: dict, schema: dict) -> str:
    """The numeric/date sort hints a Matrix row carries (P4-2).

    ``data-sort-vram`` = estimated VRAM in GB, ``data-sort-size`` = total
    parameter count (B), ``data-sort-speed`` = first decode t/s figure,
    ``data-sort-date`` = the submission's ISO date (lexicographically
    sortable). Empty attribute when a value is unknown — the client
    orders unknowns last.
    """
    vram = estimate_vram_gb(s, schema)
    size = parse_model_size(model_name(s))
    speed = parse_speed(perf(s).get("decode_tps"))
    date = str((s.get("source") or {}).get("submitted_at", ""))[:10]
    return (
        f'data-sort-vram="{vram:g}"' if vram is not None else 'data-sort-vram=""'
    ) + (
        f' data-sort-size="{size:g}"' if size is not None else ' data-sort-size=""'
    ) + (
        f' data-sort-speed="{speed:g}"' if speed is not None else ' data-sort-speed=""'
    ) + f' data-sort-date="{html_escape(date)}"'


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
