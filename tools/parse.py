#!/usr/bin/env python3
"""
parse.py — Parse all submissions from the thread into canonical JSON.

Usage:
    python tools/parse.py

Reads:
    data/raw/latest.json    (the thread data)
    tools/schema.json       (valid fields/values)
    tools/tags.json         (manual curation overrides)

Writes:
    data/submissions.json   (the canonical dataset)

Prints:
    Summary + any parse warnings (unknown values, missing fields, etc.)

Data-quality handling:
    - Unfilled template/placeholder submissions are detected and skipped.
    - Unfilled template VALUES are blanked in every field (not just the
      four core ones) and scrubbed from the stored raw block, so
      instruction text ("Prefill tok/s (if measured)", ...) never reaches
      the dataset or the site.
    - Multi-model submissions separated by a `------` line are split and
      parsed as individual submissions.
    - Non-standard field names are aliased to canonical names.
    - Speed strings carrying both a prefill and a decode figure
      ("PP 120t/s, TG 2.5 t/s", "prefill: X, decode: Y",
      "X t/s prefill, Y t/s decode") are split into prefill_tps /
      decode_tps so the prompt-processing number never corrupts the
      decode ranking.
    - Tier normalization maps to the schema's DISJOINT bands (v2.3:
      t1 <16 <= t2 <24 <= t3 <32 <= t4 <48 <= t5 <96 <= t6).
      Most-specific patterns first (no substring false-positives like bare
      '16' matching inside '16-23'); multi-GPU figures are summed
      (4×24 = 96 -> t6); legacy range labels that straddle two bands are
      refined against the hardware description, and vendor inference
      collects ALL GPU vendors present (2+ -> "Mixed", none -> "").
    - List/bullet artifacts in values are cleaned.
    - No-measurement sentinels ("N/A (bench.sh planned)", "TBD", "unknown",
      "none", "-", "—") are blanked in every field (B8), so the absence of
      a measurement never survives into the dataset and renders in the
      detail panel as if it were one. A genuine figure with a sentinel
      appended ("45 N/A") keeps the figure.
    - os_driver is extracted from the block and emitted on the entry
      (schema canonical field; displayed in the detail panel).
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
DATA_DIR = WORKSPACE / "data"
RAW_LATEST = DATA_DIR / "raw" / "latest.json"
SCHEMA = WORKSPACE / "tools" / "schema.json"
TAGS = WORKSPACE / "tools" / "tags.json"
OUTPUT = DATA_DIR / "submissions.json"
CANDIDATES = DATA_DIR / "candidates.json"

# Reuse the site generator's helpers (the single source of truth, shared
# with validate.py and the site pages): the backend normalizer (free-text
# detail like "vulkan with no performance tuning" is moved into the
# submission's notes), the placeholder detector (an unfilled template value
# is blanked in EVERY field, not just the core four), and the speed
# decomposer (a "PP 120t/s, TG 2.5 t/s" string splits into prefill + decode
# so the prompt-processing figure never corrupts the decode ranking).
_REPO_ROOT = str(WORKSPACE)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from tools.site.utils import (  # noqa: E402
    OPTION_LIST_RE,
    TEMPLATE_CONTENT_RE,
    clean_sentinel,
    is_placeholder,
    scrub_placeholders,
    split_backend,
    split_speed,
)

# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------

def load_json(path):
    with open(path) as f:
        return json.load(f)

# E2: the GPU / model / vendor token lists live in tools/schema.json (the
# single source of truth) — adding a new GPU or model is a schema edit, not
# a code change. The module-level constants below are BUILT from the schema
# at import time.
_SCHEMA_CACHE = None

def _schema():
    """Load tools/schema.json (cached for the module's lifetime).

    A missing/corrupt schema degrades to an empty view at IMPORT time so
    importing this module never breaks (tests load it as a file); main()
    loads the schema itself and fails loudly if it is genuinely broken.
    """
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        try:
            _SCHEMA_CACHE = load_json(SCHEMA)
        except (OSError, ValueError):
            _SCHEMA_CACHE = {}
    return _SCHEMA_CACHE

def strip_html(cooked):
    """Remove HTML tags, decode entities, normalize whitespace."""
    text = re.sub(r'<br\s*/?>', '\n', cooked)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

# ---------------------------------------------------------------------------
# Submission block parsing
# ---------------------------------------------------------------------------

def _clean_item(line):
    """Strip leading bullet markers (* / -) and trailing list commas."""
    item = re.sub(r'^[\*\-]\s*', '', line.strip())
    item = item.rstrip(',').strip()
    return item

def _join_list(items):
    return ', '.join(i for i in items if i)

def parse_submission_block(block_text):
    """Parse a [COMMUNITY-SUBMISSION] or [QUICK-SUBMIT] block into a dict.

    Handles:
      - "key: value" lines (key is a single identifier word + colon)
      - multi-line values (continuation lines are folded into the value)
      - bullet lists (`* item` / `- item`) joined with ", "
      - bracketed lists that open on the key line, on a following line, or
        inline (`[a, b, c]` is kept verbatim)
    """
    data = {}
    lines = block_text.split('\n')
    current_key = None
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        # Inside an open bracketed list: every line is list content, never a
        # new key (prevents e.g. "https://..." from being misread as a key
        # and breaking the list). Checked before key matching.
        if current_key is not None and isinstance(data.get(current_key), list):
            if line == ']':
                data[current_key] = _join_list(data[current_key])
                current_key = None
            elif line.endswith(']') and len(line) > 1:
                # Closing bracket attached to the last content line (e.g. a
                # multi-line value whose final line is "... 8888]"). Capture
                # the content, then close the list so a following "key:" line
                # is not absorbed as list content.
                item = _clean_item(line[:-1].rstrip())
                if item:
                    data[current_key].append(item)
                data[current_key] = _join_list(data[current_key])
                current_key = None
            elif line not in ('[', ','):
                item = _clean_item(line)
                if item:
                    data[current_key].append(item)
            continue

        # New key line: a single identifier word immediately followed by a
        # colon. Requiring the first char to be a letter/underscore and the
        # colon to follow directly prevents continuation prose that contains
        # a colon (e.g. "Slow prefill: 41s TTFT") from being misread as a key.
        match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$', line)
        if match:
            current_key = match.group(1).lower()
            value = match.group(2).strip()
            if value.startswith('[') and ']' not in value:
                # Open bracketed list: initial content (if any) is first item.
                first = value[1:].strip()
                data[current_key] = [first] if first else []
            elif value.startswith('[') and ']' in value:
                # Complete inline list — keep verbatim (preserves template
                # markers for downstream detection).
                data[current_key] = value
            elif value:
                data[current_key] = value
            else:
                data[current_key] = ""
            continue

        if current_key is None:
            continue

        val = data.get(current_key)

        if val == "":
            # Value was empty; this line begins it.
            if line == '[':
                data[current_key] = []
            elif line == ']':
                data[current_key] = ""
            elif line.startswith('[') and ']' in line:
                data[current_key] = line  # complete inline list, verbatim
            else:
                item = _clean_item(line)
                data[current_key] = [item] if item else ""
        else:
            # Non-empty string value: fold continuation lines in with a space.
            cont = _clean_item(line)
            if cont:
                data[current_key] = (val + ' ' + cont).strip()

    # Close any lists that were left open at end of block.
    for key, val in data.items():
        if isinstance(val, list):
            data[key] = _join_list(val)

    return data

# ---------------------------------------------------------------------------
# Field aliasing (non-standard key names -> canonical names)
# ---------------------------------------------------------------------------

FIELD_ALIASES = {
    'power': 'power_draw',
    'cold_load_ttft': 'ttft_cold',
    'context_length': 'stable_context_tested',
    'tps': 'throughput_tps',
    # Friendly template names (the forum promo template and the thread's
    # Quick Submit use these). MUST mirror schema.json "fields.aliases" —
    # tests/test_schema.py enforces the sync.
    'gpu': 'hardware',
    'vram': 'tier',
    'model': 'model_name',
    'quant': 'quant_package',
    'use_case': 'primary_use_case',
    'notes': 'setup_notes',
    'verdict': 'setup_notes',
    'speed': 'throughput_tps',
    'tok_s': 'throughput_tps',
    'tokens_per_second': 'throughput_tps',
}

def apply_aliases(data):
    """Rename non-standard field names to their canonical equivalents."""
    for alias, canonical in FIELD_ALIASES.items():
        if alias in data and canonical not in data:
            data[canonical] = data.pop(alias)
        elif alias in data:
            del data[alias]
    return data

def _unbracket(v):
    """Strip a user's surrounding-bracket styling from a canonical value.

    Some contributors wrap genuine values in brackets (``[llama-cpp]``,
    ``[8192]``). The canonical fields are normalized display values, so the
    decoration comes off; the verbatim text is preserved in ``raw``.
    """
    s = str(v if v is not None else "").strip()
    if len(s) >= 2 and s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if inner:
            return inner
    return s

# ---------------------------------------------------------------------------
# Multi-model block splitting
# ---------------------------------------------------------------------------

# A separator line of 4+ dashes on its own line (e.g. PawingUnplug's posts).
SEPARATOR_RE = re.compile(r'^[ \t]*-{4,}[ \t]*$', re.MULTILINE)

def split_on_separator(block):
    """Split a submission block on `------` separator lines.

    Returns a list of sub-blocks (length 1 when no separator is present).
    """
    if not SEPARATOR_RE.search(block):
        return [block]
    return [p.strip() for p in SEPARATOR_RE.split(block) if p.strip()]

# Canonical field names (incl. aliases) recognized for inline-field recovery.
# Only unambiguous, technical tokens are listed: common English words
# (``model``, ``quant``, ``notes``, ``speed``, ``verdict``) are deliberately
# excluded so prose containing " notes:" / " speed:" in a value never gets
# mis-split into a new key line. The multi-line forum template needs no
# inline recovery — its keys are parsed by the key regex directly.
KNOWN_FIELDS = (
    'tier', 'hardware', 'backend', 'os_driver', 'model_name', 'quant_package',
    'weight_precision', 'download_url', 'primary_use_case', 'stable_context_tested',
    'context_length', 'kv_cache_setting', 'engine_mode', 'throughput_tps', 'tps',
    'prefill_tps', 'ttft_cold', 'cold_load_ttft', 'power', 'power_draw', 'setup_notes',
    'gpu', 'vram', 'use_case', 'tok_s', 'tokens_per_second',
)
_INLINE_FIELD_RE = re.compile(r'\s+(?=(?:' + '|'.join(KNOWN_FIELDS) + r'):\s)')

def split_inline_fields(block):
    """Recover submissions written on a single line.

    Some contributors write every field on one line, comma-separated
    (``model_name: a, quant_package: b, download_url: c, ...``). Insert a
    newline before each known field name followed by a colon so the block
    parser sees proper key/value lines. Field names inside values (e.g. a
    model name containing "thinking:") are untouched — only the canonical
    field set triggers a split.
    """
    return _INLINE_FIELD_RE.sub('\n', block)

# Marker patterns. Bracketed form is the standard template; bare form covers
# user variants (e.g. markers wrapped in <div class="math">) where the marker
# sits alone on a line without brackets.
SUBMISSION_PATTERNS = (
    (r'\[COMMUNITY-SUBMISSION\](.*?)\[\/COMMUNITY-SUBMISSION\]', 'full'),
    (r'(?m)^\s*COMMUNITY-SUBMISSION\s*$(.*?)^\s*/?COMMUNITY-SUBMISSION\s*$', 'full'),
    (r'\[QUICK-SUBMIT\](.*?)\[\/QUICK-SUBMIT\]', 'quick'),
    (r'(?m)^\s*QUICK-SUBMIT\s*$(.*?)^\s*/?QUICK-SUBMIT\s*$', 'quick'),
)

def extract_submissions_from_post(post):
    """Extract all submission blocks from a post's cooked HTML.

    Returns a list of dicts, each with:
      - ``type``: "full" / "quick" (marker blocks) or "full" (unmarked)
      - ``data``: the parsed + alias-mapped key/value dict
      - ``prose``: cleaned prose around the block (P1-2 attribution)
      - ``marked``: True for [COMMUNITY-SUBMISSION]/[QUICK-SUBMIT] blocks,
        False for unmarked-structure blocks (P1-1 transparency flag)

    Pass 1 is marker-based (with positional spans so the prose before /
    between / after each block can be attributed). Pass 2 (P1-1) fires only
    when a post has NO markers, recovering unmarked structured posts.
    """
    text = strip_html(post.get("cooked", ""))
    submissions = []

    # Pass 1: marker-based extraction, tracking each span's position.
    spans = []
    for pattern, sub_type in SUBMISSION_PATTERNS:
        for match in re.finditer(pattern, text, re.DOTALL):
            block = match.group(1).strip()
            if not block:
                continue
            spans.append((match.start(), match.end(), sub_type, block))
    spans.sort(key=lambda s: s[0])

    for idx, (start, end, sub_type, block) in enumerate(spans):
        # P1-2: prose around the span. "Before" prose (only the first span)
        # attaches to the span's first sub-block; "after" prose (up to the
        # next span, or end of post) attaches to its last sub-block.
        before = text[:start] if idx == 0 and start > 0 else ""
        next_start = spans[idx + 1][0] if idx + 1 < len(spans) else len(text)
        after = text[end:next_start] if next_start > end else ""
        sub_blocks = split_on_separator(block)
        for j, sub_block in enumerate(sub_blocks):
            prose = ""
            if j == 0:
                prose = clean_prose(before)
            if j == len(sub_blocks) - 1:
                tail = clean_prose(after)
                prose = f"{prose} {tail}".strip()
            submissions.append({
                "type": sub_type,
                "data": apply_aliases(parse_submission_block(split_inline_fields(sub_block))),
                "prose": prose,
                "marked": True,
            })

    # Pass 2 (P1-1): unmarked structured posts. Only when no markers exist,
    # so a post is never double-counted. Deterministic structure detection.
    if not spans:
        detected = detect_unmarked_structure(text)
        if detected is not None:
            start_line, end_line, block_text = detected
            lines = text.split("\n")
            after = clean_prose("\n".join(lines[end_line + 1:]))
            submissions.append({
                "type": "full",
                "data": apply_aliases(parse_submission_block(split_inline_fields(block_text))),
                "prose": after,
                "marked": False,
            })

    return submissions

# ---------------------------------------------------------------------------
# P1-1: unmarked structure detection (Layer 2)
# ---------------------------------------------------------------------------

# A bare "key:" line (brackets optional) after HTML decoding.
KEY_LINE_RE = re.compile(r"^\[?[a-z_]+\]?:\s")
# Max continuation lines allowed between two key lines in one structure.
MAX_KEY_GAP = 6

#: Canonical field names (post alias-mapping). Used to decide how "real" an
#: unmarked key/value run is and to spot unmapped keys (P1-4).
CANONICAL_FIELDS = {
    "tier", "hardware", "backend", "os_driver", "model_name", "quant_package",
    "weight_precision", "download_url", "primary_use_case", "stable_context_tested",
    "kv_cache_setting", "engine_mode", "throughput_tps", "prefill_tps",
    "ttft_cold", "power_draw", "setup_notes",
}


def clean_prose(t):
    """Collapse whitespace in already-HTML-stripped prose (P1-2 / P1-5)."""
    return re.sub(r"\s+", " ", t or "").strip()


def detect_unmarked_structure(text):
    """Detect an unmarked structured submission (P1-1, Layer 2).

    Signal: a cluster of >=3 key lines (``key: value``, brackets optional)
    with bounded gaps (so a multi-line value like ``setup_notes:`` doesn't
    break the run), where >=2 of the keys map to canonical field names.

    Returns ``(start_line, end_line, block_text)`` for the strongest
    qualifying cluster, or ``None``. Deterministic (structure-based), no NLP.
    """
    lines = text.split("\n")
    key_idx = [i for i, l in enumerate(lines) if KEY_LINE_RE.match(l.strip())]
    if len(key_idx) < 3:
        return None
    # Cluster key lines separated by at most MAX_KEY_GAP continuation lines.
    clusters = []
    cur = [key_idx[0]]
    for k in key_idx[1:]:
        if k - cur[-1] <= MAX_KEY_GAP:
            cur.append(k)
        else:
            clusters.append(cur)
            cur = [k]
    clusters.append(cur)
    best = None
    for cluster in clusters:
        if len(cluster) < 3:
            continue
        start, end = cluster[0], cluster[-1]
        block_text = "\n".join(lines[start:end + 1])
        data = apply_aliases(parse_submission_block(split_inline_fields(block_text)))
        mapped = sum(1 for k, v in data.items()
                     if k in CANONICAL_FIELDS and str(v).strip())
        if mapped >= 2:
            if best is None or len(cluster) > len(best[2]):
                best = (start, end, block_text)
    return best

# ---------------------------------------------------------------------------
# P1-3: cross-block inheritance
# ---------------------------------------------------------------------------

# Quant-format signatures, most-specific first, for comparing a model name's
# implied quant against a primary block's stated quant.
_QUANT_SIG_PATTERNS = (
    "q8_k_xl", "q6_k_xl", "q4_k_xl", "q2_k_xl",
    "q8_0", "q4_0", "q5_0",
    "q5_k_m", "q4_k_m", "q3_k_m",
    "iq4_xs", "iq3_s", "iq2_s",
    "nvfp4", "mxfp4", "fp8", "bf16", "fp16",
    "q4", "q5", "q6", "q8",
)


def _quant_sig(s):
    """A comparable quant-format signature from a model name or quant string.

    ``None`` when no known quant token is present (so a block whose model
    name names no quant never inherits a possibly-wrong primary quant).
    """
    t = (s or "").lower().replace("-", "_")
    for pat in _QUANT_SIG_PATTERNS:
        if pat in t:
            return pat
    return None


def apply_cross_block_inheritance(entries):
    """P1-3: inherit hardware/backend/quant from the primary block.

    The primary block is the first one with the most fields filled. A
    subsequent block that is genuinely empty for ``hardware`` / ``backend``
    inherits the primary's value. ``quant_package`` is inherited ONLY when the
    block's model name carries the SAME quant signature as the primary (a
    differing or absent quant is left empty rather than guessed — the quality
    bar forbids force-fitting). Each inherited field is provenance-flagged.

    ``model`` / ``use_case`` / ``speed`` / ``notes`` are never inherited
    (they are per-block).
    """
    if len(entries) < 2:
        return entries

    def _field_count(e):
        n = 0
        if (e.get("hardware") or {}).get("description"):
            n += 1
        if e.get("backend"):
            n += 1
        if (e.get("model") or {}).get("name"):
            n += 1
        if e.get("quant"):
            n += 1
        if e.get("tier"):
            n += 1
        if (e.get("context") or {}).get("stable"):
            n += 1
        if e.get("use_cases"):
            n += 1
        return n

    primary_idx = max(range(len(entries)), key=lambda i: _field_count(entries[i]))
    primary = entries[primary_idx]
    p_hw = (primary.get("hardware") or {}).get("description", "")
    p_vendor = (primary.get("hardware") or {}).get("vendor")
    p_be = primary.get("backend", "")
    p_q = primary.get("quant", "")
    p_qs = _quant_sig(p_q)

    for i, e in enumerate(entries):
        if i == primary_idx:
            continue
        inh = {}
        hw = e.get("hardware") or {}
        if not hw.get("description") and p_hw:
            hw["description"] = p_hw
            hw["vendor"] = p_vendor
            e["hardware"] = hw
            inh["hardware"] = f"block_{primary_idx}"
        if not e.get("backend") and p_be:
            e["backend"] = p_be
            inh["backend"] = f"block_{primary_idx}"
        if not e.get("quant") and p_q:
            e_qs = _quant_sig((e.get("model") or {}).get("name", ""))
            if e_qs == p_qs:
                e["quant"] = p_q
                inh["quant"] = f"block_{primary_idx}"
        if inh:
            e["inherited_from"] = inh
    return entries

# ---------------------------------------------------------------------------
# P1-5: prose-only candidates (Layer 3, conservative / human-in-the-loop)
# ---------------------------------------------------------------------------

# A first-person statement about the submitter's OWN setup (not a question).
FIRST_PERSON_SETUP_RE = re.compile(
    r"\bI (?:run|use|'m using|am using|have|switched|switch|'ve run|don't|do|came|shot)\b"
    r"|\bmy (?:system|systems|rig|use|setup|GPU|hardware|evals|workload)\b",
    re.IGNORECASE,
)
# E2: the known-GPU list from schema.json. "R9700" / "RTX 4090" style names
# carry the vendor prefix in their canonical form, but the community writes
# them as bare numbers ("I run a 9700"), so each name also yields a bare
# search token: drop a leading "rtx " (decorative) and a single leading "r"
# when what remains is all digits ("R9700" -> "9700"). Everything else
# ("mi210", "a100", "v620", "4090", ...) is its own token.
KNOWN_GPUS = _schema().get("known_gpus", [])

def _gpu_token(name):
    """The searchable (lowercase) token for a known GPU name."""
    tok = name.lower()
    tok = re.sub(r"^rtx\s+", "", tok)
    tok = re.sub(r"^r(?=\d+$)", "", tok)
    return tok

def _hardware_signal_pattern():
    """The hardware/model-signal regex, built from schema.json (E2).

    Canonical GPU names first, then any bare search tokens they yield that
    are not already present (case-insensitively), then the VRAM-amount
    shapes, the schema's model families, and the backend names.
    """
    gpu_alts = list(KNOWN_GPUS)
    for name in KNOWN_GPUS:
        tok = _gpu_token(name)
        if not any(a.lower() == tok for a in gpu_alts):
            gpu_alts.append(tok)
    families = [re.escape(f) for f in _schema().get("known_model_families", [])]
    backends = [
        r"LiteLLM", r"llama\.cpp", r"vLLM", r"Ollama", r"Strata",
        r"Radiance", r"Colibri", r"MLX", r"Unsloth",
    ]
    parts = [
        "|".join(gpu_alts),
        r"\d+\s?GB", r"\d+\s?gig",
        "|".join(families),
        "|".join(backends),
    ]
    return "|".join(p for p in parts if p)

# An explicit hardware / model / VRAM / backend signal.
HARDWARE_SIGNAL_RE = re.compile(_hardware_signal_pattern(), re.IGNORECASE)
# A first line opening with a question word marks a question, not a submission.
_QUESTION_FIRST_RE = re.compile(
    r"^(How|What|Why|When|Where|Who|Which|Do|Does|Did|Have|Has|Had|"
    r"Can|Could|Would|Will|Is|Are|Was|Were)\b",
    re.IGNORECASE,
)

# Search token -> canonical name (the candidate queue's GPU field).
_GPU_TOKENS = {_gpu_token(n): n for n in KNOWN_GPUS}
_BACKEND_TOKENS = (
    "LiteLLM", "llama.cpp", "llama-cpp", "vLLM", "Ollama",
    "Strata", "Radiance", "Colibri", "MLX", "Unsloth",
)
# Named-model tokens (schema.json "known_models"): full model names the
# community writes in prose, for the candidate queue's models field.
_MODEL_TOKENS = tuple(_schema().get("known_models", ()))


def extract_candidate(post):
    """P1-5 (Layer 3, conservative): a prose-only post that reads as a
    first-person setup description carrying a hardware/model signal becomes a
    *review candidate* — NOT a submission.

    Candidates are the human-in-the-loop queue: the raw prose is always
    preserved so the curator can read it, and only high-confidence fields
    (explicit GPU model, VRAM amount, backend, named model) are extracted.
    The site owner's posts (admin/changelog) and question-first posts are
    excluded. Returns ``None`` when the post is not a candidate.
    """
    text = strip_html(post.get("cooked", ""))
    if not text.strip():
        return None
    user = post.get("username", "unknown")
    if user.strip().lower() == "madgoat":
        return None
    # Normalize curly apostrophes/quotes so the signals match reliably.
    norm = (text.replace("\u2019", "'").replace("\u2018", "'")
                .replace("\u201c", '"').replace("\u201d", '"'))
    first_line = next((l.strip() for l in norm.split("\n") if l.strip()), "")
    if _QUESTION_FIRST_RE.match(first_line):
        return None
    if not FIRST_PERSON_SETUP_RE.search(norm):
        return None
    if not HARDWARE_SIGNAL_RE.search(norm):
        return None

    low = norm.lower()
    fields = {}
    gpus = []
    for tok, name in _GPU_TOKENS.items():
        if tok in low and name not in gpus:
            gpus.append(name)
    if "quad" in low:
        gpus.insert(0, "quad (4x)")
    if gpus:
        fields["gpu"] = ", ".join(gpus)
    vrams = sorted({m for m in re.findall(r"(\d+)\s?(?:GB|gig)", norm, re.IGNORECASE)},
                   key=int)
    if vrams:
        fields["vram_gb"] = ", ".join(vrams)
    backends = []
    for b in _BACKEND_TOKENS:
        if b.lower() not in low:
            continue
        # A backend named only in a negative / hypothetical context (e.g.
        # "I haven't tried Strata") is NOT high-confidence — skip it so the
        # candidate queue stays honest (the raw text still shows the context).
        ctx = low[max(0, low.find(b.lower()) - 14):low.find(b.lower())]
        if re.search(r"haven'?t|have not|never|don'?t|didn'?t|not tried|not use|not run", ctx):
            continue
        backends.append(b)
    if backends:
        fields["backend"] = ", ".join(backends)
    models = []
    for m in _MODEL_TOKENS:
        if m.lower() in low and m not in models:
            models.append(m)
    if models:
        fields["models"] = ", ".join(models)

    return {
        "id": f"candidate_post_{post.get('post_number', 0)}_{user.lower()}",
        "confidence": "unverified",
        "source_post": post.get("post_number", 0),
        "source_user": user,
        "raw_text": clean_prose(norm),
        "fields": fields,
    }

# ---------------------------------------------------------------------------
# Template / placeholder detection
# ---------------------------------------------------------------------------

# Placeholder markers per core field. Each tuple is checked as a substring;
# a leading-bracket check on the raw value catches any unfilled `[...]` field.
TEMPLATE_MARKERS = {
    'model_name': ('[Full model',),
    'hardware': ('[e.g.,',),
    'backend': ('[vLLM |',),
    'tier': ('[e.g., 24GB',),
}
CORE_FIELDS = ('tier', 'hardware', 'backend', 'model_name')

# Template *content* detection lives in tools/site/utils.py (the single
# source of truth, shared with the site generator and validate.py): an
# option list (pipe, inside brackets), an example marker, or a fill-in
# instruction phrase. Covers both the Full Submit template ("[e.g., ...]",
# "[vLLM | llama.cpp | ...]", "[Full model ...]") and the Quick Submit
# template's bracketed instructions ("[Your GPU model + VRAM]",
# "[Model name + quant]", "[What you use it for]", "[One sentence: ...]"),
# plus the per-field placeholders contributors leave in otherwise genuine
# submissions ("[Prefill tok/s (if measured)]", "[Seconds for first token
# after cold load]", "[Launch flags, rope/yarn config, ...]"). Genuine
# values that users simply wrap in brackets (e.g. ``[llama-cpp]``,
# ``[8192]``, ``[DeepSeek-R1:671b-0528_q8_0]``) match none of these.

def _looks_like_placeholder(v):
    """A bracketed value is an unfilled template placeholder when it is an
    option list (contains a pipe) or a fill-in instruction phrase. Genuine
    values that users simply wrapped in brackets (e.g. ``[llama-cpp]``,
    ``[DeepSeek-R1:671b-0528_q8_0]``) do NOT look like placeholders.
    """
    inner = v.strip()
    if not inner.startswith('['):
        return False
    body = inner.strip('[]').strip()
    return bool(OPTION_LIST_RE.search(body)) or bool(TEMPLATE_CONTENT_RE.search(body))

def is_field_placeholder(v):
    """Placeholder check for a raw field value: both the bracketed form
    (a bracketed option list like "[Windows 11 | Linux | macOS]") and the
    unbracketed form (a bare instruction string) are considered."""
    return is_placeholder(v) or is_placeholder(_unbracket(v))

def clean_field(v):
    """Unbracket a value and blank it when it is an unfilled template
    placeholder OR a no-measurement sentinel. Applied to EVERY field (not
    just the core four) so an instruction like "Prefill tok/s (if measured)"
    and a sentinel like "N/A (bench.sh planned)" never survive into the
    dataset; genuine values — including ones users wrapped in brackets —
    keep their content.
    """
    s = _unbracket(v)
    if is_field_placeholder(v):
        return ""
    return clean_sentinel(s)

def is_template_submission(data_dict):
    """Return True if the submission is clearly an unfilled template."""
    for field, markers in TEMPLATE_MARKERS.items():
        v = str(data_dict.get(field, '') or '')
        if any(m in v for m in markers) or _looks_like_placeholder(v):
            return True
    # All core fields empty -> nothing was actually filled in.
    if not any(str(data_dict.get(f, '') or '').strip() for f in CORE_FIELDS):
        return True
    return False

# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Vendor inference (B5: multi-vendor aware)
# ---------------------------------------------------------------------------

# GPU vendor signals (E2: schema.json "vendor_keywords"). CPU names
# (Xeon, Ryzen, Threadripper, EPYC) are deliberately ABSENT — a CPU is not
# a GPU vendor, so "RTX 5090 + IceLake Xeon" stays NVIDIA, not Mixed.
def _vendor_substrings():
    vk = _schema().get("vendor_keywords", {})
    out = {}
    for vendor, toks in vk.items():
        if vendor == "Apple":
            # M-series chip tokens (m1..m4) are NOT plain substrings — they
            # match via _APPLE_CHIP_RE with word boundaries (see below).
            out[vendor] = tuple(t for t in toks
                                if not re.fullmatch(r"m[1-4]", t))
        else:
            out[vendor] = tuple(toks)
    return out

_VENDOR_SUBSTRINGS = _vendor_substrings()
# Apple M-series chips need word boundaries: the substring "m2" appears
# inside RAM-module names ("CMK64GX4M2D3") and would otherwise flip a
# single-NVIDIA rig to Mixed. Schema tokens shaped "m<digit>" get the
# word-boundary treatment.
_M_CHIP_TOKENS = [t for t in _schema().get("vendor_keywords", {})
                  .get("Apple", ()) if re.fullmatch(r"m[1-4]", t)]
_APPLE_CHIP_RE = (re.compile(r"\b(?:" + "|".join(_M_CHIP_TOKENS) + r")\b")
                  if _M_CHIP_TOKENS else None)


def infer_vendor(hardware_str):
    """Infer the GPU vendor(s) from a hardware description.

    Collects EVERY vendor signal present (not just the first): exactly one
    -> that vendor; two or more -> "Mixed" (a "4090 + R9700" rig is neither
    "NVIDIA" nor "AMD"); none -> "" (unknown, e.g. a CPU-only rig). CPU
    names (Xeon, Ryzen, Threadripper, EPYC) never count as GPU signals.
    """
    s = (hardware_str or '').lower()
    found = {vendor for vendor, signals in _VENDOR_SUBSTRINGS.items()
             if any(sig in s for sig in signals)}
    if _APPLE_CHIP_RE is not None and _APPLE_CHIP_RE.search(s):
        found.add("Apple")
    if len(found) == 1:
        return found.pop()
    if len(found) > 1:
        return "Mixed"
    return ""

# ---------------------------------------------------------------------------
# Tier normalization (A3: disjoint bands)
# ---------------------------------------------------------------------------

# The schema's tiers are disjoint bands (v2.3):
#   t1 < 16 <= t2 < 24 <= t3 < 32 <= t4 < 48 <= t5 < 96 <= t6
def _tier_for_vram(vram_gb):
    """The tier band a single VRAM amount (GB) falls into."""
    if vram_gb < 16:
        return "t1"
    if vram_gb < 24:
        return "t2"
    if vram_gb < 32:
        return "t3"
    if vram_gb < 48:
        return "t4"
    if vram_gb < 96:
        return "t5"
    return "t6"


# Multi-GPU figures: "N x [MODEL] G GB" (count before the per-card capacity:
# "4x24GB", "2 x 16 GB", "2 x R9700 32GB") and "G GB x N" (count after it:
# "Intel Arc B60 24GB x4"). The per-card capacity is the number glued to GB.
# The count is 1-2 digits and the capacity 1-3 digits, and neither may be
# preceded by another digit: model names like "Ryzen 9 5900X" (a trailing
# "x") must not be read as "5900 x 128GB" — that would multiply a CPU name
# by the system RAM and send a 24GB rig to t6.
_MULTI_GB_RE = re.compile(
    r'(?<!\d)(\d{1,2})\s*[x×]\s*(?:[A-Za-z0-9\.\-/]+\s+)?'
    r'(\d{1,3}(?:\.\d+)?)\s*GB',
    re.IGNORECASE)
_REV_MULTI_GB_RE = re.compile(
    r'(?<!\d)(\d{1,3}(?:\.\d+)?)\s*GB\s*[x×]\s*(\d{1,2})\b',
    re.IGNORECASE)
_SINGLE_GB_RE = re.compile(r'(?<!\d)(\d{1,3}(?:\.\d+)?)\s*GB', re.IGNORECASE)


def _hardware_vram_total(hardware_str):
    """Total VRAM (GB) implied by a hardware description, or ``None``.

    Multi-GPU first (the count applies to the per-card capacity:
    "2 x R9700 32GB" -> 64, "Intel Arc B60 24GB x4" -> 96), then a single
    explicit "N GB" figure ("Radeon VII 16GB HBM2" -> 16).

    A multi-GPU match is trusted only when its capacity is the FIRST "N GB"
    figure in the string: GPUs are stated before CPUs/RAM in this dataset,
    and "N x N GB" shapes occur in RAM context too ("128GB DDR4 ...
    4x32GB double-rank" — that is four RAM modules, not four GPUs).
    No number -> None (the caller then keeps the conservative default).
    """
    s = hardware_str or ''
    first_gb = _SINGLE_GB_RE.search(s)
    for rx, cap_group in ((_MULTI_GB_RE, 2), (_REV_MULTI_GB_RE, 1)):
        for m in rx.finditer(s):
            if first_gb is None or m.start(cap_group) == first_gb.start():
                return float(m.group(1)) * float(m.group(2))
    if first_gb is not None:
        return float(first_gb.group(1))
    return None


# Legacy range labels that straddle two of the new disjoint bands, mapped to
# (lower band, upper band). Only these need hardware refinement; a range that
# lies wholly inside one band maps directly (no guesswork).
_STRADDLING_RANGES = {
    '<=16': ('t1', 't2'),
    '16-24': ('t2', 't3'),
    '24-32': ('t3', 't4'),
    '32-64': ('t4', 't5'),
    '48-96': ('t5', 't6'),
}
# Ranges that sit entirely inside a single new band (new + legacy labels).
_CLEAN_RANGES = [
    ('16-23', 't2'), ('24-31', 't3'), ('32-47', 't4'), ('48-95', 't5'),
    ('48-64', 't5'),
    ('96-128', 't6'), ('128-196', 't6'), ('192-256', 't6'), ('196-256', 't6'),
]


def normalize_tier(tier_str, hardware_str=""):
    """Normalize a free-text VRAM value to a schema tier.

    The schema's tiers are disjoint bands (v2.3), so a value has exactly one
    home. Most-specific patterns are checked first, so a bare "16" never
    matches inside "16-23":

    1. a multi-GPU figure in the value ("4x24", "2 x 16") — the per-card
       capacity is summed (4×24 = 96 -> t6);
    2. a named range that lies wholly inside one band (the new labels
       "16-23" … "96", plus legacy labels "48-64", "96-128", "128-196",
       "196-256");
    3. a legacy range that straddles two bands ("≤16", "16-24", "24-32",
       "32-64", "48-96") — refined against the hardware description when it
       names an explicit total ("2 x R9700 32GB" -> 64 -> t5); when it does
       not, the LOWER band is kept (never guess up);
    4. a single number ("8" -> t1, "16" -> t2, "20" -> t2, "24" -> t3,
       "28" -> t3, "32" -> t4, "36" -> t4, "40" -> t4, "48" -> t5,
       "96" -> t6).

    ``None`` when no rule fires (the entry renders under the matrix's
    "Unclassified" group).
    """
    if not tier_str:
        return None
    s = str(tier_str).lower()
    s = s.replace('gb', '').replace('+', '').strip()
    s = s.replace('–', '-').replace('—', '-').replace('≤', '<=')
    s = re.sub(r'\s*-\s*', '-', s)

    # 1. Multi-GPU in the value itself: count x per-card capacity.
    m = re.search(r'(?<!\d)(\d{1,2})\s*[x×]\s*(\d{1,3}(?:\.\d+)?)', s)
    if m:
        return _tier_for_vram(float(m.group(1)) * float(m.group(2)))

    # 2. Ranges wholly inside one band.
    for pattern, tid in _CLEAN_RANGES:
        if pattern in s:
            return tid

    # 3. Legacy ranges that straddle two bands.
    for pattern, (low, _high) in _STRADDLING_RANGES.items():
        if pattern in s:
            total = _hardware_vram_total(hardware_str)
            if total is not None:
                return _tier_for_vram(total)
            return low

    # The new t1 label in word form.
    if 'under 16' in s:
        return 't1'

    # 4. A single number.
    m = re.search(r'(\d+(?:\.\d+)?)', s)
    if m:
        return _tier_for_vram(float(m.group(1)))

    return None

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not RAW_LATEST.exists():
        print("No thread data. Run `python tools/pull.py` first.")
        sys.exit(1)

    thread = load_json(RAW_LATEST)
    schema = load_json(SCHEMA)
    tags_data = load_json(TAGS) if TAGS.exists() else {"submissions": {}, "forum_feedback": {}}

    posts = thread.get("post_stream", {}).get("posts", [])
    submissions = []
    candidates = []
    warnings = []
    skipped_templates = 0
    valid_backends = set(schema.get("backends", []))

    for post in posts:
        post_num = post.get("post_number", 0)
        username = post.get("username", "unknown")

        subs = extract_submissions_from_post(post)
        post_entries = []

        for i, sub in enumerate(subs):
            # Skip unfilled template/placeholder submissions entirely.
            if is_template_submission(sub["data"]):
                skipped_templates += 1
                continue

            # Normalize the backend to a schema-legal value; any free-text
            # detail the contributor tacked onto the name (e.g. "vulkan with
            # no performance tuning") is moved into the notes field. An
            # unfilled placeholder backend is blanked (never matched).
            backend_raw = clean_field(sub["data"].get("backend", ""))
            backend, backend_detail = split_backend(backend_raw, schema)
            notes = clean_field(sub["data"].get("setup_notes", ""))
            if backend_detail:
                notes = f"{notes} | {backend_detail}" if notes else backend_detail

            # P1-4: fold any parsed keys that map to NO canonical field into
            # the notes (e.g. post 8's "coherence:") so nothing is silently
            # lost in the `raw` block that trim_for_client drops.
            unmapped = {k: v for k, v in sub["data"].items()
                        if k not in CANONICAL_FIELDS and str(v).strip()}
            if unmapped:
                extra = " ".join(f"{k}: {v}" for k, v in unmapped.items())
                notes = f"{notes} {extra}" if notes else extra

            # P1-2: attribute the prose before/between/after this block to its
            # notes (cleaned in extract_submissions_from_post). Kept simple —
            # appended verbatim, no NLP parsing. Guard: prose that itself reads
            # as a template placeholder (e.g. a long preamble containing
            # "e.g.,") is NOT appended, so the P0 placeholder sweep stays clean.
            prose = sub.get("prose", "")
            if prose and not is_placeholder(prose):
                notes = f"{notes} {prose}" if notes else prose
            notes = notes.strip()

            # Speed: a single unlabeled figure is the decode speed; a string
            # carrying BOTH a prefill and a decode figure ("PP 120t/s, TG
            # 2.5 t/s") is split so the prompt-processing number never lands
            # in decode_tps and corrupts the "fastest setups" ranking.
            prefill, decode = split_speed(
                clean_field(sub["data"].get("throughput_tps", "")),
                clean_field(sub["data"].get("prefill_tps", "")),
            )

            entry = {
                "id": f"post_{post_num}_{username.lower()}_{i}",
                "source": {
                    "post_number": post_num,
                    "post_id": post.get("id"),
                    "username": username,
                    "submitted_at": post.get("created_at", ""),
                    # P1-1 transparency: False for unmarked-structure blocks.
                    "marked": bool(sub.get("marked", True)),
                },
                "type": sub["type"],
                # Verbatim block, with unfilled template values and
                # no-measurement sentinels blanked — the instruction text
                # and the "N/A"/"TBD" markers must not survive into the
                # dataset (B8).
                "raw": {
                    k: ("" if is_field_placeholder(v) else clean_sentinel(v))
                    for k, v in sub["data"].items()
                },
                # Parsed/normalized fields. The tier is resolved against the
                # hardware string too: a legacy range label that straddles
                # two of the new disjoint bands (e.g. "32-64") is refined by
                # the rig's actual VRAM total when the description names one.
                "tier": normalize_tier(clean_field(sub["data"].get("tier", "")),
                                       clean_field(sub["data"].get("hardware", ""))),
                "hardware": {
                    "description": clean_field(sub["data"].get("hardware", "")),
                    "vendor": infer_vendor(clean_field(sub["data"].get("hardware", "")))
                },
                "backend": backend,
                "os_driver": clean_field(sub["data"].get("os_driver", "")),
                "model": {
                    "name": clean_field(sub["data"].get("model_name", "")),
                    "url": clean_field(sub["data"].get("download_url", ""))
                },
                "quant": clean_field(sub["data"].get("quant_package", "")),
                "weight_precision": clean_field(sub["data"].get("weight_precision", "")),
                "use_cases": clean_field(sub["data"].get("primary_use_case", "")),
                "context": {
                    "stable": clean_field(sub["data"].get("stable_context_tested", "")),
                    "kv_cache": clean_field(sub["data"].get("kv_cache_setting", ""))
                },
                "performance": {
                    "decode_tps": decode,
                    "prefill_tps": prefill,
                    "ttft_cold": clean_field(sub["data"].get("ttft_cold", "")),
                    "power_w": clean_field(sub["data"].get("power_draw", ""))
                },
                "engine_mode": clean_field(sub["data"].get("engine_mode", "")),
                "notes": notes,
                # Curation fields (from tags.json)
                "confidence": "community-reported",
                "lifecycle": "current",
                "highlight": False,
                "tags": []
            }

            # Apply tags/overrides
            tag_key = f"post_{post_num}_{username.lower()}"
            # Try to match in tags (fuzzy - look for post number + username)
            for tag_id, tag_val in tags_data.get("submissions", {}).items():
                if str(post_num) in tag_id and username.lower() in tag_id:
                    entry["confidence"] = tag_val.get("confidence", entry["confidence"])
                    entry["lifecycle"] = tag_val.get("lifecycle", entry["lifecycle"])
                    entry["highlight"] = tag_val.get("highlight", False)
                    entry["highlight_reason"] = tag_val.get("highlight_reason", "")
                    entry["tags"] = tag_val.get("tags", [])
                    break

            post_entries.append(entry)

        # P1-3: cross-block inheritance — needs the post's full entry set, so
        # it runs after every entry for this post is built.
        post_entries = apply_cross_block_inheritance(post_entries)

        # Warnings (computed AFTER inheritance, so a block whose backend was
        # inherited is not falsely flagged as missing one).
        for entry in post_entries:
            if not entry["tier"]:
                warnings.append(f"Post #{post_num} ({username}): tier not normalizable (left empty)")
            if not entry["backend"]:
                warnings.append(f"Post #{post_num} ({username}): No backend specified")
            elif entry["backend"] not in valid_backends:
                # A backend that names no known engine is kept as-is (data
                # quality note, not a hard failure — one unusual entry must
                # not block the pipeline).
                warnings.append(f"Post #{post_num} ({username}): backend '{entry['backend']}' matched no known backend (kept as-is)")

        submissions.extend(post_entries)

        # P1-5: prose-only candidates (no markers AND no unmarked structure).
        if not subs:
            cand = extract_candidate(post)
            if cand:
                candidates.append(cand)

    # Write output. `submissions` contains only real (non-template) entries,
    # so total_submissions and all stats below reflect real data only.
    output = {
        "generated_at": datetime.now().isoformat(),
        "schema_version": schema.get("version", "unknown"),
        "source_thread": "https://forum.level1techs.com/t/256443",
        "total_submissions": len(submissions),
        "skipped_templates": skipped_templates,
        "submissions": submissions
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, 'w') as f:
        json.dump(output, f, indent=2)

    # P1-5: write the conservative prose-only candidate queue (NOT part of the
    # site output until a curator promotes an entry).
    candidate_output = {
        "generated_at": datetime.now().isoformat(),
        "source_thread": "https://forum.level1techs.com/t/256443",
        "total_candidates": len(candidates),
        "note": ("Conservative prose-only candidates (Layer 3). Each is flagged "
                 "unverified for curator review and is NOT included in "
                 "submissions.json or the site until promoted."),
        "candidates": candidates,
    }
    with open(CANDIDATES, 'w') as f:
        json.dump(candidate_output, f, indent=2)

    # Summary
    print(f"✓ Parsed {len(submissions)} real submissions from {len(posts)} posts")
    print(f"✓ Skipped {skipped_templates} template/placeholder submission(s)")
    print(f"✓ Queued {len(candidates)} prose-only candidate(s) for review")
    print(f"✓ Output: {OUTPUT}")
    print(f"✓ Candidates: {CANDIDATES}")

    # Tier distribution (real submissions only)
    tier_counts = {}
    for s in submissions:
        t = s["tier"] or "unclassified"
        tier_counts[t] = tier_counts.get(t, 0) + 1
    print(f"\nTier distribution:")
    for t in sorted(tier_counts.keys()):
        print(f"  {t}: {tier_counts[t]}")

    # Vendor distribution (real submissions only)
    vendor_counts = {}
    for s in submissions:
        v = s["hardware"]["vendor"]
        vendor_counts[v] = vendor_counts.get(v, 0) + 1
    print(f"\nHardware vendors:")
    for v in sorted(vendor_counts.keys()):
        print(f"  {v}: {vendor_counts[v]}")

    if warnings:
        print(f"\n⚠️  {len(warnings)} warning(s):")
        for w in warnings:
            print(f"  - {w}")

if __name__ == "__main__":
    main()
