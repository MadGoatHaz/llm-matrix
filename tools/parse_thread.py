#!/usr/bin/env python3
"""
parse_thread.py — Parse secondary monitored threads.

Usage:
    python tools/parse_thread.py            # Parse all monitored threads
    python tools/parse_thread.py --thread crucible  # Parse one specific

Reads:
    data/raw/{thread_id}_latest.json
    tools/schema.json (for monitored_threads config)

Writes:
    data/benchmarks.json
    data/hardware.json
    data/category_threads.json
"""

import json
import argparse
import re
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
DATA_DIR = WORKSPACE / "data"
SCHEMA = WORKSPACE / "tools" / "schema.json"

def load_json(path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)

def extract_posts(data):
    """Get list of posts from a Discourse thread JSON."""
    return data.get("post_stream", {}).get("posts", [])

def strip_html(cooked):
    text = re.sub(r'<[^>]+>', ' ', cooked)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_crucible(data):
    """Extract benchmark data from the Crucible thread."""
    results = []
    for post in extract_posts(data):
        text = strip_html(post.get("cooked", ""))
        # Look for performance numbers
        has_bench = any(x in text.lower() for x in ['ttft', 'tok/s', 'tokens/sec', 'latency', 'throughput', 'prefill', 'decode'])
        if has_bench:
            results.append({
                "post_number": post.get("post_number"),
                "username": post.get("username"),
                "date": post.get("created_at", "")[:10],
                "title": post.get("title", ""),
                "preview": text[:300],
                "has_benchmark_data": True
            })
    return results

def parse_rigs(data):
    """Extract hardware configs from the AI Rig thread."""
    results = []
    for post in extract_posts(data):
        text = strip_html(post.get("cooked", ""))
        # Look for hardware mentions
        has_hardware = any(x in text.lower() for x in ['rtx', 'r9700', 'mi300', 'a100', 'h100', '5090', '4090', '3090', 'rx 7', 'radeon', 'gpu', 'vram'])
        if has_hardware:
            results.append({
                "post_number": post.get("post_number"),
                "username": post.get("username"),
                "date": post.get("created_at", "")[:10],
                "title": post.get("title", ""),
                "preview": text[:300],
                "has_hardware": True
            })
    return results

def parse_category(data):
    """Track new threads in the ML/AI category."""
    # Category JSON structure is different - it has a list of topics
    topics = data.get("topic_list", {}).get("topics", [])
    results = []
    for t in topics:
        results.append({
            "id": t.get("id"),
            "title": t.get("title"),
            "slug": t.get("slug"),
            "posts_count": t.get("posts_count"),
            "created_at": t.get("created_at", "")[:10],
            "last_posted_at": t.get("last_posted_at", "")[:10],
            "views": t.get("views"),
            "like_count": t.get("like_count"),
            "url": f"https://forum.level1techs.com/t/{t.get('slug', '')}/{t.get('id')}"
        })
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--thread", default="all", help="Thread ID to parse (or 'all')")
    args = parser.parse_args()

    schema = load_json(SCHEMA)
    if schema is None:
        print(f"Missing schema: {SCHEMA}")
        return
    threads = schema.get("monitored_threads", [])

    if args.thread != "all":
        threads = [t for t in threads if t["id"] == args.thread]

    for thread in threads:
        tid = thread["id"]
        raw_path = DATA_DIR / "raw" / f"{tid}_latest.json"

        if not raw_path.exists():
            print(f"\u26a0\ufe0f  No data for '{tid}' ({raw_path}). Run pull.py first.")
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

        output = {
            "source": thread["name"],
            "thread_id": tid,
            "url": thread["url"].replace(".json", ""),
            "count": len(results),
            "items": results
        }

        with open(out_path, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"  \u2713 {len(results)} items \u2192 {out_path}")

if __name__ == "__main__":
    main()
