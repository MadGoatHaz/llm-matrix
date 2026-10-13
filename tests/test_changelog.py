"""Changelog page (C5) — structural + contract tests.

"Nothing goes stale silently": the project's evolution is visible at
``changelog/index.html``. Runs the generator into a temp workspace and
verifies:

* the page is written, non-empty, tag-balanced, and free of template leaks;
* it carries the shared shell (nav / footer / OG tags / skip link /
  theme-color), exactly one ``<h1>`` ("Changelog") with no heading skips,
  and the front-matter title + description;
* the authored release entries render (v2.1 / v2.0 / v1.1 / v1.0, each an
  ``<h2>`` inside the ``.changelog`` section);
* the shared footer links to the changelog on **every** page with the
  correct depth-relative path (footer placement: the top nav already
  carries nine links, so the changelog — a low-frequency page — lives in
  the footer next to the Data API link).
"""

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.util import ROOT
from tests.test_generate import TagChecker
from tests.test_a11y import HeadingOrderParser

#: Every page the shared footer (and its changelog link) must cover.
ALL_PAGES = (
    "index.html", "matrix.html", "community.html", "guides.html",
    "about.html", "compare/index.html", "recommend/index.html",
    "submit/index.html", "api/index.html", "changelog/index.html",
    "guides/index.html",
)


class TestChangelogPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        cls.tmp = Path(tempfile.mkdtemp(prefix="las_changelog_"))
        # Mirror the inputs the generator needs for the full site.
        for rel in (
            "data/submissions.json",
            "tools/schema.json",
            "css/style.css",
            "js/main.js",
            "content/changelog.md",
            "content/recommend.md",
            "content/submit.md",
            "content/api.md",
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

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _page(self):
        return (self.tmp / "changelog" / "index.html").read_text(encoding="utf-8")

    # --- page existence + hygiene ----------------------------------------
    def test_page_written_nonempty(self):
        path = self.tmp / "changelog" / "index.html"
        self.assertTrue(path.exists(), "changelog/index.html was not written")
        self.assertGreater(path.stat().st_size, 0, "changelog page is empty")

    def test_tags_balanced_no_brace_leaks(self):
        text = self._page()
        checker = TagChecker()
        checker.feed(text)
        checker.close()
        self.assertEqual(checker.finished(), [], "tag imbalance")
        self.assertNotIn("{{", text, "template {{ leak")
        self.assertNotIn("}}", text, "template }} leak")

    def test_shared_shell_landmarks_and_og(self):
        text = self._page()
        self.assertIn('<html lang="en">', text)
        self.assertIn('<a class="skip-link" href="#main-content">', text)
        self.assertIn("<nav", text)
        self.assertIn("<main", text)
        self.assertIn("<footer", text)
        self.assertIn('name="theme-color"', text)
        self.assertIn('property="og:title"', text)
        self.assertIn('property="og:image"', text)

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

    # --- content contract --------------------------------------------------
    def test_front_matter_title_and_description(self):
        text = self._page()
        self.assertIn("<h1>Changelog</h1>", text)
        # The description's apostrophe is HTML-escaped by the generator.
        self.assertIn("What&#x27;s new and what changed", text)
        self.assertIn("<title>Changelog — The Local AI Stack</title>", text)

    def test_release_entries_render(self):
        text = self._page()
        self.assertIn('class="changelog"', text)
        for version in ("v2.1", "v2.0", "v1.1", "v1.0"):
            with self.subTest(version=version):
                self.assertRegex(
                    text, rf'<h2[^>]*>{re.escape(version)} — \w+ \d{{4}}</h2>',
                    f"release entry {version} missing")
        # The newest release is first (scannable, nothing goes stale).
        order = [text.index(f">{v} — ") for v in
                 ("v2.1", "v2.0", "v1.1", "v1.0")]
        self.assertEqual(order, sorted(order),
                         "releases must be newest-first")

    def test_release_lists_are_real_lists(self):
        text = self._page()
        self.assertGreaterEqual(text.count("<li>"), 8,
                                "each release carries a list of changes")

    # --- footer wiring (every page, depth-correct) --------------------------
    def test_footer_changelog_link_on_every_page(self):
        for name in ALL_PAGES:
            with self.subTest(page=name):
                text = (self.tmp / name).read_text(encoding="utf-8")
                prefix = "" if name.count("/") == 0 else "../"
                self.assertIn(f'href="{prefix}changelog/"', text,
                              f"{name} footer missing the Changelog link")

    def test_changelog_link_lives_in_the_footer(self):
        # Design decision: the top nav already carries nine links, so the
        # low-frequency changelog link sits in the shared footer (next to
        # the Data API link), not in the nav.
        text = self._page()
        footer = text.split("<footer", 1)[1]
        self.assertIn('changelog/', footer)
        nav = text.split("<nav", 1)[0] + text.split("<nav", 1)[1].split("</nav>", 1)[0]
        self.assertNotIn('changelog/', nav,
                         "the changelog link belongs in the footer, not the nav")


if __name__ == "__main__":
    unittest.main()
