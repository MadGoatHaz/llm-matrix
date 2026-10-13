"""Charts & visualizations (P4-1) — structure + data-driven tests.

Runs the generator into a temp workspace and verifies:

* the Matrix carries three inline-SVG charts (VRAM distribution bar,
  backend-usage donut, model-size-vs-VRAM scatter) and the homepage
  carries two (bar + donut);
* every ``<svg>`` is self-contained and accessible: ``role="img"``,
  ``<title>`` + ``<desc>`` wired through ``aria-labelledby``, a
  responsive ``viewBox``, and no external references (no ``http``, no
  ``<script>``, no ``<image>``);
* the charts are **data-driven**, not hard-coded: the bar values equal
  the dataset's tier counts, the donut has one segment per distinct
  backend, the scatter has one point per submission with a parseable
  model size, and feeding the pure functions a synthetic dataset
  changes the output accordingly.

Also unit-tests the data helpers the charts rely on
(``utils.parse_model_size``, ``utils.estimate_vram_gb``).
"""

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.util import ROOT, load_json
from tests.test_generate import TagChecker

SVG_RE = re.compile(r"<svg[^>]*>.*?</svg>", re.DOTALL)
# The chart palette has 6 slots; a donut with more backends cycles it.
MAX_SEGMENTS = 6


def _svgs(text: str) -> list[str]:
    return SVG_RE.findall(text)


def _figs(text: str) -> int:
    return text.count('<figure class="chart-card"')


class _TempSite:
    """Generate the site once into a temp workspace (shared by tests)."""

    tmp = None

    @classmethod
    def build(cls):
        if cls.tmp is not None:
            return cls
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        cls.tmp = Path(tempfile.mkdtemp(prefix="las_charts_"))
        for rel in (
            "data/submissions.json",
            "tools/schema.json",
            "css/style.css",
            "js/main.js",
            "content/recommend.md",
            "content/submit.md",
        ):
            src = ROOT / rel
            dst = cls.tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        shutil.copytree(ROOT / "content" / "guides",
                        cls.tmp / "content" / "guides")
        from tools.site import main as site_main
        site_main(
            workspace=cls.tmp,
            data_dir=cls.tmp / "data",
            submissions=cls.tmp / "data" / "submissions.json",
            schema=cls.tmp / "tools" / "schema.json",
        )
        return cls

    @classmethod
    def page(cls, name: str) -> str:
        return (cls.tmp / name).read_text(encoding="utf-8")

    @classmethod
    def cleanup(cls):
        if cls.tmp is not None:
            shutil.rmtree(cls.tmp, ignore_errors=True)
            cls.tmp = None


class TestChartStructure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _TempSite.build()

    @classmethod
    def tearDownClass(cls):
        _TempSite.cleanup()

    def test_matrix_has_three_charts_and_homepage_two(self):
        matrix = _TempSite.page("matrix.html")
        index = _TempSite.page("index.html")
        self.assertEqual(_figs(matrix), 3, "matrix should carry 3 chart cards")
        self.assertEqual(len(_svgs(matrix)), 3, "matrix should carry 3 <svg>")
        self.assertEqual(_figs(index), 2, "homepage should carry 2 chart cards")
        self.assertEqual(len(_svgs(index)), 2, "homepage should carry 2 <svg>")

    def test_every_svg_is_accessible_and_self_contained(self):
        for name in ("matrix.html", "index.html"):
            with self.subTest(page=name):
                text = _TempSite.page(name)
                for svg in _svgs(text):
                    self.assertIn('role="img"', svg)
                    self.assertIn("<title", svg)
                    self.assertIn("<desc", svg)
                    self.assertRegex(svg, r'aria-labelledby="[^"]+ [^"]+"')
                    self.assertIn("viewBox", svg, "responsive viewBox required")
                    # no external requests / scripts / images inside the SVG
                    self.assertNotIn("http", svg)
                    self.assertNotIn("<script", svg)
                    self.assertNotIn("<image", svg)
                    self.assertNotIn('href="http', svg)

    def test_figures_carry_container_aria_label(self):
        text = _TempSite.page("matrix.html")
        for m in re.finditer(r'<figure class="chart-card" aria-label="([^"]+)">', text):
            self.assertTrue(m.group(1).strip())
        self.assertGreaterEqual(len(re.findall(
            r'<figure class="chart-card" aria-label="[^"]+">', text)), 3)

    def test_pages_stay_balanced_and_leak_free(self):
        for name in ("matrix.html", "index.html"):
            with self.subTest(page=name):
                text = _TempSite.page(name)
                checker = TagChecker()
                checker.feed(text)
                checker.close()
                self.assertEqual(checker.finished(), [], "tag imbalance")
                self.assertNotIn("{{", text)
                self.assertNotIn("}}", text)


class TestChartDataDriven(unittest.TestCase):
    """The charts must track the dataset, not hard-coded values."""

    @classmethod
    def setUpClass(cls):
        _TempSite.build()
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from tools.site import charts, utils
        cls.charts = charts
        cls.utils = utils
        cls.data = load_json("data/submissions.json")
        cls.schema = load_json("tools/schema.json")
        cls.subs = utils.real_submissions(cls.data)

    @classmethod
    def tearDownClass(cls):
        _TempSite.cleanup()

    # --- bar chart: one value per tier, matching the dataset --------------
    def test_bar_chart_counts_match_dataset(self):
        from collections import Counter
        counts = Counter(s.get("tier") for s in self.subs)
        svg = self.charts.vram_distribution(self.subs, self.schema)
        for t in self.schema["tiers"]:
            expected = counts.get(t["id"], 0)
            # the value label sits above each bar
            self.assertRegex(
                svg,
                r'<text class="bar-value"[^>]*>' + re.escape(str(expected)) + "</text>",
                f"tier {t['id']} bar should read {expected}",
            )
        # the accessible summary lists every tier count
        desc = re.search(r"<desc[^>]*>(.*?)</desc>", svg, re.DOTALL).group(1)
        self.assertIn(f"{self.schema['tiers'][0]['label']}: {counts.get('t1', 0)}", desc)
        self.assertIn(f"{self.schema['tiers'][3]['label']}: {counts.get('t4', 0)}", desc)

    def test_bar_chart_is_synthetic_data_sensitive(self):
        base = self.charts.vram_distribution(self.subs, self.schema)
        doubled = self.subs + self.subs
        grown = self.charts.vram_distribution(doubled, self.schema)
        self.assertNotEqual(base, grown, "duplicating the data must change the chart")
        self.assertIn(f"{2 * len(self.subs)} submissions",
                      re.search(r"<title[^>]*>(.*?)</title>", grown, re.DOTALL).group(1))

    def test_bar_chart_renders_empty_dataset(self):
        svg = self.charts.vram_distribution([], self.schema)
        self.assertIn('role="img"', svg)
        self.assertIn("0 submissions",
                      re.search(r"<title[^>]*>(.*?)</title>", svg, re.DOTALL).group(1))

    # --- donut: one segment per distinct backend ---------------------------
    def test_donut_has_one_segment_per_backend(self):
        from tools.site.utils import normalize_backend
        from collections import Counter
        # Empty backends (unreported) are not chart segments.
        counts = Counter(normalize_backend(s.get("backend", ""), self.schema)
                         for s in self.subs)
        counts.pop("", None)
        svg, legend = self.charts.backend_donut(self.subs, self.schema)
        segments = len(re.findall(r"<path class=\"seg-\d\"|<circle class=\"seg-\d\"", svg))
        self.assertEqual(segments, len(counts),
                         f"expected {len(counts)} segments, found {segments}")
        for b in counts:
            self.assertIn(f">{b} ", legend)
        # legend entries = backends
        self.assertEqual(len(re.findall(r"<li class=\"chart-legend-item\">", legend)),
                         len(counts))

    def test_donut_single_backend_uses_ring_fallback(self):
        one = [s for s in self.subs][:1]
        svg, legend = self.charts.backend_donut(one, self.schema)
        self.assertIn("<circle class=\"seg-1\"", svg)
        self.assertIn(">1</text>", svg)  # center total

    def test_donut_segments_respect_palette_cycle(self):
        svg, _ = self.charts.backend_donut(self.subs, self.schema)
        for i in range(1, MAX_SEGMENTS + 1):
            self.assertLessEqual(
                len(re.findall(rf"class=\"seg-{i}\"", svg)), 1,
                f"seg-{i} used more than once")

    # --- scatter: one point per submission with a parseable size -----------
    def test_scatter_point_count_matches_parseable_sizes(self):
        expected = 0
        for s in self.subs:
            size = self.utils.parse_model_size(self.utils.model_name(s))
            vram = self.utils.estimate_vram_gb(s, self.schema)
            if size is not None and vram is not None:
                expected += 1
        svg = self.charts.size_vram_scatter(self.subs, self.schema)
        dots = len(re.findall(r"<circle class=\"dot\"", svg))
        self.assertEqual(dots, expected,
                         f"expected {expected} points, found {dots}")
        # every point carries its own accessible <title>
        self.assertEqual(len(re.findall(r"<circle class=\"dot\"[^>]*><title>", svg)),
                         dots)

    def test_scatter_empty_dataset(self):
        svg = self.charts.size_vram_scatter([], self.schema)
        self.assertIn("0 submissions plotted",
                      re.search(r"<title[^>]*>(.*?)</title>", svg, re.DOTALL).group(1))

    # --- data helpers --------------------------------------------------------
    def test_parse_model_size(self):
        p = self.utils.parse_model_size
        self.assertEqual(p("samuelcardillo/Carnice-Qwen3.6-MoE-35B-A3B"), 35.0)
        self.assertEqual(p("d0xin/Swift-Qwen3.8-27B-Uncensored-FP8"), 27.0)
        self.assertEqual(p("Qwen3.8-Flash-Next (GGUF IQ3_S)"), None)  # size only in notes
        self.assertEqual(p("bartowski/Qwen_Qwen3.5-4B-GGUF"), 4.0)
        self.assertEqual(p("MaziyarPanahi/DeepSeek-R1-0528-Qwen3-8B-GGUF"), 8.0)
        self.assertEqual(p("Qwen3.6-27b-q4_KM, lfm2.5-thinking:1.2b-q8_0"), 27.0)
        self.assertEqual(p(""), None)
        self.assertEqual(p(None), None)
        self.assertEqual(p("KAT-Coder-V2.5-Dev-Q5_K_M.gguf"), None)

    def test_estimate_vram_gb_precedence(self):
        e = self.utils.estimate_vram_gb
        # notes win over hardware
        s = {"tier": "t1", "notes": "fits 12.7GB incl. KV",
             "hardware": {"description": "1x Radeon VII 16GB"}}
        self.assertEqual(e(s, self.schema), 12.7)
        # then hardware
        s = {"tier": "t1", "notes": "no size here",
             "hardware": {"description": "1x RTX 4090 24GB"}}
        self.assertEqual(e(s, self.schema), 24.0)
        # then the tier range maximum
        s = {"tier": "t4", "notes": "", "hardware": {"description": "2x R9700"}}
        self.assertEqual(e(s, self.schema), 64.0)
        # nothing at all
        s = {"tier": None, "notes": "", "hardware": {}}
        self.assertIsNone(e(s, self.schema))


class TestChartPlacementInRealPages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _TempSite.build()
        from tools.site import utils
        cls.data = load_json("data/submissions.json")
        cls.subs = utils.real_submissions(cls.data)

    @classmethod
    def tearDownClass(cls):
        _TempSite.cleanup()

    def test_matrix_section_and_homepage_section_present(self):
        matrix = _TempSite.page("matrix.html")
        self.assertIn('id="charts-title"', matrix)
        self.assertIn("The data at a glance", matrix)
        index = _TempSite.page("index.html")
        self.assertIn('id="numbers-title"', index)
        self.assertIn("By the numbers", index)

    def test_real_dataset_values_appear_in_generated_charts(self):
        # The chart title/desc must reflect the real dataset's size and t1 share.
        matrix = _TempSite.page("matrix.html")
        svg = _svgs(matrix)[0]
        total = len(self.subs)
        t1 = sum(1 for s in self.subs if s.get("tier") == "t1")
        self.assertIn(f"{total} submissions across",
                      re.search(r"<title[^>]*>(.*?)</title>", svg, re.DOTALL).group(1))
        self.assertIn(f"≤16GB: {t1}",
                      re.search(r"<desc[^>]*>(.*?)</desc>", svg, re.DOTALL).group(1))


if __name__ == "__main__":
    unittest.main()
