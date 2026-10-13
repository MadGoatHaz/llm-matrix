"""Start Here 3-step wizard (C1) — structural + contract tests.

Runs the generator into a temp workspace and verifies the wizard layer on
``recommend/index.html``:

* the wizard sits BEFORE the form (``#wizard`` precedes ``#rec-form``);
* the three steps carry the plain-language titles ("What do you have?",
  "What do you want to do?", "What matters most to you?"), steps 2-3 start
  hidden, and every step heading is focusable (``tabindex="-1"``) so the
  script can move focus to it on entry;
* every card is a real ``<button type="button">`` (not a div), its emoji
  icon is ``aria-hidden`` (the visible title + description is the
  accessible name), and its ``data-value`` is schema-legal: step 1 maps to
  conservative VRAM tiers (t2/t3/t5 + "" for "Not sure"), step 2 to the
  schema's use-case categories (+ "" for "Just exploring"), step 3 to the
  four priority values;
* the skip / refine / reset controls exist (the wizard is skippable for
  returning users; "Refine your search" opens the advanced options;
  "Start over" resets), and the form's ``<details>`` carries
  ``id="rec-advanced"`` for the script to open;
* the page stays structurally sound (balanced tags, no ``{{`` leaks, one
  ``<h1>`` with no heading-level skips) and loads ``js/wizard.js``
  deferred, after ``js/recommend.js``.

The live behavior (step progression, value mapping, event dispatch,
skip/reset, focus management) is exercised by
``work/scratch/verify_wizard_c1.js`` — a DOM shim that runs the REAL
``js/wizard.js`` against markup extracted from the REAL generated page.
"""

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.util import ROOT, load_json
from tests.test_generate import TagChecker
from tests.test_a11y import HeadingOrderParser


class TestWizardPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        cls.tmp = Path(tempfile.mkdtemp(prefix="las_wizard_"))
        # Mirror the inputs the generator needs for the full site.
        for rel in (
            "data/submissions.json",
            "tools/schema.json",
            "css/style.css",
            "js/main.js",
            "content/recommend.md",
            "content/changelog.md",
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

    # --- placement + structure ------------------------------------------
    def test_wizard_present_before_form(self):
        text = self._page()
        self.assertIn('id="wizard"', text, "wizard section missing")
        self.assertIn('id="rec-form"', text, "form missing")
        self.assertLess(
            text.index('id="wizard"'), text.index('id="rec-form"'),
            "the wizard must come BEFORE the form")

    def test_three_steps_with_plain_language_titles(self):
        text = self._page()
        for n, title in ((1, "What do you have?"),
                         (2, "What do you want to do?"),
                         (3, "What matters most to you?")):
            with self.subTest(step=n):
                self.assertIn(f'id="wizard-step-{n}"', text)
                self.assertRegex(
                    text,
                    rf'<h2 id="wizard-step-{n}-title" tabindex="-1">'
                    rf'{re.escape(title)}</h2>',
                    f"step {n} heading missing (focusable h2)")
        # Only step 1 is visible on load.
        self.assertIn('id="wizard-step-2" hidden', text)
        self.assertIn('id="wizard-step-3" hidden', text)

    def test_cards_are_real_buttons_with_schema_legal_values(self):
        text = self._page()
        schema = load_json("tools/schema.json")
        use_cases = set(schema["use_cases"])
        tiers = {t["id"] for t in schema["tiers"]}
        values = re.findall(
            r'<button type="button" class="wizard-card" '
            r'data-value="([^"]*)">', text)
        self.assertEqual(len(values), 14,
                         "expected 14 wizard cards (5 + 5 + 4)")

        step1, step2, step3 = values[:5], values[5:10], values[10:]

        # Step 1: conservative VRAM mapping — a tap never promises more
        # than the card describes (gaming -> t2, high-end -> t3,
        # multi-GPU/server -> t5, mac -> t2) + "" for "Not sure".
        self.assertIn("", step1, "'Not sure' card must carry the empty value")
        self.assertEqual(set(step1) - {""}, {"t2", "t3", "t5"},
                         "step 1 tiers must be the conservative mapping")
        self.assertTrue(set(step1) <= tiers | {""})

        # Step 2: every non-empty value is a schema-legal use case;
        # "" = "Just exploring" (no filter).
        self.assertIn("", step2, "'Just exploring' must apply no filter")
        for v in step2:
            with self.subTest(value=v):
                self.assertTrue(v == "" or v in use_cases,
                                f"step 2 value {v!r} is not schema-legal")

        # Step 3: exactly the four priority values the form offers.
        self.assertEqual(sorted(step3),
                         sorted(["speed", "quality", "context", "balanced"]))

    def test_every_card_icon_is_aria_hidden(self):
        text = self._page()
        icons = re.findall(
            r'<button type="button" class="wizard-card" data-value="[^"]*">\n'
            r'\s*<span class="icon" aria-hidden="true">[^<]+</span>', text)
        self.assertEqual(len(icons), 14,
                         "every card's emoji must be aria-hidden")

    # --- skip / refine / reset controls ----------------------------------
    def test_wizard_is_skippable(self):
        text = self._page()
        self.assertRegex(
            text,
            r'<a class="wizard-skip" href="#rec-form" id="wizard-skip">'
            r'Skip to advanced options →</a>')

    def test_refine_and_reset_actions(self):
        text = self._page()
        self.assertRegex(text,
                         r'<div class="wizard-actions" id="wizard-actions" hidden>')
        self.assertRegex(text,
                         r'<a class="btn" href="#rec-form" id="wizard-refine">'
                         r'Refine your search</a>')
        self.assertRegex(text,
                         r'<button type="button" class="btn" id="wizard-reset">'
                         r'Start over</button>')
        # The advanced <details> needs an id for "Refine your search" to open.
        self.assertRegex(text, r'<details class="rec-advanced" id="rec-advanced">')

    def test_back_buttons_on_steps_2_and_3(self):
        text = self._page()
        self.assertIn('<button type="button" class="wizard-back" data-back="1">', text)
        self.assertIn('<button type="button" class="wizard-back" data-back="2">', text)

    # --- page hygiene ------------------------------------------------------
    def test_tags_balanced_no_brace_leaks(self):
        text = self._page()
        checker = TagChecker()
        checker.feed(text)
        checker.close()
        self.assertEqual(checker.finished(), [], "tag imbalance")
        self.assertNotIn("{{", text, "template {{ leak")
        self.assertNotIn("}}", text, "template }} leak")

    def test_one_h1_and_no_heading_skips(self):
        text = self._page()
        parser = HeadingOrderParser()
        parser.feed(text)
        parser.close()
        self.assertEqual(parser.h1_count, 1, "expected exactly one <h1>")
        prev = 0
        for level, txt in parser.headings:
            self.assertLessEqual(
                level, prev + 1,
                f"heading level skip {prev} -> {level} at '{txt[:50]}'")
            prev = level

    def test_wizard_script_loaded_deferred_after_recommend(self):
        text = self._page()
        m = re.search(r'<script src="\.\./js/wizard\.js"[^>]*>', text)
        self.assertIsNotNone(m, "js/wizard.js not loaded on the page")
        self.assertIn("defer", m.group(0), "wizard.js must be deferred")
        self.assertLess(
            text.index("js/recommend.js"), text.index("js/wizard.js"),
            "wizard.js must load after recommend.js (its change handler "
            "must be registered before the wizard fires events)")


class TestWizardJsContract(unittest.TestCase):
    """Source-level locks on ``js/wizard.js``.

    The wizard is a UX layer over the form: it must write into the form's
    OWN controls and drive the recommend engine through its EXISTING change
    handler — one ranking path, not two. The live behavior is proven by
    work/scratch/verify_wizard_c1.js.
    """

    @classmethod
    def setUpClass(cls):
        cls.js = (ROOT / "js" / "wizard.js").read_text(encoding="utf-8")

    def test_writes_into_the_forms_own_controls(self):
        for sel in ("rec-tier", "rec-usecase", "rec-priority"):
            with self.subTest(control=sel):
                self.assertIn(f"getElementById('{sel}')", self.js,
                              f"wizard must drive #{sel}")

    def test_drives_the_engine_via_its_existing_change_handler(self):
        self.assertIn("CustomEvent('change'", self.js,
                      "wizard must fire the selects' change events")
        self.assertIn("wizard: true", self.js,
                      "script-dispatched events must be marked so a real "
                      "user change can be told apart")

    def test_no_network_no_frameworks(self):
        # The static-site promise: the wizard is pure DOM.
        self.assertNotIn("fetch(", self.js)
        self.assertNotIn("http", self.js)

    def test_respects_reduced_motion(self):
        self.assertIn("prefers-reduced-motion", self.js)

    def test_skip_refine_reset_and_default_priority_wired(self):
        for control in ("wizard-skip", "wizard-refine", "wizard-reset"):
            self.assertIn(control, self.js, f"#{control} handler missing")
        self.assertIn("'balanced'", self.js,
                      "'Start over' must restore the form's default priority")

    def test_only_acts_on_the_recommend_page(self):
        self.assertRegex(
            self.js,
            r"var wizard = document\.getElementById\('wizard'\);\s*"
            r"if \(!wizard\) return;")


if __name__ == "__main__":
    unittest.main()
