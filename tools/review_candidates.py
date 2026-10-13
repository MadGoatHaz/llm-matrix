#!/usr/bin/env python3
"""
review_candidates.py — list the conservative prose-only review candidates.

P1-5 (Layer 3) extracts real hardware/model info from *prose-only* forum
posts (no [COMMUNITY-SUBMISSION] markers, no unmarked structure) into
``data/candidates.json``. Those candidates are flagged ``unverified`` and are
NOT part of ``submissions.json`` or the site — they are a human-in-the-loop
queue for the curator (the maintainer) to review and promote.

This script prints each candidate with its source post and any high-confidence
fields that were extracted, so a curator can scan them quickly:

    python tools/review_candidates.py

Exit code is always 0 (it is a read-only listing tool, not a gate).
"""

import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
CANDIDATES = WORKSPACE / "data" / "candidates.json"


def main():
    if not CANDIDATES.exists():
        print("No candidates file. Run `python tools/parse.py` first.")
        return 0
    with open(CANDIDATES) as f:
        data = json.load(f)

    candidates = data.get("candidates", [])
    print("=" * 72)
    print(f"PROSE-ONLY REVIEW CANDIDATES  ({data.get('total_candidates', 0)} total)")
    print("=" * 72)
    print("These are UNVERIFIED — review the raw text, then promote the good\n"
          "ones into submissions (e.g. via tools/tags.json or a re-parse).\n")
    if not candidates:
        print("(none queued)")
        return 0

    for c in candidates:
        print(f"--- {c.get('id')}  [confidence: {c.get('confidence')}]")
        print(f"    post #{c.get('source_post')}  by  {c.get('source_user')}")
        fields = c.get("fields", {})
        if fields:
            for k in ("gpu", "vram_gb", "backend", "models"):
                if fields.get(k):
                    print(f"    {k:>8}: {fields[k]}")
        else:
            print("    fields:  (none extracted with high confidence)")
        raw = (c.get("raw_text") or "").strip()
        if len(raw) > 220:
            raw = raw[:220] + " …"
        print(f"    raw     : {raw}")
        print()
    print("To promote a candidate, add its fields to a [COMMUNITY-SUBMISSION]\n"
          "block (or tools/tags.json) and re-run the pipeline. Until then it\n"
          "stays out of submissions.json and the site.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
