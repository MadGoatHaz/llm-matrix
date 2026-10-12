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

def extract_submissions(cooked):
    """Find all submission blocks in cooked HTML."""
    import re
    # Strip HTML tags to get plain text for parsing
    text = re.sub(r'<[^>]+>', ' ', cooked)
    text = re.sub(r'\s+', ' ', text)
    blocks = []
    # Find [COMMUNITY-SUBMISSION] ... [/COMMUNITY-SUBMISSION]
    for match in re.finditer(r'\[COMMUNITY-SUBMISSION\](.*?)\[\/COMMUNITY-SUBMISSION\]', text, re.DOTALL):
        blocks.append(match.group(1).strip())
    # Find [QUICK-SUBMIT] ... [/QUICK-SUBMIT]
    for match in re.finditer(r'\[QUICK-SUBMIT\](.*?)\[\/QUICK-SUBMIT\]', text, re.DOTALL):
        blocks.append(match.group(1).strip())
    return blocks

def main():
    if not LATEST.exists():
        print("No data yet. Run `python tools/pull.py` first.")
        sys.exit(1)

    latest = load_json(LATEST)
    prev = load_json(LAST_SEEN)

    if prev is None:
        print("=== FIRST RUN — No previous state ===\n")
        print("All posts are new. Here's what's in the thread:\n")
        posts = get_posts(latest)
        for pid, post in sorted(posts.items(), key=lambda x: x[1]["post_number"]):
            subs = extract_submissions(post.get("cooked", ""))
            marker = f" [{len(subs)} submission(s)]" if subs else ""
            print(f"  #{post['post_number']:>2} {post['username']:<20} {post['created_at'][:10]}{marker}")
        # Save as baseline
        shutil.copy2(LATEST, LAST_SEEN)
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

    # Update last_seen
    shutil.copy2(LATEST, LAST_SEEN)
    print(f"\n✓ State updated. Next diff will be against this snapshot.")

if __name__ == "__main__":
    main()
