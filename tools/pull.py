#!/usr/bin/env python3
"""
pull.py — Fetch the LLM Matrix thread JSON from Discourse.

Usage:
    python tools/pull.py
    python tools/pull.py --url "https://forum.level1techs.com/t/256443.json"
    python tools/pull.py --file data/raw/my_download.json  (import a local file)

Output:
    data/raw/thread_YYYY-MM-DD.json  (timestamped snapshot)
    data/raw/latest.json             (symlink or copy of most recent)
    Prints summary: post count, submission block count
"""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

WORKSPACE = Path(__file__).parent.parent
RAW_DIR = WORKSPACE / "data" / "raw"

DEFAULT_URL = "https://forum.level1techs.com/t/256443.json"

def fetch_url(url):
    """Fetch JSON from URL."""
    print(f"Fetching: {url}")
    resp = urlopen(url)
    data = json.loads(resp.read().decode('utf-8'))
    return data

def import_file(filepath):
    """Import a local JSON file."""
    print(f"Importing: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def count_submissions(data):
    """Count [COMMUNITY-SUBMISSION] and [QUICK-SUBMIT] blocks in the thread."""
    count = 0
    posts = data.get("post_stream", {}).get("posts", [])
    for post in posts:
        cooked = post.get("cooked", "")
        count += cooked.count("[COMMUNITY-SUBMISSION]")
        count += cooked.count("[QUICK-SUBMIT]")
    return len(posts), count

def main():
    parser = argparse.ArgumentParser(description="Pull LLM Matrix thread data")
    parser.add_argument("--url", default=DEFAULT_URL, help="Discourse thread JSON URL")
    parser.add_argument("--file", help="Import from local file instead of URL")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if args.file:
        data = import_file(args.file)
    else:
        data = fetch_url(args.url)

    # Save timestamped snapshot
    today = datetime.now().strftime("%Y-%m-%d")
    snapshot_path = RAW_DIR / f"thread_{today}.json"
    with open(snapshot_path, 'w') as f:
        json.dump(data, f, indent=2)

    # Save as latest
    latest_path = RAW_DIR / "latest.json"
    shutil.copy2(snapshot_path, latest_path)

    # Summary
    post_count, sub_count = count_submissions(data)
    print(f"\n✓ Saved: {snapshot_path}")
    print(f"✓ Latest: {latest_path}")
    print(f"\nSummary: {post_count} posts, {sub_count} submission blocks")

if __name__ == "__main__":
    main()
