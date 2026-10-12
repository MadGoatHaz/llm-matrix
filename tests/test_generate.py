"""Generator validation: ``tools/generate_site.py`` runs clean.

The generator writes into its module-level ``WORKSPACE``. To keep the test
deterministic and non-destructive, this test copies the inputs (dataset,
schema, shared assets) into a temp directory mirroring the repo layout,
points the module's path constants there, and runs ``main()``.

Assertions (per PLAN.md §5.4 structural checks):

* all 5 pages + ``data.json`` are written;
* ``data.json`` round-trips the input dataset exactly;
* every page has balanced tags (``html.parser``);
* no ``{{`` / ``}}`` template leaks in any page;
* every page carries the shared nav, footer, and OG tags.
"""

import json
import shutil
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

from tests.util import ROOT, load_tool

PAGES = ("index.html", "matrix.html", "community.html", "guides.html", "about.html")

#: Files the generator requires at runtime (authored, not generated).
REQUIRED_INPUTS = (
    "data/submissions.json",
    "tools/schema.json",
    "css/style.css",
    "js/main.js",
)


class TagChecker(HTMLParser):
    """Collects tag-balance errors for a document.

    Void elements never get pushed, so self-closing markup (``<br/>``)
    is handled by the default ``handle_startendtag`` flow without
    imbalance.
    """

    VOID = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "source", "track", "wbr",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, tuple[int, int]]] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if not self.stack:
            self.errors.append(f"closing </{tag}> with empty stack at {self.getpos()}")
            return
        open_tag, pos = self.stack.pop()
        if open_tag != tag:
            self.errors.append(
                f"<{open_tag}> opened at {pos} closed by </{tag}> at {self.getpos()}"
            )

    def finished(self):
        if self.stack:
            tag, pos = self.stack[-1]
            self.errors.append(f"<{tag}> opened at {pos} never closed")
        return self.errors


class TestGeneratorOutput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="las_test_"))
        # Mirror the repo layout inside the temp workspace.
        for rel in REQUIRED_INPUTS:
            src = ROOT / rel
            dst = cls.tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        # Point the module's path constants at the temp workspace.
        cls.module = load_tool("tools/generate_site.py")
        cls.module.WORKSPACE = cls.tmp
        cls.module.DATA_DIR = cls.tmp / "data"
        cls.module.SUBMISSIONS = cls.tmp / "data" / "submissions.json"
        cls.module.SCHEMA = cls.tmp / "tools" / "schema.json"
        cls.module.main()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_all_pages_and_data_written(self):
        for name in (*PAGES, "data.json"):
            with self.subTest(page=name):
                path = self.tmp / name
                self.assertTrue(path.exists(), f"{name} was not written")
                self.assertGreater(path.stat().st_size, 0, f"{name} is empty")

    def test_data_json_round_trips_input(self):
        # P4-4: data.json is the dataset plus the API `version` field,
        # placed first (the contract generation is visible up front).
        from tools.site import api
        with open(self.tmp / "data.json", encoding="utf-8") as f:
            out = json.load(f)
        with open(self.tmp / "data" / "submissions.json", encoding="utf-8") as f:
            src = json.load(f)
        self.assertEqual(out, {"version": api.API_VERSION, **src})

    def test_tags_balanced_on_every_page(self):
        for name in PAGES:
            with self.subTest(page=name):
                checker = TagChecker()
                checker.feed((self.tmp / name).read_text(encoding="utf-8"))
                checker.close()
                self.assertEqual(checker.finished(), [], "tag imbalance")

    def test_no_template_brace_leaks(self):
        for name in PAGES:
            with self.subTest(page=name):
                text = (self.tmp / name).read_text(encoding="utf-8")
                self.assertNotIn("{{", text)
                self.assertNotIn("}}", text)

    def test_shared_nav_footer_and_og_tags_on_every_page(self):
        for name in PAGES:
            with self.subTest(page=name):
                text = (self.tmp / name).read_text(encoding="utf-8")
                self.assertIn("<nav", text)
                self.assertIn("<footer", text)
                self.assertIn('property="og:title"', text)
                self.assertIn('property="og:image"', text)
                self.assertIn("og-image.png", text)

    def test_one_h1_and_main_landmark_per_page(self):
        for name in PAGES:
            with self.subTest(page=name):
                text = (self.tmp / name).read_text(encoding="utf-8")
                self.assertEqual(text.count("<h1>"), 1, "expected exactly one <h1>")
                self.assertIn("<main", text)


class TestGoldenRegression(unittest.TestCase):
    """The P1-0 refactor must be byte-identical to the legacy monolith.

    Regenerates every page + ``data.json`` via the new ``tools.site`` package
    into a temp workspace and compares each output byte-for-byte against the
    committed baselines in ``tests/golden/`` (captured from the pre-refactor
    ``tools/generate_site.py``). Any drift — an accidental rewrite, a template
    change, a missing escape — fails here.
    """

    #: The canonical golden set: the 5 core pages + data.json + the /api/
    #: documentation page (P4-4).
    GOLDEN = (*PAGES, "data.json", "api/index.html")

    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        cls.tmp = Path(tempfile.mkdtemp(prefix="las_golden_"))
        for rel in REQUIRED_INPUTS:
            src = ROOT / rel
            dst = cls.tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        # The /api/ page renders from content/api.md (markdown layer), so the
        # golden workspace carries the authored content dir.
        shutil.copytree(ROOT / "content", cls.tmp / "content",
                        dirs_exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_golden_baselines_exist(self):
        golden = ROOT / "tests" / "golden"
        for name in self.GOLDEN:
            with self.subTest(page=name):
                self.assertTrue(
                    (golden / name).exists(),
                    f"missing golden baseline tests/golden/{name}",
                )

    def test_all_outputs_match_golden_baselines(self):
        from tools.site import main as site_main

        site_main(
            workspace=self.tmp,
            data_dir=self.tmp / "data",
            submissions=self.tmp / "data" / "submissions.json",
            schema=self.tmp / "tools" / "schema.json",
        )
        golden = ROOT / "tests" / "golden"
        for name in self.GOLDEN:
            with self.subTest(page=name):
                new_bytes = (self.tmp / name).read_bytes()
                gold_bytes = (golden / name).read_bytes()
                self.assertEqual(
                    new_bytes,
                    gold_bytes,
                    f"{name} is not byte-identical to the golden baseline "
                    "(refactor regression)",
                )


if __name__ == "__main__":
    unittest.main()
