"""Parser edge cases: ``tools/parse.py`` is the data engine's front door.

These tests lock in the tricky parsing behavior a naive implementation gets
wrong (PLAN.md P3-2):

* ``parse_submission_block`` — key/value lines, continuation folds, bullet
  lists, bracketed lists, and prose-with-a-colon not being misread as a key;
* ``apply_aliases`` — non-standard field names -> canonical names;
* ``split_on_separator`` — multi-model posts split on ``----`` lines;
* ``extract_submissions_from_post`` — full + quick blocks, several per post;
* ``is_template_submission`` — unfilled templates detected and skipped;
* ``infer_vendor`` — hardware string -> vendor;
* ``normalize_tier`` — most-specific-first matching (no substring false
  positives such as bare ``16`` matching ``16-24``).

Every test is a pure function over string inputs — no network, no clock, no
filesystem — so the suite stays deterministic and CI-ready.
"""

import unittest

from tests.util import load_tool


class TestParseSubmissionBlock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parse = load_tool("tools/parse.py")

    def test_simple_key_value(self):
        data = self.parse.parse_submission_block(
            "model_name: Swift-Qwen3.8-27B\nbackend: llama.cpp"
        )
        self.assertEqual(data["model_name"], "Swift-Qwen3.8-27B")
        self.assertEqual(data["backend"], "llama.cpp")

    def test_nonempty_value_folds_with_space(self):
        # A non-empty string value folds continuation lines in with a space.
        data = self.parse.parse_submission_block(
            "setup_notes: Cold start was slow\nPrefill took 41s on first run"
        )
        self.assertEqual(
            data["setup_notes"],
            "Cold start was slow Prefill took 41s on first run",
        )

    def test_empty_value_then_lines_become_comma_list(self):
        # An empty value followed by plain lines is collected as a list and
        # joined with ", ".
        data = self.parse.parse_submission_block(
            "hardware:\n2x AMD R9700\n128GB RAM"
        )
        self.assertEqual(data["hardware"], "2x AMD R9700, 128GB RAM")

    def test_bullet_list_joined(self):
        data = self.parse.parse_submission_block(
            "primary_use_case:\n* Agentic Coding\n* Roleplay"
        )
        self.assertEqual(data["primary_use_case"], "Agentic Coding, Roleplay")

    def test_inline_bracket_list_kept_verbatim(self):
        # A complete inline ``[a, b]`` is kept verbatim (preserves the
        # template markers for downstream detection).
        data = self.parse.parse_submission_block("tier: [≤16GB | 16-24GB]")
        self.assertEqual(data["tier"], "[≤16GB | 16-24GB]")

    def test_prose_with_colon_not_misread_as_key(self):
        # "Slow prefill: 41s TTFT" must fold into the prior value, not start a
        # new key — a key is a single identifier word followed directly by a
        # colon, so "Slow prefill" (with a space) never qualifies.
        data = self.parse.parse_submission_block(
            "setup_notes: Cold start was slow\nSlow prefill: 41s TTFT on first run"
        )
        self.assertNotIn("slow", data)
        self.assertIn("41s TTFT", data["setup_notes"])

    def test_empty_value_then_single_line(self):
        data = self.parse.parse_submission_block(
            "model_name:\nSwift-Qwen3.8-27B-Uncensored"
        )
        self.assertEqual(data["model_name"], "Swift-Qwen3.8-27B-Uncensored")


class TestApplyAliases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parse = load_tool("tools/parse.py")

    def test_alias_renamed_to_canonical(self):
        data = self.parse.apply_aliases({"power": "350W", "tps": "42"})
        self.assertEqual(data["power_draw"], "350W")
        self.assertEqual(data["throughput_tps"], "42")
        self.assertNotIn("power", data)
        self.assertNotIn("tps", data)

    def test_all_aliases_renamed(self):
        data = self.parse.apply_aliases(
            {
                "power": "350W",
                "cold_load_ttft": "41s",
                "context_length": "32k",
                "tps": "42",
            }
        )
        self.assertEqual(
            set(data),
            {"power_draw", "ttft_cold", "stable_context_tested", "throughput_tps"},
        )

    def test_canonical_wins_over_alias(self):
        # If both the alias and the canonical name are present, the alias is
        # dropped and the canonical value is preserved.
        data = self.parse.apply_aliases({"power": "300W", "power_draw": "350W"})
        self.assertEqual(data["power_draw"], "350W")
        self.assertNotIn("power", data)


class TestSplitOnSeparator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parse = load_tool("tools/parse.py")

    def test_no_separator_single_block(self):
        block = "model_name: A\nbackend: x"
        self.assertEqual(self.parse.split_on_separator(block), [block])

    def test_one_separator_two_blocks(self):
        block = "model_name: A\nbackend: x\n------\nmodel_name: B\nbackend: y"
        parts = self.parse.split_on_separator(block)
        self.assertEqual(len(parts), 2)
        self.assertIn("model_name: A", parts[0])
        self.assertIn("model_name: B", parts[1])

    def test_short_dashes_are_not_a_separator(self):
        # Fewer than 4 dashes is not a separator line.
        block = "model_name: A\n---\nbackend: x"
        self.assertEqual(len(self.parse.split_on_separator(block)), 1)

    def test_multiple_separators(self):
        block = "A\n------\nB\n------\nC"
        self.assertEqual(len(self.parse.split_on_separator(block)), 3)


class TestExtractSubmissionsFromPost(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parse = load_tool("tools/parse.py")

    def _post(self, cooked):
        return {"cooked": cooked, "post_number": 5, "username": "tester", "id": 123}

    def test_full_submission_extracted(self):
        post = self._post(
            "[COMMUNITY-SUBMISSION]\n"
            "model_name: Qwen3.8-27B\n"
            "tier: ≤16GB\n"
            "[/COMMUNITY-SUBMISSION]"
        )
        subs = self.parse.extract_submissions_from_post(post)
        self.assertEqual(len(subs), 1)
        self.assertEqual(subs[0]["type"], "full")
        self.assertEqual(subs[0]["data"]["model_name"], "Qwen3.8-27B")

    def test_quick_submit_extracted(self):
        post = self._post(
            "[QUICK-SUBMIT]\n"
            "model_name: DeepSeek-R1-8B\n"
            "backend: llama.cpp\n"
            "[/QUICK-SUBMIT]"
        )
        subs = self.parse.extract_submissions_from_post(post)
        self.assertEqual(len(subs), 1)
        self.assertEqual(subs[0]["type"], "quick")
        self.assertEqual(subs[0]["data"]["model_name"], "DeepSeek-R1-8B")

    def test_multiple_blocks_in_one_post(self):
        post = self._post(
            "[COMMUNITY-SUBMISSION]\nmodel_name: A\n[/COMMUNITY-SUBMISSION]\n"
            "[QUICK-SUBMIT]\nmodel_name: B\n[/QUICK-SUBMIT]"
        )
        subs = self.parse.extract_submissions_from_post(post)
        self.assertEqual(len(subs), 2)

    def test_multi_model_separator_splits_into_two(self):
        # One post holding two models separated by a ``----`` line yields two
        # independent submissions.
        post = self._post(
            "[COMMUNITY-SUBMISSION]\n"
            "model_name: A\n"
            "------\n"
            "model_name: B\n"
            "[/COMMUNITY-SUBMISSION]"
        )
        subs = self.parse.extract_submissions_from_post(post)
        self.assertEqual(len(subs), 2)
        self.assertEqual(subs[0]["data"]["model_name"], "A")
        self.assertEqual(subs[1]["data"]["model_name"], "B")

    def test_post_without_blocks_is_empty(self):
        post = self._post("Just a normal forum post with no submissions.")
        self.assertEqual(self.parse.extract_submissions_from_post(post), [])


class TestIsTemplateSubmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parse = load_tool("tools/parse.py")

    def test_unfilled_template_detected(self):
        # A value carrying a template marker is an unfilled template.
        data = {
            "tier": "[≤16GB | 16-24GB | ...]",
            "hardware": "my rig",
            "backend": "llama.cpp",
            "model_name": "SomeModel",
        }
        self.assertTrue(self.parse.is_template_submission(data))

    def test_all_core_fields_empty_detected(self):
        data = {
            "tier": "", "hardware": "", "backend": "", "model_name": "",
            "notes": "left blank",
        }
        self.assertTrue(self.parse.is_template_submission(data))

    def test_real_submission_not_template(self):
        data = {
            "tier": "≤16GB",
            "hardware": "RTX 4090 24GB",
            "backend": "llama.cpp",
            "model_name": "Qwen3.8-27B Q4_K_M",
        }
        self.assertFalse(self.parse.is_template_submission(data))


class TestInferVendor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parse = load_tool("tools/parse.py")

    def test_vendor_mapping(self):
        cases = {
            "NVIDIA RTX 4090": "NVIDIA",
            "RTX 5090 32GB": "NVIDIA",
            "AMD R9700 32GB": "AMD",
            "2x Radeon RX 7900 XTX": "AMD",
            "Apple M3 Ultra Mac Studio": "Apple",
            "Intel Arc A770": "Intel",
            "some unknown box": "Mixed",
        }
        for hardware, expected in cases.items():
            with self.subTest(hardware=hardware):
                self.assertEqual(self.parse.infer_vendor(hardware), expected)


class TestNormalizeTier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parse = load_tool("tools/parse.py")

    def test_tier_mapping(self):
        cases = {
            "≤16GB": "t1",
            "16-24GB": "t2",
            "24-32GB": "t3",
            "32-64GB": "t4",
            "48-96GB": "t4",
            "96-128GB": "t5",
            "128-196GB": "t5",
            "196-256GB": "t6",
            "256GB+": "t6",
        }
        for tier_str, expected in cases.items():
            with self.subTest(tier=tier_str):
                self.assertEqual(self.parse.normalize_tier(tier_str), expected)

    def test_longest_first_prevents_false_positive(self):
        # ``16-24`` must map to t2, NOT t1 (which the bare-``16`` fallback
        # would give). This is the whole point of the most-specific-first
        # ordering in normalize_tier.
        self.assertEqual(self.parse.normalize_tier("16-24GB"), "t2")
        self.assertEqual(self.parse.normalize_tier("16GB"), "t1")

    def test_empty_and_unknown_return_none(self):
        self.assertIsNone(self.parse.normalize_tier(""))
        self.assertIsNone(self.parse.normalize_tier("some gibberish"))


if __name__ == "__main__":
    unittest.main()
