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
import html
import json
import re
import shutil
import sys
import time
import urllib.request
from pathlib import Path


class WipeGuardError(RuntimeError):
    """A1 wipe guard: a fetch would destroy more thread data than it brings.

    Raised by :func:`save_thread` when the on-disk thread mirror already has
    a non-empty ``post_stream`` and the new fetch carries 0 posts (or fewer
    than half the previous count) — the signature of a deleted/moderated
    thread, an API change returning empty, or a partial network response.
    The mirror is left untouched and the process must exit non-zero so the
    pipeline stops instead of pushing an empty site to production.
    """

WORKSPACE = Path(__file__).parent.parent
RAW_DIR = WORKSPACE / "data" / "raw"
SCHEMA = WORKSPACE / "tools" / "schema.json"

# Reuse the site generator's placeholder scrubber (the single source of
# truth, shared with parse.py) so unfilled template values are blanked in
# the raw thread mirrors on the way in — instruction text must not land in
# the data tree. Genuine values and all non-submission content are untouched.
_REPO_ROOT = str(WORKSPACE)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from tools.site.utils import scrub_placeholders  # noqa: E402

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


def fetch_html(url):
    """Fetch a page (text) with a browser User-Agent."""
    print(f"Fetching: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def topic_id_from_url(url):
    """Extract the numeric topic ID from a topic URL (/t/{id}.json or
    /t/{slug}/{id}.json). Returns None for non-topic URLs (e.g. /c/... categories).
    """
    m = re.search(r"/t/(?:[^/]+/)?(\d+)\.json?$", url)
    return m.group(1) if m else None


def extract_preloaded_topic(page, topic_id):
    """Extract the topic payload Discourse embeds in a deep-link page.

    Topic pages carry a hidden hydration div:

        <div class="hidden" id="data-preloaded"
             data-preloaded="{&quot;topic_<id>&quot;:&quot;{...}&quot;...}">

    whose value is HTML-escaped JSON mapping "topic_<id>" to a JSON-encoded
    topic payload. That payload's ``post_stream.posts`` is a 20-post window
    positioned around the deep-linked post — wider than the first-20 window
    of the plain ``/t/{id}.json`` endpoint.

    Returns the parsed topic dict, or None when the div is absent/unparseable.
    """
    m = re.search(r'id="data-preloaded"\s+data-preloaded="([^"]*)"', page)
    if not m:
        return None
    try:
        outer = json.loads(html.unescape(m.group(1)))
    except ValueError:
        return None
    key = f"topic_{topic_id}"
    if key not in outer:
        return None
    try:
        return json.loads(outer[key])
    except ValueError:
        return None


def backfill_missing_posts(url, data):
    """Fetch posts beyond a topic payload's first-20 window.

    Discourse's ``/t/{id}.json`` returns only the first 20 posts, while
    ``post_stream.stream`` lists every post ID. This forum blocks the
    ``post_ids`` endpoint (404) and ignores ``post_ids`` query params, so we
    page through deep-link pages (``/t/{id}/{post_number}``) instead: each one
    embeds a 20-post window in its ``data-preloaded`` div. Posts we don't have
    yet are merged in, and the window slides forward until the stream is
    complete (deleted post numbers are skipped; capped at 15 windows).

    Mutates ``data`` in place (posts sorted by post_number).
    Returns the number of posts added.
    """
    topic_id = topic_id_from_url(url)
    if topic_id is None:
        return 0
    post_stream = data.get("post_stream")
    if not post_stream:
        return 0

    posts = post_stream.get("posts", [])
    stream = post_stream.get("stream", [])
    have = {p.get("id") for p in posts}
    missing = [pid for pid in stream if pid not in have]
    if not missing:
        return 0
    missing_set = set(missing)
    print(f"  {len(missing)} post(s) beyond the first-20 window; "
          f"backfilling via deep-link pages...")

    base = url[:-5] if url.endswith(".json") else url
    added = 0
    next_num = max((p.get("post_number", 0) for p in posts), default=0) + 1
    stalled = 0
    for _ in range(15):
        if not missing_set:
            break
        page = None
        try:
            page = fetch_html(f"{base}/{next_num}")
        except Exception as e:
            print(f"  (deep-link {next_num}: {e})")
        payload = extract_preloaded_topic(page, topic_id) if page else None
        window = payload.get("post_stream", {}).get("posts", []) if payload else []

        window_max = next_num
        new_here = 0
        for p in window:
            window_max = max(window_max, p.get("post_number", 0))
            if p.get("id") in missing_set:
                posts.append(p)
                missing_set.discard(p.get("id"))
                added += 1
                new_here += 1
        if new_here:
            print(f"  \u21bb window @ {next_num}: +{new_here} post(s)")
            stalled = 0
        else:
            stalled += 1
        # Slide past the window we just covered (or past a dead number).
        next_num = max(window_max, next_num) + 1
        if stalled >= 3:
            print(f"  (stalled 3 deep-link pages in a row; stopping)")
            break
        time.sleep(1)  # be polite to the forum

    if missing_set:
        print(f"  \u26a0\ufe0f {len(missing_set)} post id(s) still not retrieved "
              f"(deleted or unreachable): {sorted(missing_set)}")
    if added:
        posts.sort(key=lambda p: p.get("post_number", 0))
        post_stream["posts"] = posts
    return added


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

    Unfilled template values in the posts' cooked HTML are blanked on the
    way in (see :func:`tools.site.utils.scrub_placeholders`); genuine values
    and all non-submission content are untouched.

    A1 wipe guard: if the mirror already exists with a non-empty
    ``post_stream`` and the new fetch carries 0 posts (or fewer than half
    the previous count), the write is REFUSED and a :class:`WipeGuardError`
    is raised. A deleted/moderated thread, an API change, or a partial
    network response must never silently erase the dataset.

    Returns (path, label, count, size_bytes).
    """
    tid = thread["id"]
    out_path = RAW_DIR / f"{tid}_latest.json"
    new_count = len(data.get("post_stream", {}).get("posts", []))
    if out_path.exists():
        try:
            existing = load_json(out_path)
        except (ValueError, OSError):
            existing = {}
        prev_count = len(existing.get("post_stream", {}).get("posts", []))
        if prev_count > 0 and new_count < prev_count / 2:
            print(f"\u26a0 Refusing to overwrite {tid} — new fetch has "
                  f"{new_count} posts vs {prev_count} previously. This looks "
                  f"like a data loss event. Not saving.")
            raise WipeGuardError(
                f"{tid}: new fetch has {new_count} posts vs {prev_count} "
                f"previously (wipe guard) — {out_path.name} left untouched")
    for post in data.get("post_stream", {}).get("posts", []):
        cooked = post.get("cooked")
        if cooked:
            post["cooked"] = scrub_placeholders(cooked)
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
    backfill_missing_posts(label_src, data)
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
        try:
            _single_pull(args.file, import_file(args.file))
        except WipeGuardError:
            # A1: the warning was already printed in save_thread; stop the
            # pipeline with a non-zero exit so nothing downstream runs.
            sys.exit(1)
        return
    if args.url != DEFAULT_URL:
        try:
            _single_pull(args.url, fetch_url(args.url))
        except WipeGuardError:
            sys.exit(1)
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
    guard_tripped = False
    for thread in threads:
        tid = thread["id"]
        print(f"\n[{tid}] {thread['name']}")
        try:
            data = fetch_url(thread["url"])
            backfill_missing_posts(thread["url"], data)
            out_path, label, count, size = save_thread(thread, data)
            results.append((tid, thread["name"], label, count, size, out_path.name, None))
        except WipeGuardError as e:
            # A1: a thin/empty fetch was refused — the good mirror stays
            # intact and the pipeline must stop (non-zero exit below).
            guard_tripped = True
            results.append((tid, thread["name"], None, 0, 0, None, str(e)))
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

    if guard_tripped:
        print("\n\u2717 Wipe guard tripped — at least one thread fetch looks like a "
              "data loss event.")
        print("  The good mirror(s) were left untouched. Stopping the pipeline "
              "(non-zero exit) so nothing is parsed, validated, or pushed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
