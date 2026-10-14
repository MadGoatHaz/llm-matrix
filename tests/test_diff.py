"""diff.py (E5) — the "what changed this week" tool covers ALL threads.

Before E5, diff.py only compared the main thread, so changes in Crucible /
Rigs / Category were invisible to the weekly report. These tests lock in:

* per-thread state in ``data/last_seen.json`` (``main`` / ``crucible`` /
  ``rigs`` / ``category`` keys, plus the A1 ``previous_count`` baseline);
* per-thread reporting (new / updated / removed for each of the 4 threads,
  a ``Total:`` line, and a ``(no changes)`` condition that is NO changes in
  ANY thread — a Crucible-only change is reported, not "no changes");
* the category feed diffing TOPICS (id + last_posted_at) instead of posts;
* a partial pull never wiping a thread's state (missing mirror -> kept);
* the pre-E5 state file (a bare main-thread mirror) migrating on first use
  without re-reporting whole-thread history as "new";
* the A1 wipe-guard ``previous_count`` baseline surviving every refresh.
"""

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.util import ROOT, load_tool

THREADS = ("main", "crucible", "rigs", "category")


def _make_workspace(tmp: Path) -> Path:
    """A diff test workspace: all 4 raw mirrors + a quiet E5-shaped state."""
    raw = tmp / "data" / "raw"
    raw.mkdir(parents=True)
    for f in ("main_latest.json", "crucible_latest.json", "rigs_latest.json",
              "category_latest.json", "latest.json"):
        shutil.copy2(ROOT / "data" / "raw" / f, raw / f)

    state = {}
    for tid in THREADS:
        state[tid] = json.loads((raw / f"{tid}_latest.json").read_text(encoding="utf-8"))
    state["previous_count"] = 26
    (tmp / "data" / "last_seen.json").write_text(
        json.dumps(state, indent=2), encoding="utf-8")
    return tmp


def _run_diff(tmp: Path) -> str:
    """Run diff.py's main() against ``tmp`` and capture its stdout."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    diff = load_tool("tools/diff.py")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = diff.main(str(tmp))
    assert rc == 0
    return buf.getvalue()


def _read_state(tmp: Path) -> dict:
    return json.loads((tmp / "data" / "last_seen.json").read_text(encoding="utf-8"))


def _bump_post_mirror(tmp: Path, tid: str, idx: int, ts: str) -> None:
    p = tmp / "data" / "raw" / f"{tid}_latest.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    data["post_stream"]["posts"][idx]["updated_at"] = ts
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    if tid == "main":
        # keep the backfilled copy in step (raw_mirror prefers *_latest.json,
        # but a real pull rewrites both)
        (tmp / "data" / "raw" / "latest.json").write_text(
            json.dumps(data, indent=2), encoding="utf-8")


class TestQuietWeek(unittest.TestCase):
    """No changes in ANY thread -> the report says so and the state is stable."""

    def test_no_changes_in_any_thread(self):
        tmp = Path(tempfile.mkdtemp(prefix="las_diff_quiet_"))
        try:
            _make_workspace(tmp)
            before = (tmp / "data" / "last_seen.json").read_bytes()
            out = _run_diff(tmp)
            for tid in THREADS:
                with self.subTest(thread=tid):
                    self.assertIn(
                        f"{tid.capitalize()}: 0 new, 0 updated, 0 removed", out)
            self.assertIn("Total: 0 new, 0 updated, 0 removed", out)
            self.assertIn("(no changes)", out)
            # A quiet week rewrites the state byte-identically (no churn).
            self.assertEqual(before, (tmp / "data" / "last_seen.json").read_bytes())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestPerThreadDetection(unittest.TestCase):
    """A change in ANY single thread is reported — not "no changes"."""

    def test_crucible_only_change_is_reported(self):
        tmp = Path(tempfile.mkdtemp(prefix="las_diff_crucible_"))
        try:
            _make_workspace(tmp)
            _bump_post_mirror(tmp, "crucible", 0, "2026-10-13T23:59:59.999Z")
            out = _run_diff(tmp)
            self.assertIn("Crucible: 0 new, 1 updated, 0 removed", out)
            self.assertIn("Main: 0 new, 0 updated, 0 removed", out)
            self.assertIn("Total: 0 new, 1 updated, 0 removed", out)
            self.assertNotIn("(no changes)", out,
                             "a Crucible-only change must not read 'no changes'")
            self.assertIn("Crucible — UPDATED POSTS", out)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_main_new_post_is_reported(self):
        tmp = Path(tempfile.mkdtemp(prefix="las_diff_main_"))
        try:
            _make_workspace(tmp)
            p = tmp / "data" / "raw" / "main_latest.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            post = dict(data["post_stream"]["posts"][0])
            post["id"] = 9999999
            post["post_number"] = 99
            post["username"] = "testuser"
            post["created_at"] = "2026-10-13T23:00:00.000Z"
            post["updated_at"] = "2026-10-13T23:00:00.000Z"
            data["post_stream"]["posts"].append(post)
            p.write_text(json.dumps(data, indent=2), encoding="utf-8")
            out = _run_diff(tmp)
            self.assertIn("Main: 1 new, 0 updated, 0 removed", out)
            self.assertIn("MAIN — NEW POSTS", out)
            self.assertIn("#99 by testuser", out)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_category_topic_update_is_reported(self):
        # The category feed has no posts: it diffs TOPICS by id + last_posted_at.
        tmp = Path(tempfile.mkdtemp(prefix="las_diff_category_"))
        try:
            _make_workspace(tmp)
            p = tmp / "data" / "raw" / "category_latest.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["topic_list"]["topics"][1]["last_posted_at"] = \
                "2026-10-13T23:59:59.999Z"
            p.write_text(json.dumps(data, indent=2), encoding="utf-8")
            out = _run_diff(tmp)
            self.assertIn("Category: 0 new, 1 updated, 0 removed", out)
            self.assertIn("Category — UPDATED TOPICS", out)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_category_new_topic_is_reported(self):
        tmp = Path(tempfile.mkdtemp(prefix="las_diff_catnew_"))
        try:
            _make_workspace(tmp)
            p = tmp / "data" / "raw" / "category_latest.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["topic_list"]["topics"].append({
                "id": 999999, "title": "A brand new thread",
                "created_at": "2026-10-13T23:00:00.000Z",
                "last_posted_at": "2026-10-13T23:00:00.000Z",
            })
            p.write_text(json.dumps(data, indent=2), encoding="utf-8")
            out = _run_diff(tmp)
            self.assertIn("Category: 1 new, 0 updated, 0 removed", out)
            self.assertIn("NEW TOPICS", out)
            self.assertIn("A brand new thread", out)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_combined_total_sums_all_threads(self):
        tmp = Path(tempfile.mkdtemp(prefix="las_diff_total_"))
        try:
            _make_workspace(tmp)
            _bump_post_mirror(tmp, "crucible", 0, "2026-10-13T23:59:59.999Z")
            _bump_post_mirror(tmp, "rigs", 1, "2026-10-13T23:59:58.999Z")
            out = _run_diff(tmp)
            self.assertIn("Total: 0 new, 2 updated, 0 removed", out)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestStateContract(unittest.TestCase):
    """The per-thread state file: shape, migration, and the A1 baseline."""

    def test_state_has_all_thread_keys_and_baseline(self):
        tmp = Path(tempfile.mkdtemp(prefix="las_diff_state_"))
        try:
            _make_workspace(tmp)
            _run_diff(tmp)
            state = _read_state(tmp)
            for tid in THREADS:
                with self.subTest(thread=tid):
                    self.assertIn(tid, state)
            self.assertEqual(state["previous_count"], 26,
                             "the A1 wipe-guard baseline must survive the refresh")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_missing_mirror_keeps_previous_state(self):
        # A partial pull (one thread's mirror missing) must not wipe that
        # thread's history from the state.
        tmp = Path(tempfile.mkdtemp(prefix="las_diff_partial_"))
        try:
            _make_workspace(tmp)
            (tmp / "data" / "raw" / "rigs_latest.json").unlink()
            out = _run_diff(tmp)
            self.assertIn("Rigs: no mirror this run", out)
            state = _read_state(tmp)
            self.assertIn("rigs", state)
            self.assertEqual(
                len(state["rigs"]["post_stream"]["posts"]),
                len(json.loads(
                    (ROOT / "data" / "raw" / "rigs_latest.json")
                    .read_text(encoding="utf-8"))["post_stream"]["posts"]),
                "the previous rigs state must be kept, not dropped")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_pre_e5_state_migrates_without_history_replay(self):
        # A pre-E5 last_seen.json is a BARE main-thread mirror (top-level
        # post_stream) with previous_count at the top level. The first E5 run
        # wraps it under "main", seeds the other threads from the current
        # mirrors, and reports NO changes (no whole-thread history replay).
        tmp = Path(tempfile.mkdtemp(prefix="las_diff_migrate_"))
        try:
            raw = tmp / "data" / "raw"
            raw.mkdir(parents=True)
            for f in ("main_latest.json", "crucible_latest.json",
                      "rigs_latest.json", "category_latest.json", "latest.json"):
                shutil.copy2(ROOT / "data" / "raw" / f, raw / f)
            old = json.loads((ROOT / "data" / "last_seen.json")
                             .read_text(encoding="utf-8"))
            # Re-create the pre-E5 shape from the real (now migrated) file:
            # the bare main mirror + top-level previous_count.
            pre_e5 = dict(old["main"])
            pre_e5["previous_count"] = old.get("previous_count", 26)
            (tmp / "data" / "last_seen.json").write_text(
                json.dumps(pre_e5, indent=2), encoding="utf-8")

            out = _run_diff(tmp)
            self.assertIn("Total: 0 new, 0 updated, 0 removed", out,
                          "migration must not replay thread history as new")
            self.assertIn("(no changes)", out)
            state = _read_state(tmp)
            self.assertEqual(
                {k for k in state if k != "previous_count"}, set(THREADS))
            self.assertEqual(state["previous_count"], 26,
                             "the baseline must be re-homed to the top level")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_first_run_establishes_baseline(self):
        tmp = Path(tempfile.mkdtemp(prefix="las_diff_first_"))
        try:
            raw = tmp / "data" / "raw"
            raw.mkdir(parents=True)
            for f in ("main_latest.json", "crucible_latest.json",
                      "rigs_latest.json", "category_latest.json", "latest.json"):
                shutil.copy2(ROOT / "data" / "raw" / f, raw / f)
            out = _run_diff(tmp)  # no last_seen.json -> first run
            self.assertIn("FIRST RUN", out)
            state = _read_state(tmp)
            self.assertEqual(set(state), set(THREADS),
                             "a first run baselines every mirrored thread")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
