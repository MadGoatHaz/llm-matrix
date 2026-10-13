"""Verification badges (B4/C4) — matrix dots, detail-panel lines, consistency.

The UI used to present every entry with identical visual weight. This batch
adds one quiet color system for how well-corroborated (and how current) a
setup is:

* **Matrix rows** — a small dot next to the contributor name (green =
  verified, blue = community-reported, gray = unverified) with
  ``role="img"`` + ``aria-label`` + ``title`` for screen readers, and a
  small "older" / "retired" tag after the model name for superseded /
  discontinued entries.
* **Detail panel** — a worded confidence line ("✓ Verified by maintainer" /
  "Community-reported" / "Unverified") plus lifecycle warnings, with the
  existing "★ Community highlight" badge verified alongside.
* **Recommend cards** — the batch-2 trust badges keep the SAME dot color
  system (dot + word label next to the name).
* **CSS** — one shared token system: ``--success`` / ``--accent`` /
  ``--text-muted`` for the three states, everywhere.

The client-side rendering (detail panel) is exercised separately by
``work/scratch/verify_detail_b4c4.js`` (a DOM shim running the real
``js/main.js`` against synthetic confidence/lifecycle states).
"""

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.util import ROOT, load_json

#: confidence value -> the dot class the matrix renders.
DOT_CLASS = {
    "op-verified": "verified",
    "community-verified": "verified",
    "community-reported": "community",
    "unverified": "unverified",
}

DOT_RE = re.compile(
    r'<span class="confidence-dot (verified|community|unverified)" '
    r'role="img" aria-label="([^"]+)" title="[^"]*">●</span>')


def _make_sub(**over) -> dict:
    """A minimal synthetic submission for the matrix helper unit tests."""
    s = {
        "id": "syn",
        "source": {"username": "tester"},
        "confidence": "community-reported",
        "lifecycle": "current",
        "model": {"name": "TestModel-7B"},
    }
    s.update(over)
    return s


class TestMatrixHelpers(unittest.TestCase):
    """Unit tests for the pure matrix.py badge helpers (all states)."""

    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from tools.site.pages import matrix
        cls.matrix = matrix

    def test_confidence_dot_all_states(self):
        for conf, cls in DOT_CLASS.items():
            with self.subTest(conf=conf):
                html = self.matrix.confidence_dot(_make_sub(confidence=conf))
                m = DOT_RE.search(html)
                self.assertIsNotNone(m, f"no well-formed dot for {conf}: {html}")
                self.assertEqual(m.group(1), cls)

    def test_confidence_dot_unknown_or_missing(self):
        # Honest: an unrecognized / missing confidence renders NO dot —
        # the UI never claims a verification level it doesn't have.
        self.assertEqual(self.matrix.confidence_dot(_make_sub(confidence="")), "")
        self.assertEqual(self.matrix.confidence_dot(_make_sub(confidence="bogus")), "")
        s = _make_sub()
        del s["confidence"]
        self.assertEqual(self.matrix.confidence_dot(s), "")

    def test_lifecycle_tag_all_states(self):
        self.assertRegex(
            self.matrix.lifecycle_tag(_make_sub(lifecycle="superseded")),
            r'<span class="lifecycle-tag lifecycle-tag-superseded" '
            r'title="[^"]*">older</span>')
        self.assertRegex(
            self.matrix.lifecycle_tag(_make_sub(lifecycle="discontinued")),
            r'<span class="lifecycle-tag lifecycle-tag-discontinued" '
            r'title="[^"]*">retired</span>')

    def test_lifecycle_tag_current_and_watch_are_clean(self):
        # Current and watch entries are NOT marked — only genuinely stale
        # setups carry a tag, so the matrix stays scannable.
        self.assertEqual(self.matrix.lifecycle_tag(_make_sub(lifecycle="current")), "")
        self.assertEqual(self.matrix.lifecycle_tag(_make_sub(lifecycle="watch")), "")
        self.assertEqual(self.matrix.lifecycle_tag(_make_sub(lifecycle="")), "")

    def test_td_extra_keeps_clean_tooltip(self):
        html = self.matrix.td_extra("Some Model", " <span class='x'>tag</span>")
        self.assertEqual(
            html,
            '<td title="Some Model">Some Model <span class=\'x\'>tag</span></td>')


class TestVerificationBadges(unittest.TestCase):
    """Generated-site contracts: dots in the matrix, lines in the panel,
    one shared CSS color system, recommend consistency."""

    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        cls.tmp = Path(tempfile.mkdtemp(prefix="las_verify_"))
        for rel in (
            "data/submissions.json",
            "tools/schema.json",
            "css/style.css",
            "js/main.js",
            "content/recommend.md",
        ):
            src = ROOT / rel
            dst = cls.tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        from tools.site import main as site_main
        site_main(
            workspace=cls.tmp,
            data_dir=cls.tmp / "data",
            submissions=cls.tmp / "data" / "submissions.json",
            schema=cls.tmp / "tools" / "schema.json",
        )
        from tools.site import utils as site_utils
        cls._utils = site_utils

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _page(self, name: str) -> str:
        return (self.tmp / name).read_text(encoding="utf-8")

    def _real_subs(self):
        return self._utils.real_submissions(load_json("data/submissions.json"))

    # --- matrix rows ------------------------------------------------------
    def test_matrix_has_one_dot_per_real_row(self):
        text = self._page("matrix.html")
        real = self._real_subs()
        dots = DOT_RE.findall(text)
        self.assertEqual(len(dots), len(real),
                         "one confidence dot per real row")

    def test_matrix_dots_match_submission_confidence(self):
        text = self._page("matrix.html")
        for s in self._real_subs():
            with self.subTest(sub=s["id"]):
                m = re.search(r'<tr id="' + re.escape(s["id"]) + r'"[^>]*>(.*?)</tr>',
                              text, re.DOTALL)
                self.assertIsNotNone(m, f"row for {s['id']} not found")
                row = m.group(1)
                expected = DOT_CLASS.get(s.get("confidence") or "")
                if not expected:
                    self.assertNotIn("confidence-dot", row,
                                     "unknown confidence must render no dot")
                    continue
                d = DOT_RE.search(row)
                self.assertIsNotNone(d, f"row for {s['id']} has no dot")
                self.assertEqual(d.group(1), expected,
                                 f"row {s['id']}: dot class {d.group(1)} "
                                 f"!= {expected} for confidence "
                                 f"{s.get('confidence')}")

    def test_matrix_dots_are_accessible(self):
        text = self._page("matrix.html")
        dots = DOT_RE.findall(text)
        self.assertTrue(dots)
        # every dot in the file (not just the well-formed sample) carries
        # role="img" + aria-label + title
        self.assertEqual(
            text.count('class="confidence-dot'),
            len(re.findall(
                r'class="confidence-dot [^"]+" role="img" '
                r'aria-label="[^"]+" title="[^"]*"', text)))

    def test_matrix_lifecycle_tags_are_data_driven(self):
        text = self._page("matrix.html")
        real = self._real_subs()
        expected_older = sum(1 for s in real if s.get("lifecycle") == "superseded")
        expected_retired = sum(1 for s in real if s.get("lifecycle") == "discontinued")
        self.assertEqual(text.count("lifecycle-tag-superseded"), expected_older)
        self.assertEqual(text.count("lifecycle-tag-discontinued"), expected_retired)

    # --- detail panel (js/main.js) ----------------------------------------
    def test_detail_panel_confidence_and_lifecycle_lines(self):
        js = (ROOT / "js" / "main.js").read_text(encoding="utf-8")
        # the four confidence states, worded clearly
        for needle in (
            "✓ Verified by maintainer", "✓ Verified by community",
            "Community-reported", "Unverified",
        ):
            self.assertIn(needle, js, f"detail panel missing line: {needle}")
        # the lifecycle warnings
        self.assertIn("This setup may be outdated", js)
        self.assertIn("no longer recommended", js)
        # the highlight badge (A5, batch 2) is still rendered in the panel
        self.assertIn("★ Community highlight", js)
        # the lines carry the shared CSS state classes
        for needle in ("detail-confidence", "detail-conf-verified",
                       "detail-conf-community", "detail-conf-unverified",
                       "detail-lifecycle-superseded",
                       "detail-lifecycle-discontinued"):
            self.assertIn(needle, js)

    # --- recommend consistency ---------------------------------------------
    def test_recommend_uses_same_dot_system(self):
        js = (ROOT / "js" / "recommend.js").read_text(encoding="utf-8")
        # the batch-4 change: the card's trust badge pairs the SAME
        # .confidence-dot the matrix uses with the word label
        self.assertIn('confidence-dot', js)
        self.assertIn("role=\"img\"", js)
        self.assertIn("rec-conf-", js)

    # --- one shared CSS color system ---------------------------------------
    def test_css_shared_dot_color_system(self):
        css = (ROOT / "css" / "style.css").read_text(encoding="utf-8")
        # matrix / detail / recommend all resolve to the same three tokens
        self.assertRegex(css, r"\.confidence-dot\.verified\s*{[^}]*var\(--success\)")
        self.assertRegex(css, r"\.confidence-dot\.community\s*{[^}]*var\(--accent\)")
        self.assertRegex(css, r"\.confidence-dot\.unverified\s*{[^}]*var\(--text-muted\)")
        # the detail panel lines + lifecycle tags use the same tokens
        self.assertRegex(css, r"\.detail-conf-verified\s*{[^}]*var\(--success\)")
        self.assertRegex(css, r"\.detail-conf-community\s*{[^}]*var\(--accent\)")
        self.assertRegex(css, r"\.detail-conf-unverified\s*{[^}]*var\(--text-muted\)")
        self.assertRegex(css, r"\.detail-lifecycle-superseded\s*{[^}]*var\(--warning\)")
        self.assertRegex(css, r"\.detail-lifecycle-discontinued\s*{[^}]*var\(--danger\)")
        self.assertRegex(css, r"\.lifecycle-tag-superseded\s*{[^}]*var\(--warning\)")
        self.assertRegex(css, r"\.lifecycle-tag-discontinued\s*{[^}]*var\(--danger\)")
        # the batch-2 recommend badges stay on the same tokens
        self.assertRegex(css, r"\.rec-conf-verified\s*{[^}]*var\(--success\)")
        self.assertRegex(css, r"\.rec-conf-community\s*{[^}]*var\(--accent\)")
        self.assertRegex(css, r"\.rec-conf-unverified\s*{[^}]*var\(--text-muted\)")

    # --- hygiene -------------------------------------------------------------
    def test_matrix_still_balanced_and_leak_free(self):
        text = self._page("matrix.html")
        from tests.test_generate import TagChecker
        checker = TagChecker()
        checker.feed(text)
        checker.close()
        self.assertEqual(checker.finished(), [], "tag imbalance")
        self.assertNotIn("{{", text)
        self.assertNotIn("}}", text)


if __name__ == "__main__":
    unittest.main()
