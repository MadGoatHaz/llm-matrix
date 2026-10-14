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


# Unfilled template values look like "[e.g., ...]", "[vLLM | llama.cpp | ...]",
# "[Prefill tok/s (if measured)]", "[Seconds for first token after cold load]"
# or "[Launch flags, rope/yarn config, ...]" — the whole value is wrapped in
# brackets AND the content reads as a fill-in instruction: an option list
# (pipes), an example marker, or a template phrase. Contributors who simply
# wrap real values in brackets (e.g. "[llama-cpp]", "[8192]") are NOT
# placeholders.
#
# Two precision rules keep genuine data safe (both validated against the
# whole dataset):
#
# * Instruction phrases are anchored where a real value can legitimately
#   contain the words mid-prose: a note's "verify quality for *your task*"
#   is not the template's "*Your* GPU model + VRAM"; "launch flags: --ctx
#   8192" is not the template's "Launch flags, *rope*/yarn config, ...".
# * A pipe only marks a template when it is a *bracketed* option list —
#   real notes use " | " as a separator for joined detail (a backend note
#   appended to the submitter's notes), so unbracketed pipes are ignored.
PLACEHOLDER_RE = re.compile(r"^\[.*\]$", re.DOTALL)
TEMPLATE_CONTENT_RE = re.compile(
    r"e\.g\.|^example|^full model|^your \w+|^model name|^what you|"
    r"^one sentence|name here|^insert|^fill in|if measured|"
    r"^seconds for first token|launch flags, rope|^pick:",
    re.IGNORECASE,
)
OPTION_LIST_RE = re.compile(r"\|")


def is_placeholder(value: Any) -> bool:
    """True if value is empty/None or an unfilled template placeholder.

    Bracket styling is irrelevant to the check: the template *content*
    (option lists, example markers, fill-in phrases) is what identifies an
    unfilled field, so values that parse.py has already unbracketed are
    caught just as reliably as raw bracketed ones. A pipe only counts as
    template content inside a bracketed value (an option list).
    """
    if value is None:
        return True
    s = str(value).strip()
    if not s:
        return True
    bracketed = s.startswith("[") and s.endswith("]")
    body = s[1:-1].strip() if bracketed else s
    if bracketed and OPTION_LIST_RE.search(body):
        return True
    return bool(TEMPLATE_CONTENT_RE.search(body))


# A submission key line whose value is a bracketed placeholder, e.g.
# "prefill_tps: [Prefill tok/s (if measured)]". The value must end the line —
# a literal newline, a <br>, or the end of the string (cooked HTML line
# breaks vary between <pre> blocks and <p> prose) — optionally followed by
# the template's "(optional)" / "(if measured)" decoration.
_SCRUB_VALUE_RE = re.compile(
    r"([A-Za-z_][A-Za-z0-9_]*):[ \t]*(\[[^\]]*\])(?:[ \t]*\((?:optional|if measured)\))?"
    r"(?=[ \t]*(?:<br\s*/?>|\n|\r|$))"
)

# A submission block's interior: the bracketed form
# ("[COMMUNITY-SUBMISSION] ... [/COMMUNITY-SUBMISSION]") or the bare-marker
# form (a marker line, ..., a closing marker line — user variants such as
# markers wrapped in <div class="math">). Only the interior is scrubbed, so
# prose elsewhere in a post (e.g. a diff block showing tier options) is
# never touched.
_SUBMISSION_SPAN_RE = re.compile(
    r"\[(?:COMMUNITY-SUBMISSION|QUICK-SUBMIT)\](.*?)\[(?:/(?:COMMUNITY-SUBMISSION|QUICK-SUBMIT))\]"
    r"|"
    r"^\s*(?:COMMUNITY-SUBMISSION|QUICK-SUBMIT)\s*$(.*?)^\s*/?(?:COMMUNITY-SUBMISSION|QUICK-SUBMIT)\s*$",
    re.DOTALL | re.MULTILINE,
)


def scrub_placeholders(text: str) -> str:
    """Blank unfilled template values inside submission blocks of forum text.

    Within a ``[COMMUNITY-SUBMISSION]`` / ``[QUICK-SUBMIT]`` block (bracketed
    or bare-marker form), a ``key: [instruction]`` line whose bracketed value
    is a placeholder becomes ``key:``; genuine bracketed values
    (``[llama-cpp]``, ``[8192]``) and everything outside a submission block
    are untouched. Applied to the raw thread mirrors (``pull.py``) so
    placeholder instructions never land in the data tree; ``parse.py``
    applies :func:`is_placeholder` field-by-field to the same values when
    building the dataset.
    """
    def _scrub_lines(block: str) -> str:
        def _sub(m: re.Match) -> str:
            return f"{m.group(1)}:" if is_placeholder(m.group(2)) else m.group(0)
        return _SCRUB_VALUE_RE.sub(_sub, block)

    def _scrub(m: re.Match) -> str:
        gi = 1 if m.group(1) is not None else 2
        head = text[m.start():m.start(gi)]
        tail = text[m.end(gi):m.end()]
        return head + _scrub_lines(m.group(gi)) + tail

    return _SUBMISSION_SPAN_RE.sub(_scrub, text)


def clean_value(value: Any) -> str:
    """Display string for a field: '' if placeholder, else the stripped
    value (a user's surrounding-bracket styling is removed)."""
    if is_placeholder(value):
        return ""
    s = str(value).strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1].strip()
    return s


# No-measurement sentinels. Contributors write "N/A (bench.sh planned)",
# "TBD", "unknown", "none", "-", "—" in fields they did not measure. Left
# alone, these survive into the dataset and render in the detail panel as
# if they were measurements — they are the absence of data, not data.
_SENTINEL_RE = re.compile(r"^(?:n/a|tbd|unknown|none|-|—)", re.IGNORECASE)
# A genuine figure with a sentinel appended ("45 N/A") — keep the figure.
_NUM_SENTINEL_RE = re.compile(
    r"^(\d+(?:\.\d+)?)\s*(?:n/a|tbd|unknown|none)\b", re.IGNORECASE)


def clean_sentinel(value: Any) -> str:
    """Blank a value that is a no-measurement sentinel.

    A value that STARTS with ``N/A`` / ``TBD`` / ``unknown`` / ``none`` /
    ``-`` / ``—`` (case-insensitive) is not a measurement — it becomes
    ``''``. A genuine figure with a sentinel appended (``"45 N/A"``) keeps
    the figure. Anything else passes through unchanged (stripped).
    """
    s = str(value if value is not None else "").strip()
    if not s:
        return ""
    m = _NUM_SENTINEL_RE.match(s)
    if m:
        return m.group(1)
    if _SENTINEL_RE.match(s):
        return ""
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
#: view, recommend engine, detail panel) actually need from a submission. The
#: verbose ``raw`` block and the ``tags`` curation metadata are dropped to keep
#: the baked JSON island small. ``source`` (the forum deep link) plus
#: ``confidence`` / ``lifecycle`` / ``highlight`` are kept: the recommend
#: engine weights its ranking by confidence + lifecycle, and the detail panel
#: shows a "Community highlight" badge for highlighted entries.
CLIENT_SUBMISSION_FIELDS = (
    "id", "tier", "hardware", "backend", "os_driver", "model", "quant",
    "weight_precision", "use_cases", "context", "performance",
    "engine_mode", "notes",
)


def trim_for_client(s: dict) -> dict:
    """A submission reduced to the fields the client tools consume.

    ``hardware`` / ``model`` / ``context`` / ``performance`` are kept whole
    (they are small structured objects); the flat scalar fields are copied
    verbatim. ``source`` is kept (post id + username + date) so the row
    detail panel can build the original forum deep link (``#post-N``). The
    curation metadata ``confidence`` / ``lifecycle`` / ``highlight`` is kept
    so the recommend engine can weight its ranking and the detail panel can
    show the highlight badge. Missing keys default to empty (``highlight``
    defaults to ``False``) so the JSON shape is stable.
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
    # Curation metadata (A2: recommend ranking; A5: detail-panel highlight
    # badge). ``confidence`` + ``lifecycle`` default to the common reported
    # state; ``highlight`` is a boolean flag (default off).
    out["confidence"] = s.get("confidence") or "community-reported"
    out["lifecycle"] = s.get("lifecycle") or "current"
    out["highlight"] = bool(s.get("highlight"))
    return out


# ---------------------------------------------------------------------------
# Use-case normalization (free text -> schema categories)
# ---------------------------------------------------------------------------

#: Keyword map for reducing a submission's free-text ``use_cases`` string to
#: the schema's canonical categories. THIS map is the single source of truth:
#: at build time the recommend page bakes it into its ``recommend-config``
#: island (``tools/site/pages/recommend.py``) and ``js/recommend.js`` reads it
#: from there — the client carries no hardcoded copy, so the matrix filter
#: attributes (``data-use-case``) and the recommend tooling can never drift
#: (tests/test_recommend.py enforces the sync).
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


def _clean_backend_text(raw: Any) -> tuple[str, str]:
    """Split a raw backend value into (core text, parenthetical detail).

    Drops the user's surrounding-bracket styling and separates a trailing
    parenthetical ("vLLM (custom framework)" -> ("vLLM", "custom
    framework")) so the core can be matched against the schema while the
    descriptive detail is preserved (``split_backend`` hands it to the
    caller, parse.py moves it into the submission's notes).
    """
    s = str(raw).strip()
    if s.startswith("[") and s.endswith("]"):       # drop user's bracket styling
        s = s[1:-1].strip()
    if "(" in s:
        core, _, tail = s.partition("(")
        core = core.strip()
        tail = tail.rstrip(")").strip()
    else:
        core, tail = s, ""
    core = re.sub(r"\s+\d[\w.]*$", "", core).strip()  # drop trailing version
    return core, tail


def _match_backend(s: str, schema: dict) -> tuple[str, str] | None:
    """Match a cleaned backend core against the schema's known backends.

    Returns ``(canonical_name, matched_text)`` using, in order:

    1. known aliases ("llamacpp" -> "llama.cpp");
    2. a case-insensitive exact match ("radiance" -> "Radiance");
    3. a case-insensitive substring match, longest backend name first
       (so "llama.cpp" is found inside "llama.cpp vulkan with no
       performance tuning", and a longer name always wins a tie).

    ``None`` when the text names no known backend.
    """
    if not s:
        return None
    alias = BACKEND_ALIASES.get(s.lower())
    if alias:
        return alias, s
    for sb in schema.get("backends", []):
        if sb.lower() == s.lower():
            return sb, s
    for sb in sorted(schema.get("backends", []), key=len, reverse=True):
        idx = s.lower().find(sb.lower())
        if idx != -1:
            return sb, s[idx:idx + len(sb)]
    return None


def normalize_backend(raw: Any, schema: dict) -> str:
    """Canonical backend name for filter attributes.

    'vLLM (magiccodingman/vllm-radiance, adaptive MTP=8)' -> 'vLLM'
    'Strata 0.1.42' -> 'Strata'
    'llamacpp' -> 'llama.cpp'
    'llama.cpp vulkan with no performance tuning' -> 'llama.cpp'
    """
    if not raw:
        return ""
    core, _detail = _clean_backend_text(raw)
    m = _match_backend(core, schema)
    return m[0] if m else core


def split_backend(raw: Any, schema: dict) -> tuple[str, str]:
    """``(canonical backend, leftover detail)`` for a raw backend value.

    The detail is the descriptive text a contributor tacked onto the
    backend name — what parse.py moves into the submission's notes:

    'llama.cpp vulkan with no performance tuning'
        -> ('llama.cpp', 'vulkan with no performance tuning')
    'ollama on a mac'         -> ('Ollama', 'on a mac')
    'vllm with tensor parallelism' -> ('vLLM', 'with tensor parallelism')
    'LM Studio'               -> ('LM Studio', '')
    'radiance 1.3.0'          -> ('Radiance', '')  (a version is not detail)
    'vLLM (custom framework, see below)'
        -> ('vLLM', 'custom framework, see below')
    'TotallyUnknownEngine 9.9' -> ('TotallyUnknownEngine', '') — no known
        backend matched, so the cleaned text is kept as-is and the detail
        is empty; the caller decides how to flag it (parse.py warns).
    """
    if not raw:
        return "", ""
    core, detail = _clean_backend_text(raw)
    m = _match_backend(core, schema)
    if m is None:
        return core, ""
    canonical, matched = m
    idx = core.lower().find(matched.lower())
    remainder = (core[:idx] + " " + core[idx + len(matched):]).strip()
    remainder = re.sub(r"\s+", " ", remainder).strip(" ,;:|-—")
    parts = [p for p in (remainder, detail) if p]
    return canonical, " ".join(parts)


def compute_stats(subs: list[dict], schema: dict) -> dict:
    """Headline counts: submissions, contributors, vendors, backends."""
    vendor_set = set()
    backend_set = set()
    for s in subs:
        v = hw(s).get("vendor", "")
        if v and not is_placeholder(v):
            # Exclude a bare "Mixed" that comes only from an empty-hardware
            # entry (a CPU-only rig) — it is not a real vendor signal. The
            # backend below is still counted (no `continue`).
            if v == "Mixed" and is_placeholder(hw(s).get("description")):
                pass
            else:
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


# ---------------------------------------------------------------------------
# Data tokens (C8): build-time values for authored content
# ---------------------------------------------------------------------------

#: GGUF file signatures — a quant name or a model-file name that identifies a
#: GGUF payload, whether the evidence sits in the ``quant`` field
#: ("GGUF Q4_K_M", "I-Nano", "UD-Q2_K_XL") or only in the model name
#: ("…-Q8_0.gguf", "…:q4_K_M", "…_q8_0"). The patterns are deliberately
#: narrow: the digit is glued to the ``q``/``iq``/``ud-q`` token and the
#: token must not follow a letter or digit, so a model name like
#: "Qwen3.8-27B" can never match (the digit there follows a "w"). A leading
#: look-behind (not ``\b``) is used because quant tags are often glued to a
#: word character by an underscore ("0528_q8_0").
_GGUF_TOKEN_RE = re.compile(
    r"(?i)(?<![a-z0-9])(gguf"
    r"|q[2-8]_k"
    r"|iq[2-8](?=[\s_./-]|$)"
    r"|i-nano"
    r"|ud-q[2-8]"
    r"|q[2-8]_0"
    r"|q[2-8](?=$|[\s:/.-]))"
)

#: A ``{{token}}`` marker in authored content (see :func:`fill_tokens`).
_TOKEN_RE = re.compile(r"\{\{(\w+)\}\}")


def is_gguf_submission(sub: dict) -> bool:
    """True when the submission's model file is a GGUF.

    Evidence is checked in the ``quant`` field first, then the model name —
    some entries state the format only there (e.g. ``gemma-4-31B-it-
    BF16.gguf``, Ollama-style tags like ``:q8_0``). Entries with no GGUF
    signature in either field (FP8, W4A16, or unstated) are NOT counted:
    the guide's "X of Y run GGUF" line must never overclaim.
    """
    text = " ".join((sub.get("quant", ""),
                     sub.get("model", {}).get("name", "")))
    return bool(_GGUF_TOKEN_RE.search(text))


def data_tokens(subs: list[dict], schema: dict,
               data: dict | None = None) -> dict[str, str]:
    """The build-time token values for authored content (C8).

    Guides (and the API docs page) carry ``{{token}}`` markers in their
    markdown source; the renderer fills them at build time so the numbers
    track the dataset instead of going stale. Values:

    * ``submission_count``  — real (non-template) submissions
    * ``backend_count``     — distinct normalized backends
    * ``vendor_count``      — distinct hardware vendors
    * ``contributor_count`` — distinct contributors
    * ``last_updated``      — the most recent ``source.submitted_at`` (date),
      falling back to the dataset's ``generated_at`` stamp
    * ``gguf_count``        — submissions whose model file is GGUF
    """
    stats = compute_stats(subs, schema)
    dates = [s.get("source", {}).get("submitted_at", "") for s in subs]
    dates = [d for d in dates if d]
    if not dates and data:
        dates = [data.get("generated_at", "")]
    last = max(dates) if dates else ""
    return {
        "submission_count": str(stats["submissions"]),
        "backend_count": str(stats["backends"]),
        "vendor_count": str(stats["vendors"]),
        "contributor_count": str(stats["contributors"]),
        "last_updated": last[:10] if last else "the latest pull",
        "gguf_count": str(sum(1 for s in subs if is_gguf_submission(s))),
    }


def has_tokens(text: str) -> bool:
    """True when ``text`` carries any ``{{token}}`` marker."""
    return bool(_TOKEN_RE.search(text))


def fill_tokens(text: str, tokens: dict[str, str]) -> str:
    """Replace every ``{{name}}`` in ``text`` with its value.

    A marker whose name is not in ``tokens`` raises :class:`ValueError`
    naming every unknown marker — a typo in authored content must fail the
    build loudly instead of leaking raw ``{{...}}`` into the published
    HTML. Text without markers is returned unchanged.
    """
    unknown = sorted({m.group(1) for m in _TOKEN_RE.finditer(text)}
                     - tokens.keys())
    if unknown:
        raise ValueError("unknown data token(s) in content: "
                         + ", ".join("{{" + k + "}}" for k in unknown))
    return _TOKEN_RE.sub(lambda m: str(tokens[m.group(1)]), text)


def group_by_tier(subs: list[dict], tiers: list[dict]) -> list[tuple[str, str, list[dict]]]:
    """Ordered [(tier_id, tier_label, [subs...])] for tiers that have rows.

    Submissions with no VRAM tier (e.g. a CPU-only rig) are NOT dropped: they
    collect into a trailing ``unclassified`` bucket so every real submission is
    represented on the tier-grouped matrix.
    """
    labels = {t["id"]: t["label"] for t in tiers}
    out = []
    for t in tiers:
        tier_subs = [s for s in subs if s.get("tier") == t["id"]]
        if tier_subs:
            out.append((t["id"], labels[t["id"]], tier_subs))
    unclassified = [s for s in subs if not s.get("tier")]
    if unclassified:
        out.append(("unclassified", "Unclassified (no VRAM tier)", unclassified))
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
#
# E2: the author/org name prefixes come from schema.json
# ("model_author_prefixes") — a new quant publisher is a schema edit, not
# a code change. Built at import time; ``None`` when the schema is missing
# or carries no prefixes (model_family() then keeps names un-stripped).
_SCHEMA_CACHE: dict | None = None


def _schema() -> dict:
    """Load tools/schema.json (cached for the module's lifetime)."""
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        try:
            _SCHEMA_CACHE = load_json(SCHEMA)
        except (OSError, ValueError):
            _SCHEMA_CACHE = {}
    return _SCHEMA_CACHE


_MODEL_AUTHOR_PREFIXES = _schema().get("model_author_prefixes", [])
FAMILY_AUTHOR_PREFIX = (
    re.compile(
        r"^(?:" + "|".join(re.escape(p) for p in _MODEL_AUTHOR_PREFIXES)
        + r")[-_]?", re.I)
    if _MODEL_AUTHOR_PREFIXES else None
)
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
    if FAMILY_AUTHOR_PREFIX is not None:
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
# Speed decomposition (prefill vs decode)
#
# Contributors report speed in several shapes. A *single* unlabeled figure is
# the decode speed (the Matrix "Speed" column and every speed ranking read
# decode, never the much faster prompt-processing figure). A string that
# carries BOTH a prefill and a decode figure must be split, or the prefill
# number corrupts the decode ranking:
#
#   "PP 120t/s, TG 2.5 t/s"            (llama.cpp convention)
#   "prefill: 120, decode: 2.5"        (label-first)
#   "120 t/s prefill, 2.5 t/s decode"  (label-trailing)
#   "54.4 tps decode / 215 tok/s prefill"
# ---------------------------------------------------------------------------

_NUM = r"(\d+(?:\.\d+)?)"
# Optional speed unit ("120t/s", "54.4 tps", "200t/s+", or bare "128") — the
# unit is not required, so "99-128 decode" (a range, no unit) still splits.
_SPEED_UNIT = r"\s*(?:(?:t(?:ok)?/s|tps|tokens?/(?:sec|second)s?)\+?)?"

#: Label-first figures.
_PP_RE = re.compile(r"\bpp\b\s*[:=]?\s*" + _NUM, re.IGNORECASE)
_TG_RE = re.compile(r"\btg\b\s*[:=]?\s*" + _NUM, re.IGNORECASE)
_PREFILL_RE = re.compile(r"\bprefill\b\s*[:=]?\s*" + _NUM, re.IGNORECASE)
_DECODE_RE = re.compile(r"\bdecode\b\s*[:=]?\s*" + _NUM, re.IGNORECASE)
#: Label-trailing figures ("120 t/s prefill", "54.4 tps decode", "200t/s+ decode").
_PREFILL_TAIL_RE = re.compile(_NUM + _SPEED_UNIT + r"\s+prefill\b", re.IGNORECASE)
_DECODE_TAIL_RE = re.compile(_NUM + _SPEED_UNIT + r"\s+decode\b", re.IGNORECASE)


def split_speed(raw: Any, existing_prefill: str = "") -> tuple[str, str]:
    """Split a raw speed value into ``(prefill, decode)`` strings.

    See the section comment for the shapes handled. Rules:

    * both a prefill and a decode figure present -> each fills its own field;
    * only one labeled figure present -> it fills its own field, the other
      keeps ``existing_prefill`` / stays empty (a lone "PP 120 t/s" is NOT a
      decode measurement);
    * no labels at all -> the whole string is the decode figure (the
      historic behavior) and ``existing_prefill`` is preserved;
    * empty / placeholder input -> both fields empty.
    """
    s = clean_value(raw)
    prefill0 = str(existing_prefill or "").strip()
    if not s:
        return prefill0, ""
    pp = _PP_RE.search(s)
    tg = _TG_RE.search(s)
    if pp and tg:
        return pp.group(1), tg.group(1)
    if pp:
        return pp.group(1), ""
    if tg:
        return prefill0, tg.group(1)
    pre = _PREFILL_RE.search(s) or _PREFILL_TAIL_RE.search(s)
    dec = _DECODE_RE.search(s) or _DECODE_TAIL_RE.search(s)
    if pre and dec:
        return pre.group(1), dec.group(1)
    if pre:
        return pre.group(1), ""
    if dec:
        return prefill0, dec.group(1)
    return prefill0, s


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
        s.get("os_driver"),
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
