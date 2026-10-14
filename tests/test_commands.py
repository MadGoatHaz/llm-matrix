"""Launch-command generator (P2-3) — structural + contract tests.

Runs the generator into a temp workspace and verifies the launch-command
feature and the cross-page changes it requires:

* the ``#commands-config`` island is present on the Matrix, Recommend, and
  Compare pages, parses, matches the schema's backends/tiers, and carries a
  trimmed submission per real row;
* the Backends guide opts into the tool via ``extra_scripts`` (loads
  ``js/commands.js`` at its depth-2 path, carries the island, and embeds the
  "pick a backend" widget);
* the Matrix has a launch button (``data-launch-sub``) on each real row;
* the Recommend page loads ``js/commands.js`` after ``js/recommend.js``;
* ``js/commands.js`` carries a command template for each major backend
  (llama.cpp, Ollama, vLLM, Strata, Radiance, MLX, …) plus the GUI backends
  and a graceful unknown-backend fallback, and wires an accessible dialog +
  clipboard copy.
"""

import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.util import ROOT, load_json

ISLAND_RE = re.compile(
    r'<script type="application/json" id="commands-config">(.*?)</script>',
    re.DOTALL)

# The backends the command map must cover (from schema.json).
MAP_BACKENDS = (
    "llama.cpp", "llama-swap", "Ollama", "vLLM", "Strata", "Radiance",
    "MLX", "Colibri", "TensorRT-LLM", "LM Studio", "Unsloth Desktop",
)


class TestCommands(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        cls.tmp = Path(tempfile.mkdtemp(prefix="las_commands_"))
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
        # Also copy the Backends guide so the guide opt-in is testable.
        bg_src = ROOT / "content" / "guides" / "backends.md"
        bg_dst = cls.tmp / "content" / "guides" / "backends.md"
        bg_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bg_src, bg_dst)

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

    def _real_subs(self):
        return self._utils.real_submissions(load_json("data/submissions.json"))

    def _island(self, text):
        m = ISLAND_RE.search(text)
        self.assertIsNotNone(m, "commands-config island missing")
        return json.loads(m.group(1))

    # --- island present on every access page --------------------------
    def test_island_on_matrix_recommend_compare(self):
        schema = load_json("tools/schema.json")
        real = self._real_subs()
        for name in ("matrix.html", "recommend/index.html", "compare/index.html"):
            with self.subTest(page=name):
                text = (self.tmp / name).read_text(encoding="utf-8")
                config = self._island(text)
                self.assertEqual(config["backends"], schema["backends"])
                self.assertEqual(config["tiers"], schema["tiers"])
                self.assertEqual({s["id"] for s in config["submissions"]},
                                 {s["id"] for s in real})

    def test_matrix_has_a_launch_button_per_row(self):
        text = (self.tmp / "matrix.html").read_text(encoding="utf-8")
        real = self._real_subs()
        self.assertEqual(text.count('data-launch-sub='), len(real))

    def test_recommend_loads_commands_after_recommend_js(self):
        text = (self.tmp / "recommend/index.html").read_text(encoding="utf-8")
        self.assertIn("js/recommend.js", text)
        self.assertIn("js/commands.js", text)
        self.assertLess(text.index("js/recommend.js"), text.index("js/commands.js"))

    # --- the Backends guide opts into the tool ------------------------
    def test_backends_guide_has_widget_island_and_script(self):
        guide = (self.tmp / "guides" / "backends" / "index.html")
        self.assertTrue(guide.exists(), "backends guide was not generated")
        text = guide.read_text(encoding="utf-8")
        self.assertIn('data-cmd-picker', text, "guide is missing the picker widget")
        self._island(text)  # raises if the island is absent
        # depth 2 -> ../../ prefix
        self.assertRegex(text, r'src="\.\./\.\./js/commands\.js"')

    # --- the command map covers the major backends --------------------
    def test_commands_js_covers_the_backend_map(self):
        js = (ROOT / "js" / "commands.js").read_text(encoding="utf-8")
        self.assertIn("COMMAND_MAP", js)
        for backend in MAP_BACKENDS:
            with self.subTest(backend=backend):
                self.assertIn("'" + backend + "'", js,
                              f"command map is missing the {backend} template")
        self.assertIn("isGui", js)
        self.assertIn("isUnknown", js)

    def test_commands_js_has_copy_and_accessible_dialog(self):
        js = (ROOT / "js" / "commands.js").read_text(encoding="utf-8")
        self.assertIn("navigator.clipboard", js)
        self.assertIn('role="dialog"', js)
        self.assertIn("aria-modal", js)

    def test_no_private_speed_context_parsers(self):
        # E7: parseSpeed / parseContext live ONCE in js/main.js (window.*) —
        # commands.js must consume the shared implementations, not its own
        # copies (duplicate parsers are how the same string ends up two
        # different numbers).
        js = (ROOT / "js" / "commands.js").read_text(encoding="utf-8")
        self.assertNotIn("function parseSpeed", js)
        self.assertNotIn("function parseContext", js)
        # The test-suite export points at the shared window functions.
        self.assertIn("parseContext: window.parseContext", js)
        self.assertIn("parseSpeed: window.parseSpeed", js)


if __name__ == "__main__":
    unittest.main()
