#!/usr/bin/env python3
"""
pull.py — Fetch LLM Matrix thread JSON from Discourse (single or multi-thread).

Usage:
    python tools/pull.py                      # Pull ALL monitored threads (default)
    python tools/pull.py --thread all        # Pull all monitored threads
    python tools/pull.py --thread crucible   # Pull one specific thread
    python tools/pull.py --url "https://..." # Single-URL fallback (legacy behavior)
    python tools/pull.py --file data/raw/x.json  # Import a local file

Reads:
    tools/schema.json  (monitored_threads config)

Output:
    data/raw/{thread_id}_latest.json   (per monitored thread, e.g. main_latest.json)
    data/raw/latest.json               (copy of the main thread, backward compat)
    Prints a summary table: per-thread post/topic counts + file sizes
"""

import argparse
import json
import shutil
import sys
import urllib.request
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
RAW_DIR = WORKSPACE / "data" / "raw"
SCHEMA = WORKSPACE / "tools" / "schema.json"

DEFAULT_URL = "https://forum.level1techs.com/t/256443.json"

# Browser-like User-Agent to avoid Discourse 403 bot-protection on plain urllib.
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def load_json(path):
    with open(path) as f:
        return json.load(f)


def fetch_url(url):
    """Fetch JSON from URL with a browser User-Agent (avoids 403 bot-block)."""
    print(f"Fetching: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data


def import_file(filepath):
    """Import a local JSON file."""
    print(f"Importing: {filepath}")
    with open(filepath, "r") as f:
        return json.load(f)


def summarize(data):
    """Inspect a Discourse payload and return (label, count, size_bytes).

    Topics (main/crucible/rigs) carry post_stream.posts.
    Categories (category) carry topic_list.topics.
    """
    size = len(json.dumps(data))
    posts = data.get("post_stream", {}).get("posts", [])
    if posts:
        return "posts", len(posts), size
    topics = data.get("topic_list", {}).get("topics", [])
    if topics:
        return "topics", len(topics), size
    return "items", 0, size


def save_thread(thread, data):
    """Save a thread's JSON to data/raw/{id}_latest.json.

    Returns (path, label, count, size_bytes).
    """
    tid = thread["id"]
    out_path = RAW_DIR / f"{tid}_latest.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    label, count, size = summarize(data)
    return out_path, label, count, size


def backfill_latest(source_path):
    """Keep data/raw/latest.json as a copy of the given source (main thread)."""
    if not source_path.exists():
        print(f"  (no {source_path.name} to backfill latest.json from; left untouched)")
        return
    latest_path = RAW_DIR / "latest.json"
    shutil.copy2(source_path, latest_path)
    print(f"\u2713 Backfilled latest.json \u2190 {source_path.name}")


def _single_pull(label_src, data):
    """Legacy single-URL/file path: save as main + backfill latest + summarize."""
    out_path, lbl, count, size = save_thread({"id": "main", "url": label_src}, data)
    backfill_latest(out_path)
    print(f"\n\u2713 Saved: {out_path}")
    print(f"Summary: {count} {lbl} ({size / 1024:.1f} KB)")


def main():
    parser = argparse.ArgumentParser(description="Pull LLM Matrix thread data (multi-thread)")
    parser.add_argument("--thread", default="all",
                        help="Thread ID from schema.json monitored_threads (or 'all'). Default: all")
    parser.add_argument("--url", default=DEFAULT_URL,
                        help="Single-URL fallback: pull one URL directly (legacy behavior)")
    parser.add_argument("--file", help="Import from a local file instead of URL")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # ---- Legacy fallbacks: explicit --file or non-default --url ----
    if args.file:
        _single_pull(args.file, import_file(args.file))
        return
    if args.url != DEFAULT_URL:
        _single_pull(args.url, fetch_url(args.url))
        return

    # ---- Multi-thread mode: read monitored_threads from schema.json ----
    schema = load_json(SCHEMA)
    threads = schema.get("monitored_threads", [])
    if not threads:
        print("No monitored_threads in schema.json. Falling back to default URL.")
        _single_pull(DEFAULT_URL, fetch_url(DEFAULT_URL))
        return

    if args.thread != "all":
        selected = [t for t in threads if t["id"] == args.thread]
        if not selected:
            known = ", ".join(t["id"] for t in threads)
            print(f"Unknown thread '{args.thread}'. Known threads: {known}")
            sys.exit(1)
        threads = selected

    results = []
    for thread in threads:
        tid = thread["id"]
        print(f"\n[{tid}] {thread['name']}")
        try:
            data = fetch_url(thread["url"])
            out_path, label, count, size = save_thread(thread, data)
            results.append((tid, thread["name"], label, count, size, out_path.name, None))
        except Exception as e:
            results.append((tid, thread["name"], None, 0, 0, None, str(e)))

    # Backward compat: keep data/raw/latest.json as a copy of the main thread.
    backfill_latest(RAW_DIR / "main_latest.json")

    # Summary table
    print("\n" + "=" * 64)
    print("PULL SUMMARY")
    print("=" * 64)
    for tid, name, label, count, size, fname, err in results:
        if err:
            print(f"  \u2717 {tid:<10} {name[:34]:<36} ERROR: {err}")
        else:
            print(f"  \u2713 {tid:<10} {count:>4} {label:<6} {size / 1024:8.1f} KB  {fname}")
    print("=" * 64)


if __name__ == "__main__":
    main()
