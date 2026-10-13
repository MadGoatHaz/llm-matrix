"""Row detail panel (P2-5) — structural + contract tests.

Runs the generator into a temp workspace and verifies:

* the Matrix carries the ``#detail-panel`` (``role=dialog``,
  ``aria-modal``, ``aria-labelledby``, and closed by default via
  ``aria-hidden`` + ``inert``) plus the ``#detail-scrim``;
* every real row is a clickable, keyboard-focusable affordance:
  ``class="data-row"``, ``tabindex="0"``, ``aria-haspopup="dialog"``,
  and an ⓘ ``data-detail-sub`` button in the Actions cell;
* the ``#commands-config`` island carries ``source.post_id`` +
  ``username`` for every submission (the forum deep-link data);
* ``js/main.js`` implements the panel behavior: open/populate/close,
  the focus trap (Tab cycling), Escape-to-close, focus restoration,
  the ``#<row-id>`` hash deep link, and the forum deep-link format;
* ``css/style.css`` defines the slide-in ``.detail-panel``, the
  full-screen mobile variant, and the ``prefers-reduced-motion``
  fallback.
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


class TestDetailPanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        cls.tmp = Path(tempfile.mkdtemp(prefix="las_detail_"))
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

    def _island(self, text):
        m = ISLAND_RE.search(text)
        self.assertIsNotNone(m, "commands-config island missing")
        return json.loads(m.group(1))

    # --- panel shell ------------------------------------------------------------
    def test_panel_shell_is_an_accessible_dialog(self):
        text = self._page("matrix.html")
        m = re.search(r'<aside class="detail-panel" id="detail-panel"[^>]*>', text)
        self.assertIsNotNone(m, "#detail-panel missing from the matrix")
        shell = m.group(0)
        self.assertIn('role="dialog"', shell)
        self.assertIn('aria-modal="true"', shell)
        self.assertIn('aria-labelledby="detail-title"', shell)
        # closed by default: hidden from AT and the tab order
        self.assertIn('aria-hidden="true"', shell)
        self.assertIn("inert", shell)
        self.assertIn('id="detail-scrim"', text)
        self.assertIn('id="detail-close"', text)
        self.assertIn('id="detail-body"', text)

    # --- per-row affordances ------------------------------------------------------
    def test_every_row_is_clickable_and_focusable(self):
        text = self._page("matrix.html")
        real = self._real_subs()
        for sub in real:
            with self.subTest(sub=sub["id"]):
                m = re.search(r'<tr id="' + re.escape(sub["id"]) + r'"[^>]*>', text)
                self.assertIsNotNone(m, f"row for {sub['id']} not found")
                tag = m.group(0)
                self.assertIn('class="data-row', tag)
                self.assertIn('tabindex="0"', tag)
                self.assertIn('aria-haspopup="dialog"', tag)
        self.assertEqual(text.count("data-detail-sub="), len(real),
                         "one ⓘ detail button per real row")

    # --- island carries the forum deep-link data -----------------------------------
    def test_island_carries_source_for_forum_link(self):
        config = self._island(self._page("matrix.html"))
        real = self._real_subs()
        self.assertEqual({s["id"] for s in config["submissions"]},
                         {s["id"] for s in real})
        for s in config["submissions"]:
            with self.subTest(sub=s["id"]):
                self.assertIn("source", s)
                self.assertIsInstance(s["source"]["post_id"], int,
                                      "post_id needed for the #post-N deep link")
                self.assertTrue(s["source"]["username"])
                self.assertNotIn("raw", s, "verbose raw block must stay out")

    # --- OS/driver is exposed to the panel (P0-3) ------------------------------
    def test_detail_panel_shows_os_driver(self):
        # The schema registry declares os_driver as a detail-panel field; the
        # island must carry it on every row and main.js must render it.
        js = (ROOT / "js" / "main.js").read_text(encoding="utf-8")
        self.assertIn("os_driver", js, "detail panel must render the OS/driver field")
        config = self._island(self._page("matrix.html"))
        for s in config["submissions"]:
            with self.subTest(sub=s["id"]):
                self.assertIn("os_driver", s, "island row missing os_driver")
        by_id = {s["id"]: s for s in config["submissions"]}
        self.assertEqual(by_id["post_22_sgtawesomesauce_0"]["os_driver"],
                         "Linux/ROCm")

    # --- main.js implements the panel behavior --------------------------------------
    def test_main_js_panel_behavior(self):
        js = (ROOT / "js" / "main.js").read_text(encoding="utf-8")
        # open/populate/close
        self.assertIn("detail-panel", js)
        self.assertIn("detail-scrim", js)
        # focus management
        self.assertIn("Escape", js)
        self.assertIn("focus", js)
        self.assertIn("lastFocused", js)
        # the focus trap cycles Tab inside the dialog
        self.assertIn("shiftKey", js)
        # aria/inert toggling
        self.assertIn("aria-hidden", js)
        self.assertIn("inert", js)
        # the #<row-id> hash deep link (open on load, write on open,
        # clear on close)
        self.assertIn("location.hash", js)
        # the forum deep link: <thread>#post-<post_id>
        self.assertIn("forum.level1techs.com/t/256443", js)
        self.assertIn("#post-", js)
        # reuses the P2-3 launch-command dialog
        self.assertIn("data-launch-sub", js)
        # add-to-comparison toggles the row's compare checkbox
        self.assertIn("compare-check", js)
        self.assertIn("aria-pressed", js)

    # --- CSS: slide-in, mobile full-screen, reduced motion -------------------------
    def test_css_detail_panel_and_reduced_motion(self):
        css = (ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".detail-panel", css)
        # hidden off-screen, slides in
        self.assertIn("translateX(100%)", css)
        self.assertIn(".detail-panel.open", css)
        self.assertIn(".detail-scrim", css)
        # body scroll lock while open
        self.assertIn("body.detail-open", css)
        # reduced-motion fallback (no forced animation)
        self.assertRegex(css, r"prefers-reduced-motion:\s*reduce")
        # full-screen on small screens
        self.assertRegex(css, r"@media \(max-width: 768px\)[\s\S]*?\.detail-panel\s*\{\s*width:\s*100%")

    # --- hygiene --------------------------------------------------------------------
    def test_matrix_still_balanced_and_leak_free(self):
        text = self._page("matrix.html")
        checker = TagChecker()
        checker.feed(text)
        checker.close()
        self.assertEqual(checker.finished(), [], "tag imbalance")
        self.assertNotIn("{{", text)
        self.assertNotIn("}}", text)
        self.assertEqual(text.count("<h1>"), 1)


if __name__ == "__main__":
    unittest.main()
