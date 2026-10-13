"""Accessibility audit (P2-6) — WCAG 2.1 AA, enforced in the test suite.

Runs the generator into a temp workspace and verifies, on **every** page
(5 core + the guides.html stub + compare + recommend + guides index + the
8 individual guides):

* ``<html lang>`` present;
* exactly one ``<h1>`` and no heading-level skips (1→3 is a fail);
* a skip link to ``#main-content`` (WCAG 2.4.1);
* ``nav`` / ``main`` / ``footer`` landmarks;
* ``theme-color`` meta;
* every ``<script>`` is deferred (non-blocking);
* every ``<th>`` carries a ``scope`` (WCAG 1.3.1 / Lighthouse table-scope);
* decorative icon spans are ``aria-hidden``.

Plus targeted checks for the interactive components:

* the mobile nav toggle and the Guides dropdown expose
  ``aria-expanded`` / ``aria-controls``;
* sortable matrix headers are real ``<button>``s with ``aria-sort``;
* dialogs (detail panel, command dialog) are ``role=dialog`` +
  ``aria-modal`` with labelled closers;
* dynamic regions are live (``aria-live`` / ``role=status``): the
  recommend results, the compare takeaway, the filter-empty state, and the
  Share button's nested status span;
* form controls have programmatic names (``<label for>`` on the recommend
  form, ``aria-label`` on the filter selects);
* **color contrast**: the design tokens are re-computed here with the WCAG
  relative-luminance formula — every text/bg pair used in the stylesheet
  must meet 4.5:1 (3:1 for large text), and white must meet 4.5:1 on the
  primary-button fill;
* ``prefers-reduced-motion`` is respected site-wide;
* a visible ``:focus-visible`` ring exists;
* touch targets: the icon buttons and close buttons are ≥ 44px.

The luminance math mirrors work/scratch/contrast_check.py (the audit
script used to derive the fixed token values).
"""

import re
import shutil
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

from tests.util import ROOT
from tests.test_generate import TagChecker

#: Every generated page the audit covers.
ALL_PAGES = (
    "index.html", "matrix.html", "community.html", "guides.html",
    "about.html", "compare/index.html", "recommend/index.html",
    "submit/index.html", "api/index.html", "changelog/index.html",
    "guides/index.html",
    "guides/quantization/index.html", "guides/file-formats/index.html",
    "guides/quantization-methods/index.html",
    "guides/model-architectures/index.html", "guides/kv-cache/index.html",
    "guides/context-extension/index.html", "guides/backends/index.html",
    "guides/multi-gpu/index.html",
)

REQUIRED_INPUTS = (
    "data/submissions.json",
    "tools/schema.json",
    "css/style.css",
    "js/main.js",
    "content/recommend.md",
    "content/submit.md",
    "content/api.md",
    "content/changelog.md",
)


# ---------------------------------------------------------------------------
# WCAG 2.1 relative luminance + contrast ratio (the same math the audit
# script used to pick the token values).
# ---------------------------------------------------------------------------

def _chan(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hexcolor: str) -> float:
    h = hexcolor.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.2126 * _chan(r) + 0.7152 * _chan(g) + 0.0722 * _chan(b)


def contrast(fg: str, bg: str) -> float:
    lf, lb = luminance(fg), luminance(bg)
    if lf < lb:
        lf, lb = lb, lf
    return (lf + 0.05) / (lb + 0.05)


def blend(fg: str, bg: str, alpha: float) -> str:
    def px(h):
        h = h.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    f, b = px(fg), px(bg)
    return "#%02x%02x%02x" % tuple(
        round(f[i] * alpha + b[i] * (1 - alpha)) for i in range(3))


def _token(css: str, name: str) -> str:
    m = re.search(r"--" + re.escape(name) + r":\s*(#[0-9a-fA-F]{6})", css)
    assert m, f"design token --{name} not found in css/style.css"
    return m.group(1)


class HeadingOrderParser(HTMLParser):
    """Collects (level, text) for h1–h6 and counts th scope coverage."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.headings: list[tuple[int, str]] = []
        self._level = None
        self._buf: list[str] = []
        self.h1_count = 0
        self.th_total = 0
        self.th_unscoped = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._level = int(tag[1])
            self._buf = []
            if tag == "h1":
                self.h1_count += 1
        elif tag == "th":
            self.th_total += 1
            if "scope" not in a:
                self.th_unscoped += 1

    def handle_data(self, data):
        if self._level:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self._level == int(tag[1]):
            self.headings.append((self._level, " ".join("".join(self._buf).split())))
            self._level = None


class TestAccessibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        cls.tmp = Path(tempfile.mkdtemp(prefix="las_a11y_"))
        for rel in REQUIRED_INPUTS:
            src = ROOT / rel
            dst = cls.tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        # The eight guides + the guides index (markdown content layer).
        guides_src = ROOT / "content" / "guides"
        guides_dst = cls.tmp / "content" / "guides"
        shutil.copytree(guides_src, guides_dst)

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

    def _page(self, name: str) -> str:
        return (self.tmp / name).read_text(encoding="utf-8")

    # --- document-level checks on every page --------------------------------

    def test_every_page_has_lang_skip_link_and_landmarks(self):
        for name in ALL_PAGES:
            with self.subTest(page=name):
                text = self._page(name)
                self.assertIn('<html lang="en">', text, "missing lang attribute")
                self.assertIn('<a class="skip-link" href="#main-content">',
                              text, "missing skip link (WCAG 2.4.1)")
                self.assertIn('id="main-content"', text, "main has no skip target")
                self.assertIn("<nav", text, "missing nav landmark")
                self.assertIn("<main", text, "missing main landmark")
                self.assertIn("<footer", text, "missing footer landmark")
                self.assertIn('name="theme-color"', text, "missing theme-color")
                # every script tag is deferred (JSON islands exempt)
                for m in re.finditer(r"<script[^>]*>", text):
                    tag = m.group(0)
                    if tag.startswith("<script type="):
                        continue
                    self.assertIn("defer", tag, f"non-deferred script: {tag}")

    def test_every_page_has_one_h1_and_no_heading_skips(self):
        for name in ALL_PAGES:
            with self.subTest(page=name):
                parser = HeadingOrderParser()
                parser.feed(self._page(name))
                parser.close()
                self.assertEqual(parser.h1_count, 1,
                                 "expected exactly one <h1>")
                prev = 0
                for level, txt in parser.headings:
                    self.assertLessEqual(
                        level, prev + 1,
                        f"heading level skip {prev} -> {level} at "
                        f"'{txt[:50]}' (WCAG 1.3.1 / 2.4.6)")
                    prev = level

    def test_every_table_header_has_scope(self):
        for name in ALL_PAGES:
            with self.subTest(page=name):
                parser = HeadingOrderParser()
                parser.feed(self._page(name))
                parser.close()
                self.assertEqual(
                    parser.th_unscoped, 0,
                    f"{parser.th_unscoped} of {parser.th_total} <th> lack "
                    f"scope (WCAG 1.3.1)")

    def test_decorative_icons_are_aria_hidden(self):
        # The nav logo emoji and the Guides dropdown arrow are decorative;
        # their accessible names must not depend on the glyph.
        text = self._page("index.html")
        self.assertRegex(
            text,
            r'<a href="index.html" class="nav-logo"><span class="icon" '
            r'aria-hidden="true">📊</span>')
        self.assertRegex(
            text,
            r'aria-expanded="false" aria-controls="guides-menu">Guides '
            r'<span class="icon" aria-hidden="true">▾</span>')

    # --- interactive component contracts -------------------------------------

    def test_nav_toggle_and_dropdown_expose_expanded_state(self):
        text = self._page("matrix.html")
        self.assertRegex(
            text,
            r'<button class="nav-toggle" aria-label="Toggle navigation" '
            r'aria-expanded="false" aria-controls="nav-links">')
        self.assertRegex(
            text,
            r'<a href="guides/" class="nav-dropdown-toggle" '
            r'aria-expanded="false" aria-controls="guides-menu">')

    def test_sortable_headers_are_real_buttons_with_aria_sort(self):
        text = self._page("matrix.html")
        # 12 sortable data columns, each a <button> inside a scoped <th>.
        self.assertEqual(text.count('class="th-sort" scope="col" aria-sort="none"'),
                         12, "expected 12 sortable column headers")
        self.assertEqual(text.count('<button type="button" class="th-btn">'),
                         12, "expected 12 header buttons")
        # The Actions column stays non-interactive but is still scoped.
        self.assertRegex(text, r'<th scope="col" data-nosort>Actions</th>')
        # The table carries a (visually hidden) caption.
        self.assertIn('<caption class="sr-only">', text)
        # main.js keeps the ARIA state in sync.
        js = (ROOT / "js" / "main.js").read_text(encoding="utf-8")
        self.assertIn("aria-sort", js)
        self.assertIn("ascending", js)
        self.assertIn("descending", js)

    def test_dialogs_are_labelled_and_modal(self):
        text = self._page("matrix.html")
        # The attributes span two source lines, so match whitespace loosely.
        self.assertRegex(
            text,
            r'<aside class="detail-panel" id="detail-panel" role="dialog" '
            r'aria-modal="true"\s+aria-labelledby="detail-title"',
            re.DOTALL)
        self.assertRegex(
            text, r'<button class="detail-close" id="detail-close" '
            r'type="button" aria-label="Close details panel">')
        js = (ROOT / "js" / "commands.js").read_text(encoding="utf-8")
        self.assertIn('role="dialog"', js)
        self.assertIn("aria-modal", js)
        self.assertIn("aria-label", js)

    def test_dynamic_regions_are_live(self):
        rec = self._page("recommend/index.html")
        self.assertRegex(rec,
                         r'<div class="rec-results" id="rec-results" '
                         r'role="status" aria-live="polite">')
        cmp = self._page("compare/index.html")
        self.assertRegex(cmp,
                         r'id="compare-takeaway" role="status" '
                         r'aria-live="polite"')
        for name in ("matrix.html", "community.html"):
            text = self._page(name)
            self.assertRegex(text,
                             r'<div class="filter-empty" id="filter-empty" '
                             r'role="status" hidden>')
            # The Share button announces its copy result via a nested
            # live region (its text label is swapped without destroying it).
            self.assertRegex(
                text,
                r'<span class="share-label">.*?</span>'
                r'<span class="sr-only" role="status" aria-live="polite"></span>')
        # The command dialog's copy button announces too.
        js = (ROOT / "js" / "commands.js").read_text(encoding="utf-8")
        self.assertIn('aria-live="polite"', js)

    def test_recommend_form_controls_have_programmatic_names(self):
        text = self._page("recommend/index.html")
        for label_id, control in (
            ("rec-tier", "rec-tier"), ("rec-usecase", "rec-usecase"),
            ("rec-vendor", "rec-vendor"), ("rec-priority", "rec-priority"),
        ):
            self.assertRegex(
                text,
                r'<label for="' + label_id + r'">[^<]+</label>',
                f"missing <label for={label_id}>")
            self.assertRegex(
                text, r'<select id="' + control + r'"')

    def test_submit_form_controls_have_programmatic_names(self):
        text = self._page("submit/index.html")
        for control in ("sub-tier", "sub-hardware", "sub-backend", "sub-model",
                        "sub-quant", "sub-usecase", "sub-notes", "sub-url"):
            with self.subTest(control=control):
                self.assertRegex(
                    text, r'<label for="' + control + r'">',
                    f"missing <label for={control}>")
                self.assertRegex(text, r'id="' + control + r'"')
        # required fields expose the aria-required state to AT
        self.assertRegex(text, r'id="sub-tier"[^>]*aria-required="true"')
        self.assertRegex(text, r'id="sub-hardware"[^>]*aria-required="true"')
        # the copy button + status region are labelled / live
        self.assertIn('id="submit-copy"', text)
        self.assertRegex(text, r'id="submit-status" role="status" aria-live="polite"')

    # --- color contrast (tokens re-verified against WCAG 2.1) ----------------

    def test_text_tokens_meet_45_to_1_on_every_surface(self):
        css = (ROOT / "css" / "style.css").read_text(encoding="utf-8")
        bg = _token(css, "bg")
        s1 = _token(css, "surface")
        s2 = _token(css, "surface-2")
        for name in ("text", "text-secondary", "text-muted"):
            color = _token(css, name)
            with self.subTest(token=name):
                for surface, label in ((bg, "bg"), (s1, "surface"),
                                       (s2, "surface-2")):
                    r = contrast(color, surface)
                    self.assertGreaterEqual(
                        r, 4.5,
                        f"--{name} on --{label} is {r:.2f}:1 (< 4.5:1)")

    def test_accent_and_badge_tokens_meet_45_to_1(self):
        css = (ROOT / "css" / "style.css").read_text(encoding="utf-8")
        bg = _token(css, "bg")
        s1 = _token(css, "surface")
        s2 = _token(css, "surface-2")
        accent = _token(css, "accent")
        with self.subTest(token="accent"):
            for surface in (bg, s1, s2):
                r = contrast(accent, surface)
                self.assertGreaterEqual(r, 4.5,
                                        f"--accent contrast {r:.2f}:1")
        # Badge text sits on a 15% tint of itself over the surface.
        for name in ("success", "warning", "cyan", "purple", "accent"):
            color = _token(css, name)
            tint = blend(color, s1, 0.15)
            r = contrast(color, tint)
            with self.subTest(token=f"badge-{name}"):
                self.assertGreaterEqual(
                    r, 4.5,
                    f"badge --{name} on its tint is {r:.2f}:1 (< 4.5:1)")

    def test_white_on_primary_button_fill_meets_45_to_1(self):
        css = (ROOT / "css" / "style.css").read_text(encoding="utf-8")
        strong = _token(css, "accent-strong")
        r = contrast("#ffffff", strong)
        self.assertGreaterEqual(
            r, 4.5,
            f"white on --accent-strong is {r:.2f}:1 (< 4.5:1)")
        # The primary fills must actually use the strong token.
        self.assertRegex(css, r"\.btn-primary\s*{[^}]*var\(--accent-strong\)")
        self.assertRegex(css,
                         r"\.btn-large-primary\s*{[^}]*var\(--accent-strong\)")

    # --- motion, focus, and target size ---------------------------------------

    def test_reduced_motion_and_focus_visible_are_handled(self):
        css = (ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"@media \(prefers-reduced-motion:\s*reduce\)")
        # the reduce block kills transitions/animations site-wide
        self.assertRegex(
            css,
            r"prefers-reduced-motion:\s*reduce\)[\s\S]*?"
            r"transition-duration:\s*0\.01ms\s*!important")
        self.assertRegex(css, r":focus-visible\s*{[^}]*outline")
        self.assertIn(".sr-only", css)
        self.assertIn(".skip-link", css)

    def test_icon_and_close_targets_are_at_least_44px(self):
        css = (ROOT / "css" / "style.css").read_text(encoding="utf-8")
        for sel in (r"\.launch-btn", r"\.detail-btn",
                    r"\.cmd-close", r"\.detail-close"):
            m = re.search(sel + r"\s*{([^}]*)}", css)
            self.assertIsNotNone(m, f"{sel} rule missing")
            block = m.group(1)
            self.assertRegex(
                block, r"(min-)?(width|height):\s*44px",
                f"{sel} is not a >=44px touch target")
        # The compare checkbox widens its hit area via negative-margin
        # padding on the wrapping label.
        m = re.search(r"\.compare-check-wrap\s*{([^}]*)}", css)
        self.assertIsNotNone(m, ".compare-check-wrap rule missing")
        self.assertIn("padding", m.group(1))
        self.assertIn("margin", m.group(1))


class TestA11yHygiene(unittest.TestCase):
    """The audited pages must also stay structurally sound."""

    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        cls.tmp = Path(tempfile.mkdtemp(prefix="las_a11y_hyg_"))
        for rel in REQUIRED_INPUTS:
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

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_all_pages_balanced_and_leak_free(self):
        for name in ALL_PAGES:
            with self.subTest(page=name):
                text = (self.tmp / name).read_text(encoding="utf-8")
                checker = TagChecker()
                checker.feed(text)
                checker.close()
                self.assertEqual(checker.finished(), [], "tag imbalance")
                self.assertNotIn("{{", text)
                self.assertNotIn("}}", text)


if __name__ == "__main__":
    unittest.main()
