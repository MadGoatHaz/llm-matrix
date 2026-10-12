"""Markdown layer: ``tools/site/markdown.py`` (front-matter + rendering).

The guide layer wraps the single third-party ``markdown`` dependency. These
tests lock in (PLAN.md P3-2):

* ``split_front_matter`` — a leading ``--- ... ---`` block parses to a dict;
  absent front-matter returns the text unchanged. This is pure-stdlib regex
  parsing and runs even without the ``markdown`` package installed.
* ``render_markdown`` — tables render, fenced code renders, raw
  ``<div class="diagram">`` HTML passes through untouched (how the CSS-only
  diagrams survive the conversion), and the two a11y post-passes apply
  (``<th scope="col">`` and ``aria-hidden`` guide icons). These tests are
  skipped automatically when ``markdown`` is not installed.
"""

import unittest

from tests.util import load_tool


def _markdown_available() -> bool:
    """True when the content-layer ``markdown`` dependency is importable."""
    try:
        import markdown  # noqa: F401
        return True
    except ImportError:
        return False


class TestSplitFrontMatter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Distinct module name avoids any collision with the `markdown` pkg.
        cls.md = load_tool("tools/site/markdown.py", module_name="site_markdown")

    def test_with_front_matter(self):
        text = (
            "---\n"
            "title: Quantization Basics\n"
            "description: What a quant is\n"
            "icon: 🧮\n"
            "---\n"
            "# Body heading\n"
            "Some body text."
        )
        meta, body = self.md.split_front_matter(text)
        self.assertEqual(meta["title"], "Quantization Basics")
        self.assertEqual(meta["description"], "What a quant is")
        self.assertEqual(meta["icon"], "🧮")
        self.assertEqual(body, "# Body heading\nSome body text.")

    def test_without_front_matter_returns_text_unchanged(self):
        text = "# Just a heading\nNo front matter here."
        meta, body = self.md.split_front_matter(text)
        self.assertEqual(meta, {})
        self.assertEqual(body, text)

    def test_quoted_values_are_stripped(self):
        text = "---\ntitle: \"Quoted Title\"\nnav: 'Guides'\n---\nbody"
        meta, body = self.md.split_front_matter(text)
        self.assertEqual(meta["title"], "Quoted Title")
        self.assertEqual(meta["nav"], "Guides")
        self.assertEqual(body, "body")

    def test_comments_and_blank_lines_ignored(self):
        text = (
            "---\n"
            "# this is a comment\n"
            "\n"
            "title: Real Title\n"
            "---\n"
            "body"
        )
        meta, body = self.md.split_front_matter(text)
        self.assertEqual(meta, {"title": "Real Title"})
        self.assertEqual(body, "body")

    def test_related_list_kept_as_raw_string(self):
        text = "---\nrelated: quantization, file-formats, backends\n---\nbody"
        meta, body = self.md.split_front_matter(text)
        self.assertEqual(meta["related"], "quantization, file-formats, backends")


@unittest.skipIf(
    not _markdown_available(), "the `markdown` content dependency is not installed"
)
class TestRenderMarkdown(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.md = load_tool("tools/site/markdown.py", module_name="site_markdown")

    def test_table_renders(self):
        body = "| a | b |\n|---|---|\n| 1 | 2 |"
        html = self.md.render_markdown(body)
        self.assertIn("<table", html)
        self.assertIn("<th", html)
        self.assertIn("<td", html)

    def test_th_gets_scope_col_attribute(self):
        # a11y post-pass: every ``<th>`` becomes ``<th scope="col">``.
        body = "| a | b |\n|---|---|\n| 1 | 2 |"
        html = self.md.render_markdown(body)
        self.assertIn('<th scope="col">', html)

    def test_fenced_code_renders(self):
        body = "```bash\nllama-server -m model.gguf\n```"
        html = self.md.render_markdown(body)
        self.assertIn("<pre", html)
        self.assertIn("<code", html)
        self.assertIn("llama-server", html)

    def test_raw_html_diagram_passes_through(self):
        # Raw ``<div class="diagram">`` blocks must survive the conversion
        # untouched — this is how the CSS-only diagrams are authored inline.
        body = (
            "Intro text.\n\n"
            '<div class="diagram diagram--kv">\n'
            '  <div class="bar"></div>\n'
            "</div>\n\n"
            "After the diagram."
        )
        html = self.md.render_markdown(body)
        self.assertIn('class="diagram diagram--kv"', html)
        self.assertIn('<div class="bar"></div>', html)

    def test_guide_icon_gets_aria_hidden(self):
        # a11y post-pass: decorative guide-icon divs are hidden from the
        # accessibility tree.
        body = '<div class="guide-icon">🧮</div>\n\n# Heading'
        html = self.md.render_markdown(body)
        self.assertIn('<div class="guide-icon" aria-hidden="true">🧮</div>', html)


if __name__ == "__main__":
    unittest.main()
