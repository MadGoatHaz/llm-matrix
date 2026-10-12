"""Shareable filters (P2-4) — structural + contract tests.

Runs the generator into a temp workspace and verifies:

* the Matrix carries all six filter axes (search + tier + vendor +
  backend + use-case + engine-mode) plus Reset and the 🔗 Share button;
* the use-case options come from ``schema.use_cases`` (minus "Other")
  and the engine-mode options from ``schema.engine_modes``;
* every real row carries a ``data-use-case`` attribute normalized from
  the free-text ``use_cases`` (via ``utils.match_use_cases``) and a
  ``data-mode`` attribute;
* known free-text rows normalize to the expected categories;
* a ``#filter-empty`` status region (with a clear button) is present;
* the Community page carries the same filter bar and every setup-list
  item carries the data attributes the filter reads;
* ``js/main.js`` implements the URL contract: restore from
  ``URLSearchParams`` on load, ``history.pushState`` for discrete
  changes, ``history.replaceState`` for typing, ``popstate`` handling,
  and the share button's clipboard copy.
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

ISLAND_RE = re.compile(
    r'<script type="application/json" id="commands-config">(.*?)</script>',
    re.DOTALL)

FILTER_AXES = ("tier", "vendor", "backend", "use-case", "mode")


def _select_block(text: str, data_filter: str) -> str:
    """The <select data-filter=...>...</select> block for one axis."""
    m = re.search(
        r'<select class="filter-select" data-filter="' + re.escape(data_filter)
        + r'".*?</select>', text, re.DOTALL)
    assert m, f"filter select for '{data_filter}' not found"
    return m.group(0)


def _option_values(block: str) -> list[str]:
    return re.findall(r'<option value="([^"]*)">', block)


class TestShareableFilters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        cls.tmp = Path(tempfile.mkdtemp(prefix="las_filters_"))
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

    # --- Matrix filter bar ------------------------------------------------
    def test_matrix_has_all_six_filter_axes(self):
        text = self._page("matrix.html")
        self.assertIn('id="filter-search"', text)
        for axis in FILTER_AXES:
            with self.subTest(axis=axis):
                self.assertIn(f'data-filter="{axis}"', text)
        self.assertIn('id="filter-reset"', text)
        self.assertIn('id="filter-share"', text)

    def test_use_case_options_match_schema(self):
        text = self._page("matrix.html")
        schema = load_json("tools/schema.json")
        values = [v for v in _option_values(_select_block(text, "use-case")) if v]
        expected = [c for c in schema["use_cases"] if c != "Other"]
        self.assertEqual(values, expected,
                         "use-case options must be the schema categories (minus Other)")

    def test_engine_mode_options_match_schema(self):
        text = self._page("matrix.html")
        schema = load_json("tools/schema.json")
        values = [v for v in _option_values(_select_block(text, "mode")) if v]
        self.assertEqual(values, schema["engine_modes"])

    # --- Row data attributes (normalized at gen time) ----------------------
    def test_every_row_carries_use_case_and_mode_attrs(self):
        text = self._page("matrix.html")
        for sub in self._real_subs():
            with self.subTest(sub=sub["id"]):
                m = re.search(
                    r'<tr id="' + re.escape(sub["id"]) + r'"[^>]*>', text)
                self.assertIsNotNone(m, f"row for {sub['id']} not found")
                tag = m.group(0)
                expected_uc = self._utils.match_use_cases(sub.get("use_cases"),
                                                          load_json("tools/schema.json"))
                uc = expected_uc[0] if expected_uc else ""
                mode = self._utils.clean_value(sub.get("engine_mode"))
                self.assertIn(f'data-use-case="{uc}"', tag,
                              f"{sub['id']}: data-use-case should be {uc!r}")
                self.assertIn(f'data-mode="{mode}"', tag,
                              f"{sub['id']}: data-mode should be {mode!r}")

    def test_known_free_text_normalizations(self):
        text = self._page("matrix.html")
        cases = {
            # "LLM-assisted coding / technical documentation" -> Agentic Coding
            "post_2_madgoat_1": ("Agentic Coding", ""),
            # "Coding, Security Research (DoS attack tracking)" -> Agentic Coding first
            "post_2_madgoat_2": ("Agentic Coding", ""),
            # the only hybrid-flagged submission
            "post_2_madgoat_3": ("Agentic Coding", "Hybrid (VRAM+RAM+SSD)"),
            # empty use_cases -> empty attribute
            "post_6_burhan_0": ("", ""),
        }
        for sub_id, (uc, mode) in cases.items():
            with self.subTest(sub=sub_id):
                m = re.search(r'<tr id="' + re.escape(sub_id) + r'"[^>]*>', text)
                self.assertIsNotNone(m)
                self.assertIn(f'data-use-case="{uc}"', m.group(0))
                self.assertIn(f'data-mode="{mode}"', m.group(0))

    # --- Empty state ---------------------------------------------------------
    def test_empty_state_region_with_clear_button(self):
        for name in ("matrix.html", "community.html"):
            with self.subTest(page=name):
                text = self._page(name)
                m = re.search(r'<div class="filter-empty" id="filter-empty"[^>]*>', text)
                self.assertIsNotNone(m, f"{name} missing #filter-empty")
                self.assertIn('role="status"', m.group(0))
                self.assertIn("hidden", m.group(0))
                self.assertIn('id="filter-empty-clear"', text)

    # --- Community page carries the same contract -----------------------------
    def test_community_has_same_filter_bar(self):
        text = self._page("community.html")
        self.assertIn('id="filter-search"', text)
        for axis in FILTER_AXES:
            with self.subTest(axis=axis):
                self.assertIn(f'data-filter="{axis}"', text)
        self.assertIn('id="filter-share"', text)
        self.assertIn('id="filter-reset"', text)

    def test_community_setup_items_carry_filter_attrs(self):
        text = self._page("community.html")
        real = self._real_subs()
        items = re.findall(r'<li data-sub-id="([^"]*)"', text)
        self.assertEqual(len(items), len(real), "one data-sub-id per real submission")
        self.assertEqual(set(items), {s["id"] for s in real})
        for sub in real:
            with self.subTest(sub=sub["id"]):
                m = re.search(r'<li data-sub-id="' + re.escape(sub["id"]) + r'"[^>]*>', text)
                self.assertIsNotNone(m)
                for attr in ("data-tier", "data-vendor", "data-backend",
                             "data-use-case", "data-mode"):
                    self.assertIn(attr, m.group(0))

    # --- main.js implements the URL contract -----------------------------------
    def test_main_js_url_sync_contract(self):
        js = (ROOT / "js" / "main.js").read_text(encoding="utf-8")
        # restore on load
        self.assertIn("URLSearchParams", js)
        # discrete changes push, typing replaces
        self.assertIn("history.pushState", js)
        self.assertIn("history.replaceState", js)
        # back/forward
        self.assertIn("popstate", js)
        # the six param keys (hyphenated data-filter -> underscore URL key)
        for key in ("tier", "vendor", "backend", "use_case", "mode", "q"):
            with self.subTest(key=key):
                self.assertIn(key, js)
        # the share button copies the current URL to the clipboard
        self.assertIn("filter-share", js)
        self.assertIn("navigator.clipboard", js)

    # --- hygiene ---------------------------------------------------------------
    def test_pages_still_balanced_and_leak_free(self):
        for name in ("matrix.html", "community.html"):
            with self.subTest(page=name):
                text = self._page(name)
                checker = TagChecker()
                checker.feed(text)
                checker.close()
                self.assertEqual(checker.finished(), [], "tag imbalance")
                self.assertNotIn("{{", text)
                self.assertNotIn("}}", text)
                self.assertEqual(text.count("<h1>"), 1)


if __name__ == "__main__":
    unittest.main()
