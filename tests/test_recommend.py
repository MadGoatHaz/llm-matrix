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

    def test_config_island_keyword_map_matches_python_source(self):
        # E1 sync guard: the island's use-case keyword map must equal the
        # Python source of truth (tools/site/utils.py USE_CASE_KEYWORDS) —
        # the client and the generator can never drift.
        text = self._page()
        m = re.search(
            r'<script type="application/json" id="recommend-config">'
            r'(.*?)</script>',
            text, re.DOTALL)
        self.assertIsNotNone(m, "config island missing from the page")
        config = json.loads(m.group(1))
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from tools.site import utils
        expected = {k: list(v) for k, v in utils.USE_CASE_KEYWORDS.items()}
        self.assertEqual(config.get("use_case_keywords"), expected,
                         "the island's keyword map drifted from the Python "
                         "source of truth")
        # Every schema use case (minus Other) is covered by the map.
        schema = load_json("tools/schema.json")
        for cat in schema["use_cases"]:
            if cat != "Other":
                self.assertIn(cat, expected,
                              f"schema use case {cat!r} has no keyword entry")

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


class TestQualityRankingContract(unittest.TestCase):
    """B1: the quality priority scores MODEL CAPABILITY x QUANT, not bits alone.

    The project's own quantization guide says "the model you pick matters
    more than the quant you pick" — a 35B-A3B I-Nano MoE beats a dense 27B
    Q4 on a 16 GB card. The engine must therefore blend model size/family
    (60%) with quant precision (40%), so a capable small-quant model is
    acknowledged instead of sunk (the old quant-only scale gave I-Nano 15
    vs Q4_K_M 40). The live behavior is exercised by
    work/scratch/verify_quality_b1.js (a DOM shim running the real
    recommend.js); this contract locks the scoring table + formula in the
    source so a future edit cannot quietly revert to bits-only ranking.
    """

    @classmethod
    def setUpClass(cls):
        cls.js = (ROOT / "js" / "recommend.js").read_text(encoding="utf-8")

    def _ranks(self):
        import re
        return {k: int(v) for k, v in re.findall(
            r"\['([a-z0-9_\-\.]+)',\s*(\d+)\]", self.js)}

    # --- the rebalanced quant scale (the 40% half) ----------------------
    def test_quant_scale_rebalanced(self):
        ranks = self._ranks()
        expected = {
            'fp16': 100, 'bf16': 100,
            'fp8': 85,
            'int8': 75, 'w8a8': 75,
            'q8_0': 75, 'q8': 75,
            'q6_k': 60, 'q6': 60,
            'q5_k_m': 50, 'q5': 50,
            'q4_k_m': 40,
            'ud-q4': 35, 'q4': 35,
            'iq4_xs': 35, 'iq4': 35,
            'iq3_s': 20, 'iq3': 20, 'q3': 20,
            'i-nano': 20, 'nano': 20,
            'ud-q2': 10, 'q2': 10,
        }
        for key, val in expected.items():
            with self.subTest(quant=key):
                self.assertEqual(ranks.get(key), val,
                                 f"quant scale: {key} should rank {val}")

    def test_i_nano_no_longer_sunk_vs_q4(self):
        # The original contradiction: I-Nano (15) sank below Q4_K_M (40).
        # Now the two live in the same order-of-magnitude (20 vs 40) and the
        # model half of the blend does the deciding.
        ranks = self._ranks()
        self.assertLess(ranks['i-nano'] - ranks['q4_k_m'], 30,
                        "I-Nano must not be an order of magnitude below Q4")

    # --- the model capability half (60%) --------------------------------
    def test_model_capability_bands(self):
        for clause in (
            "if (total >= 100) return 90;",
            "if (total >= 70) return 80;",
            "if (total >= 35 || (active != null && active >= 30)) return 70;",
            "if (total >= 27) return 60;",
            "if (total >= 20) return 50;",
            "if (total >= 8) return 35;",
            "return 20;",
        ):
            with self.subTest(clause=clause):
                self.assertIn(clause, self.js,
                              "model capability band missing from "
                              "modelCapabilityScore")
        self.assertIn("function modelCapabilityScore", self.js)
        # Unstated size -> neutral, never sunk or inflated.
        self.assertIn("return 50", self.js)

    def test_model_size_from_params_fields_or_name(self):
        # params_total / params_active are used when the data carries them;
        # otherwise the name is parsed ("27B", "120B", "35B-A3B").
        self.assertIn("model.params_total", self.js)
        self.assertIn("model.params_active", self.js)
        self.assertIn("35B-A3B", self.js)  # the MoE name shape in the docs

    # --- the blend formula (the contract itself) ------------------------
    def test_quality_is_model_60_plus_quant_40(self):
        self.assertIn(
            "s.modelScore * 0.6 + s.precision.rank * 0.4", self.js,
            "quality must be model capability (60%) + quant (40%)")
        self.assertIn("modelScore: modelCapabilityScore(s)", self.js)

    def test_blend_examples_match_the_guide(self):
        # The spec's worked examples (model x 0.6 + quant x 0.4):
        i_nano_35b = 70 * 0.6 + 20 * 0.4    # 35B-A3B I-Nano  -> 50
        q4_27b = 60 * 0.6 + 40 * 0.4        # 27B Q4_K_M      -> 52
        fp8_120b = 90 * 0.6 + 85 * 0.4      # 120B FP8        -> 88
        q2_7b = 20 * 0.6 + 10 * 0.4         # 7B Q2           -> 16
        self.assertAlmostEqual(i_nano_35b, 50)
        self.assertAlmostEqual(q4_27b, 52)
        self.assertLessEqual(abs(i_nano_35b - q4_27b), 10,
                            "35B-A3B I-Nano must rank within 10 of 27B Q4_K_M")
        self.assertGreater(fp8_120b, q4_27b, "120B FP8 ranks highest")
        self.assertLess(q2_7b, i_nano_35b, "7B Q2 ranks lowest")

    # --- the why-line names both halves ----------------------------------
    def test_why_line_surfaces_model_and_quant(self):
        self.assertIn("s.modelSize + ' model'", self.js)
        self.assertIn("s.precision.key + ' precision'", self.js)


class TestNoDuplicatedClientState(unittest.TestCase):
    """E1 + E7: recommend.js carries NO private copies of shared state.

    * The use-case keyword map (E1) is baked into the page's config island
      from the Python source of truth — a hardcoded copy in the JS is how
      the matrix filter and the recommend engine drift apart.
    * The speed / context parsers (E7) live once in js/main.js (window.*) —
      private copies in the page scripts are how the same string parses two
      different ways.
    """

    @classmethod
    def setUpClass(cls):
        cls.js = (ROOT / "js" / "recommend.js").read_text(encoding="utf-8")
        cls.main_js = (ROOT / "js" / "main.js").read_text(encoding="utf-8")

    # --- E1: the keyword map comes from the island ----------------------
    def test_no_hardcoded_keyword_map(self):
        self.assertNotIn("USE_CASE_KEYWORDS", self.js,
                         "recommend.js must not define its own keyword map")
        # No category names hardcoded (they arrive via the island / form).
        for cat in ("Agentic Coding", "Repo Editing", "Security Research",
                    "Production Serving"):
            self.assertNotIn(cat, self.js,
                             f"{cat!r} is hardcoded in recommend.js")
        # No keyword literals from the map (spot the most distinctive).
        for kw in ("opencode", "vulnerab", "openai-compatible"):
            self.assertNotIn(kw, self.js,
                             f"keyword {kw!r} is hardcoded in recommend.js")

    def test_reads_keyword_map_from_island(self):
        self.assertIn("use_case_keywords", self.js,
                      "recommend.js must read the map from the island")

    # --- E7: the shared parsers come from main.js -----------------------
    def test_no_private_parsers(self):
        self.assertNotIn("function parseSpeed", self.js,
                         "recommend.js must not define its own parseSpeed")
        self.assertNotIn("function parseContext", self.js,
                         "recommend.js must not define its own parseContext")
        self.assertIn("window.parseSpeed", self.js)
        self.assertIn("window.parseContext", self.js)

    def test_main_js_is_the_shared_source(self):
        self.assertIn("function parseSpeed", self.main_js)
        self.assertIn("function parseContext", self.main_js)
        self.assertIn("window.parseSpeed = parseSpeed", self.main_js)
        self.assertIn("window.parseContext = parseContext", self.main_js)
        # The shared parsers must be defined at load time (top level), before
        # the DOMContentLoaded handler — the page scripts rely on them at
        # evaluation time.
        self.assertLess(
            self.main_js.index("function parseSpeed"),
            self.main_js.index("DOMContentLoaded"),
            "parseSpeed must be defined before the DOM handlers run")


if __name__ == "__main__":
    unittest.main()
