#!/usr/bin/env python3
"""
parse_thread.py — Parse secondary monitored threads (two-pass extraction).

Usage:
    python tools/parse_thread.py            # Parse all monitored threads
    python tools/parse_thread.py --thread crucible  # Parse one specific

Reads:
    data/raw/{thread_id}_latest.json
    tools/schema.json (for monitored_threads config)

Writes:
    data/benchmarks.json      (Crucible thread -> structured benchmark items)
    data/hardware.json        (AI Rigs thread  -> structured rig items)
    data/category_threads.json (ML/AI category -> topic list, unchanged)

Two-pass design
---------------
PASS 1 — relevance. Keyword matching flags posts that talk about
performance (Crucible) or hardware (Rigs). Every flagged post becomes an
item, so a relevant post is never silently dropped.

PASS 2 — structured extraction. Per-item fields are extracted from the
post's OWN text under a conservative policy:

  * Quoted content (``<aside class="quote">``) belongs to the quoted
    author, so it is removed before extraction — a reply quoting "3x
    RTX 6000 Pro WS" does not credit the replying user with that rig.
  * Questions ("With 4x9700?"), hypotheticals ("I might get a couple of
    DGX sparks"), and envy ("jealous of the MI210") are never treated
    as the poster's own specs.
  * Inequality thresholds ("comfortable >= 30 tokens/sec" — a design
    target) and unlabeled examples ("each one gets 2 tokens/sec") are
    not measurements.
  * A field that cannot be confidently extracted stays ``null`` — it is
    never guessed. The 300-char ``preview`` remains on every item as the
    fallback content.

Every non-null string value is verbatim (or a trivial case/spelling
cleanup of verbatim text) from the post, so extracted data is
verifiable against the raw forum text.
"""

import argparse
import html as _html
import json
import re
import sys
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
DATA_DIR = WORKSPACE / "data"
SCHEMA = WORKSPACE / "tools" / "schema.json"

PREVIEW_LEN = 300

# ---------------------------------------------------------------------------
# Shared text utilities
# ---------------------------------------------------------------------------

#: Typographic characters the forum emits as \u-escapes in the raw JSON,
#: normalized to ASCII so patterns and output are stable.
_UNICODE_MAP = {
    0x2018: "'", 0x2019: "'", 0x201A: "'", 0x201B: "'",
    0x201C: '"', 0x201D: '"',
    0x2013: "-", 0x2014: "-",
    0x00D7: "x",   # multiplication sign -> x (count phrases)
    0x2265: ">=",  # ≥
    0x2264: "<=",  # ≤
    0x2026: "...",
}


def load_json(path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def extract_posts(data):
    """Get list of posts from a Discourse thread JSON."""
    return data.get("post_stream", {}).get("posts", [])


def strip_html(cooked, keep_newlines=False):
    """Cooked HTML -> plain text.

    With ``keep_newlines`` the line structure is preserved (``<br>`` and
    block-level closers become newlines) — needed for neofetch blocks.
    Entities are unescaped and typographic Unicode is normalized to ASCII.
    """
    if not cooked:
        return ""
    text = cooked
    if keep_newlines:
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
        text = re.sub(r"</p>", "\n", text, flags=re.I)
        text = re.sub(r"</div>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = _html.unescape(text)
    text = text.translate(_UNICODE_MAP)
    # Discourse image stamps ("PXL_xxx.MP 916x874 204 KB") are upload
    # metadata, not post content — drop them before extraction.
    text = re.sub(r"[\w.-]+\s+\d{3,4}x\d{3,4}\s+\d+(?:\.\d+)?\s*KB", " ",
                  text)
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.split("\n")]
    if keep_newlines:
        return "\n".join(lines)
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def remove_quotes(cooked):
    """Drop ``<aside class="quote">...</aside>`` blocks.

    The quoted content is the *quoted user's* words (their rig, their
    numbers). Extracting from it would misattribute specs to this
    post's author — e.g. a reply that quotes "3x rtx 6000 pro ws" to
    ask a question about it.
    """
    return re.sub(r'<aside\s+class="quote[^"]*"[^>]*>.*?</aside>', " ",
                  cooked, flags=re.S)


def sentences(text):
    """Split collapsed text into sentences (delimiter kept with its part)."""
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def sentence_at(text, pos):
    """The sentence containing character position ``pos`` (or nearest)."""
    fallback = None
    for s in sentences(text):
        i = text.find(s)
        if i == -1:
            continue
        if i <= pos < i + len(s):
            return s
        if fallback is None:
            fallback = s
    return fallback or text


# ---------------------------------------------------------------------------
# First pass — relevance keywords
# ---------------------------------------------------------------------------

#: Crucible: a post is benchmark-relevant if it mentions a performance
#: metric, a context figure, power, or concrete GPU hardware.
CRUCIBLE_KEYWORDS = (
    "ttft", "tok/s", "tokens/sec", "tokens/s", "tk/s", "tps",
    "latency", "throughput", "prefill", "pre-fill", "decode",
    "context", "watt", "power", "9700", "5090",
)

#: Rigs: a post is hardware-relevant if it mentions GPU model families,
#: server CPUs, or the words gpu/vram.
RIGS_KEYWORDS = (
    "rtx", "quadro", "dgx", "r9700", "9700", "mi210", "mi300",
    "a100", "h100", "radeon", "rx 5", "rx 7", "v620",
    "5090", "4090", "3090", "3080", "5060", "m4 max", "m1 max",
    "epyc", "instinct", "gpu", "vram",
)


def is_crucible_relevant(text):
    low = text.lower()
    return any(k in low for k in CRUCIBLE_KEYWORDS)


def is_rigs_relevant(text):
    low = text.lower()
    return any(k in low for k in RIGS_KEYWORDS)


# ---------------------------------------------------------------------------
# Shared hardware vocabulary
# ---------------------------------------------------------------------------

def _gpu_alt(bounded=True):
    """GPU model alternation, most specific first.

    ``bounded`` adds a leading word boundary to each alternative — needed
    for bare mentions, but it must be OFF in count-phrase context where
    the digit+x prefix is a word character ("4xDGX Sparks").
    """
    b = r"\b" if bounded else r""
    return (
        rf"{b}RTX\s+6000\s+Pro(?:\s+WS)?"
        rf"|{b}RTX\s+A\d{{3,4}}"
        rf"|{b}RTX\s+\d{{4}}(?:\s+Ti)?"
        rf"|{b}Quadro\s+RTX\s+\d{{4}}"
        rf"|{b}H200\b|{b}H100\b|{b}A100\b"
        rf"|{b}DGX\s+Sparks?\b"
        rf"|{b}R9700s?(?:\s+Pro)?"
        rf"|{b}MI\d{{3}}s?"
        rf"|{b}V\d{{3}}s?"
        rf"|{b}Radeon\s+VIIs?"
        rf"|{b}RX\s*\d{{4}}\w?"
        rf"|{b}M[1-9]\s+Max\b"
        rf"|{b}9700s?(?:\s+Pro)?"
        rf"|{b}(?:5090|4090|3090|3080|4060|3060|5070|4070|5060)(?:\s*ti)?"
    )


GPU_MODEL_ALT = _gpu_alt(bounded=True)
GPU_MODEL_ALT_NB = _gpu_alt(bounded=False)

#: Vendor prefix, OPTIONAL (a bare "5090" is as valid as "NVIDIA 5090").
VENDOR_OPT = r"(?:AMD\s+Instinct|NVIDIA|AMD|Apple|Intel)?\s*"

#: Capturing version of the vendor prefix (group 1 = vendor or empty).
VENDOR_CAP = r"((?:AMD\s+Instinct|NVIDIA|AMD|Apple|Intel)?)\s*"

# Inference backends, longest/most specific first so "vllm-radiance" wins
# over bare "vllm".
BACKENDS = (
    ("vllm-radiance", r"vllm-radiance"),
    ("llama.cpp", r"llama\.cpp"),
    ("vLLM", r"(?<![a-z])vllm(?![a-z-])"),
    ("Ollama", r"\bollama\b"),
    ("LM Studio", r"\blm studio\b"),
    ("SGLang", r"\bsglang\b"),
    ("Radiance", r"\bradiance\b"),
    ("Unsloth", r"\bunsloth\b"),
    ("TGI", r"\btgi\b"),
    ("Colibri", r"\bcolibri\b"),
    ("LiteLLM", r"\blitellm\b"),
)

#: LLM model families. The family name must be followed by a non-letter
#: boundary (digit / dot / dash / space / end) so "phillips" is never
#: read as a "Phi" model; the suffix may carry version/quant tokens.
LLM_MODEL_RE = re.compile(
    r"\b(?:[A-Za-z0-9_.-]+/)?"
    r"(?:Qwen|Gemma|DeepSeek|Llama|GLM|Mistral|Phi|Swift|Kimi|Yi)"
    r"(?=[\s.:_\-/\d]|$)[\w.\-:]*",
    re.I,
)

_FAMILY_CASE = {
    "qwen": "Qwen", "gemma": "Gemma", "deepseek": "DeepSeek",
    "llama": "Llama", "glm": "GLM", "mistral": "Mistral", "phi": "Phi",
    "swift": "Swift", "kimi": "Kimi", "yi": "Yi",
}

#: Trailing tokens that are legitimate model-name qualifiers.
_TRAIL_WHITELIST = {
    "flash", "next", "pro", "max", "mini", "lite", "ultra", "instruct",
    "it", "xl", "gguf", "fp8", "bf16", "q4", "q8", "q4_k_m", "q8_0",
    "w4a16", "auto", "round", "gptq", "quant", "uncensored", "coder",
    "vl", "abli", "unsloth", "flash-next", "atm-free",
}

#: Trailing tokens that are ordinary English — a model name stops here.
_TRAIL_STOP = {
    "with", "the", "maximum", "context", "set", "and", "or", "of", "for",
    "on", "in", "to", "a", "an", "my", "i", "we", "you", "your", "is",
    "are", "was", "were", "that", "this", "it", "they", "them", "their",
    "which", "while", "when", "where", "what", "how", "why", "run",
    "running", "using", "used", "via", "at", "by", "from", "into",
    "over", "under", "about", "after", "before", "between", "during",
    "since", "out", "up", "down", "off", "so", "no", "yes", "not", "all",
    "any", "each", "every", "one", "two", "three", "more", "most",
    "less", "such", "than", "then", "there", "here", "who", "whom",
    "whose", "does", "do", "did", "have", "has", "had", "will",
    "would", "can", "could", "may", "must", "should", "just", "very",
    "really", "also", "too", "only", "even", "still", "now", "new",
    "old", "big", "small", "fast", "slow", "good", "bad", "great",
    "nice", "whole", "pure", "live", "real", "true", "false", "own",
    "same", "other", "another", "first", "second", "third", "per",
    "roughly", "approximately", "nearly", "almost", "exactly",
    "precisely", "simply", "easily", "quickly", "slowly", "smoothly",
    "quietly", "loudly", "clearly", "honestly", "openly", "freely",
    "locally", "globally", "remotely", "directly", "indirectly",
    "immediately", "eventually", "ultimately", "initially", "originally",
    "basically", "generally", "typically", "usually", "often", "rarely",
    "seldom", "sometimes", "always", "never", "ever", "again", "once",
    "twice", "alone", "together", "apart", "aside", "around", "along",
    "across", "through", "toward", "towards", "against", "behind",
    "below", "beneath", "beside", "besides", "beyond", "near", "nearby",
    "inside", "outside", "within", "without", "these", "those", "atm",
}


def _extract_model_name(text):
    """The first LLM model name with a version/size signal.

    A bare family name ("Qwen") with no digit anywhere is too vague to
    record — it is rejected, never padded with guesses. Trailing
    qualifiers ("3.8 flash next") are taken from the text after the
    match and stop at the first ordinary-English word.
    """
    for m in LLM_MODEL_RE.finditer(text):
        head = m.group(0)
        # "Llama.cpp" / "vLLM" etc. are engines, not models — a family
        # match that keeps running into a known extension is rejected.
        if re.search(r"\.(cpp|py|rs|sh|go)\b", head, re.I):
            continue
        # Family = up to the first digit/dot/dash/space (last path segment
        # for HuggingFace-style "org/name" ids).
        fam = re.split(r"[\s.:_\-/\d]", head.rsplit("/", 1)[-1],
                       maxsplit=1)[0].lower()
        if fam not in _FAMILY_CASE:
            continue
        trail = []
        pos = m.end()
        for _ in range(3):
            mm = re.match(r"\s+([\w.\-]{1,16})", text[pos:])
            if not mm:
                break
            pos += mm.end(1)
            if pos < len(text) and re.match(r"[\w.\-]", text[pos]):
                break  # the real token is longer than 16 chars
            t = mm.group(1)
            if t.lower() in _TRAIL_STOP:
                break
            # A token that starts ANOTHER family name is the next model,
            # not a qualifier ("Qwen3.6-35B-A3B Qwen3-Coder-30B ...").
            if re.match(
                    r"(?i)^(qwen|gemma|deepseek|llama|glm|mistral|phi|"
                    r"swift|kimi|yi)(?=[\s.:_\-/\d]|$)", t):
                break
            if re.search(r"\d", t) or t.lower() in _TRAIL_WHITELIST:
                trail.append(t)
            else:
                break
        full = head + (" " + " ".join(trail) if trail else "")
        full = re.sub(r"[.,;:]+$", "", full)
        # Capitalize the family name only (verbatim otherwise).
        fam_len = len(re.split(r"[\s.:_\-/\d]",
                               head.rsplit("/", 1)[-1],
                               maxsplit=1)[0])
        if "/" in head:
            prefix, last = head.split("/", 1)
            full = prefix + "/" + _FAMILY_CASE[fam] + last[fam_len:]
        else:
            full = _FAMILY_CASE[fam] + full[fam_len:]
        # A bare family name with no version, size, or known variant
        # token ("Qwen with the maximum context set") is too vague to
        # record — reject, never pad.
        if not re.search(r"\d", full) and not trail:
            continue
        return full[:48]
    return None


# ---------------------------------------------------------------------------
# Conservative-context guards
# ---------------------------------------------------------------------------

_NEGATIVE_RE = re.compile(
    r"\b(jealous|might|would|considering|thinking|plan to|planning|"
    r"i had to|wish|bargain hunting|shopping)\b", re.I)

_POSSESSION_RE = re.compile(
    r"\b(my|mine|i have|i am|i still have|i built|i wound up|i use|i run|"
    r"popping|running|throw my|setup|rig|machine|computer|start it off|"
    r"bought|same computer|upgrade|\bI\b)\b", re.I)

#: First person anywhere in the post (used to relax the sentence-level
#: ownership check for showcase-style spec dumps).
_POST_FIRST_PERSON = re.compile(r"\b(i|i'm|i've|i'll|my|mine)\b", re.I)


def _prior_sentence(text, i):
    """The sentence immediately before position ``i`` (empty if none).

    Ellipses ("...") are collapsed to single dots first — a raw rsplit
    would land inside the dot run and return an empty "sentence".
    """
    before = re.sub(r"\.{2,}", ".", text[:i])
    if before.count(".") < 1:
        return ""
    return before.rsplit(".", 2)[1]


def _window_ok(text, pos):
    """True if the 2-sentence window around ``pos`` is a first-person
    statement (not a question, hypothetical, or envy)."""
    s = sentence_at(text, pos)
    i = text.find(s)
    window = (_prior_sentence(text, i) + " " + s).strip()
    if window.rstrip().endswith("?"):
        return False
    if _NEGATIVE_RE.search(window):
        return False
    return bool(_POSSESSION_RE.search(window))


def _clean_sentence(text, pos):
    """Sentence at ``pos`` with question/negative context checked."""
    s = sentence_at(text, pos)
    if s.strip().endswith("?"):
        return None
    if _NEGATIVE_RE.search(s):
        return None
    return s


def _is_spec_dump(text):
    """A showcase-style spec list (2+ distinct spec signals) — the
    "Show Off Your AI Rig" idiom. Used to accept GPU mentions the
    poster never explicitly claims ("3x rtx 6000 pro ws ... case")."""
    signals = 0
    if re.search(GPU_MODEL_ALT, text, re.I):
        signals += 1
    if re.search(r"\b\d{2,3}\s*(?:GB|GiB|gig)\b", text, re.I):
        signals += 1
    if re.search(r"\b(?:ddr[45]|ram)\b", text, re.I):
        signals += 1
    if re.search(r"\b\d{3,4}(?:kf|x)\b|\b(?:xeon|ryzen|epyc|threadripper|"
                 r"5700|5950|13900|6230|7532)\b", text, re.I):
        signals += 1
    if re.search(r"\b(?:case|psu|motherboard|board|enclosure)\b", text,
                 re.I):
        signals += 1
    if re.search(r"\b\d+\s*(?:x\s*)?(?:tb|nvme|ssd)\b", text, re.I):
        signals += 1
    return signals >= 2


# ---------------------------------------------------------------------------
# Crucible — second pass
# ---------------------------------------------------------------------------

def _normalize_gpu(s):
    """Light case/spelling cleanup of a GPU model name (verbatim tokens;
    no vendor word is ever added that the post does not state)."""
    s = re.sub(r"\s+", " ", s).strip()
    rules = (
        (r"^(?:nvidia\s+)?rtx\s+a(\d{3,4})$", r"RTX A\1"),
        (r"^(?:nvidia\s+)?rtx\s+(\d{4})\s*ti$", r"RTX \1 Ti"),
        (r"^(?:nvidia\s+)?rtx\s+6000\s+pro\s+ws$", "RTX 6000 Pro WS"),
        (r"^(?:nvidia\s+)?rtx\s+(\d{4})$", r"RTX \1"),
        (r"^(?:nvidia\s+)?quadro\s+rtx\s+(\d{4})$", r"Quadro RTX \1"),
        (r"^dgx\s+sparks?$", "DGX Spark"),
        (r"^amd\s+instinct\s+mi(\d{3})s?$", r"AMD Instinct MI\1"),
        (r"^amd\s+mi(\d{3})s?$", r"AMD MI\1"),
        (r"^mi(\d{3})s?$", r"MI\1"),
        (r"^(?:amd\s+)?v(\d{3})s?$", r"V\1"),
        (r"^(?:amd\s+)?r9700s?(?:\s+pro)?$",
         lambda m: "R9700 Pro" if re.search(r"pro", m.group(0), re.I)
         else "R9700"),
        (r"^(?:amd\s+)?9700s?(?:\s+pro)?$",
         lambda m: "9700 Pro" if re.search(r"pro", m.group(0), re.I)
         else "9700"),
        (r"^radeon\s+viis?$", "Radeon VII"),
        (r"^rx\s*(\d{4}\w?)$", lambda m: f"RX {m.group(1).upper()}"),
        (r"^m([1-9])\s+max$", r"M\1 Max"),
        (r"^(5060)\s*ti$", r"\1 Ti"),
        (r"^(\d{4})s?$", r"\1"),
    )
    for pat, rep in rules:
        s2 = re.sub(pat, rep, s, flags=re.I)
        if s2 != s:
            s = s2
            break
    return s


def _vendor_model(vendor, model):
    """Combine an (optional) stated vendor with the model — a vendor word
    is never added that the post does not state."""
    m = _normalize_gpu(model)
    if vendor:
        v = re.sub(r"\s+", " ", vendor).strip()
        if v and v.lower() not in m.lower():
            m = f"{v} {m}"
    return m


def _strip_vendor(s):
    return re.sub(r"^(?:AMD\s+Instinct|NVIDIA|AMD|Apple|Intel)\s+", "", s,
                  flags=re.I)


def _vendor_of(s):
    """The vendor prefix of a GPU line, if it states one."""
    m = re.match(r"^(AMD\s+Instinct|NVIDIA|AMD|Apple|Intel)\s+", s, re.I)
    return m.group(1) if m else ""


def _gpu_key(s):
    k = _strip_vendor(s).lower()
    k = re.sub(r"\s+", " ", k).strip()
    k = re.sub(r"\[.*?\]", "", k)  # neofetch tags: "[Discrete]"
    k = re.sub(r"s$", "", k)  # "v620s" == "v620"
    return k


def _extract_crucible_hardware(text):
    """A stated GPU, with count when stated. None when it is not
    confidently the poster's own card (question / hypothetical)."""
    for m in re.finditer(
            rf"(\d+)\s*x\s*{VENDOR_CAP}({GPU_MODEL_ALT})", text, re.I):
        if not _window_ok(text, m.start()):
            continue
        return f"{m.group(1)}x {_vendor_model(m.group(2), m.group(3))}"
    for m in re.finditer(
            rf"\b(pair|dual|triple|quad)\b\s+(?:of\s+)?"
            rf"{VENDOR_CAP}({GPU_MODEL_ALT})", text, re.I):
        if not _window_ok(text, m.start()):
            continue
        n = {"pair": 2, "dual": 2, "triple": 3, "quad": 4}[
            m.group(1).lower()]
        return f"{n}x {_vendor_model(m.group(2), m.group(3))}"
    for m in re.finditer(rf"{VENDOR_CAP}({GPU_MODEL_ALT})", text, re.I):
        if _window_ok(text, m.start()):
            return _vendor_model(m.group(1), m.group(2))
    return None


def _extract_crucible_model(text):
    return _extract_model_name(text)


def _model_has_signal(text):
    """A model name alone is not a benchmark — require at least one
    hardware / speed / context / power signal in the same post."""
    return (_extract_crucible_hardware(text) is not None
            or _extract_crucible_speeds(text) != (None, None)
            or _extract_crucible_context(text) is not None
            or _extract_crucible_power(text) is not None)


def _in_paren(text, start, end):
    """True if [start:end] sits inside an unbalanced ( parenthetical)."""
    seg = text[:start]
    return seg.count("(") > seg.count(")")


def _extract_crucible_backend(text):
    """The poster's own inference engine.

    Skipped when: the sentence is conditional ("If you're running ..."),
    the sentence lists 2+ backends (a capability list, not a stack), or
    the mention is a parenthetical aside ("(llama.cpp)").
    """
    for name, pat in BACKENDS:
        for m in re.finditer(pat, text, re.I):
            s = sentence_at(text, m.start())
            if re.match(r"^\s*(if|when)\s+(you|we|it)", s, re.I):
                continue
            distinct = sum(
                1 for n2, p2 in BACKENDS if re.search(p2, s, re.I))
            if distinct >= 2:
                continue  # capability list
            if _in_paren(text, m.start(), m.end()):
                continue
            return name
    return None


_SPEED_UNITS = r"(?:t/s|tokens?/s|tokens?/sec|tps|tk/s)"
_SPEED_LABELS = re.compile(
    r"\b(decode|prefill|pre-fill|generation|eval|ttft|code gen|"
    r"single-request|peak|throughput|tg|pp)\b", re.I)
_INEQUALITY_BEFORE = re.compile(r"(>=|>|<|at least|over|more than)\s*$")


def _extract_crucible_speeds(text):
    """(decode_tps, prefill_tps) — labeled figures only.

    A figure is a measurement when its sentence names the metric
    (decode / prefill / generation / eval / TTFT / ...). Design targets
    ("comfortable >= 30 tokens/sec") and unlabeled examples ("each one
    gets 2 tokens/sec") are not.
    """
    decode = prefill = None
    for m in re.finditer(
            rf"(~|>=|>|<)?\s*(\d[\d,]*(?:\.\d+)?)"
            rf"(?:\s*-\s*(\d[\d,]*(?:\.\d+)?))?"
            rf"\s*(?:ish|about|roughly|approximately)?\s*{_SPEED_UNITS}\b",
            text, re.I):
        before = text[max(0, m.start(2) - 12):m.start(2)].rstrip()
        if _INEQUALITY_BEFORE.search(before):
            continue  # threshold / bound, not a measurement
        s = sentence_at(text, m.start())
        # The label must be NEAR the figure: a sentence can carry several
        # labeled figures ("3200t/s prefill, 80t/s generation, 120t/s
        # code gen") and a far-away label must not claim a different
        # figure. Fall back to the whole sentence only when the local
        # window is label-free.
        local = text[max(0, m.start(2) - 25):m.end() + 25].lower()
        labeled_local = bool(_SPEED_LABELS.search(local))
        labeled = local if labeled_local else s.lower()
        if not _SPEED_LABELS.search(labeled):
            continue
        val = m.group(2)
        if m.group(3):
            val = f"{val}-{m.group(3)}"
        if re.search(r"\b(prefill|pre-fill|pp)\b", labeled):
            if prefill is None:
                prefill = val
        if re.search(r"\b(decode|generation|eval|tg|code gen)\b",
                     labeled):
            if decode is None:
                decode = val
    return decode, prefill


def _extract_crucible_ttft(text):
    m = re.search(
        r"\b(?:ttft|time to first token)\D{0,15}(\d+(?:\.\d+)?)\s*(ms|s|sec)"
        r"\b", text, re.I)
    if not m:
        return None
    val = float(m.group(1))
    return val / 1000.0 if m.group(2).lower() == "ms" else val


def _extract_crucible_vram(text):
    m = re.search(r"(\d+(?:\.\d+)?)\s*GB\s*(?:of\s*)?VRAM\b", text, re.I)
    if not m:
        m = re.search(r"VRAM\D{0,12}(\d+(?:\.\d+)?)\s*GB\b", text, re.I)
    return float(m.group(1)) if m else None


def _extract_crucible_context(text):
    m = re.search(r"\b(\d{2,4})\s*([KkMm])?\s+context\b", text)
    if not m:
        return None
    # Verbatim casing ("128k", "650k", "1M") — the value must stay
    # checkable against the post text.
    return f"{m.group(1)}{m.group(2) or ''}"


def _extract_crucible_power(text):
    m = re.search(r"\b(\d{2,4})\s*(watts?|W)\b", text)
    return float(m.group(1)) if m else None


def _crucible_notes(text, **fields):
    """Verbatim sentences that carry the extracted signals (max 2)."""
    wanted = []
    for v in fields.values():
        if v is None:
            continue
        if isinstance(v, float) and v == int(v):
            v = int(v)  # "400", not "400.0", for text matching
        wanted.append(v)
    if not wanted:
        return None
    notes = []
    for s in sentences(text):
        low = s.lower()
        if any(str(w).lower() in low for w in wanted):
            notes.append(re.sub(r"\s+", " ", s).strip())
        if len(notes) >= 2:
            break
    return " | ".join(notes) if notes else None


def parse_crucible(data):
    """Extract benchmark items from the Crucible thread (two-pass)."""
    results = []
    for post in extract_posts(data):
        full_text = strip_html(post.get("cooked", ""))
        if not is_crucible_relevant(full_text):
            continue
        # Extraction runs on the post's own words only (quotes removed).
        own_text = strip_html(remove_quotes(post.get("cooked", "")))

        decode, prefill = _extract_crucible_speeds(own_text)
        model = _extract_crucible_model(own_text)
        if model is not None and not _model_has_signal(own_text):
            model = None  # a model name with no other signal is not a bench

        hardware = _extract_crucible_hardware(own_text)
        backend = _extract_crucible_backend(own_text)
        context = _extract_crucible_context(own_text)
        power = _extract_crucible_power(own_text)
        ttft = _extract_crucible_ttft(own_text)
        vram = _extract_crucible_vram(own_text)

        structured = any(v is not None for v in
                         (model, hardware, backend, decode, prefill,
                          vram, ttft, context, power))

        pn = post.get("post_number")
        results.append({
            "id": f"crucible_post_{pn}_0",
            "post_id": post.get("id"),
            "post_number": pn,
            "contributor": post.get("username"),
            "date": (post.get("created_at") or "")[:10],
            "model": model,
            "hardware": hardware,
            "backend": backend,
            "performance": {
                "decode_tps": decode,
                "prefill_tps": prefill,
                "vram_gb": vram,
                "ttft_s": ttft,
            },
            "context_length": context,
            "power_w": power,
            "notes": _crucible_notes(own_text, model=model,
                                     hardware=hardware, backend=backend,
                                     decode=decode, prefill=prefill,
                                     context=context, power=power),
            "preview": full_text[:PREVIEW_LEN],
            "structured": structured,
        })
    return results


# ---------------------------------------------------------------------------
# Rigs — second pass
# ---------------------------------------------------------------------------

_NEOFETCH_ANCHOR = re.compile(r"\b\w+@\w+\s+OS:", re.I)


def split_machines(text):
    """Split a post into per-machine segments.

    A new neofetch block (``user@host OS:``) starts a new machine. A post
    with a single (or no) neofetch block is one segment. Leading prose
    before the first anchor is kept only if it is long enough to carry
    its own specs.
    """
    anchors = [m.start() for m in _NEOFETCH_ANCHOR.finditer(text)]
    if len(anchors) < 2:
        return [text] if text.strip() else []
    segments = []
    lead = text[:anchors[0]].strip()
    if len(lead) >= 40 and re.search(
            rf"{GPU_MODEL_ALT}|\bCPU:|\bRAM:|\bOS:", lead, re.I):
        segments.append(lead)
    for i, a in enumerate(anchors):
        end = anchors[i + 1] if i + 1 < len(anchors) else len(text)
        segments.append(text[a:end].strip())
    return [s for s in segments if s]


def _split_lined(lined, n):
    """Split line-preserved text at the same neofetch anchors used on the
    collapsed text (anchors are unique strings, so they locate cleanly)."""
    anchors = [m.start() for m in _NEOFETCH_ANCHOR.finditer(lined)]
    if n <= 1 or len(anchors) < 2:
        return [lined]
    return [lined[a:(anchors[i + 1] if i + 1 < len(anchors) else len(lined))]
            for i, a in enumerate(anchors)]


def _neofetch(lined):
    """Parse neofetch-style key lines from line-preserved text."""
    nv = {"GPUs": []}
    for line in lined.split("\n"):
        line = line.strip()
        m = re.match(r"^(OS|Kernel|CPU|Memory|Swap|Resolution|Uptime|Shell):"
                     r"\s*(.+)$", line)
        if m:
            nv[m.group(1).lower()] = m.group(2).strip()
        m = re.match(r"^Disk \([^)]*\):\s*(.+)$", line)
        if m:
            nv["disk"] = m.group(1).strip()
        m = re.match(r"^GPU \d+:\s*(.+)$", line)
        if m:
            g = re.sub(r"\s*\[[^\]]*\]", "", m.group(1)).strip()
            nv["GPUs"].append(g)
    return nv


def _neofetch_cpu(raw):
    """'Intel(R) Xeon(R) E5-2697A v4 (32) @ 3.60 GHz' -> model name."""
    s = re.sub(r"\(R\)", "", raw)
    s = re.sub(r"\s*\(\d+\)\s*@.*$", "", s)
    s = s.split(",")[0]
    return re.sub(r"\s+", " ", s).strip()


def _neofetch_ram(raw):
    """'31.32 GiB / 125.76 GiB (25%)' -> total."""
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:GiB|GB)\s*\(", raw)
    if not m:
        m = re.search(r"/\s*(\d+(?:\.\d+)?)\s*(?:GiB|GB)", raw)
    return float(m.group(1)) if m else None


def _neofetch_disk(raw):
    """'889.43 GiB / 1.73 TiB (50%) - btrfs' -> '1.73 TiB (btrfs)'."""
    m = re.search(r"/\s*(\d+(?:\.\d+)?\s*(?:TiB|GiB|GB))\s*\(.*?\)\s*-"
                  r"\s*([\w-]+)", raw)
    if m:
        return f"{m.group(1)} ({m.group(2)})"
    m = re.search(r"(\d+(?:\.\d+)?\s*(?:TiB|GiB|GB))", raw)
    return m.group(1) if m else None


def _extract_rig_gpu(lined, text):
    """(model, count) for the segment's primary GPU.

    Priority: neofetch GPU lines (dominant model by card count) >
    count phrases ("4x 9700 pro", "a pair of R9700s") > "GPU:" label
    lines > bare model with an ownership (or showcase spec-dump) window.
    (None, None) when the segment does not state a GPU the poster owns.
    """
    nv = _neofetch(lined)
    if nv["GPUs"]:
        groups = {}
        for g in nv["GPUs"]:
            key = _gpu_key(g)
            grp = groups.setdefault(
                key, {"model": _vendor_model(_vendor_of(g),
                                             _strip_vendor(g)), "n": 0})
            grp["n"] += 1
        best = max(groups.values(), key=lambda g: g["n"])
        return best["model"], best["n"]

    dump = _is_spec_dump(text)

    def _accept(m):
        s = _clean_sentence(text, m.start())
        if s is None:
            return False
        if _window_ok(text, m.start()):
            return True
        # Showcase spec dumps state specs without "my" — accept when the
        # sentence itself is clean (not a question, not hypothetical).
        return dump

    for m in re.finditer(
            rf"(\d+)\s*x\s*{VENDOR_CAP}({GPU_MODEL_ALT_NB})", text, re.I):
        if _accept(m):
            return _vendor_model(m.group(2), m.group(3)), int(m.group(1))

    for m in re.finditer(
            rf"\b(pair|dual|triple|quad)\b\s+(?:of\s+)?"
            rf"{VENDOR_CAP}({GPU_MODEL_ALT_NB})", text, re.I):
        if _accept(m):
            n = {"pair": 2, "dual": 2, "triple": 3, "quad": 4}[
                m.group(1).lower()]
            return _vendor_model(m.group(2), m.group(3)), n

    m = re.search(rf"\bGPU:\s*{VENDOR_CAP}({GPU_MODEL_ALT})", text, re.I)
    if m and _accept(m):
        return _vendor_model(m.group(1), m.group(2)), 1

    for m in re.finditer(rf"{VENDOR_CAP}({GPU_MODEL_ALT})", text, re.I):
        if _accept(m):
            return _vendor_model(m.group(1), m.group(2)), 1
    return None, None


def _extract_vram_total(text, gpu_model, count):
    """Total VRAM in GB, from figures the post actually states.

    Explicit totals win ("Total 40GB"); otherwise per-card capacity
    stated next to the GPU model is multiplied by the stated count
    (the same summing rule the main-thread parser uses for tiers).
    Unified memory ("128GB M4 Max") is taken as-is.
    """
    m = re.search(r"Total\s+(\d+(?:\.\d+)?)\s*GB\b", text, re.I)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s*GB\s+M[1-9]\s+Max\b", text, re.I)
    if m:
        return float(m.group(1))
    # Per-card capacity stated next to a GPU model ("5060ti 16g",
    # "MI210 (64GB HBM2") — matched on the raw model form (the
    # normalized name may differ in spacing: "5060 Ti" vs "5060ti").
    # The alternation is wrapped: `|` binds loosest, so an ungrouped
    # alternation would attach the GB tail to its last branch only.
    m = re.search(
        rf"(?:{GPU_MODEL_ALT})\s*\(?\s*(\d+(?:\.\d+)?)\s*(?:GB|g)\b",
        text, re.I)
    if m and count:
        return float(m.group(1)) * count
    return None


def _extract_cpu(lined, text):
    nv = _neofetch(lined)
    if nv.get("cpu"):
        return _neofetch_cpu(nv["cpu"])
    m = re.search(r"\bCPU:\s*([^,\.]+)", text, re.I)
    if m:
        s = _clean_sentence(text, m.start())
        if s is not None:
            return re.sub(r"\s+", " ", m.group(1)).strip()
        return None
    for pat in (
            r"\b2x\s+AMD\s+EPYC\s+(\d{4})\b",
            r"\bEPYC\s+(\w+)\s+(\d{4})\b",
            r"\bDual\s+Xeon\s+Gold\s+(\d{4})\b",
            r"\bThreadripper\s+(\d{4}[a-z]?)\b",
            r"\b(\d{4,5})KF\b",
            r"\b(5700X|5950X|5800X|5600X)\b",
    ):
        m = re.search(pat, text, re.I)
        if not m:
            continue
        s = _clean_sentence(text, m.start())
        if s is None:
            continue
        if not (_window_ok(text, m.start()) or _is_spec_dump(text)):
            continue
        raw = m.group(0)
        if pat.startswith(r"\bThreadripper"):
            return f"Threadripper {m.group(1).upper()}"
        if "KF" in pat:
            return raw.upper()
        # Known-case fixes only (EPYC is an acronym; the rest stays
        # verbatim).
        return re.sub(r"(?i)\bepyc\b", "EPYC", raw)
    return None


def _extract_ram(text):
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:GB|GiB|gig|G)\b\s*(?:of\s+)?"
        r"(?:DDR[45]|REG-?ECC|ECC)\b", text, re.I)
    if m:
        return float(m.group(1))
    m = re.search(r"\bMemory:\s*[\d.]+\s*\w+\s*/\s*([\d.]+)\s*(?:GiB|GB)",
                  text)
    if m:
        return float(m.group(1))
    return None


_STORAGE_DESC = (r"(?:(?:\s+(?:of\s+)?)(?:samsung|team\s+group|wd|intel|"
                 r"mlc|nvme|ssd|hdd|evo|870|sn850|black|pcie|4\.0|raid|"
                 r"z1|storage))")

#: Brand/model casing fixes for storage descriptions (verbatim tokens).
_STORAGE_CASE = {
    "samsung": "Samsung", "team group": "Team Group", "wd": "WD",
    "intel": "Intel", "seagate": "Seagate", "crucial": "Crucial",
    "kingston": "Kingston", "corsair": "Corsair", "g.skill": "G.Skill",
    "sn850": "SN850", "870 evo": "870 EVO", "mlc": "MLC", "nvme": "NVMe",
    "ssd": "SSD", "hdd": "HDD", "raid": "RAID", "pcie": "PCIe",
}


def _case_storage_desc(desc):
    out = desc
    for k, v in _STORAGE_CASE.items():
        out = re.sub(rf"(?i)\b{re.escape(k)}\b", v, out)
    return out


def _extract_storage(lined, text):
    nv = _neofetch(lined)
    if nv.get("disk"):
        return _neofetch_disk(nv["disk"])
    parts = []
    # "2x 4TB samsung ..." — explicit x-count
    for m in re.finditer(
            r"(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*(TB|TiB|GB)\b"
            rf"({_STORAGE_DESC}?)", text, re.I):
        desc = _case_storage_desc(re.sub(r"\s+", " ",
                                         (m.group(4) or "")).strip())
        parts.append(f"{m.group(1)}x {m.group(2)}{m.group(3).upper()}"
                     + (f" {desc}" if desc else ""))
    # "2 4TB samsung ..." — count then capacity, no x (require a storage
    # keyword to follow, so "7532 128GB DDR4" (CPU + RAM) never matches)
    for m in re.finditer(
            r"(\d+)\s+(\d+(?:\.\d+)?)\s*(TB|GB)\b"
            rf"({_STORAGE_DESC}?)", text, re.I):
        desc = (m.group(4) or "").strip()
        if not re.search(r"(samsung|team|group|wd|intel|mlc|nvme|ssd|"
                         r"hdd|evo|870|sn850|raid)", desc, re.I):
            continue
        if re.search(r"(ddr|ram)", desc, re.I):
            continue
        desc = _case_storage_desc(re.sub(r"\s+", " ", desc).strip())
        parts.append(f"{m.group(1)}x {m.group(2)}{m.group(3).upper()}"
                     + (f" {desc}" if desc else ""))
    # "6 slots filled with 2TB samsung 870 evo drives in raid-z1"
    for m in re.finditer(
            r"(\d+)\s+slots?\s+filled\s+with\s+(\d+(?:\.\d+)?)\s*(TB|GB)\b"
            rf"({_STORAGE_DESC}?)", text, re.I):
        desc = _case_storage_desc(re.sub(r"\s+", " ",
                                         (m.group(4) or "")).strip())
        parts.append(f"{m.group(1)}x {m.group(2)}{m.group(3).upper()}"
                     + (f" {desc}" if desc else ""))
    # bare capacities: "~5TB of storage", "a handy 2TB MLC SSD"
    for m in re.finditer(
            r"(~)?(\d+(?:\.\d+)?)\s*(TB|TiB)\b"
            rf"({_STORAGE_DESC}?)", text, re.I):
        desc = re.sub(r"\s+", " ", (m.group(4) or "")).strip()
        desc = re.sub(r"^(?:of\s+)?", "", desc)
        desc = _case_storage_desc(desc)
        cap = f"{m.group(2)}{m.group(3).upper()}"
        # Subsumed when a counted part already covers this capacity
        # ("2x 4TB samsung ..." covers the bare "4TB samsung ...").
        if any(re.search(re.escape(cap) + (r"\s+" + re.escape(
                desc.split()[0]) if desc else r"\b"), p)
                for p in parts):
            continue
        cand = f"{m.group(1) or ''}{cap}"
        if desc:
            cand += f" {desc}"
        parts.append(cand)
    if not parts:
        return None
    return " + ".join(dict.fromkeys(parts))[:120]


_OS_CASE = {
    "ubuntu": "Ubuntu", "debian": "Debian", "fedora": "Fedora",
    "arch": "Arch", "endeavouros": "EndeavourOS", "windows": "Windows",
    "macos": "macOS", "proxmox": "Proxmox", "rocky": "Rocky",
    "almalinux": "AlmaLinux",
}


def _extract_os(lined, text):
    nv = _neofetch(lined)
    if nv.get("os"):
        raw = re.sub(r"\s+x86_64.*$", "", nv["os"]).strip()
        name = raw.split()[0] if raw else ""
        return _OS_CASE.get(name.lower(), name)
    m = re.search(
        r"\b(Ubuntu|Debian|Fedora|Arch|EndeavourOS|Windows|macOS|"
        r"Proxmox|Rocky|AlmaLinux)\b(\s+\d{2}\.\d{2})?", text, re.I)
    if m:
        name = _OS_CASE.get(m.group(1).lower(), m.group(1))
        return (name + (m.group(2) or "")).strip()
    return None


def _extract_context(text):
    m = re.search(r"\b(\d{2,4})\s*([KkMm])?\s+context\b", text)
    if not m:
        return None
    # Verbatim casing ("256k", "650k", "1M") — the value must stay
    # checkable against the post text.
    return f"{m.group(1)}{m.group(2) or ''}"


def _speed_clusters(text, limit=2):
    """Verbatim snippets around t/s figures.

    Each match contributes a window (40 chars before the figure, 60
    after); overlapping windows merge into one cluster, so a
    multi-figure sentence ("3200t/s prefill, 80t/s generation, 120t/s
    code gen") stays one readable snippet. The window is then trimmed at
    sentence boundaries on both sides, and a mid-word start is trimmed
    past ordinary English words (never past a number).
    """
    spans = []
    for m in re.finditer(
            rf"(~|>=)?\s*(\d[\d,]*(?:\.\d+)?)?"
            rf"(?:\s*-\s*(\d[\d,]*(?:\.\d+)?))?"
            rf"\s*(?:ish|about|roughly)?\s*(?:t/s|tokens?/s|tokens?/sec|"
            rf"tps|tk/s)\b", text, re.I):
        if not m.group(2) and not m.group(3):
            continue  # unit with no number ("tokens/sec" alone)
        a = max(0, m.start(2) - 40)
        b = min(len(text), m.end() + 60)
        # Cut the post-window at the first sentence boundary inside it, so
        # a merged cluster never bridges into the next sentence (or a
        # punctuation-free wall such as a pasted repo description).
        tail = text[m.end():b]
        jb = min((x for x in (tail.find(". "), tail.find("! "),
                              tail.find("? ")) if x > 0),
                 default=-1)
        if jb > 0:
            b = m.end() + jb + 1
        if spans and a <= spans[-1][1]:
            spans[-1] = (spans[-1][0], max(spans[-1][1], b))
        else:
            spans.append((a, b))
        if len(spans) >= limit:
            break
    out = []
    for a, b in spans:
        snippet = re.sub(r"\s+", " ", text[a:b])
        # Anchor on the first NUMBERED speed figure inside the cluster —
        # the pre-trim stops at the last boundary BEFORE it, the
        # post-trim at the first boundary AFTER it (so a long window
        # between two figures keeps both, and a punctuation-free wall
        # after the last figure is cut away).
        nm = re.search(
            r"(\d[\d,]*(?:\.\d+)?)\s*(?:-\s*\d[\d,]*(?:\.\d+)?)?"
            r"\s*(?:ish|about|roughly)?\s*(?:t/s|tokens?/s|tokens?/sec|"
            r"tps|tk/s)\b", snippet, re.I)
        nstart = nm.start() if nm else 0
        nend = nm.end() if nm else len(snippet)
        i = max(snippet.rfind(". ", 0, nstart),
                snippet.rfind("! ", 0, nstart),
                snippet.rfind("? ", 0, nstart))
        if 0 < i < nstart:
            nstart -= i + 1
            nend -= i + 1
            snippet = snippet[i + 1:]
        j = min((x for x in (snippet.find(". ", nend),
                             snippet.find("! ", nend),
                             snippet.find("? ", nend)) if x > 0),
                default=-1)
        if 0 < j < len(snippet) - 1:
            snippet = snippet[:j + 1]
        snippet = snippet.strip()
        # Trim mid-word starts (the window cut inside a token, e.g.
        # "ised version ...") — but never past a number, and only past
        # words that are not ordinary English sentence starters.
        ok_start = (
            r"^(a|an|the|it|its|they|them|their|we|us|our|you|your|he|"
            r"she|i|me|my|his|her|who|what|which|when|where|why|how|"
            r"this|that|these|those|here|there|then|just|only|even|"
            r"still|about|roughly|nearly|almost|exactly|precisely|"
            r"simply|easily|quickly|smoothly|clearly|honestly|openly|"
            r"really|very|quite|pretty|kinda|sorta|some|any|all|each|"
            r"every|both|few|several|more|most|less|least|much|many|"
            r"one|two|three|four|five|six|seven|eight|nine|ten|"
            r"not|never|always|sometimes|often|rarely|now|new|fresh|"
            r"same|other|another|big|small|fast|slow|good|bad|great|"
            r"nice|whole|live|real|true|false|own|full|empty|total|"
            r"single|pure|flat|steady|stable|consistent|variable|"
            r"recent|currently|eventually|ultimately|initially|"
            r"basically|generally|typically|usually|immediately|"
            r"directly|indirectly|remotely|locally|globally|freely|"
            r"again|once|twice|alone|together|apart|aside|nearby|"
            r"first|second|third|fourth|next|last|final|main|primary|"
            r"old|older|newer|higher|lower|better|best|worse|worst|"
            r"larger|smaller|faster|slower|stronger|weaker|lighter|"
            r"heavier|thinner|narrower|wider|deeper|shallower|longer|"
            r"shorter|earlier|later|recently|presently|officially|"
            r"publicly|privately|for|to|in|on|at|by|with|from|out|"
            r"up|down|off|over|under|across|through|toward|towards|"
            r"against|behind|below|beneath|beside|besides|beyond|"
            r"inside|outside|within|without|around|along|between|"
            r"during|since|after|before|while|is|are|was|were|be|"
            r"been|being|do|does|did|can|could|will|would|should|"
            r"may|might|must|has|have|had|get|gets|got|go|goes|going|"
            r"gone|run|runs|ran|running|take|takes|took|taking|"
            r"make|makes|made|making|show|shows|showed|shown|hit|"
            r"hits|hit|top|tops|topped|reaching|reached|reach|pull|"
            r"pulls|pulled|push|pushes|pushed|spike|spikes|spiked|"
            r"drop|drops|dropped|dip|dips|dipped|slip|slips|slipped|"
            r"fall|falls|fell|rise|rises|rose|grow|grows|grew|"
            r"shrink|shrinks|shrank|expand|expands|expanded|"
            r"contract|contracts|improve|improves|improved|"
            r"degrade|degrades|optimized|optimize|optimizes|tune|"
            r"tunes|tuned|scale|scales|scaled|bump|bumps|bumped|"
            r"boost|boosts|boosted|cut|cuts|slashed|slash|raise|"
            r"raises|raised|lower|lowers|lowered|reduce|reduces|"
            r"reduced|increase|increases|increased|double|doubles|"
            r"doubled|halve|halves|halved|measure|measures|measured|"
            r"reading|read|reads|report|reports|reported|working|"
            r"work|works|worked|test|tests|tested|testing|check|"
            r"checks|checked|checking|average|averages|averaged|"
            r"peak|peaks|peaked|tick|ticks|ticked|climb|climbs|"
            r"climbed)[\s.,;:|—-]")
        while snippet:
            first_end = snippet.find(" ")
            first = (snippet[:first_end] if first_end != -1
                     else snippet).strip(" .,;|—-('\"")
            if (not first or first[0].isupper()
                    or re.search(r"\d", first)
                    or re.match(ok_start, snippet)):
                break
            if first_end == -1:
                break
            snippet = snippet[first_end + 1:].lstrip(" .,;|—-")
        snippet = snippet.strip(" .,;|—-")
        if snippet:
            out.append(snippet)
    return out


def _backend_is_own(text, name):
    """The backend is the poster's own when not used generically
    ("if you're just throwing llama.cpp at it")."""
    for m in re.finditer(re.escape(name), text, re.I):
        s = sentence_at(text, m.start())
        if re.search(r"throwing|crossing your fingers|you might want|"
                     r"if you're just", s, re.I):
            return False
    return True


def _extract_workload(text):
    """What the rig runs: model + backend + context + speed clusters."""
    parts = []
    model = _extract_model_name(text)
    backend = None
    for name, pat in BACKENDS:
        if re.search(pat, text, re.I) and _backend_is_own(text, name):
            backend = name
            break
    if model:
        parts.append(f"{model} via {backend}" if backend else model)
    ctx = _extract_context(text)
    if ctx:
        parts.append(f"{ctx} context")
    clusters = _speed_clusters(text)
    if clusters:
        joined = " ".join(clusters)
        # Don't repeat the backend when a part already names it.
        if backend and not any(
                re.search(re.escape(backend.lower()), p, re.I)
                for p in parts):
            joined = f"via {backend} — {joined}"
        parts.append(joined)
    if not parts:
        return None
    return " | ".join(dict.fromkeys(parts))[:240]


def _extract_rig_notes(lined, text, gpu_model, count):
    notes = []
    # secondary GPUs mentioned in prose (spares) — never from a
    # github-repo description wall (that text describes someone else's
    # optimization project, not this poster's hardware).
    primary_key = _gpu_key(gpu_model) if gpu_model else None
    for m in re.finditer(rf"{VENDOR_CAP}({GPU_MODEL_ALT})", text, re.I):
        key = _gpu_key(m.group(2))
        if key == primary_key:
            continue
        s = _clean_sentence(text, m.start())
        if s is None:
            continue
        # A github-repo description wall (pasted link text) describes
        # someone else's project, not this poster's hardware.
        i = text.find(s)
        window = (_prior_sentence(text, i) + " " + s) if i > 0 else s
        if re.search(r"\brepo\b|github|llm-stack", window, re.I):
            continue
        # A spare card is announced ("a spare RX5700 for funsies",
        # "also a ..."), not just mentioned — ownership alone is not
        # required for the note.
        if _window_ok(text, m.start()) or re.search(
                r"\bspare\b|\balso\b|\boccasionally\b|\bsecond\b|"
                r"\bbackup\b", s, re.I):
            notes.append(f"also {_vendor_model(m.group(1), m.group(2))}")
    # power draw
    m = re.search(r"(\d+)\s*w(?:atts?)?\s+at idle.*?(\d+)\s*w(?:atts?)?"
                  r"\s+under load", text, re.I)
    if m:
        notes.append(f"{m.group(1)}W idle / {m.group(2)}W under load")
    else:
        m = re.search(r"(?:measured|about|up to)\s+(\d+)\s*w(?:atts?)?\s+at "
                      r"idle", text, re.I)
        if m:
            notes.append(f"{m.group(1)}W at idle")
    # PSU
    m = re.search(r"(\d{3,4})\s+watt\s+([\w ]{0,20}psu|psu)", text, re.I)
    if m:
        notes.append(f"{m.group(1)}W PSU")
    return " | ".join(dict.fromkeys(notes))[:160] or None


def parse_rigs(data):
    """Extract rig items from the AI Rigs thread (two-pass).

    A post describing several machines (detected via multiple neofetch
    anchors) yields one item per machine.
    """
    results = []
    for post in extract_posts(data):
        full_text = strip_html(post.get("cooked", ""))
        if not is_rigs_relevant(full_text):
            continue
        own_cooked = remove_quotes(post.get("cooked", ""))
        own_text = strip_html(own_cooked)
        own_lined = strip_html(own_cooked, keep_newlines=True)

        segments = split_machines(own_text)
        lined_segments = _split_lined(own_lined, len(segments))

        for i, seg in enumerate(segments):
            seg_lined = lined_segments[i] if i < len(lined_segments) else seg
            gpu_model, gpu_count = _extract_rig_gpu(seg_lined, seg)
            vram = _extract_vram_total(seg, gpu_model, gpu_count)
            cpu = _extract_cpu(seg_lined, seg)
            ram = _extract_ram(seg)
            storage = _extract_storage(seg_lined, seg)
            os_name = _extract_os(seg_lined, seg)
            workload = _extract_workload(seg)
            notes = _extract_rig_notes(seg_lined, seg, gpu_model,
                                       gpu_count)

            structured = any(v is not None for v in
                             (gpu_model, vram, cpu, ram, storage, os_name))

            pn = post.get("post_number")
            results.append({
                "id": f"rigs_post_{pn}_{i}",
                "post_id": post.get("id"),
                "post_number": pn,
                "contributor": post.get("username"),
                "date": (post.get("created_at") or "")[:10],
                "gpu": {
                    "model": gpu_model,
                    "count": gpu_count,
                },
                "vram_total_gb": vram,
                "cpu": cpu,
                "ram_gb": ram,
                "storage": storage,
                "os": os_name,
                "workload": workload,
                "notes": notes,
                "preview": full_text[:PREVIEW_LEN],
                "structured": structured,
            })
    return results


# ---------------------------------------------------------------------------
# Category (unchanged — topic list only)
# ---------------------------------------------------------------------------

def parse_category(data):
    """Track new threads in the ML/AI category."""
    topics = data.get("topic_list", {}).get("topics", [])
    results = []
    for t in topics:
        results.append({
            "id": t.get("id"),
            "title": t.get("title"),
            "slug": t.get("slug"),
            "posts_count": t.get("posts_count"),
            "created_at": (t.get("created_at") or "")[:10],
            "last_posted_at": (t.get("last_posted_at") or "")[:10],
            "views": t.get("views"),
            "like_count": t.get("like_count"),
            "url": f"https://forum.level1techs.com/t/"
                   f"{t.get('slug', '')}/{t.get('id')}",
        })
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--thread", default="all",
                        help="Thread ID to parse (or 'all')")
    args = parser.parse_args()

    schema = load_json(SCHEMA)
    if schema is None:
        print(f"Missing schema: {SCHEMA}")
        return 1
    threads = schema.get("monitored_threads", [])

    if args.thread != "all":
        threads = [t for t in threads if t["id"] == args.thread]

    for thread in threads:
        tid = thread["id"]
        raw_path = DATA_DIR / "raw" / f"{tid}_latest.json"

        if not raw_path.exists():
            print(f"\u26a0\ufe0f  No data for '{tid}' ({raw_path}). "
                  f"Run pull.py first.")
            continue

        data = load_json(raw_path)
        if not data:
            continue

        print(f"\nParsing '{thread['name']}' ({tid})...")

        if tid == "crucible":
            results = parse_crucible(data)
            out_path = DATA_DIR / "benchmarks.json"
        elif tid == "rigs":
            results = parse_rigs(data)
            out_path = DATA_DIR / "hardware.json"
        elif tid == "category":
            results = parse_category(data)
            out_path = DATA_DIR / "category_threads.json"
        else:
            # The main thread is handled by parse.py, not here.
            continue

        structured = sum(1 for r in results if r.get("structured"))
        output = {
            "source": thread["name"],
            "thread_id": tid,
            "url": thread["url"].replace(".json", ""),
            "count": len(results),
            "items": results
        }

        with open(out_path, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"  \u2713 {len(results)} items ({structured} structured, "
              f"{len(results) - structured} preview-only) "
              f"\u2192 {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
