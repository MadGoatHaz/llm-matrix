"""Secondary-thread parser tests (Batch 7) — two-pass structured extraction.

The contract under test:

* PASS 1 (keyword relevance) never drops a post that talks about
  performance / hardware, and never flags pure chatter;
* PASS 2 (structured extraction) is CONSERVATIVE: a field is set only
  when the post's own text states it. Quoted content belongs to the
  quoted author; questions, hypotheticals, envy, inequality thresholds,
  and capability lists are never treated as data. Anything unstated is
  null — never guessed;
* every extracted value is verifiable against the raw post text
  (the live-dataset test enforces this token by token);
* the 300-char preview is kept on every item as the fallback;
* the authored v1 schemas (benchmarks/hardware) are well-formed and the
  generated datasets conform to them.

Stdlib only, per project convention.
"""

import json
import re
import sys
import unittest
from pathlib import Path

from tests.util import ROOT, load_tool

pt = load_tool("tools/parse_thread.py", "parse_thread")

# The stdlib mini-validator + schema well-formedness checker from
# tests/test_api.py (the same ones CI uses for the submissions payload).
sys.path.insert(0, str(ROOT))
from tests.test_api import schema_structure_errors, validate  # noqa: E402


def make_post(cooked, username="tester", post_number=1, post_id=100,
              created="2026-10-01T00:00:00.000Z"):
    return {
        "id": post_id,
        "post_number": post_number,
        "username": username,
        "created_at": created,
        "title": "",
        "cooked": cooked,
    }


def thread_data(*posts):
    return {"post_stream": {"posts": list(posts)}}


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------

class TestTextUtils(unittest.TestCase):
    def test_strip_html_collapse(self):
        text = pt.strip_html("<p>Hello &amp; welcome</p><br><b>world</b>")
        self.assertEqual(text, "Hello & welcome world")

    def test_strip_html_keep_newlines(self):
        cooked = ("<p>a<br>b</p>\n<p>c</p>")
        text = pt.strip_html(cooked, keep_newlines=True)
        self.assertIn("\n", text)
        # <br> is a line break: the first line is just "a".
        self.assertEqual(text.split("\n")[0].strip(), "a")
        self.assertEqual(text.split("\n")[1].strip(), "b")

    def test_strip_html_normalizes_typography(self):
        # The raw JSON carries \u-escaped curly quotes / times / ge.
        cooked = "<p>It\u2019s 1920\u00d71080 and \u2265 30 tokens/sec.</p>"
        text = pt.strip_html(cooked)
        self.assertIn("'s", text)
        self.assertIn("1920x1080", text)
        self.assertIn(">= 30", text)

    def test_strip_html_drops_image_stamps(self):
        cooked = ("<p>PXL_20260910_232524354.MP 916\u00d7874 204 KB "
                  "the rig is fast</p>")
        text = pt.strip_html(cooked)
        self.assertNotIn("916x874", text)
        self.assertNotIn("204 KB", text)
        self.assertIn("the rig is fast", text)

    def test_remove_quotes(self):
        cooked = (
            "<p>My own words here.</p> "
            '<aside class="quote no-group" data-username="other">'
            " <div class=\"title\"> other:</div> "
            "<blockquote> <p>3x rtx 6000 pro ws</p> </blockquote> "
            "</aside> <p>And more of mine.</p>"
        )
        own = pt.strip_html(pt.remove_quotes(cooked))
        self.assertIn("My own words here.", own)
        self.assertIn("And more of mine.", own)
        self.assertNotIn("rtx 6000", own)

    def test_split_machines_two_neofetch_blocks(self):
        text = ("I'll start it off: aigoat@aigoat OS: EndeavourOS x86_64 "
                "CPU: Intel(R) Xeon(R) E5-2697A v4 (32) @ 3.60 GHz "
                "GPU 1: NVIDIA RTX A4000 "
                "omnigoat@omnigoat OS: EndeavourOS x86_64 "
                "CPU: AMD Ryzen 5 5600X (12) @ 4.88 GHz "
                "GPU 1: NVIDIA Quadro RTX 5000")
        segs = pt.split_machines(text)
        self.assertEqual(len(segs), 2)
        self.assertIn("Xeon", segs[0])
        self.assertIn("Ryzen", segs[1])

    def test_split_machines_single_block(self):
        text = "myrig@myrig OS: Ubuntu 22.04 GPU 1: NVIDIA RTX 4090"
        self.assertEqual(pt.split_machines(text), [text])

    def test_split_machines_no_block(self):
        text = "just a normal post with no neofetch"
        self.assertEqual(pt.split_machines(text), [text])


# ---------------------------------------------------------------------------
# First pass (relevance)
# ---------------------------------------------------------------------------

class TestFirstPass(unittest.TestCase):
    def test_crucible_performance_keywords(self):
        self.assertTrue(pt.is_crucible_relevant("about 80 tokens/sec decode"))
        self.assertTrue(pt.is_crucible_relevant("the pre-fill is slow"))
        self.assertTrue(pt.is_crucible_relevant("128K context test"))
        self.assertTrue(pt.is_crucible_relevant("spikes over 400 watts"))

    def test_crucible_chatter_not_relevant(self):
        self.assertFalse(pt.is_crucible_relevant(
            "Thanks for the feedback! Great work on the tool."))

    def test_rigs_gpu_keywords(self):
        self.assertTrue(pt.is_rigs_relevant("a pair of R9700s in x8/x8"))
        self.assertTrue(pt.is_rigs_relevant("4x AMD V620 on a bench"))
        self.assertTrue(pt.is_rigs_relevant("my 128GB M4 Max machine"))
        self.assertTrue(pt.is_rigs_relevant("dual 5060ti 16g build"))

    def test_rigs_chatter_not_relevant(self):
        self.assertFalse(pt.is_rigs_relevant(
            "That's too nice, I don't know if I can sit at your table."))
        self.assertFalse(pt.is_rigs_relevant(
            "The tech priests require art and evidence of your devotion."))


# ---------------------------------------------------------------------------
# Crucible second pass
# ---------------------------------------------------------------------------

class TestCrucibleExtraction(unittest.TestCase):
    def test_power_and_hardware(self):
        # The prior first-person sentence is what makes the bare "9700"
        # the poster's own card (live post 12).
        text = ("It reports only the first card? This feature is very new. "
                "I can say, what it's reporting is definitely correct. "
                "The 9700 spikes over 400 watts on NIAH test because "
                "it's pure prefill.")
        self.assertEqual(pt._extract_crucible_hardware(text), "9700")
        self.assertEqual(pt._extract_crucible_power(text), 400.0)

    def test_context_and_hardware(self):
        text = ("like the 5090 in my daily driver, and so on. So far, not "
                "a single model that I've loaded has been able to return "
                "anything at all on any position in the 128K context.")
        self.assertEqual(pt._extract_crucible_hardware(text), "5090")
        self.assertEqual(pt._extract_crucible_context(text), "128K")

    def test_full_post_model_hardware_backend(self):
        text = ("I am in fact using 4x 9700 pro cards. Mostly qwen 3.8 "
                "flash next, qwen 3.8 27b models and their derivatives. "
                "I recently switched to Radiance which is a real game "
                "changer for these cards.")
        self.assertEqual(pt._extract_crucible_hardware(text),
                         "4x 9700 Pro")
        self.assertEqual(pt._extract_crucible_model(text),
                         "Qwen 3.8 flash next")
        self.assertEqual(pt._extract_crucible_backend(text), "Radiance")

    def test_inequality_threshold_is_not_a_measurement(self):
        # Live trap: post 16 quotes the "practical sweet spot" definition.
        text = ("The maximum number of users where each one still gets a "
                "comfortable >= 30 tokens/sec. May you consider a "
                "dispersion behaviour in latency?")
        decode, prefill = pt._extract_crucible_speeds(text)
        self.assertIsNone(decode)
        self.assertIsNone(prefill)

    def test_unlabeled_example_is_not_a_measurement(self):
        # Live trap: post 1's hypothetical "32 users -> 2 tokens/sec".
        text = ("Most benchmarks shout fast numbers and stop. But when 32 "
                "users hit that server at once, each one gets 2 "
                "tokens/sec.")
        decode, prefill = pt._extract_crucible_speeds(text)
        self.assertIsNone(decode)
        self.assertIsNone(prefill)

    def test_labeled_speed_is_a_measurement(self):
        text = ("Roughly 3200t/s prefill, 80t/s general generation, "
                "120t/s code gen on my box.")
        decode, prefill = pt._extract_crucible_speeds(text)
        self.assertEqual(decode, "80")
        self.assertEqual(prefill, "3200")

    def test_question_is_not_own_hardware(self):
        text = "With 4x9700?"
        self.assertIsNone(pt._extract_crucible_hardware(text))

    def test_conditional_backend_list_is_not_a_stack(self):
        text = ("If you're running vLLM, llama.cpp, Ollama, LM Studio, "
                "SGLang — grab it and tell me if the numbers look right.")
        self.assertIsNone(pt._extract_crucible_backend(text))

    def test_capability_list_is_not_a_stack(self):
        text = ("Supports SGLang and vLLM engines. This is the blackwell "
                "performance community gold standard right now.")
        self.assertIsNone(pt._extract_crucible_backend(text))

    def test_parenthetical_aside_is_not_a_stack(self):
        text = ("keep-alive-prefixed streams (llama.cpp) no longer "
                "misroute on my server.")
        self.assertIsNone(pt._extract_crucible_backend(text))

    def test_bare_family_name_is_too_vague(self):
        text = ("I've been using Qwen with the maximum context set, and "
                "I'd like to see how it does with rope/yarn.")
        self.assertIsNone(pt._extract_crucible_model(text))

    def test_model_without_other_signal_is_rejected(self):
        # Release-note chatter about a model family, no hardware/speed/
        # context/power in the post -> not a benchmark entry.
        text = ("Qwen3.5+ won't honor /no_think, which silently turned "
                "good models into fake failures.")
        model = pt._extract_crucible_model(text)
        self.assertIsNotNone(model)  # the name itself is well-formed...
        self.assertFalse(pt._model_has_signal(text))  # ...but no signal

    def test_engine_name_is_not_a_model(self):
        # "Llama.cpp" must not be read as a "Llama" model.
        text = ("CPU via Llama.cpp: Qwen3.6-35B-A3B Qwen3-Coder-30B "
                "on my rig.")
        self.assertEqual(pt._extract_crucible_model(text),
                         "Qwen3.6-35B-A3B")

    def test_unversioned_named_variant_is_kept(self):
        text = ("currently serving an mxfp4 optimised version of qwen "
                "flash-next on vLLM with 1M total context cache and a C8 "
                "of 300 tk/s and a C1 at 80 tk/s")
        self.assertEqual(pt._extract_crucible_model(text),
                         "Qwen flash-next")

    def test_hf_prefixed_model_name(self):
        text = ("Mostly runs Vishva007/Qwen3.8-27B-W4A16-AutoRound-GPTQ "
                "ATM via vllm @ 650k context on my box.")
        self.assertEqual(
            pt._extract_crucible_model(text),
            "Vishva007/Qwen3.8-27B-W4A16-AutoRound-GPTQ")


# ---------------------------------------------------------------------------
# Rigs second pass
# ---------------------------------------------------------------------------

class TestRigExtraction(unittest.TestCase):
    def test_neofetch_dominant_gpu_wins(self):
        lined = ("\n".join(
            ["aigoat@aigoat",
             "OS: EndeavourOS x86_64",
             "CPU: Intel(R) Xeon(R) E5-2697A v4 (32) @ 3.60 GHz",
             "GPU 1: ASPEED Technology, Inc. ASPEED Graphics Family"]
            + [f"GPU {i}: NVIDIA RTX A4000" for i in range(2, 10)]
            + ["Memory: 31.32 GiB / 125.76 GiB (25%)",
               "Disk (/): 889.43 GiB / 1.73 TiB (50%) - btrfs"]))
        model, count = pt._extract_rig_gpu(lined, lined)
        self.assertEqual(model, "NVIDIA RTX A4000")
        self.assertEqual(count, 8)
        self.assertEqual(pt._extract_cpu(lined, lined),
                         "Intel Xeon E5-2697A v4")
        self.assertEqual(pt._extract_os(lined, lined), "EndeavourOS")
        self.assertEqual(pt._extract_ram(lined), 125.76)
        self.assertEqual(pt._extract_storage(lined, lined),
                         "1.73 TiB (btrfs)")

    def test_neofetch_bracket_tags_stripped(self):
        lined = "omnigoat@omnigoat\nOS: EndeavourOS x86_64\n" \
                "GPU 1: NVIDIA Quadro RTX 5000 [Discrete]\n" \
                "GPU 2: NVIDIA Quadro RTX 5000 [Discrete]"
        model, count = pt._extract_rig_gpu(lined, lined)
        self.assertEqual(model, "NVIDIA Quadro RTX 5000")
        self.assertEqual(count, 2)

    def test_dual_with_percard_vram(self):
        text = ("Pretty boring compared to some of the posts here. Dual "
                "5060ti 16g, 64 gig ddr4, 5700X on an MSI board, Meshify C "
                "case Ubuntu 26.04 (desktop even), llama.cpp (llama-server)"
                " Qwen 3.8 27b, Q4 weights, Q8 kv, sampler settings for "
                "coding, full 256k context.")
        model, count = pt._extract_rig_gpu("", text)
        self.assertEqual(model, "5060 Ti")
        self.assertEqual(count, 2)
        self.assertEqual(pt._extract_vram_total(text, model, count), 32.0)
        self.assertEqual(pt._extract_cpu("", text), "5700X")
        self.assertEqual(pt._extract_ram(text), 64.0)
        self.assertEqual(pt._extract_os("", text), "Ubuntu 26.04")
        self.assertEqual(pt._extract_context(text), "256k")

    def test_explicit_total_vram(self):
        text = ("2x AMD EPYC 7532 512 GB DDR4 3200 Some storage "
                "2x 3080 20GB (Total 40GB)")
        model, count = pt._extract_rig_gpu("", text)
        self.assertEqual(model, "3080")
        self.assertEqual(count, 2)
        self.assertEqual(pt._extract_vram_total(text, model, count), 40.0)
        self.assertEqual(pt._extract_cpu("", text), "2x AMD EPYC 7532")
        self.assertEqual(pt._extract_ram(text), 512.0)

    def test_instinct_with_stated_vram_and_os(self):
        text = ("I wound up popping an AMD Instinct MI210 (64GB HBM2, "
                "1600GB/s) into my existing main Proxmox node, and "
                "passing it through to a VM.")
        model, count = pt._extract_rig_gpu("", text)
        self.assertEqual(model, "AMD Instinct MI210")
        self.assertEqual(count, 1)
        self.assertEqual(pt._extract_vram_total(text, model, count), 64.0)
        self.assertEqual(pt._extract_os("", text), "Proxmox")

    def test_label_lines(self):
        text = ("CPU: Dual Xeon Gold 6230, for a total of 80 threads. "
                "RAM: 768GB DDR4 REG-ECC GPU: Radeon VII, but "
                "occasionally also a spare RX5700 for funsies "
                "Storage: Yes Case: open air test bench. System runs "
                "Proxmox, with a spread of several containers.")
        model, count = pt._extract_rig_gpu("", text)
        self.assertEqual(model, "Radeon VII")
        self.assertEqual(count, 1)
        self.assertEqual(pt._extract_cpu("", text), "Dual Xeon Gold 6230")
        self.assertEqual(pt._extract_ram(text), 768.0)
        self.assertEqual(pt._extract_os("", text), "Proxmox")
        notes = pt._extract_rig_notes("", text, model, count)
        self.assertIn("RX 5700", notes)

    def test_jealousy_is_not_a_spec(self):
        text = "Hey, I'm thoroughly jealous of the MI210. That's a lot of GB/s"
        self.assertEqual(pt._extract_rig_gpu("", text), (None, None))

    def test_hypothetical_is_not_a_spec(self):
        text = ("If I had to make a decision all over again, for the money "
                "I spent, I might get a couple of DGX sparks.")
        self.assertEqual(pt._extract_rig_gpu("", text), (None, None))

    def test_question_is_not_a_spec(self):
        text = "With 4x9700? Are you sure that's stable?"
        self.assertEqual(pt._extract_rig_gpu("", text), (None, None))

    def test_prior_sentence_ownership_counts(self):
        text = ("I still have the same computer i built last year in a "
                "Mitx case. (a 5090 for 2700 euro and 128gb of ddr5 for "
                "500 euro) It runs vllm with qwen3.8 27b about 80-100 t/s")
        model, count = pt._extract_rig_gpu("", text)
        self.assertEqual(model, "5090")
        self.assertEqual(count, 1)
        self.assertEqual(pt._extract_ram(text), 128.0)

    def test_unified_memory(self):
        text = 'My "ai rig" is a boring 128GB M4 Max. On one site its ' \
               'kinda slow to process requests but on the bright side it ' \
               'literally uses measured 1W at idle.'
        model, count = pt._extract_rig_gpu("", text)
        self.assertEqual(model, "M4 Max")
        self.assertEqual(count, 1)
        self.assertEqual(pt._extract_vram_total(text, model, count), 128.0)

    def test_spec_dump_without_first_person(self):
        text = ("IMG 1920x3413 970 KB 13900kf on z790 taichi carrea "
                "256gb ddr5 5800mhz 3x rtx 6000 pro ws 2x 4tb team group "
                "nvme and 2x 2tb wd sn850 black MSI ai1600ts All in a "
                "lian li evo dynamic xl case")
        model, count = pt._extract_rig_gpu("", text)
        self.assertEqual(model, "RTX 6000 Pro WS")
        self.assertEqual(count, 3)
        self.assertEqual(pt._extract_cpu("", text), "13900KF")
        self.assertEqual(pt._extract_ram(text), 256.0)
        storage = pt._extract_storage("", text)
        self.assertIn("2x 4TB Team Group", storage)
        self.assertIn("2x 2TB WD", storage)

    def test_no_vendor_is_never_fabricated(self):
        text = "I just got a 5090 and I'm stoked."
        model, count = pt._extract_rig_gpu("", text)
        self.assertEqual(model, "5090")
        self.assertNotIn("NVIDIA", model)

    def test_hypothetical_cpu_upgrade_is_not_a_spec(self):
        text = ("Currently thinking about making my own enclosure for the "
                "machine, set up such that the GPUs each have their own "
                "airflow. That seems like a lovely solution, except I "
                "guess I could transplant the NAS into it, which would "
                "also give me the option of using one of the ATX boards "
                "to give it a serious CPU and RAM upgrade (3400g to "
                "5700X).")
        self.assertIsNone(pt._extract_cpu("", text))

    def test_workload_speed_cluster_merges_figures(self):
        text = ("Open-WebUI fronting a vllm-radiance instance running "
                "Qwen 3.8 27B FP8. Roughly 3200t/s prefill, 80t/s general "
                "generation, 120t/s code gen. I really dislike vLLM, "
                "particularly the slow model launch.")
        wl = pt._extract_workload(text)
        self.assertIn("Qwen 3.8 27B FP8", wl)
        self.assertIn("vllm-radiance", wl)
        self.assertIn("3200t/s prefill, 80t/s general generation, "
                      "120t/s code gen", wl)
        self.assertNotIn("dislike vLLM", wl)

    def test_workload_generic_backend_not_claimed(self):
        text = ("You might want to take a look at this repo, if you're "
                "just throwing llama.cpp at it and crossing your fingers. "
                "My 4x v620s does about 1200TPS prefill with "
                "qwen3.8-flash-next.")
        wl = pt._extract_workload(text)
        self.assertIn("1200TPS prefill", wl)
        self.assertNotIn("throwing llama.cpp", wl)

    def test_repo_wall_not_in_notes(self):
        text = ("That's how I went from 20t/s on my stack to up to 90. "
                "github.com GitHub - davetha/mi210-llm-stack: AMD MI210 "
                "(gfx90a/CDNA2) LLM inference optimization. My 4x v620s "
                "does about 1200TPS prefill.")
        notes = pt._extract_rig_notes("", text, "V620", 4)
        self.assertIsNone(notes)

    def test_quote_never_credits_the_quoter(self):
        cooked = (
            "<p>quadrapole: 3x rtx 6000 pro ws Where's the third one? "
            "And are you having issues with a lack of PCIE lanes between "
            "them?</p>"
        )
        # Simulate what parse_rigs does: quotes removed before extraction.
        own = pt.strip_html(pt.remove_quotes(
            '<aside class="quote no-group" data-username="quadrapole">'
            "<blockquote><p>3x rtx 6000 pro ws</p></blockquote></aside>"
            "<p>Where's the third one? And are you having issues with a "
            "lack of PCIE lanes between them?</p>"))
        model, count = pt._extract_rig_gpu("", own)
        self.assertEqual((model, count), (None, None))
        del cooked


# ---------------------------------------------------------------------------
# Live dataset (the real raw thread mirrors)
# ---------------------------------------------------------------------------

class TestLiveDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.crucible = pt.parse_crucible(
            pt.load_json(ROOT / "data/raw/crucible_latest.json"))
        cls.rigs = pt.parse_rigs(
            pt.load_json(ROOT / "data/raw/rigs_latest.json"))
        cls.crucible_posts = {
            p["post_number"]: p for p in pt.extract_posts(
                pt.load_json(ROOT / "data/raw/crucible_latest.json"))}
        cls.rigs_posts = {
            p["post_number"]: p for p in pt.extract_posts(
                pt.load_json(ROOT / "data/raw/rigs_latest.json"))}

    def _crucible(self, pn):
        return next(it for it in self.crucible
                    if it["post_number"] == pn)

    def _rigs(self, pn):
        return next((it for it in self.rigs if it["post_number"] == pn),
                    None)

    # --- crucible ----------------------------------------------------------

    def test_crucible_item_count(self):
        self.assertEqual(len(self.crucible), 16)

    def test_crucible_structured_set(self):
        structured = {it["post_number"] for it in self.crucible
                      if it["structured"]}
        self.assertEqual(structured, {12, 14, 19})

    def test_crucible_post12(self):
        it = self._crucible(12)
        self.assertEqual(it["hardware"], "9700")
        self.assertEqual(it["power_w"], 400.0)
        self.assertIsNone(it["model"])
        self.assertIsNone(it["backend"])

    def test_crucible_post14(self):
        it = self._crucible(14)
        self.assertEqual(it["hardware"], "5090")
        # The post writes "128K" (capital K) — verbatim is preserved.
        self.assertEqual(it["context_length"], "128K")

    def test_crucible_post19(self):
        it = self._crucible(19)
        self.assertEqual(it["hardware"], "4x 9700 Pro")
        self.assertEqual(it["model"], "Qwen 3.8 flash next")
        self.assertEqual(it["backend"], "Radiance")

    def test_crucible_inequality_quote_not_extracted(self):
        # Post 16 quotes the ">= 30 tokens/sec" sweet-spot definition.
        it = self._crucible(16)
        self.assertFalse(it["structured"])
        self.assertIsNone(it["performance"]["decode_tps"])
        self.assertIsNone(it["performance"]["prefill_tps"])

    def test_crucible_release_notes_stay_preview_only(self):
        for pn in (1, 2, 22, 23):
            with self.subTest(post=pn):
                it = self._crucible(pn)
                self.assertFalse(it["structured"])
                self.assertIsNone(it["model"])
                self.assertIsNone(it["hardware"])
                self.assertIsNone(it["backend"])

    # --- rigs --------------------------------------------------------------

    def test_rigs_item_count(self):
        self.assertEqual(len(self.rigs), 22)

    def test_rigs_structured_set(self):
        structured = {it["post_number"] for it in self.rigs
                      if it["structured"]}
        self.assertEqual(
            structured,
            {2, 3, 4, 8, 11, 19, 22, 24, 25, 27, 28, 32, 35, 36, 40})
        self.assertEqual(len(structured), 15)

    def test_rigs_post2_splits_two_machines(self):
        p2 = [it for it in self.rigs if it["post_number"] == 2]
        self.assertEqual(len(p2), 2)
        self.assertEqual(p2[0]["id"], "rigs_post_2_0")
        self.assertEqual(p2[1]["id"], "rigs_post_2_1")
        self.assertEqual(p2[0]["gpu"], {"model": "NVIDIA RTX A4000",
                                        "count": 8})
        self.assertEqual(p2[1]["gpu"], {"model": "NVIDIA Quadro RTX 5000",
                                        "count": 2})
        self.assertEqual(p2[0]["cpu"], "Intel Xeon E5-2697A v4")
        self.assertEqual(p2[1]["cpu"], "AMD Ryzen 5 5600X")
        self.assertEqual(p2[0]["os"], "EndeavourOS")

    def test_rigs_post24(self):
        it = self._rigs(24)
        self.assertEqual(it["gpu"], {"model": "R9700", "count": 2})
        self.assertEqual(it["cpu"], "5700X")
        self.assertEqual(it["ram_gb"], 128.0)
        self.assertIn("3200t/s prefill", it["workload"])
        self.assertIn("80t/s", it["workload"])
        self.assertIn("120t/s", it["workload"])

    def test_rigs_post35(self):
        it = self._rigs(35)
        self.assertEqual(it["gpu"], {"model": "R9700", "count": 4})
        self.assertEqual(it["cpu"], "5950X")
        self.assertEqual(it["ram_gb"], 128.0)
        self.assertIn("300 tk/s", it["workload"])
        self.assertIn("80 tk/s", it["workload"])

    def test_rigs_post36(self):
        it = self._rigs(36)
        self.assertEqual(it["gpu"], {"model": "RTX 6000 Pro WS", "count": 3})
        self.assertEqual(it["cpu"], "13900KF")
        self.assertEqual(it["ram_gb"], 256.0)

    def test_rigs_post40(self):
        it = self._rigs(40)
        self.assertEqual(it["gpu"], {"model": "M4 Max", "count": 1})
        self.assertEqual(it["vram_total_gb"], 128.0)

    def test_rigs_post37_quote_not_attributed(self):
        # digitalscream QUOTES "3x rtx 6000 pro ws" to ask a question —
        # the rig belongs to quadrapole, not to him.
        it = self._rigs(37)
        self.assertFalse(it["structured"])
        self.assertIsNone(it["gpu"]["model"])

    def test_rigs_post17_jealousy_not_a_spec(self):
        it = self._rigs(17)
        self.assertFalse(it["structured"])
        self.assertIsNone(it["gpu"]["model"])

    def test_rigs_post18_hypothetical_not_a_spec(self):
        it = self._rigs(18)
        self.assertFalse(it["structured"])
        self.assertIsNone(it["gpu"]["model"])

    def test_rigs_post29_hypothetical_upgrade_not_a_spec(self):
        it = self._rigs(29)
        self.assertFalse(it["structured"])
        self.assertIsNone(it["cpu"])

    # --- verifiability (the quality bar) ------------------------------------

    _CONNECTORS = set(
        "via also and or with on at to for in of from up down total single "
        "peak pure flat steady stable roughly about per the a an it my i we "
        "you not no yes all any each every both few several one two three "
        "four five six seven eight nine ten this that these those here there "
        "then just only even still now new old big small fast slow good bad "
        "great nice whole live real true false own same other another first "
        "second third".split())

    def _data_tokens(self, value):
        return [t for t in re.findall(r"[A-Za-z][A-Za-z0-9.\-]{2,}", value)
                if t.lower() not in self._CONNECTORS]

    def test_every_string_field_is_verbatim(self):
        for items, posts in ((self.crucible, self.crucible_posts),
                             (self.rigs, self.rigs_posts)):
            for it in items:
                post = posts[it["post_number"]]
                low = pt.strip_html(post["cooked"]).lower()
                with self.subTest(item=it["id"]):
                    if it.get("model"):
                        for tok in self._data_tokens(it["model"]):
                            self.assertIn(tok.lower(), low,
                                          f"{it['id']} model token {tok}")
                    if it.get("hardware"):
                        for tok in self._data_tokens(it["hardware"]):
                            self.assertIn(tok.lower(), low,
                                          f"{it['id']} hw token {tok}")
                    if it.get("backend"):
                        self.assertIn(it["backend"].lower(), low)
                    if it.get("context_length"):
                        # context values keep the post's casing ("128K",
                        # "650k") — compare case-insensitively.
                        self.assertIn(it["context_length"].lower(), low)
                    if it.get("cpu"):
                        for tok in self._data_tokens(it["cpu"]):
                            self.assertIn(tok.lower(), low,
                                          f"{it['id']} cpu token {tok}")
                    if it.get("os"):
                        self.assertIn(it["os"].lower(), low)
                    if it.get("storage"):
                        for tok in self._data_tokens(it["storage"]):
                            self.assertIn(tok.lower(), low,
                                          f"{it['id']} storage token {tok}")
                    gpu = it.get("gpu", {})
                    if gpu.get("model"):
                        for tok in self._data_tokens(gpu["model"]):
                            self.assertIn(tok.lower(), low,
                                          f"{it['id']} gpu token {tok}")

    def test_every_number_is_grounded_in_the_post(self):
        for items, posts in ((self.crucible, self.crucible_posts),
                             (self.rigs, self.rigs_posts)):
            for it in items:
                post = posts[it["post_number"]]
                low = pt.strip_html(post["cooked"]).lower()
                nums = [float(x) for x in
                        re.findall(r"\d+(?:\.\d+)?", low)]
                with self.subTest(item=it["id"]):
                    for key in ("vram_total_gb", "ram_gb", "power_w"):
                        v = it.get(key)
                        if v is None:
                            continue
                        self.assertTrue(
                            self._number_grounded(v, nums, low),
                            f"{it['id']} {key}={v} not in post text")
                    perf = it.get("performance", {})
                    for key in ("vram_gb", "ttft_s"):
                        v = perf.get(key)
                        if v is not None:
                            self.assertTrue(
                                self._number_grounded(v, nums, low),
                                f"{it['id']} perf.{key}={v}")

    @staticmethod
    def _number_grounded(value, text_nums, low):
        f = float(value)
        if str(f) in low or (f == int(f) and str(int(f)) in low):
            return True
        return any(a * b == f for a in text_nums for b in text_nums)

    def test_previews_are_true_prefixes(self):
        for items, posts in ((self.crucible, self.crucible_posts),
                             (self.rigs, self.rigs_posts)):
            for it in items:
                full = pt.strip_html(posts[it["post_number"]]["cooked"])
                with self.subTest(item=it["id"]):
                    self.assertTrue(full.startswith(it["preview"]))
                    self.assertLessEqual(len(it["preview"]), 300)
                    self.assertGreater(len(it["preview"]), 0)

    def test_envelope_and_ids(self):
        for items, prefix, posts in (
                (self.crucible, "crucible_post_", self.crucible_posts),
                (self.rigs, "rigs_post_", self.rigs_posts)):
            for it in items:
                with self.subTest(item=it["id"]):
                    self.assertTrue(it["id"].startswith(prefix))
                    self.assertEqual(it["id"].split("_")[2],
                                     str(it["post_number"]))
                    self.assertEqual(it["post_id"],
                                     posts[it["post_number"]]["id"])
                    self.assertRegex(it["date"],
                                     r"^\d{4}-\d{2}-\d{2}$")
                    self.assertIsInstance(it["structured"], bool)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class TestSecondarySchemas(unittest.TestCase):
    def test_schemas_are_well_formed(self):
        for name in ("benchmarks_schema.json", "hardware_schema.json"):
            schema = json.loads(
                (ROOT / "data/api/v1" / name).read_text(encoding="utf-8"))
            with self.subTest(schema=name):
                self.assertEqual(
                    schema_structure_errors(schema), [],
                    f"{name} is not a well-formed JSON Schema")

    def test_generated_datasets_conform(self):
        cases = (
            ("data/benchmarks.json",
             "data/api/v1/benchmarks_schema.json"),
            ("data/hardware.json",
             "data/api/v1/hardware_schema.json"),
            # The published v1 copies (with the version stamp) conform too.
            ("data/api/v1/benchmarks.json",
             "data/api/v1/benchmarks_schema.json"),
            ("data/api/v1/hardware.json",
             "data/api/v1/hardware_schema.json"),
        )
        for data_rel, schema_rel in cases:
            data = json.loads(
                (ROOT / data_rel).read_text(encoding="utf-8"))
            schema = json.loads(
                (ROOT / schema_rel).read_text(encoding="utf-8"))
            with self.subTest(data=data_rel):
                self.assertEqual(
                    validate(data, schema, schema), [],
                    f"{data_rel} does not conform to {schema_rel}")

    def test_count_matches_items(self):
        for data_rel in ("data/benchmarks.json", "data/hardware.json"):
            data = json.loads(
                (ROOT / data_rel).read_text(encoding="utf-8"))
            with self.subTest(data=data_rel):
                self.assertEqual(data["count"], len(data["items"]))
                ids = [it["id"] for it in data["items"]]
                self.assertEqual(len(ids), len(set(ids)),
                                 "duplicate item ids")


if __name__ == "__main__":
    unittest.main()
