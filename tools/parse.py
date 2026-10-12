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
    - Multi-model submissions separated by a `------` line are split and
      parsed as individual submissions.
    - Non-standard field names are aliased to canonical names.
    - Tier normalization matches most-specific patterns first (no substring
      false-positives like '16' matching inside '16-24').
    - List/bullet artifacts in values are cleaned.
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

# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------

def load_json(path):
    with open(path) as f:
        return json.load(f)

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
}

def apply_aliases(data):
    """Rename non-standard field names to their canonical equivalents."""
    for alias, canonical in FIELD_ALIASES.items():
        if alias in data and canonical not in data:
            data[canonical] = data.pop(alias)
        elif alias in data:
            del data[alias]
    return data

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

def extract_submissions_from_post(post):
    """Extract all submission blocks from a post's cooked HTML."""
    text = strip_html(post.get("cooked", ""))
    submissions = []

    # Full submissions
    for match in re.finditer(r'\[COMMUNITY-SUBMISSION\](.*?)\[\/COMMUNITY-SUBMISSION\]', text, re.DOTALL):
        block = match.group(1).strip()
        if not block:
            continue
        for sub_block in split_on_separator(block):
            submissions.append({
                "type": "full",
                "data": apply_aliases(parse_submission_block(sub_block))
            })

    # Quick submits
    for match in re.finditer(r'\[QUICK-SUBMIT\](.*?)\[\/QUICK-SUBMIT\]', text, re.DOTALL):
        block = match.group(1).strip()
        if not block:
            continue
        for sub_block in split_on_separator(block):
            submissions.append({
                "type": "quick",
                "data": apply_aliases(parse_submission_block(sub_block))
            })

    return submissions

# ---------------------------------------------------------------------------
# Template / placeholder detection
# ---------------------------------------------------------------------------

# Placeholder markers per core field. Each tuple is checked as a substring;
# a leading-bracket check on the raw value catches any unfilled `[...]` field.
TEMPLATE_MARKERS = {
    'model_name': ('[Full model',),
    'hardware': ('[e.g.,',),
    'backend': ('[vLLM |',),
    'tier': ('[≤16GB |',),
}
CORE_FIELDS = ('tier', 'hardware', 'backend', 'model_name')

def is_template_submission(data_dict):
    """Return True if the submission is clearly an unfilled template."""
    for field, markers in TEMPLATE_MARKERS.items():
        v = str(data_dict.get(field, '') or '')
        if v.startswith('[') or any(m in v for m in markers):
            return True
    # All core fields empty -> nothing was actually filled in.
    if not any(str(data_dict.get(f, '') or '').strip() for f in CORE_FIELDS):
        return True
    return False

# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def infer_vendor(hardware_str):
    """Infer hardware vendor from description string."""
    s = hardware_str.lower()
    if 'nvidia' in s or 'rtx' in s or 'geforce' in s or 'a100' in s or 'h100' in s or 'quadro' in s or 'rtx 50' in s:
        return "NVIDIA"
    if 'amd' in s or 'r9700' in s or 'r9600' in s or 'mi210' in s or 'mi250' in s or 'mi300' in s or 'radeon' in s or 'rx 7' in s or 'w7900' in s or 'v620' in s:
        return "AMD"
    if 'apple' in s or 'mac' in s or 'm1' in s or 'm2' in s or 'm3' in s or 'm4' in s or 'mlx' in s:
        return "Apple"
    if 'intel' in s:
        return "Intel"
    return "Mixed"

def normalize_tier(tier_str):
    """Normalize tier strings to match schema.

    Checks most-specific (longest) patterns first so e.g. '16-24' is not
    matched by the bare '16' substring.
    """
    if not tier_str:
        return None
    s = tier_str.lower().replace('gb', '').replace('+', '').strip()
    # Check most specific (longest) patterns first
    ordered_checks = [
        ('196-256', 't6'), ('192-256', 't6'), ('256', 't6'),
        ('128-196', 't5'), ('96-128', 't5'), ('96-96', 't5'),
        ('48-96', 't4'), ('48-64', 't4'), ('32-64', 't4'),
        ('24-32', 't3'), ('16-24', 't2'),
        ('≤16', 't1'), ('<=16', 't1'),
    ]
    for pattern, tid in ordered_checks:
        if pattern in s:
            return tid
    # Fallback: single number
    for num, tid in [('16', 't1'), ('24', 't3'), ('48', 't4'), ('96', 't5'), ('128', 't5'), ('196', 't6'), ('256', 't6')]:
        if s == num or s.startswith(num):
            return tid
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
    warnings = []
    skipped_templates = 0

    for post in posts:
        post_num = post.get("post_number", 0)
        username = post.get("username", "unknown")

        subs = extract_submissions_from_post(post)

        for i, sub in enumerate(subs):
            # Skip unfilled template/placeholder submissions entirely.
            if is_template_submission(sub["data"]):
                skipped_templates += 1
                continue

            entry = {
                "id": f"post_{post_num}_{username.lower()}_{i}",
                "source": {
                    "post_number": post_num,
                    "post_id": post.get("id"),
                    "username": username,
                    "submitted_at": post.get("created_at", "")
                },
                "type": sub["type"],
                "raw": sub["data"],
                # Parsed/normalized fields
                "tier": normalize_tier(sub["data"].get("tier", "")),
                "hardware": {
                    "description": sub["data"].get("hardware", ""),
                    "vendor": infer_vendor(sub["data"].get("hardware", ""))
                },
                "backend": sub["data"].get("backend", ""),
                "model": {
                    "name": sub["data"].get("model_name", ""),
                    "url": sub["data"].get("download_url", "")
                },
                "quant": sub["data"].get("quant_package", ""),
                "weight_precision": sub["data"].get("weight_precision", ""),
                "use_cases": sub["data"].get("primary_use_case", ""),
                "context": {
                    "stable": sub["data"].get("stable_context_tested", ""),
                    "kv_cache": sub["data"].get("kv_cache_setting", "")
                },
                "performance": {
                    "decode_tps": sub["data"].get("throughput_tps", ""),
                    "prefill_tps": sub["data"].get("prefill_tps", ""),
                    "ttft_cold": sub["data"].get("ttft_cold", ""),
                    "power_w": sub["data"].get("power_draw", "")
                },
                "engine_mode": sub["data"].get("engine_mode", ""),
                "notes": sub["data"].get("setup_notes", ""),
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

            submissions.append(entry)

            # Warnings
            if not entry["tier"]:
                warnings.append(f"Post #{post_num} ({username}): Could not normalize tier from '{sub['data'].get('tier', 'N/A')}'")
            if not entry["backend"]:
                warnings.append(f"Post #{post_num} ({username}): No backend specified")

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

    # Summary
    print(f"✓ Parsed {len(submissions)} real submissions from {len(posts)} posts")
    print(f"✓ Skipped {skipped_templates} template/placeholder submission(s)")
    print(f"✓ Output: {OUTPUT}")

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
