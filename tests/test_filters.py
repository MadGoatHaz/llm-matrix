"""Shareable filters (P2-4) + advanced filtering (P4-2) — structural +
contract tests.

Runs the generator into a temp workspace and verifies:

* the Matrix carries all six filter axes (search + tier + vendor +
  backend + use-case + engine-mode) plus Clear-all and the 🔗 Share
  button; Backend and Use Case are **multi-select** dropdowns (P4-2),
  the other axes stay single-select;
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
  and the share button's clipboard copy;
* P4-2: the sort dropdown (VRAM / model size / speed / date) + direction
  toggle, the active-filter chips container, the live "Showing N of M"
  count, each row's ``data-search`` blob (full-field text search incl.
  notes) and ``data-sort-*`` hints, and the row re-entry transition
  (killed by the site-wide ``prefers-reduced-motion`` block).
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


def _multiselect_block(text: str, data_filter: str) -> str:
    """The <div class="multiselect" data-filter=...> block for one axis (P4-2)."""
    start = text.find(f'class="multiselect" data-filter="{data_filter}"')
    assert start != -1, f"multiselect for '{data_filter}' not found"
    end = text.find("</div>\n    </div>", start)
    assert end != -1, f"multiselect close for '{data_filter}' not found"
    return text[start - 11:end]


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
        # P4-2: the use-case axis is a multi-select (checkboxes), not a
        # <select> — its options must still be the schema categories.
        text = self._page("matrix.html")
        schema = load_json("tools/schema.json")
        block = _multiselect_block(text, "use-case")
        values = re.findall(r'<input type="checkbox" value="([^"]*)"', block)
        expected = [c for c in schema["use_cases"] if c != "Other"]
        self.assertEqual(values, expected,
                         "use-case options must be the schema categories (minus Other)")

    def test_engine_mode_options_match_schema(self):
        text = self._page("matrix.html")
        schema = load_json("tools/schema.json")
        values = [v for v in _option_values(_select_block(text, "mode")) if v]
        self.assertEqual(values, schema["engine_modes"])

    def test_backend_axis_is_multiselect_with_data_backends(self):
        text = self._page("matrix.html")
        block = _multiselect_block(text, "backend")
        values = re.findall(r'<input type="checkbox" value="([^"]*)"', block)
        # one checkbox per distinct (normalized) backend in the dataset
        expected = sorted({
            self._utils.normalize_backend(s.get("backend", ""),
                                          load_json("tools/schema.json"))
            for s in self._real_subs()
        } - {""})
        self.assertEqual(sorted(values), expected,
                         "backend multi-select must offer the dataset's backends")

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
            # "Document Q&A, Deep Research, Brainstorming, Coding" ->
            # primary category (first in schema order) is Agentic Coding
            "post_6_burhan_0": ("Agentic Coding", "Hybrid (VRAM+RAM)"),
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


class TestAdvancedFiltering(unittest.TestCase):
    """P4-2: multi-select, full-field search, sort, chips, count, URL sync."""

    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        cls.tmp = Path(tempfile.mkdtemp(prefix="las_p42_"))
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

    # --- multi-select structure --------------------------------------------
    def test_multiselects_are_disclosure_button_plus_checkbox_menu(self):
        text = self._page("matrix.html")
        for axis in ("backend", "use-case"):
            with self.subTest(axis=axis):
                block = _multiselect_block(text, axis)
                self.assertIn('class="multiselect-toggle"', block)
                self.assertIn('aria-expanded="false"', block)
                self.assertRegex(block, r'aria-controls="ms-[a-z_]+-menu"')
                self.assertIn('class="multiselect-menu"', block)
                self.assertIn("hidden", block)
                self.assertGreaterEqual(
                    len(re.findall(r'<input type="checkbox"', block)), 2,
                    f"{axis} menu needs real checkboxes")

    # --- chips + count + clear-all ------------------------------------------
    def test_chips_container_result_count_and_clear_all(self):
        text = self._page("matrix.html")
        self.assertIn('id="filter-chips"', text)
        self.assertRegex(text, r'<p class="filter-count" id="filter-count" '
                              r'role="status" aria-live="polite">')
        m = re.search(r'<button id="filter-reset"[^>]*>([^<]*)</button>', text)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "Clear all filters")

    # --- sort dropdown -------------------------------------------------------
    def test_sort_dropdown_and_direction_toggle(self):
        text = self._page("matrix.html")
        self.assertIn('id="filter-sort"', text)
        for value in ("default", "vram", "size", "speed", "date"):
            with self.subTest(value=value):
                self.assertIn(f'<option value="{value}">', text)
        self.assertRegex(
            text,
            r'<button id="filter-dir" class="btn" type="button" '
            r'aria-label="Toggle sort direction[^"]*" aria-pressed="false">')

    # --- row data attributes for search + sort -------------------------------
    def test_rows_carry_search_blob_and_sort_hints(self):
        text = self._page("matrix.html")
        for sub in self._utils.real_submissions(load_json("data/submissions.json")):
            with self.subTest(sub=sub["id"]):
                m = re.search(r'<tr id="' + re.escape(sub["id"]) + r'"[^>]*>', text)
                self.assertIsNotNone(m, f"row for {sub['id']} not found")
                tag = m.group(0)
                # full-field search blob (lowercase, escaped)
                self.assertIn("data-search=", tag)
                blob = re.search(r'data-search="([^"]*)"', tag).group(1)
                self.assertEqual(blob, blob.lower(), "data-search must be lowercase")
                self.assertGreater(len(blob), 10)
                # the notes are in the blob (they are not a table column)
                notes = self._utils.clean_value(sub.get("notes"))
                if notes:
                    self.assertIn(notes.lower()[:20], blob)
                # sort hints
                for attr in ("data-sort-vram", "data-sort-size",
                             "data-sort-speed", "data-sort-date"):
                    self.assertIn(attr, tag, f"{sub['id']} missing {attr}")
                # ISO date always present
                date = re.search(r'data-sort-date="([^"]*)"', tag).group(1)
                self.assertRegex(date, r"^\d{4}-\d{2}-\d{2}$")

    def test_sort_hints_match_known_rows(self):
        text = self._page("matrix.html")
        # "MoE A3B — fits 12.7GB incl. KV" + 35B-A3B name
        tag = re.search(r'<tr id="post_2_madgoat_1"[^>]*>', text).group(0)
        self.assertIn('data-sort-vram="12.7"', tag)
        self.assertIn('data-sort-size="35"', tag)
        # 27B dense at 48GB hardware
        tag = re.search(r'<tr id="post_2_madgoat_2"[^>]*>', text).group(0)
        self.assertIn('data-sort-size="27"', tag)
        self.assertIn('data-sort-vram="48"', tag)
        # size unknown (125B only in notes) -> empty hint
        tag = re.search(r'<tr id="post_2_madgoat_3"[^>]*>', text).group(0)
        self.assertIn('data-sort-size=""', tag)

    # --- main.js implements the extended contract ----------------------------
    def test_main_js_extended_url_contract(self):
        js = (ROOT / "js" / "main.js").read_text(encoding="utf-8")
        # repeated multi-value params + restore via getAll
        self.assertIn("params.append", js)
        self.assertIn("getAll", js)
        # the new param keys
        for key in ("sort", "dir"):
            with self.subTest(key=key):
                self.assertIn(key, js)
        # full-field search via the row blob
        self.assertIn("dataset.search", js)
        # chips, count, sort, multiselect machinery
        for needle in ("filter-chips", "filter-count", "filter-sort",
                       "multiselect-toggle", "multiselect-label",
                       "updateMsLabel", "renderChips"):
            with self.subTest(needle=needle):
                self.assertIn(needle, js)
        # row re-entry transition
        self.assertIn("row-enter", js)
        # multi-select disclosure ARIA
        self.assertIn('aria-expanded', js)

    def test_reduced_motion_covers_row_transition(self):
        css = (ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn("row-fade-in", css)
        self.assertRegex(css, r"@media \(prefers-reduced-motion:\s*reduce\)[\s\S]*?"
                             r"transition-duration:\s*0\.01ms\s*!important")
        # the transition classes are part of the design system (style.css),
        # not inline styles
        for sel in (".multiselect-toggle", ".multiselect-option", ".filter-chip",
                    ".filter-count", ".chart-svg"):
            with self.subTest(sel=sel):
                self.assertRegex(css, re.escape(sel) + r"\s*{",
                                 f"{sel} missing from style.css")

    # --- community page keeps the single-select contract ----------------------
    def test_community_keeps_single_selects(self):
        text = self._page("community.html")
        # no multi-selects on the community page
        self.assertNotIn('class="multiselect"', text)
        # but all five single-select axes + search remain
        for axis in ("tier", "vendor", "backend", "use-case", "mode"):
            with self.subTest(axis=axis):
                self.assertIn(_select_block(text, axis), text)
        self.assertIn('id="filter-search"', text)
        self.assertNotIn('id="filter-chips"', text)
        self.assertNotIn('id="filter-sort"', text)


if __name__ == "__main__":
    unittest.main()
