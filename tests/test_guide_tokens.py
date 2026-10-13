"""C8: Guide↔data freshness — ``{{data tokens}}`` in authored content.

Guides (and the API docs page) carry ``{{token}}`` markers in their markdown
source; the generator fills them at build time from the live dataset so the
figures in prose (submission counts, backend/vendor/contributor counts,
GGUF share, last update) track the data instead of going stale weekly.

These tests lock in:

* the pure functions — ``fill_tokens`` (known values replace, unknown
  names raise naming every offender, token-free text passes through),
  ``data_tokens`` (values derived from the dataset), and
  ``is_gguf_submission`` (the narrow GGUF signature: no "Qwen3.8"
  false positives, FP8/W4A16 excluded);
* the integration — every rendered guide page + the guides index + the
  /api/ page carries the current numbers and **no** raw ``{{``/``}}``
  anywhere;
* the failure mode — a guide with an unknown token is skipped with a
  warning while the other guides still ship (a typo never leaks into
  the published HTML).
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.util import ROOT, load_json

REQUIRED_INPUTS = (
    "data/submissions.json",
    "tools/schema.json",
    "css/style.css",
    "js/main.js",
)

#: The 8 authored guides (content/guides/*.md minus the index).
GUIDE_SLUGS = (
    "quantization", "file-formats", "quantization-methods",
    "model-architectures", "kv-cache", "context-extension",
    "backends", "multi-gpu",
)


def _make_workspace() -> Path:
    """A throwaway workspace mirroring the repo layout (inputs + content)."""
    tmp = Path(tempfile.mkdtemp(prefix="las_guide_tokens_"))
    for rel in REQUIRED_INPUTS:
        src = ROOT / rel
        dst = tmp / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    shutil.copytree(ROOT / "content", tmp / "content", dirs_exist_ok=True)
    return tmp


class TestFillTokens(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from tools.site import utils
        cls.utils = utils

    def test_known_tokens_replaced(self):
        text = ("The matrix tracks {{backend_count}} backends across "
                "{{submission_count}} submissions.")
        out = self.utils.fill_tokens(
            text, {"backend_count": "7", "submission_count": "26"})
        self.assertEqual(
            out, "The matrix tracks 7 backends across 26 submissions.")

    def test_token_free_text_unchanged(self):
        text = "No markers here — just prose with {single} braces."
        self.assertEqual(self.utils.fill_tokens(text, {"a": "1"}), text)

    def test_unknown_token_raises_naming_it(self):
        with self.assertRaises(ValueError) as ctx:
            self.utils.fill_tokens("{{nope}} and {{backend_count}}",
                                   {"backend_count": "7"})
        self.assertIn("nope", str(ctx.exception))

    def test_all_unknown_tokens_reported_at_once(self):
        with self.assertRaises(ValueError) as ctx:
            self.utils.fill_tokens("{{aaa}} {{bbb}} {{ccc}}", {})
        msg = str(ctx.exception)
        for name in ("aaa", "bbb", "ccc"):
            self.assertIn(name, msg)


class TestIsGgufSubmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from tools.site import utils
        cls.utils = utils

    def _sub(self, quant, model):
        return {"quant": quant, "model": {"name": model}}

    def test_gguf_in_quant_field(self):
        for quant in ("GGUF Q4_K_M", "GGUF Q8_0", "GGUF I-Nano",
                      "GGUF UD-Q2_K_XL", "GGUF IQ3_S (ISTA-DASLab GSQ-RCO)"):
            with self.subTest(quant=quant):
                self.assertTrue(self.utils.is_gguf_submission(self._sub(quant, "")))

    def test_gguf_only_in_model_name(self):
        for model in ("gemma-4-31B-it-BF16.gguf", "DeepSeek-R1:671b-0528_q8_0",
                      "Gemma4:26b-a4b-it-mtp-q4_K_M",
                      "Qwen3:235b-a22b-thinking-2507-q4",
                      "GLM-5.2-UD-Q6_K_XL"):
            with self.subTest(model=model):
                self.assertTrue(self.utils.is_gguf_submission(self._sub("", model)))

    def test_iq_quant_with_space(self):
        # "IQ4 weights, FP8 PLE" — the quant evidence, not the model name.
        self.assertTrue(self.utils.is_gguf_submission(
            self._sub("IQ4 weights, FP8 PLE", "Swift 1.5 Flash Next")))

    def test_non_gguf_excluded(self):
        for quant, model in (
            ("FP8", "d0xin/Swift-Qwen3.8-27B-Uncensored-FP8"),
            ("W4A16", "qwen3.8-flash-next"),
            ("BF16", "some-plain-model"),
            ("", "nemotron-3-super:120b"),  # no GGUF evidence anywhere
        ):
            with self.subTest(quant=quant, model=model):
                self.assertFalse(self.utils.is_gguf_submission(self._sub(quant, model)))

    def test_model_family_names_never_match(self):
        # The digit must be glued to the q/iq/ud token: "Qwen3.8-27B",
        # "Qwen3.5-4B", "Qwen4..." are model names, not quant signatures.
        for model in ("Qwen3.8-27B", "Qwen3.5-4B", "Qwen3.6-MoE-35B-A3B"):
            with self.subTest(model=model):
                self.assertFalse(self.utils.is_gguf_submission(self._sub("", model)))


class TestDataTokensLiveDataset(unittest.TestCase):
    """The token values are derived from — and agree with — the dataset."""

    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from tools.site import utils
        cls.utils = utils
        data = load_json("data/submissions.json")
        cls.data = data
        cls.subs = utils.real_submissions(data)
        cls.schema = load_json("tools/schema.json")
        cls.tokens = utils.data_tokens(cls.subs, cls.schema, data)

    def test_submission_count_is_dataset_length(self):
        self.assertEqual(self.tokens["submission_count"], str(len(self.subs)))

    def test_counts_match_compute_stats(self):
        stats = self.utils.compute_stats(self.subs, self.schema)
        self.assertEqual(self.tokens["backend_count"], str(stats["backends"]))
        self.assertEqual(self.tokens["vendor_count"], str(stats["vendors"]))
        self.assertEqual(self.tokens["contributor_count"],
                         str(stats["contributors"]))

    def test_last_updated_is_newest_submission(self):
        dates = [s["source"]["submitted_at"] for s in self.subs
                 if s["source"].get("submitted_at")]
        self.assertTrue(dates, "the dataset must carry submitted_at stamps")
        self.assertEqual(self.tokens["last_updated"], max(dates)[:10])

    def test_gguf_count_is_a_genuine_partial(self):
        expected = sum(1 for s in self.subs
                       if self.utils.is_gguf_submission(s))
        self.assertEqual(self.tokens["gguf_count"], str(expected))
        # A real split, not a tautology: some submissions are not GGUF.
        self.assertLess(expected, len(self.subs))


class TestRenderedPagesCarryCurrentData(unittest.TestCase):
    """Integration: the generated guides + API page show live numbers."""

    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        cls.tmp = _make_workspace()
        from tools.site import utils
        cls.utils = utils
        data = load_json("data/submissions.json")
        cls.data = data
        cls.tokens = utils.data_tokens(utils.real_submissions(data),
                                       load_json("tools/schema.json"), data)
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

    def _read(self, rel: str) -> str:
        return (self.tmp / rel).read_text(encoding="utf-8")

    def test_no_brace_leaks_in_any_data_token_page(self):
        pages = [f"guides/{slug}/index.html" for slug in GUIDE_SLUGS]
        pages += ["guides/index.html", "api/index.html"]
        for rel in pages:
            with self.subTest(page=rel):
                text = self._read(rel)
                self.assertNotIn("{{", text)
                self.assertNotIn("}}", text)

    def test_backends_guide_shows_live_counts(self):
        text = self._read("guides/backends/index.html")
        self.assertIn(
            f"tracks {self.tokens['backend_count']} backends across its "
            f"{self.tokens['submission_count']} submissions", text)

    def test_file_formats_guide_shows_gguf_split(self):
        text = self._read("guides/file-formats/index.html")
        self.assertIn(
            f"{self.tokens['gguf_count']} of "
            f"{self.tokens['submission_count']} community submissions "
            "run GGUF", text)

    def test_quantization_methods_guide_shows_gguf_split(self):
        text = self._read("guides/quantization-methods/index.html")
        self.assertIn(
            f"{self.tokens['gguf_count']} of the Matrix's "
            f"{self.tokens['submission_count']} submissions live", text)

    def test_multi_gpu_guide_shows_vendor_span(self):
        text = self._read("guides/multi-gpu/index.html")
        self.assertIn(
            f"spans {self.tokens['vendor_count']} vendors across "
            f"{self.tokens['submission_count']} submissions", text)

    def test_guides_index_shows_dataset_line(self):
        text = self._read("guides/index.html")
        self.assertIn(f"last updated <strong>{self.tokens['last_updated']}</strong>",
                      text)
        self.assertIn(
            f"<strong>{self.tokens['submission_count']} community submissions</strong>",
            text)

    def test_api_page_example_payload_is_current(self):
        # The JSON lives in a rendered <code> block, so the quotes are
        # HTML-escaped as &quot; in the page source.
        from tools.site import api as api_module
        text = self._read("api/index.html")
        self.assertIn(f'&quot;version&quot;: &quot;{api_module.API_VERSION}&quot;',
                      text)
        self.assertIn(
            f'&quot;schema_version&quot;: &quot;{self.data["schema_version"]}&quot;',
            text)
        self.assertIn(
            f'&quot;total_submissions&quot;: {self.tokens["submission_count"]}',
            text)
        self.assertIn(
            f'&quot;generated_at&quot;: &quot;{self.data["generated_at"]}&quot;',
            text)


class TestUnknownTokenSkipsGuideOnly(unittest.TestCase):
    """A typo'd token fails its own guide loudly; the others still ship."""

    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        cls.tmp = _make_workspace()
        bad = cls.tmp / "content" / "guides" / "bad-token.md"
        bad.write_text(
            "---\ntitle: Bad Token\ndescription: A deliberate typo\n---\n\n"
            "This guide references {{no_such_token}} on purpose.\n",
            encoding="utf-8")
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

    def test_bad_guide_not_written(self):
        self.assertFalse(
            (self.tmp / "guides" / "bad-token" / "index.html").exists(),
            "a guide with an unknown token must not ship (raw {{}} leak)")

    def test_other_guides_still_written(self):
        for slug in GUIDE_SLUGS:
            with self.subTest(slug=slug):
                self.assertTrue(
                    (self.tmp / "guides" / slug / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
