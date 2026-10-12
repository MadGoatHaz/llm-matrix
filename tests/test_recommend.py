"""Recommendation engine (P2-1) — structural + contract tests.

Runs the generator into a temp workspace and verifies the new
``recommend/index.html`` page plus the cross-page changes it requires:

* the page is written, non-empty, tag-balanced, and free of template leaks;
* it carries the shared nav (now including Recommend), footer, and OG tags,
  with exactly one ``<h1>`` and a ``<main>`` landmark;
* the JSON config island is present, parses, and matches the schema's
  tiers / use_cases / vendors exactly;
* the interactive form has the required tier select + the optional
  use-case / vendor / priority selects, each with an associated ``<label>``,
  and an ``aria-live`` results region (WCAG 2.1 AA);
* the page loads ``js/recommend.js`` after ``js/main.js``;
* every core page's nav now links to ``recommend/``;
* matrix rows carry stable ``id`` anchors matching the submission ids (so a
  result card can deep-link to its row);
* the homepage surfaces the "Find My Model" CTA.

The client-side ranking logic itself is exercised separately by
``work/scratch/verify_recommend.js`` (a DOM shim running the real
``js/recommend.js`` against the real ``data.json``).
"""

import json
import re
import shutil
import sys
import tempfile
import unittest
from html.parser import HTMLParser  # noqa: F401  (TagChecker imported below)
from pathlib import Path

from tests.util import ROOT, load_json
from tests.test_generate import TagChecker

CORE_PAGES = ("index.html", "matrix.html", "community.html", "guides.html",
              "about.html")


class TestRecommendPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        cls.tmp = Path(tempfile.mkdtemp(prefix="las_recommend_"))
        # Mirror the inputs the generator needs for the core pages + the
        # recommend content.
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

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _page(self):
        return (self.tmp / "recommend" / "index.html").read_text(encoding="utf-8")

    # --- page existence + hygiene -------------------------------------
    def test_page_written_nonempty(self):
        path = self.tmp / "recommend" / "index.html"
        self.assertTrue(path.exists(), "recommend/index.html was not written")
        self.assertGreater(path.stat().st_size, 0, "recommend page is empty")

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
        self.assertIn("og-image.png", text)
        self.assertEqual(text.count("<h1>"), 1, "expected exactly one <h1>")
        self.assertIn("<main", text)

    # --- cross-page nav wiring ----------------------------------------
    def test_nav_includes_recommend_on_every_page(self):
        for name in (*CORE_PAGES, "recommend/index.html"):
            with self.subTest(page=name):
                text = (self.tmp / name).read_text(encoding="utf-8")
                # depth 0 -> "recommend/"; depth 1 -> "../recommend/"
                self.assertRegex(
                    text, r'href="(\.\./)?recommend/"',
                    f"{name} nav is missing the Recommend link")

    # --- config island (the client's pick-lists) ----------------------
    def test_config_island_valid_and_matches_schema(self):
        text = self._page()
        m = re.search(
            r'<script type="application/json" id="recommend-config">'
            r'(.*?)</script>',
            text, re.DOTALL)
        self.assertIsNotNone(m, "config island missing from the page")
        config = json.loads(m.group(1))
        schema = load_json("tools/schema.json")
        self.assertEqual(config["tiers"], schema["tiers"])
        self.assertEqual(config["use_cases"], schema["use_cases"])
        self.assertEqual(config["vendors"], schema["hardware_vendors"])

    # --- form controls + accessibility --------------------------------
    def test_form_controls_have_labels(self):
        text = self._page()
        for sel in ("rec-tier", "rec-usecase", "rec-vendor", "rec-priority"):
            with self.subTest(control=sel):
                self.assertIn(f'id="{sel}"', text, f"missing #{sel}")
                self.assertIn(f'<label for="{sel}">', text,
                              f"#{sel} has no associated <label>")

    def test_results_region_is_live(self):
        text = self._page()
        self.assertIn('id="rec-results"', text)
        self.assertIn('aria-live="polite"', text)

    def test_tier_select_is_the_required_gate(self):
        # The placeholder option is disabled+selected; a real tier must be
        # chosen before results render (progressive disclosure: simple first).
        text = self._page()
        self.assertRegex(
            text,
            r'<option value="" disabled selected>.*?</option>')

    # --- script loading order -----------------------------------------
    def test_extra_script_loaded_after_main(self):
        text = self._page()
        self.assertIn("js/main.js", text)
        self.assertIn("js/recommend.js", text)
        self.assertLess(
            text.index("js/main.js"), text.index("js/recommend.js"),
            "recommend.js must load after main.js")

    # --- matrix row anchors (deep-link targets) -----------------------
    def test_matrix_rows_have_id_anchors(self):
        text = (self.tmp / "matrix.html").read_text(encoding="utf-8")
        data = load_json("data/submissions.json")
        for s in data["submissions"]:
            with self.subTest(sub=s["id"]):
                self.assertIn(f'<tr id="{s["id"]}"', text,
                              f"matrix row for {s['id']} has no id anchor")

    # --- homepage CTA -------------------------------------------------
    def test_homepage_has_find_my_model_cta(self):
        text = (self.tmp / "index.html").read_text(encoding="utf-8")
        self.assertIn("Find My Model", text)
        self.assertIn('href="recommend/"', text)


if __name__ == "__main__":
    unittest.main()
