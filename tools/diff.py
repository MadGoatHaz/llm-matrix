#!/usr/bin/env python3
"""
diff.py — Show what's new/changed since the last seen state.

Usage:
    python tools/diff.py

Compares data/raw/latest.json against data/last_seen.json.
Shows: new posts, new submission blocks, edited posts.
Updates data/last_seen.json after run.

This is your "what do I need to look at this week?" tool.
"""

import json
import shutil
import sys
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
RAW_DIR = WORKSPACE / "data" / "raw"
LATEST = RAW_DIR / "latest.json"
LAST_SEEN = WORKSPACE / "data" / "last_seen.json"

def load_json(path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)

def get_posts(data):
    return {p["id"]: p for p in data.get("post_stream", {}).get("posts", [])}

def refresh_baseline(prev_count=None):
    """Refresh data/last_seen.json from the fresh pull (data/raw/latest.json).

    A1 wipe guard: the ``previous_count`` baseline (the last *validated*
    submission count, stamped by validate.py after a clean pass) is carried
    over the refresh so the next run's submission-drop check can compare
    against the last known-good state. With no baseline to carry (first run,
    or a pre-A1 state file) the copy is byte-identical to before.
    """
    shutil.copy2(LATEST, LAST_SEEN)
    if prev_count is None:
        return
    data = load_json(LAST_SEEN)
    data["previous_count"] = prev_count
    with open(LAST_SEEN, "w") as f:
        json.dump(data, f, indent=2)

def extract_submissions(cooked):
    """Find all submission blocks in cooked HTML.

    Matches both the standard bracketed markers ([COMMUNITY-SUBMISSION] ...
    [/COMMUNITY-SUBMISSION]) and bare marker lines (user variants where the
    marker sits alone on a line, e.g. inside <div class="math">). Line
    structure is preserved (br -> newline) so the bare-line patterns work.
    """
    import re
    text = re.sub(r'<br\s*/?>', '\n', cooked)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    blocks = []
    patterns = (
        r'\[COMMUNITY-SUBMISSION\](.*?)\[\/COMMUNITY-SUBMISSION\]',
        r'(?m)^\s*COMMUNITY-SUBMISSION\s*$(.*?)^\s*/?COMMUNITY-SUBMISSION\s*$',
        r'\[QUICK-SUBMIT\](.*?)\[\/QUICK-SUBMIT\]',
        r'(?m)^\s*QUICK-SUBMIT\s*$(.*?)^\s*/?QUICK-SUBMIT\s*$',
    )
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.DOTALL):
            b = match.group(1).strip()
            if b:
                blocks.append(b)
    return blocks

def main():
    if not LATEST.exists():
        print("No data yet. Run `python tools/pull.py` first.")
        sys.exit(1)

    latest = load_json(LATEST)
    prev = load_json(LAST_SEEN)

    # A1: the drop-guard baseline to carry over the refresh (None on a
    # first run or a pre-A1 state file).
    prev_count = prev.get("previous_count") if isinstance(prev, dict) else None

    if prev is None:
        print("=== FIRST RUN — No previous state ===\n")
        print("All posts are new. Here's what's in the thread:\n")
        posts = get_posts(latest)
        for pid, post in sorted(posts.items(), key=lambda x: x[1]["post_number"]):
            subs = extract_submissions(post.get("cooked", ""))
            marker = f" [{len(subs)} submission(s)]" if subs else ""
            print(f"  #{post['post_number']:>2} {post['username']:<20} {post['created_at'][:10]}{marker}")
        # Save as baseline
        refresh_baseline(prev_count)
        print(f"\n✓ Saved baseline state to {LAST_SEEN}")
        return

    prev_posts = get_posts(prev)
    latest_posts = get_posts(latest)

    new_posts = []
    updated_posts = []
    removed_posts = []

    for pid, post in latest_posts.items():
        if pid not in prev_posts:
            new_posts.append(post)
        else:
            # Check if updated
            if post.get("updated_at") != prev_posts[pid].get("updated_at"):
                updated_posts.append((prev_posts[pid], post))

    for pid in prev_posts:
        if pid not in latest_posts:
            removed_posts.append(prev_posts[pid])

    # Output
    print(f"=== DIFF: {len(new_posts)} new, {len(updated_posts)} updated, {len(removed_posts)} removed ===\n")

    if new_posts:
        print("🆕 NEW POSTS:")
        for post in sorted(new_posts, key=lambda x: x["post_number"]):
            subs = extract_submissions(post.get("cooked", ""))
            print(f"\n  #{post['post_number']} by {post['username']} ({post['created_at'][:16]})")
            if subs:
                print(f"     Contains {len(subs)} submission block(s)")
                for i, sub in enumerate(subs):
                    # Show first 200 chars of each submission
                    preview = sub[:200] + "..." if len(sub) > 200 else sub
                    print(f"     [{i+1}] {preview}")
            else:
                # Show first 150 chars of cooked (stripped)
                import re
                text = re.sub(r'<[^>]+>', ' ', post.get("cooked", ""))
                text = re.sub(r'\s+', ' ', text).strip()
                preview = text[:150] + "..." if len(text) > 150 else text
                print(f"     \"{preview}\"")

    if updated_posts:
        print(f"\n✏️ UPDATED POSTS:")
        for old, new in updated_posts:
            print(f"  #{new['post_number']} by {new['username']} (was {old['updated_at'][:16]}, now {new['updated_at'][:16]})")

    if removed_posts:
        print(f"\n🗑️ REMOVED POSTS:")
        for post in removed_posts:
            print(f"  #{post['post_number']} by {post['username']}")

    if not new_posts and not updated_posts and not removed_posts:
        print("  (no changes)")

    # Update last_seen (carrying the A1 drop-guard baseline across)
    refresh_baseline(prev_count)
    print(f"\n✓ State updated. Next diff will be against this snapshot.")

if __name__ == "__main__":
    main()
