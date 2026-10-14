#!/usr/bin/env python3
"""
diff.py — Show what's new/changed since the last seen state.

Usage:
    python tools/diff.py

E5: covers ALL monitored threads (main, crucible, rigs, category) — before,
only the main thread, so changes in the secondary threads were invisible to
the "what changed this week" report.

For each thread it compares the fresh pull (data/raw/{thread}_latest.json;
data/raw/latest.json for main, the backfilled copy) against the PER-THREAD
state stored in data/last_seen.json:

    {
      "main":     { ...full thread mirror... },
      "crucible": { ... },
      "rigs":     { ... },
      "category": { ... },
      "previous_count": N   # A1 wipe-guard baseline (owned by validate.py)
    }

Topic threads (main / crucible / rigs) track posts (keyed by id; a changed
updated_at = updated). The category feed tracks topics (keyed by id; a
changed last_posted_at = updated). The "no changes" condition is NO changes
in ANY thread. The state file is rewritten after the run (the previous_count
baseline is carried across).

A pre-E5 state file (a bare main-thread mirror) is migrated on first use:
the old content is wrapped under "main" and the other three threads are
seeded from the current mirrors, so a quiet week stays quiet — no
whole-thread history re-reported as "new".

This is your "what do I need to look at this week?" tool.
"""

import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
RAW_DIR = WORKSPACE / "data" / "raw"
LATEST = RAW_DIR / "latest.json"
LAST_SEEN = WORKSPACE / "data" / "last_seen.json"

#: The monitored threads, in report order (schema.json monitored_threads).
THREADS = ("main", "crucible", "rigs", "category")


def load_json(path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def raw_mirror(workspace, tid):
    """The raw mirror path for a thread.

    main has two names: ``main_latest.json`` (pull.py's canonical output) and
    ``latest.json`` (the backfilled copy the rest of the pipeline reads) —
    either satisfies the diff.
    """
    raw = Path(workspace) / "data" / "raw"
    p = raw / f"{tid}_latest.json"
    if not p.exists() and tid == "main":
        p = raw / "latest.json"
    return p


def get_posts(data):
    return {p["id"]: p for p in (data or {}).get("post_stream", {}).get("posts", [])}


def get_topics(data):
    """The category feed's topics, keyed by id (it has no post_stream)."""
    out = {}
    for t in (data or {}).get("topic_list", {}).get("topics", []):
        if t.get("id") is not None:
            out[t["id"]] = t
    return out


def topic_changed_at(t):
    """A category topic's last-change stamp (topics carry no updated_at)."""
    return t.get("last_posted_at") or t.get("bumped_at") or t.get("created_at") or ""


# ---------------------------------------------------------------------------
# Per-thread comparison
# ---------------------------------------------------------------------------

def diff_topic(prev_data, latest_data):
    """(new, updated, removed) posts for a topic thread (post_stream)."""
    prev_posts = get_posts(prev_data)
    latest_posts = get_posts(latest_data)
    new = [p for pid, p in latest_posts.items() if pid not in prev_posts]
    updated = [
        (prev_posts[pid], p)
        for pid, p in latest_posts.items()
        if pid in prev_posts and p.get("updated_at") != prev_posts[pid].get("updated_at")
    ]
    removed = [p for pid, p in prev_posts.items() if pid not in latest_posts]
    return new, updated, removed


def diff_category(prev_data, latest_data):
    """(new, updated, removed) topics for the category feed."""
    prev_topics = get_topics(prev_data)
    latest_topics = get_topics(latest_data)
    new = [t for tid, t in latest_topics.items() if tid not in prev_topics]
    updated = [
        (prev_topics[tid], t)
        for tid, t in latest_topics.items()
        if tid in prev_topics and topic_changed_at(t) != topic_changed_at(prev_topics[tid])
    ]
    removed = [t for tid, t in prev_topics.items() if tid not in latest_topics]
    return new, updated, removed


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


# ---------------------------------------------------------------------------
# State (per-thread) build + save
# ---------------------------------------------------------------------------

def build_state(workspace, prev_count=None, carry=None):
    """The per-thread last-seen state from the CURRENT raw mirrors (E5).

    A thread with no mirror keeps its previous state (``carry``) — a partial
    pull must never wipe a thread's history. ``prev_count`` (the A1 wipe-guard
    baseline, stamped by validate.py after a clean pass) is carried over the
    rewrite so the next run's submission-drop check compares against the last
    known-good state.
    """
    ws = Path(workspace)
    state = {}
    for tid in THREADS:
        mirror = raw_mirror(ws, tid)
        if mirror.exists():
            state[tid] = load_json(mirror)
        elif carry and tid in carry:
            state[tid] = carry[tid]
    if prev_count is not None:
        state["previous_count"] = prev_count
    return state


def save_state(workspace, state):
    """Write the per-thread state to data/last_seen.json."""
    path = Path(workspace) / "data" / "last_seen.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
    return path


def refresh_baseline(workspace=None, prev_count=None, carry=None):
    """(Pre-E5 name, kept for compatibility) rewrite data/last_seen.json from
    the fresh pull, carrying the A1 drop-guard baseline across."""
    ws = Path(workspace) if workspace is not None else WORKSPACE
    save_state(ws, build_state(ws, prev_count, carry=carry))


def migrate_state(state, workspace):
    """Wrap a pre-E5 state file (a BARE main-thread mirror) into the
    per-thread shape: the old content becomes "main" and the other three
    threads are seeded from the current mirrors — so a quiet week stays
    quiet (no whole-thread history re-reported as "new")."""
    migrated = {"main": state}
    for tid in THREADS[1:]:
        mirror = raw_mirror(workspace, tid)
        if mirror.exists():
            migrated[tid] = load_json(mirror)
    return migrated


# ---------------------------------------------------------------------------
# Detail rendering
# ---------------------------------------------------------------------------

def _print_main_details(new, updated, removed):
    """The main thread's traditional detailed output (submission previews)."""
    if new:
        print("🆕 MAIN — NEW POSTS:")
        for post in sorted(new, key=lambda x: x["post_number"]):
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

    if updated:
        print("\n✏️ MAIN — UPDATED POSTS:")
        for old, newp in updated:
            print(f"  #{newp['post_number']} by {newp['username']} (was {old['updated_at'][:16]}, now {newp['updated_at'][:16]})")

    if removed:
        print("\n🗑️ MAIN — REMOVED POSTS:")
        for post in removed:
            print(f"  #{post['post_number']} by {post['username']}")


def _print_secondary_details(tid, new, updated, removed):
    """Compact per-item lists for crucible / rigs (posts) and category
    (topics)."""
    label = tid.capitalize()
    if tid == "category":
        if new:
            print(f"🆕 {label} — NEW TOPICS:")
            for t in sorted(new, key=lambda x: x.get("created_at") or ""):
                print(f"  #{t['id']} {t.get('title', '')[:70]} (created {t.get('created_at', '')[:10]})")
        if updated:
            print(f"\n✏️ {label} — UPDATED TOPICS:")
            for old, t in updated:
                print(f"  #{t['id']} {t.get('title', '')[:70]} (last posted {topic_changed_at(old)[:16]} -> {topic_changed_at(t)[:16]})")
        if removed:
            print(f"\n🗑️ {label} — REMOVED TOPICS:")
            for t in removed:
                print(f"  #{t['id']} {t.get('title', '')[:70]}")
    else:
        if new:
            print(f"🆕 {label} — NEW POSTS:")
            for post in sorted(new, key=lambda x: x.get("post_number", 0)):
                print(f"  #{post['post_number']} by {post.get('username', '')} ({post.get('created_at', '')[:10]})")
        if updated:
            print(f"\n✏️ {label} — UPDATED POSTS:")
            for old, newp in updated:
                print(f"  #{newp.get('post_number', '')} by {newp.get('username', '')} (was {old.get('updated_at', '')[:16]}, now {newp.get('updated_at', '')[:16]})")
        if removed:
            print(f"\n🗑️ {label} — REMOVED POSTS:")
            for post in removed:
                print(f"  #{post.get('post_number', '')} by {post.get('username', '')}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(workspace=None):
    ws = Path(workspace) if workspace is not None else WORKSPACE
    last_seen_path = ws / "data" / "last_seen.json"

    if not raw_mirror(ws, "main").exists():
        print("No data yet. Run `python tools/pull.py` first.")
        return 1

    state = load_json(last_seen_path)

    # A1: the drop-guard baseline to carry over the refresh (None on a first
    # run or a pre-A1 state file).
    prev_count = None
    if isinstance(state, dict):
        # E5 migration: a pre-E5 state file is a BARE main-thread mirror
        # (top-level post_stream) with previous_count at the top level. Wrap
        # it under "main", re-home the baseline, and seed the other threads.
        if "post_stream" in state and "main" not in state:
            prev_count = state.pop("previous_count", None)
            state = migrate_state(state, ws)
            if prev_count is not None:
                state["previous_count"] = prev_count
        else:
            prev_count = state.get("previous_count")

    if state is None:
        print("=== FIRST RUN — No previous state ===\n")
        print("All posts are new. Here's what's in the thread:\n")
        posts = get_posts(load_json(raw_mirror(ws, "main")))
        for pid, post in sorted(posts.items(), key=lambda x: x[1]["post_number"]):
            subs = extract_submissions(post.get("cooked", ""))
            marker = f" [{len(subs)} submission(s)]" if subs else ""
            print(f"  #{post['post_number']:>2} {post['username']:<20} {post['created_at'][:10]}{marker}")
        # Save as baseline (all threads from the current mirrors).
        save_state(ws, build_state(ws, prev_count))
        print(f"\n✓ Saved baseline state to {last_seen_path}")
        return 0

    # --- Per-thread comparison -------------------------------------------
    print("=== PER-THREAD DIFF ===")
    per_thread = {}
    total_new = total_updated = total_removed = 0
    for tid in THREADS:
        mirror = raw_mirror(ws, tid)
        if not mirror.exists():
            # No fresh mirror this run (the pull failed for this thread):
            # report it as unchanged and keep its previous state.
            per_thread[tid] = (0, 0, 0, None)
            print(f"{tid.capitalize()}: no mirror this run — state kept")
            continue
        latest_data = load_json(mirror)
        prev_data = state.get(tid)
        if tid == "category":
            new, updated, removed = diff_category(prev_data, latest_data)
        else:
            new, updated, removed = diff_topic(prev_data, latest_data)
        if prev_data is None:
            # First time seeing this thread (a newly monitored one):
            # baseline it — everything is "new", but that is a baseline
            # event, not a change to act on.
            per_thread[tid] = (0, 0, 0, (new, updated, removed))
            print(f"{tid.capitalize()}: first seen — {len(new)} item(s) baselined")
            continue
        total_new += len(new)
        total_updated += len(updated)
        total_removed += len(removed)
        per_thread[tid] = (len(new), len(updated), len(removed), (new, updated, removed))
        print(f"{tid.capitalize()}: {len(new)} new, {len(updated)} updated, {len(removed)} removed")

    print(f"Total: {total_new} new, {total_updated} updated, {total_removed} removed")

    # --- Details ----------------------------------------------------------
    for tid in THREADS:
        detail = per_thread[tid][3]
        if detail is None:
            continue
        new, updated, removed = detail
        if tid == "main":
            _print_main_details(new, updated, removed)
        else:
            _print_secondary_details(tid, new, updated, removed)

    # E5: the "no changes" condition is NO changes in ANY thread.
    if total_new == 0 and total_updated == 0 and total_removed == 0:
        print("\n  (no changes)")

    # Update last_seen (per-thread state; carrying the A1 drop-guard baseline)
    save_state(ws, build_state(ws, prev_count, carry=state))
    print(f"\n✓ State updated ({', '.join(THREADS)}). Next diff will be against this snapshot.")
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(
        description="Show what's new/changed in ALL monitored threads "
                    "since the last seen state")
    ap.add_argument("workspace", nargs="?", default=None,
                    help="Repo-root override (tests; default: this checkout)")
    args = ap.parse_args()
    sys.exit(main(args.workspace))
