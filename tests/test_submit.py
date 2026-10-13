"""Submit form (P3-4 / B10) — the 3-field minimum contract.

The form used to require 7 fields (tier, hardware, backend, model, quant,
use case, notes) while its own copy promised "30 seconds" — a newcomer who
doesn't know their "primary use case" from a 15-item list bounced. B10
reduces the required set to the minimum for a useful entry:

    VRAM tier + hardware + model

Everything else (backend, quant, speed, use case, notes, …) is optional
(encouraged): the labels say so, the use case carries a "not sure?" hint,
the backend carries a "helps others find your setup" nudge, the JS only
blocks on the 3 required fields, and the generated block omits empty
optional fields entirely.

Runs the generator into a temp workspace and locks the HTML contract; the
live form behavior (a 3-field submit succeeding, the nudge, the block
assembly) is exercised by work/scratch/verify_submit_b10.js (a DOM shim
running the real js/submit.js).
"""

import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.util import ROOT


class TestSubmitForm(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        cls.tmp = Path(tempfile.mkdtemp(prefix="las_submit_"))
        for rel in (
            "data/submissions.json",
            "tools/schema.json",
            "css/style.css",
            "js/main.js",
            "content/submit.md",
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
        return (self.tmp / "submit" / "index.html").read_text(encoding="utf-8")

    def _js(self):
        return (ROOT / "js" / "submit.js").read_text(encoding="utf-8")

    # --- page existence --------------------------------------------------
    def test_page_written_nonempty(self):
        path = self.tmp / "submit" / "index.html"
        self.assertTrue(path.exists(), "submit/index.html was not written")
        self.assertGreater(path.stat().st_size, 0, "submit page is empty")

    # --- the 3-field minimum ---------------------------------------------
    def test_exactly_three_required_fields(self):
        text = self._page()
        for req in ("sub-tier", "sub-hardware", "sub-model"):
            with self.subTest(field=req):
                self.assertRegex(
                    text,
                    r'id="' + req + r'"[^>]*required aria-required="true"',
                    f"{req} must stay required")
        for opt in ("sub-backend", "sub-quant", "sub-usecase", "sub-notes"):
            with self.subTest(field=opt):
                m = re.search(
                    r'<(?:select|input|textarea)[^>]*id="' + opt + r'"[^>]*>',
                    text)
                self.assertIsNotNone(m, f"form is missing #{opt}")
                self.assertNotIn("required", m.group(0),
                                 f"{opt} must NOT be required (B10)")

    def test_required_fields_get_asterisk_marker(self):
        text = self._page()
        asterisks = text.count('<span class="req" title="Required">*</span>')
        self.assertEqual(asterisks, 3,
                         "exactly the 3 required fields carry the ' *' marker")

    def test_optional_fields_labelled(self):
        text = self._page()
        self.assertGreaterEqual(
            text.count('<span class="opt">(optional)</span>'), 7,
            "optional fields must carry a '(optional)' label")

    # --- the encouragement copy -------------------------------------------
    def test_use_case_hint_not_sure(self):
        text = self._page()
        self.assertIn("Not sure? Pick the closest", text,
                      "use case needs the 'not sure' helper text")
        self.assertIn("leave it blank and we'll figure it out", text)

    def test_backend_nudge_helps_others_find(self):
        text = self._page()
        self.assertIn(
            "Adding your backend and quant helps others find your setup!",
            text,
            "optional fields need encouragement, not requirements")

    def test_copy_says_three_fields(self):
        md = (ROOT / "content" / "submit.md").read_text(encoding="utf-8")
        self.assertIn("Only three fields are required", md,
                      "the '30 seconds' promise must name the 3 fields")
        self.assertIn("VRAM tier, hardware, and model", md)

    # --- the JS validation contract ---------------------------------------
    def test_js_required_list_is_three_fields(self):
        m = re.search(r"var REQUIRED = \[([^\]]+)\]", self._js())
        self.assertIsNotNone(m, "submit.js lost its REQUIRED list")
        ids = re.findall(r"'([^']+)'", m.group(1))
        self.assertEqual(ids, ["sub-tier", "sub-hardware", "sub-model"],
                         "B10: only tier + hardware + model block submission")

    def test_js_blocks_only_on_required_fields(self):
        js = self._js()
        # The nudge exists and is appended to the post-submit status.
        self.assertIn("function optionalNudge", js)
        self.assertIn("helps others find your setup", js)

    def test_js_omits_empty_optional_fields_from_block(self):
        js = self._js()
        self.assertIn("if (v) lines.push(key + ': ' + v);", js,
                      "empty optional fields must be omitted from the block")


if __name__ == "__main__":
    unittest.main()
