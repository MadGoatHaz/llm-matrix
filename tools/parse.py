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

def parse_submission_block(block_text):
    """Parse a [COMMUNITY-SUBMISSION] or [QUICK-SUBMIT] block into a dict."""
    data = {}
    lines = block_text.split('\n')
    current_key = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Match "key: value"
        match = re.match(r'^(\w+[^:]*):\s*(.*)', line)
        if match:
            current_key = match.group(1).strip().lower().replace(' ', '_')
            value = match.group(2).strip()
            # Handle multi-line values (lists in brackets)
            if value.startswith('[') and ']' not in value:
                data[current_key] = [value]
            elif value:
                data[current_key] = value
            else:
                data[current_key] = ""
        elif current_key and data.get(current_key) == "":
            # Continuation of empty value
            data[current_key] = line
        elif current_key and isinstance(data.get(current_key), list):
            # Continuing a list
            if line.startswith('[') and ']' in line:
                data[current_key] = line
            elif line.startswith('*') or line.startswith('-'):
                data[current_key].append(line.lstrip('*- '))
            elif ']' in line:
                data[current_key].append(line.rstrip(']'))
                data[current_key] = ', '.join(data[current_key])
                current_key = None
            else:
                data[current_key].append(line)

    # Clean up list values that weren't closed
    for key, val in data.items():
        if isinstance(val, list):
            data[key] = ', '.join(val)

    return data

def extract_submissions_from_post(post):
    """Extract all submission blocks from a post's cooked HTML."""
    text = strip_html(post.get("cooked", ""))
    submissions = []

    # Full submissions
    for match in re.finditer(r'\[COMMUNITY-SUBMISSION\](.*?)\[\/COMMUNITY-SUBMISSION\]', text, re.DOTALL):
        block = match.group(1).strip()
        if block:
            submissions.append({
                "type": "full",
                "data": parse_submission_block(block)
            })

    # Quick submits
    for match in re.finditer(r'\[QUICK-SUBMIT\](.*?)\[\/QUICK-SUBMIT\]', text, re.DOTALL):
        block = match.group(1).strip()
        if block:
            submissions.append({
                "type": "quick",
                "data": parse_submission_block(block)
            })

    return submissions

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
    """Normalize tier strings to match schema."""
    if not tier_str:
        return None
    s = tier_str.lower().replace('gb', '').replace('+', '').strip()
    # Map various formats to our tier IDs
    tier_map = {
        '≤16': 't1', '<=16': 't1', '16': 't1',
        '16-24': 't2',
        '24-32': 't3', '24': 't3',
        '32-64': 't4', '48-64': 't4', '48': 't4', '64': 't4',
        '48-96': 't4', '96-128': 't5', '96': 't5', '128': 't5',
        '196-256': 't6', '192-256': 't6', '256': 't6', '128-196': 't5',
    }
    for key, tid in tier_map.items():
        if key in s:
            return tid
    return None

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

    for post in posts:
        post_num = post.get("post_number", 0)
        username = post.get("username", "unknown")
        cooked = post.get("cooked", "")

        subs = extract_submissions_from_post(post)

        for i, sub in enumerate(subs):
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

    # Write output
    output = {
        "generated_at": datetime.now().isoformat(),
        "schema_version": schema.get("version", "unknown"),
        "source_thread": "https://forum.level1techs.com/t/256443",
        "total_submissions": len(submissions),
        "submissions": submissions
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, 'w') as f:
        json.dump(output, f, indent=2)

    # Summary
    print(f"✓ Parsed {len(submissions)} submissions from {len(posts)} posts")
    print(f"✓ Output: {OUTPUT}")

    # Tier distribution
    tier_counts = {}
    for s in submissions:
        t = s["tier"] or "unclassified"
        tier_counts[t] = tier_counts.get(t, 0) + 1
    print(f"\nTier distribution:")
    for t in sorted(tier_counts.keys()):
        print(f"  {t}: {tier_counts[t]}")

    # Vendor distribution
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
