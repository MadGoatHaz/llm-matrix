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
  positives such as bare ``16`` matching ``16-24``);
* ``split_backend`` — free-text backend -> (canonical enum value, leftover
  detail for notes), with longest-match-first substring matching.

Every test is a pure function over string inputs — no network, no clock, no
filesystem — so the suite stays deterministic and CI-ready.
"""

import unittest

from tests.util import load_json, load_tool


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

    def test_friendly_template_aliases(self):
        # The forum promo template + the thread's Quick Submit use friendly
        # single-token names; they all map to the canonical fields.
        data = self.parse.apply_aliases(
            {
                "gpu": "1x RTX 4090 24GB",
                "vram": "24-32GB",
                "model": "Qwen3.8-27B",
                "quant": "GGUF Q4_K_M",
                "use_case": "daily chat",
                "notes": "fast cold load",
                "speed": "45 tok/s",
            }
        )
        self.assertEqual(
            data,
            {
                "hardware": "1x RTX 4090 24GB",
                "tier": "24-32GB",
                "model_name": "Qwen3.8-27B",
                "quant_package": "GGUF Q4_K_M",
                "primary_use_case": "daily chat",
                "setup_notes": "fast cold load",
                "throughput_tps": "45 tok/s",
            },
        )

    def test_speed_alias_variants(self):
        for alias in ("speed", "tok_s", "tokens_per_second", "tps"):
            with self.subTest(alias=alias):
                data = self.parse.apply_aliases({alias: "30 t/s"})
                self.assertEqual(data.get("throughput_tps"), "30 t/s")
                self.assertNotIn(alias, data)

    def test_friendly_alias_loses_to_canonical(self):
        # A post using both the friendly and canonical name keeps canonical.
        data = self.parse.apply_aliases(
            {"model": "OldName", "model_name": "NewName", "speed": "1 t/s",
             "throughput_tps": "45 t/s"}
        )
        self.assertEqual(data["model_name"], "NewName")
        self.assertEqual(data["throughput_tps"], "45 t/s")
        self.assertNotIn("model", data)
        self.assertNotIn("speed", data)


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

    def test_quick_submit_fill_in_phrases_are_placeholders(self):
        # The thread's Quick Submit template wraps fill-in instructions in
        # brackets. Once its friendly names alias to canonical fields, these
        # must still be detected as an unfilled template (not leak a fake
        # "Your GPU model + VRAM" submission into the dataset).
        for value in (
            "[Your GPU model + VRAM]",
            "[Model name + quant]",
            "[What you use it for]",
            "[One sentence: does it work? any quirks?]",
        ):
            with self.subTest(value=value):
                self.assertTrue(self.parse._looks_like_placeholder(value))

    def test_genuine_bracketed_values_are_not_placeholders(self):
        # Users wrap real values in brackets; none of them may trip the
        # fill-in-phrase detection.
        for value in (
            "[llama-cpp]",
            "[8192]",
            "[default]",
            "[1 tokens/sec]",
            "[192-256GB+]",
            "[RTX 5090 + IceLake Xeon]",
            "[DeepSeek-R1:671b-0528_q8_0]",
            "[ unsloth/DeepSeek-R1-GGUF-UD at main ]",
            "[translation of government journal from 481 BCE China]",
        ):
            with self.subTest(value=value):
                self.assertFalse(self.parse._looks_like_placeholder(value))

    def test_unfilled_quick_template_after_aliasing_is_skipped(self):
        # Full pipeline check: the unfilled Quick Submit template, with its
        # friendly names aliased, is recognized as a template.
        data = self.parse.apply_aliases(
            {
                "gpu": "[Your GPU model + VRAM]",
                "model": "[Model name + quant]",
                "use_case": "[What you use it for]",
                "verdict": "[One sentence: does it work? any quirks?]",
            }
        )
        self.assertTrue(self.parse.is_template_submission(data))


class TestPromoTemplateEndToEnd(unittest.TestCase):
    """The forum promo template (Post1/Post2) is the single source of truth
    for what we ask contributors. It must round-trip: every line parseable,
    every parsed field displayed on the site, and the unfilled form skipped."""

    @classmethod
    def setUpClass(cls):
        cls.parse = load_tool("tools/parse.py")

    #: The exact template block both forum posts ship (identical).
    TEMPLATE = (
        "[COMMUNITY-SUBMISSION]\n"
        "hardware: [e.g., 1x RTX 4090 24GB + 128GB RAM]\n"
        "vram:     [e.g., 24GB — pick: under 16 / 16-23 / 24-31 / 32-47 / 48-95 / 96+ GB]\n"
        "model:    [e.g., Llama 3.1 8B, Qwen3.8-27B]\n"
        "backend:  [e.g., Ollama, llama.cpp, vLLM]\n"
        "quant:    [e.g., Q4_K_M, Q5_K_S, FP16, FP8]\n"
        "speed:    [e.g., 45 tok/s, ~30 t/s] (optional)\n"
        "use_case: [e.g., daily chat, coding, summarization]\n"
        "notes:    [e.g., launch flags, quirks, anything else] (optional)\n"
        "[/COMMUNITY-SUBMISSION]"
    )

    def _post(self, body):
        return {
            "cooked": "<p>" + body.replace("\n", "<br>") + "</p>",
            "post_number": 30,
            "username": "tester",
            "id": 999,
        }

    def test_filled_template_parses_all_fields(self):
        body = (
            "[COMMUNITY-SUBMISSION]\n"
            "hardware: 1x RTX 4090 24GB + 128GB RAM\n"
            "vram: 24-32GB\n"
            "model: Qwen3.8-27B\n"
            "backend: llama.cpp\n"
            "quant: GGUF Q4_K_M\n"
            "speed: 45 tok/s\n"
            "use_case: daily chat\n"
            "notes: fast cold load\n"
            "[/COMMUNITY-SUBMISSION]"
        )
        subs = self.parse.extract_submissions_from_post(self._post(body))
        self.assertEqual(len(subs), 1)
        self.assertFalse(self.parse.is_template_submission(subs[0]["data"]))
        data = subs[0]["data"]
        self.assertEqual(data["hardware"], "1x RTX 4090 24GB + 128GB RAM")
        self.assertEqual(data["tier"], "24-32GB")
        self.assertEqual(data["model_name"], "Qwen3.8-27B")
        self.assertEqual(data["backend"], "llama.cpp")
        self.assertEqual(data["quant_package"], "GGUF Q4_K_M")
        self.assertEqual(data["throughput_tps"], "45 tok/s")
        self.assertEqual(data["primary_use_case"], "daily chat")
        self.assertEqual(data["setup_notes"], "fast cold load")

    def test_unfilled_template_is_skipped(self):
        subs = self.parse.extract_submissions_from_post(self._post(self.TEMPLATE))
        self.assertEqual(len(subs), 1, "the block itself must be extracted")
        self.assertTrue(
            self.parse.is_template_submission(subs[0]["data"]),
            "the unfilled promo template must be detected as a template",
        )


class TestInferVendor(unittest.TestCase):
    """B5: vendor inference collects ALL GPU vendor signals — exactly one
    -> that vendor, two or more -> "Mixed", none -> "" (unknown). CPU names
    (Xeon, Ryzen, Threadripper, EPYC) are never GPU vendor signals."""

    @classmethod
    def setUpClass(cls):
        cls.parse = load_tool("tools/parse.py")

    def test_single_vendor_mapping(self):
        cases = {
            "NVIDIA RTX 4090": "NVIDIA",
            "RTX 5090 32GB": "NVIDIA",
            "4090": "NVIDIA",
            "2× 3090": "NVIDIA",
            "AMD R9700 32GB": "AMD",
            "R9700": "AMD",
            "2x Radeon RX 7900 XTX": "AMD",
            "Apple M3 Ultra Mac Studio": "Apple",
            "M3 Ultra": "Apple",
            "Intel Arc A770": "Intel",
        }
        for hardware, expected in cases.items():
            with self.subTest(hardware=hardware):
                self.assertEqual(self.parse.infer_vendor(hardware), expected)

    def test_multi_vendor_is_mixed(self):
        # A rig with GPUs from two vendors is neither "NVIDIA" nor "AMD".
        for hardware in ("4090 + R9700", "RTX 5090 + R9700",
                         "2x 4090 + 1x MI300"):
            with self.subTest(hardware=hardware):
                self.assertEqual(self.parse.infer_vendor(hardware), "Mixed")

    def test_cpu_names_are_not_gpu_vendors(self):
        # A CPU next to a single GPU never flips the rig to Mixed.
        for hardware in ("5090 + Xeon 1024GB",
                         "RTX 5090 + IceLake Xeon CPU (1024 GB)",
                         "1x RTX 4090 24GB, Ryzen 9 5900X, 128GB DDR4"):
            with self.subTest(hardware=hardware):
                self.assertEqual(self.parse.infer_vendor(hardware), "NVIDIA")

    def test_no_gpu_signal_is_unknown(self):
        self.assertEqual(self.parse.infer_vendor("some unknown box"), "")
        self.assertEqual(self.parse.infer_vendor("Ryzen 9 5900X + Threadripper"), "")
        self.assertEqual(self.parse.infer_vendor(""), "")


class TestNormalizeTier(unittest.TestCase):
    """A3: the schema's tiers are DISJOINT bands (v2.3) — t1 <16 <= t2 <24
    <= t3 <32 <= t4 <48 <= t5 <96 <= t6 — so every VRAM amount has exactly
    one home. Most-specific patterns first (a bare "16" never matches
    inside "16-23"); multi-GPU figures are summed; legacy range labels that
    straddle two bands are refined against the hardware description."""

    @classmethod
    def setUpClass(cls):
        cls.parse = load_tool("tools/parse.py")

    def test_new_disjoint_labels(self):
        cases = {
            "Under 16 GB": "t1",
            "16-23GB": "t2",
            "24-31GB": "t3",
            "32-47GB": "t4",
            "48-95GB": "t5",
            "96+ GB": "t6",
            "96GB": "t6",
        }
        for tier_str, expected in cases.items():
            with self.subTest(tier=tier_str):
                self.assertEqual(self.parse.normalize_tier(tier_str), expected)

    def test_single_numbers_map_to_their_band(self):
        # The 32GB gap is closed: a bare "32" (RTX 5090) is t4, not None.
        cases = {
            "8": "t1", "12": "t1",
            "16": "t2", "20": "t2",
            "24": "t3", "28": "t3",
            "32": "t4", "36": "t4", "40": "t4",
            "48": "t5", "64": "t5", "80": "t5",
            "96": "t6", "128": "t6", "196": "t6", "256": "t6",
        }
        for num, expected in cases.items():
            with self.subTest(num=num):
                self.assertEqual(self.parse.normalize_tier(num), expected)

    def test_multigpu_figures_are_summed(self):
        cases = {
            "4x24GB": "t6",     # 4×24 = 96
            "2 x 16 GB": "t4",  # 2×16 = 32
            "4x8GB": "t4",      # 4×8 = 32
            "2×32GB": "t5",     # 2×32 = 64
        }
        for tier_str, expected in cases.items():
            with self.subTest(tier=tier_str):
                self.assertEqual(self.parse.normalize_tier(tier_str), expected)

    def test_legacy_labels_wholly_inside_one_band(self):
        cases = {
            "48-64GB": "t5",
            "96-128GB": "t6",
            "128-196GB": "t6",
            "192-256GB+": "t6",
            "196-256GB": "t6",
            "256GB+": "t6",
        }
        for tier_str, expected in cases.items():
            with self.subTest(tier=tier_str):
                self.assertEqual(self.parse.normalize_tier(tier_str), expected)

    def test_straddling_legacy_labels_refine_from_hardware(self):
        p = self.parse.normalize_tier
        # A 16GB card that picked the old "≤16" label is t2 (16GB is t2).
        self.assertEqual(p("≤16GB", "Radeon VII 16GB HBM2"), "t2")
        # A 20GB card that picked the old "16-24" label is t2.
        self.assertEqual(p("16-24GB", "1x RTX-4000 Ada SFF (20 GB)"), "t2")
        # A 24GB card that picked the old "24-32" label is t3.
        self.assertEqual(p("24-32GB", "1x RTX 4090 24GB"), "t3")
        # 2 x 32GB picked the old "32-64" label -> 64GB total -> t5.
        self.assertEqual(
            p("32-64GB", "2 x R9700 32GB, Threadripper 3960X, 128GB DDR4"), "t5")
        # The count can trail the capacity: "24GB x4" = 96 -> t6.
        self.assertEqual(p("48-96GB", "Intel Arc B60 24GB x4"), "t6")
        # The "5900X" trap: a CPU model name ending in "x" must NOT be read
        # as a multi-GPU count times the system RAM.
        self.assertEqual(
            p("24-32GB", "1x RTX 4090 24GB, Ryzen 9 5900X, 128GB DDR4"), "t3")
        # The "4x32GB" RAM trap: "128GB DDR4 ... 4x32GB double-rank" is four
        # RAM modules, not four GPUs — the GPU's 24GB (the first "N GB"
        # figure) is the refinement, so the old "24-32" label stays t3.
        self.assertEqual(
            p("24-32GB",
              "1x RTX 4090 24GB, Ryzen 9 5900X, 128GB DDR4-3600 CL18 "
              "(2x CMK64GX4M2D3600C18, 4x32GB double-rank), Aorus X570"),
            "t3")

    def test_straddling_without_hardware_keeps_the_lower_band(self):
        # No explicit total in the hardware -> the conservative lower band
        # (never guess up).
        p = self.parse.normalize_tier
        self.assertEqual(p("≤16GB"), "t1")
        self.assertEqual(p("16-24GB"), "t2")
        self.assertEqual(p("24-32GB"), "t3")
        self.assertEqual(p("32-64GB"), "t4")
        self.assertEqual(p("48-96GB"), "t5")

    def test_en_dash_and_space_variants(self):
        self.assertEqual(self.parse.normalize_tier("196 GB – 256 GB+"), "t6")

    def test_empty_and_unknown_return_none(self):
        self.assertIsNone(self.parse.normalize_tier(""))
        self.assertIsNone(self.parse.normalize_tier("some gibberish"))


class TestPlaceholderDetection(unittest.TestCase):
    """Unfilled template values — bracketed OR bare (the parser unbrackets
    before display) — are detected as placeholders, so they get blanked in
    every field. Genuine values, including prose that merely contains
    template-like words, are NOT placeholders (data-loss guard)."""

    @classmethod
    def setUpClass(cls):
        cls.parse = load_tool("tools/parse.py")

    def test_burhan_template_strings_are_placeholders(self):
        # The exact values that leaked onto the live site (P0-1): after
        # _unbracket() they are bare instruction strings, and they must be
        # caught with or without the user's bracket styling.
        for value in (
            "Prefill tok/s (if measured)",
            "[Prefill tok/s (if measured)]",
            "Seconds for first token after cold load",
            "[Seconds for first token after cold load]",
            "Launch flags, rope/yarn config, host RAM offload, prompt prefill behavior, quirks",
            "[Launch flags, rope/yarn config, host RAM offload, prompt prefill behavior, quirks]",
        ):
            with self.subTest(value=value):
                self.assertTrue(self.parse.is_placeholder(value))

    def test_instruction_phrases_are_placeholders(self):
        for value in (
            "pick: A or B",
            "[pick: A or B]",
            "Fill in your setup",
            "Your GPU model + VRAM",
            "Insert the model name",
            "Name here",
            "One sentence: does it work? any quirks?",
            "What you use it for",
            "Model name + quant",
            "Full model name + quant",
            "Example model name",
            "e.g., 45 tok/s, ~30 t/s",
        ):
            with self.subTest(value=value):
                self.assertTrue(self.parse.is_placeholder(value))

    def test_bracketed_option_list_is_a_placeholder(self):
        for value in (
            "[≤16GB | 16-24GB | 24-32GB]",
            "[vLLM | llama.cpp | Ollama]",
        ):
            with self.subTest(value=value):
                self.assertTrue(self.parse.is_placeholder(value))

    def test_genuine_values_are_not_placeholders(self):
        # Data-loss guard: real values from the live dataset — several
        # contain template-like words mid-prose and must survive.
        for value in (
            "MoE A3B — fits 12.7GB incl. KV headroom. verify quality for your task, "
            "but pipeline ran coherent through 65k. | llama.cpp subprocess, ROCm/ROCm backends",
            "launch flags: --ctx-size 8192 --flash-attn on",
            "Tuned launch flags, got 20% more throughput",
            "41 seconds for the first token",
            "Linux/ROCm",
            "amdgpu",
            "Windows 11 Pro + WSL2/Ubuntu 24.04 (96 GB allocated via .wslconfig)",
            "54.4 tps decode / 215 tok/s prefill (short ctx)",
            "120t/s code, 70t/s chat",
            "99-128 decode (median 108, on 50k+ token prompts)",
            "200t/s+ decode average",
            "llama.cpp vulkan with no performance tuning",
            "peak under load not measured",
        ):
            with self.subTest(value=value[:40]):
                self.assertFalse(self.parse.is_placeholder(value))

    def test_genuine_bracketed_values_are_not_placeholders(self):
        # Users wrap real values in brackets; none may trip detection.
        for value in (
            "[llama-cpp]",
            "[8192]",
            "[default]",
            "[1 tokens/sec]",
            "[192-256GB+]",
            "[RTX 5090 + IceLake Xeon]",
            "[DeepSeek-R1:671b-0528_q8_0]",
            "[ unsloth/DeepSeek-R1-GGUF-UD at main ]",
            "[translation of government journal from 481 BCE China]",
        ):
            with self.subTest(value=value):
                self.assertFalse(self.parse.is_placeholder(value))
                self.assertFalse(self.parse._looks_like_placeholder(value))


class TestSpeedSplit(unittest.TestCase):
    """A speed string carrying both a prefill and a decode figure is split
    so the (much faster) prompt-processing number never lands in decode_tps
    and corrupts the "fastest setups" ranking (P0-2)."""

    @classmethod
    def setUpClass(cls):
        cls.parse = load_tool("tools/parse.py")

    def test_pp_tg_split(self):
        # The exact live case: post 33 (manoreken2).
        self.assertEqual(
            self.parse.split_speed("PP 120t/s, TG 2.5 t/s", ""),
            ("120", "2.5"),
        )

    def test_pp_tg_variants(self):
        for value in (
            "PP 120 t/s, TG 2.5 t/s",
            "pp 120 t/s; tg 2.5 t/s",
            "PP: 120, TG: 2.5",
            "TG 2.5 t/s, PP 120 t/s",
        ):
            with self.subTest(value=value):
                self.assertEqual(self.parse.split_speed(value, ""), ("120", "2.5"))

    def test_label_first_split(self):
        self.assertEqual(self.parse.split_speed("prefill: 120, decode: 2.5", ""),
                         ("120", "2.5"))
        self.assertEqual(self.parse.split_speed("decode: 2.5, prefill: 120", ""),
                         ("120", "2.5"))

    def test_label_trailing_split(self):
        self.assertEqual(self.parse.split_speed("120 t/s prefill, 2.5 t/s decode", ""),
                         ("120", "2.5"))
        # The s1ugh34d live shape (decode first, unit variants, trailing note).
        self.assertEqual(
            self.parse.split_speed("54.4 tps decode / 215 tok/s prefill (short ctx)", ""),
            ("215", "54.4"),
        )
        # "200t/s+ decode average" + a separately reported prefill field.
        self.assertEqual(self.parse.split_speed("200t/s+ decode average",
                                               "5200-6200t/s"),
                         ("5200-6200t/s", "200"))
        # Kif's live shape: a range with the label trailing the last figure.
        self.assertEqual(
            self.parse.split_speed("99-128 decode (median 108, on 50k+ token prompts)",
                                   "825-3600 on uncached tokens"),
            ("825-3600 on uncached tokens", "128"),
        )

    def test_single_unlabeled_value_is_decode(self):
        # No PP/TG distinction -> historic behavior: the whole string is the
        # decode figure and any separately reported prefill is preserved.
        self.assertEqual(self.parse.split_speed("30 t/s", ""), ("", "30 t/s"))
        self.assertEqual(self.parse.split_speed("~20-30 t/s", ""), ("", "~20-30 t/s"))
        self.assertEqual(self.parse.split_speed("120t/s code, 70t/s chat", ""),
                         ("", "120t/s code, 70t/s chat"))
        self.assertEqual(self.parse.split_speed("68-92", "1200@0ctx"),
                         ("1200@0ctx", "68-92"))

    def test_lone_labeled_figure_fills_only_its_slot(self):
        # A lone prefill figure is NOT a decode measurement (and vice versa).
        self.assertEqual(self.parse.split_speed("PP 120 t/s", ""), ("120", ""))
        self.assertEqual(self.parse.split_speed("TG 2.5 t/s", ""), ("", "2.5"))
        self.assertEqual(self.parse.split_speed("prefill: 120", ""), ("120", ""))

    def test_empty_and_placeholder_input(self):
        self.assertEqual(self.parse.split_speed("", "120"), ("120", ""))
        self.assertEqual(self.parse.split_speed("[Prefill tok/s (if measured)]", ""),
                         ("", ""))


class TestOsDriverEmission(unittest.TestCase):
    """os_driver is a schema canonical field (detail panel) — it must be
    extracted from the block and emitted on the entry (P0-3)."""

    @classmethod
    def setUpClass(cls):
        cls.parse = load_tool("tools/parse.py")

    def test_os_driver_extracted_from_block(self):
        data = self.parse.parse_submission_block(
            "hardware: 4x AMD v620\nos_driver: Linux/ROCm\nmodel_name: qwen3.8"
        )
        self.assertEqual(data["os_driver"], "Linux/ROCm")

    def test_os_driver_placeholder_is_blanked(self):
        data = self.parse.parse_submission_block(
            "os_driver: [Windows 11 | Linux | macOS]\nmodel_name: X"
        )
        self.assertEqual(self.parse.clean_field(data["os_driver"]), "")

    def test_os_driver_genuine_bracketed_value_kept(self):
        data = self.parse.parse_submission_block("os_driver: [ROCm 6.3]")
        self.assertEqual(self.parse.clean_field(data["os_driver"]), "ROCm 6.3")

    def test_entry_carries_os_driver_end_to_end(self):
        post = {
            "cooked": "<pre><code>[COMMUNITY-SUBMISSION]\n"
                      "hardware: 4x AMD v620\n"
                      "os_driver: Linux/ROCm\n"
                      "backend: vLLM\n"
                      "model_name: qwen3.8-flash-next\n"
                      "[/COMMUNITY-SUBMISSION]</code></pre>",
            "post_number": 99,
            "username": "tester",
            "id": 1,
        }
        subs = self.parse.extract_submissions_from_post(post)
        self.assertEqual(len(subs), 1)
        self.assertFalse(self.parse.is_template_submission(subs[0]["data"]))
        self.assertEqual(subs[0]["data"]["os_driver"], "Linux/ROCm")


class TestRawScrub(unittest.TestCase):
    """scrub_placeholders blanks unfilled template values inside submission
    blocks only — genuine values, and prose outside blocks, stay verbatim."""

    @classmethod
    def setUpClass(cls):
        cls.parse = load_tool("tools/parse.py")

    def test_scrubs_burhan_block(self):
        block = (
            "[COMMUNITY-SUBMISSION]\n"
            "tier: 16-24GB\n"
            "hardware: 1x RTX-4000 Ada SFF (20 GB)\n"
            "throughput_tps: ~20-30 t/s\n"
            "prefill_tps: [Prefill tok/s (if measured)]\n"
            "ttft_cold: [Seconds for first token after cold load]\n"
            "power_draw: 75 W\n"
            "setup_notes: [Launch flags, rope/yarn config, host RAM offload, prompt prefill behavior, quirks]\n"
            "[/COMMUNITY-SUBMISSION]"
        )
        out = self.parse.scrub_placeholders(block)
        for gone in ("if measured", "seconds for", "launch flags"):
            self.assertNotIn(gone, out)
        for kept in ("tier: 16-24GB", "hardware: 1x RTX-4000 Ada SFF (20 GB)",
                     "throughput_tps: ~20-30 t/s", "power_draw: 75 W",
                     "prefill_tps:", "ttft_cold:", "setup_notes:"):
            self.assertIn(kept, out)

    def test_genuine_bracketed_values_survive(self):
        block = (
            "[COMMUNITY-SUBMISSION]\n"
            "backend: [llama-cpp]\n"
            "stable_context_tested: [8192]\n"
            "kv_cache_setting: [default]\n"
            "[/COMMUNITY-SUBMISSION]"
        )
        self.assertEqual(self.parse.scrub_placeholders(block), block)

    def test_optional_decoration_after_bracket(self):
        line = "notes:    [e.g., launch flags, quirks, anything else] (optional)\n"
        out = self.parse.scrub_placeholders("[COMMUNITY-SUBMISSION]\n" + line +
                                           "[/COMMUNITY-SUBMISSION]")
        self.assertNotIn("launch flags", out)
        self.assertIn("notes:", out)

    def test_br_separated_lines(self):
        text = ("[QUICK-SUBMIT]\nmodel_name: [Full model name + quant]<br>"
                "backend: [llama-cpp]<br>[/QUICK-SUBMIT]")
        out = self.parse.scrub_placeholders(text)
        self.assertNotIn("Full model", out)
        self.assertIn("backend: [llama-cpp]", out)

    def test_prose_outside_blocks_is_untouched(self):
        # A diff block suggesting tier options (post 7) is prose, not a
        # submission — it must survive verbatim.
        text = ("<p>There's a hole in the <code>tier</code> options:</p>\n"
                "<pre><code class=\"lang-diff\">- tier: [≤16GB | 24-32GB]\n"
                "+ tier: [≤16GB | 16-24GB | 24-32GB]\n</code></pre>")
        self.assertEqual(self.parse.scrub_placeholders(text), text)


class TestBackendNormalization(unittest.TestCase):
    """Free-text backend values normalize to a schema-legal enum value, with
    the descriptive remainder preserved (parse.py moves it into notes)."""

    @classmethod
    def setUpClass(cls):
        cls.parse = load_tool("tools/parse.py")
        cls.schema = load_json("tools/schema.json")

    def test_free_text_after_known_backend(self):
        backend, detail = self.parse.split_backend(
            "llama.cpp vulkan with no performance tuning", self.schema)
        self.assertEqual(backend, "llama.cpp")
        self.assertEqual(detail, "vulkan with no performance tuning")

    def test_case_insensitive_match_keeps_schema_casing(self):
        backend, detail = self.parse.split_backend("ollama on a mac", self.schema)
        self.assertEqual(backend, "Ollama")
        self.assertEqual(detail, "on a mac")
        backend, detail = self.parse.split_backend(
            "vllm with tensor parallelism", self.schema)
        self.assertEqual(backend, "vLLM")
        self.assertEqual(detail, "with tensor parallelism")

    def test_already_valid_values_pass_through(self):
        self.assertEqual(self.parse.split_backend("LM Studio", self.schema),
                         ("LM Studio", ""))
        self.assertEqual(self.parse.split_backend("llama.cpp", self.schema),
                         ("llama.cpp", ""))

    def test_aliases_still_resolve(self):
        self.assertEqual(self.parse.split_backend("llama-cpp", self.schema),
                         ("llama.cpp", ""))

    def test_version_and_parenthetical_handling(self):
        # A trailing version is not detail; a parenthetical is.
        self.assertEqual(self.parse.split_backend("radiance 1.3.0", self.schema),
                         ("Radiance", ""))
        backend, detail = self.parse.split_backend(
            "vLLM (custom framework, see below)", self.schema)
        self.assertEqual(backend, "vLLM")
        self.assertEqual(detail, "custom framework, see below")

    def test_unknown_backend_is_kept_not_invented(self):
        # No known engine matches -> the cleaned text is kept as-is (the
        # caller flags a warning) and nothing is fabricated.
        backend, detail = self.parse.split_backend(
            "TotallyUnknownEngine 9.9", self.schema)
        self.assertEqual(backend, "TotallyUnknownEngine")
        self.assertEqual(detail, "")

    def test_empty_backend(self):
        self.assertEqual(self.parse.split_backend("", self.schema), ("", ""))


if __name__ == "__main__":
    unittest.main()
