"""Comparison view (P2-2) — structural + contract tests.

Runs the generator into a temp workspace and verifies the new
``compare/index.html`` page plus the cross-page changes it requires:

* the page is written, non-empty, tag-balanced, and free of template leaks;
* it carries the shared nav (now including Compare), footer, and OG tags,
  with exactly one ``<h1>`` and a ``<main>`` landmark;
* the ``#commands-config`` JSON island is present, parses, and carries the
  schema's backends/tiers + every real submission (trimmed — no ``raw``);
* the no-selection picker has four labeled ``select.compare-pick`` dropdowns
  and a Compare button;
* the diff-table wrapper + an ``aria-live`` takeaway region are present;
* the page loads ``js/compare.js`` and ``js/commands.js`` after ``js/main.js``
  at the correct depth-1 relative path;
* every core page's nav now links to ``compare/``;
* the Matrix carries a compare checkbox + a launch button on each real row,
  a compare-selection bar, and a non-sortable "Actions" header.
"""

import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.util import ROOT, load_json
from tests.test_generate import TagChecker

CORE_PAGES = ("index.html", "matrix.html", "community.html", "guides.html",
              "about.html")

ISLAND_RE = re.compile(
    r'<script type="application/json" id="commands-config">(.*?)</script>',
    re.DOTALL)


class TestComparePage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        cls.tmp = Path(tempfile.mkdtemp(prefix="las_compare_"))
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

    def _page(self):
        return (self.tmp / "compare" / "index.html").read_text(encoding="utf-8")

    def _real_subs(self):
        return self._utils.real_submissions(load_json("data/submissions.json"))

    def _island(self, text):
        m = ISLAND_RE.search(text)
        self.assertIsNotNone(m, "commands-config island missing")
        return json.loads(m.group(1))

    # --- page existence + hygiene -------------------------------------
    def test_page_written_nonempty(self):
        path = self.tmp / "compare" / "index.html"
        self.assertTrue(path.exists(), "compare/index.html was not written")
        self.assertGreater(path.stat().st_size, 0, "compare page is empty")

    def test_tags_balanced_no_brace_leaks(self):
        text = self._page()
        checker = TagChecker()
        checker.feed(text)
        checker.close()
        self.assertEqual(checker.finished(), [], "tag imbalance")
        self.assertNotIn("{{", text, "template {{ leak")
        self.assertNotIn("}}", text, "template }} leak")

    def test_nav_footer_og_and_landmarks(self):
        text = self._page()
        self.assertIn("<nav", text)
        self.assertIn("<footer", text)
        self.assertIn('property="og:title"', text)
        self.assertIn('property="og:image"', text)
        self.assertEqual(text.count("<h1>"), 1, "expected exactly one <h1>")
        self.assertIn("<main", text)

    # --- cross-page nav wiring ----------------------------------------
    def test_nav_includes_compare_on_every_page(self):
        for name in (*CORE_PAGES, "compare/index.html", "recommend/index.html"):
            with self.subTest(page=name):
                text = (self.tmp / name).read_text(encoding="utf-8")
                self.assertRegex(
                    text, r'href="(\.\./)?compare/"',
                    f"{name} nav is missing the Compare link")

    # --- config island (trimmed submissions + schema) -----------------
    def test_island_matches_schema_and_submissions(self):
        config = self._island(self._page())
        schema = load_json("tools/schema.json")
        real = self._real_subs()
        self.assertEqual(config["backends"], schema["backends"])
        self.assertEqual(config["tiers"], schema["tiers"])
        self.assertEqual({s["id"] for s in config["submissions"]},
                         {s["id"] for s in real})

    def test_island_submissions_are_trimmed(self):
        config = self._island(self._page())
        for s in config["submissions"]:
            with self.subTest(sub=s["id"]):
                self.assertNotIn("raw", s, "verbose raw block leaked into the island")
                for key in ("id", "tier", "backend", "model", "context"):
                    self.assertIn(key, s)

    # --- picker + table + takeaway ------------------------------------
    def test_picker_has_four_labeled_selects(self):
        text = self._page()
        self.assertIn('id="compare-picker"', text)
        self.assertEqual(text.count('select class="compare-pick"'), 4,
                         "expected 4 picker dropdowns")
        self.assertIn('compare-pick-go', text)

    def test_table_wrapper_and_live_takeaway(self):
        text = self._page()
        self.assertIn('id="compare-table-wrap"', text)
        self.assertIn('id="compare-takeaway"', text)
        self.assertIn('aria-live="polite"', text)

    def test_extra_scripts_load_after_main_at_depth1(self):
        text = self._page()
        for script in ("js/main.js", "js/compare.js", "js/commands.js"):
            self.assertIn(script, text)
        self.assertRegex(text, r'src="\.\./js/compare\.js"')
        self.assertRegex(text, r'src="\.\./js/commands\.js"')
        self.assertLess(text.index("js/main.js"), text.index("js/compare.js"))
        self.assertLess(text.index("js/compare.js"), text.index("js/commands.js"))

    # --- matrix cross-page changes ------------------------------------
    def test_matrix_has_checkboxes_launch_buttons_and_bar(self):
        text = (self.tmp / "matrix.html").read_text(encoding="utf-8")
        real = self._real_subs()
        self.assertEqual(text.count('class="compare-check"'), len(real),
                         "one compare checkbox per real row")
        self.assertEqual(text.count('data-launch-sub='), len(real),
                         "one launch button per real row")
        self.assertIn('id="compare-bar"', text)
        self.assertIn("data-nosort", text, "Actions header must be non-sortable")


if __name__ == "__main__":
    unittest.main()
