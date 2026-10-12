"""Validator tests: ``tools/validate.py`` keeps the data contract honest.

The validator is the CI quality gate for *data* (as the test suite is the
gate for *code*). These tests lock in its behavior:

* the committed dataset validates cleanly (exit 0, no hard failures);
* a malformed submission (bad enum, missing field) fails the relevant check;
* duplicate ids fail, while repeated post+model is only a warning;
* absurd VRAM (0 GB or > 1000 GB) fails, sensible values pass;
* broken referential integrity (non-integer post id, missing ``main`` thread)
  fails;
* the end-to-end exit-code contract: valid data -> 0, invalid data -> 1.

Every test runs the validator's pure functions over in-memory submissions, so
the suite stays deterministic (no network, no clock, no filesystem mutation).
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.util import ROOT, load_json, load_tool


def make_sub(**overrides):
    """A minimal, fully-valid submission; ``overrides`` tweak individual fields."""
    base = {
        "id": "post_1_tester_0",
        "source": {"post_number": 1, "post_id": 100, "username": "tester",
                   "submitted_at": "2026-01-01T00:00:00Z"},
        "type": "full",
        "raw": {},
        "tier": "t1",
        "hardware": {"description": "1x RTX 4090 24GB", "vendor": "NVIDIA"},
        "backend": "llama.cpp",
        "model": {"name": "Qwen3.8-27B", "url": "https://huggingface.co/x"},
        "quant": "GGUF Q4_K_M",
        "weight_precision": "",
        "use_cases": "Agentic coding",
        "context": {"stable": "32k", "kv_cache": "FP16"},
        "performance": {"decode_tps": "40", "prefill_tps": "", "ttft_cold": "",
                        "power_w": ""},
        "engine_mode": "",
        "notes": "test submission",
        "confidence": "community-reported",
        "lifecycle": "current",
        "highlight": False,
        "tags": [],
    }
    base.update(overrides)
    return base


class TestValidatorOnRealData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_tool("tools/validate.py")

    def test_current_data_is_valid(self):
        results, valid = self.mod.validate()
        self.assertTrue(valid, f"committed data should validate: {results}")

    def test_no_hard_failures_on_current_data(self):
        results, _ = self.mod.validate()
        fails = [r for r in results if r["status"] == "fail"]
        self.assertEqual(fails, [], f"unexpected failures: {fails}")

    def test_report_is_rendered(self):
        results, _ = self.mod.validate()
        report = self.mod.render_report(results)
        self.assertIn("DATA QUALITY REPORT", report)
        self.assertIn("SUMMARY:", report)

    def test_main_returns_zero_on_valid_data(self):
        self.assertEqual(self.mod.main(), 0)


class TestIndividualChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_tool("tools/validate.py")
        cls.schema = load_json("tools/schema.json")

    # --- check 2: required fields -------------------------------------------
    def test_missing_required_field_fails(self):
        s = make_sub()
        del s["quant"]
        results = self.mod.check_required_fields([s])
        self.assertEqual(results[0]["status"], "fail")
        self.assertIn("quant", results[0]["detail"])

    def test_complete_submission_passes(self):
        results = self.mod.check_required_fields([make_sub()])
        self.assertEqual(results[0]["status"], "pass")

    # --- check 3: enum conformance ------------------------------------------
    def test_bad_tier_fails(self):
        results = self.mod.check_enum_conformance([make_sub(tier="t9")],
                                                 self.schema)
        self.assertEqual(results[0]["status"], "fail")
        self.assertIn("tier", results[0]["detail"])

    def test_bad_vendor_fails(self):
        results = self.mod.check_enum_conformance(
            [make_sub(hardware={"description": "weird box", "vendor": "Qualcomm"})],
            self.schema)
        self.assertEqual(results[0]["status"], "fail")

    def test_unknown_backend_fails(self):
        # A backend that normalizes to something not in the schema set.
        results = self.mod.check_enum_conformance(
            [make_sub(backend="TotallyUnknownEngine 9.9")], self.schema)
        self.assertEqual(results[0]["status"], "fail")

    def test_valid_enums_pass(self):
        results = self.mod.check_enum_conformance([make_sub()], self.schema)
        self.assertEqual(results[0]["status"], "pass")

    # --- check 4: duplicates ------------------------------------------------
    def test_duplicate_id_fails(self):
        a = make_sub(id="post_1_x_0")
        b = make_sub(id="post_1_x_0")
        results = self.mod.check_duplicates([a, b])
        self.assertEqual(results[0]["status"], "fail")

    def test_repeated_post_model_is_warning_not_failure(self):
        a = make_sub(id="post_5_y_0", source={"post_number": 5, "post_id": 200,
                                              "username": "y", "submitted_at": ""},
                     model={"name": "SameModel", "url": ""})
        b = make_sub(id="post_5_y_1", source={"post_number": 5, "post_id": 200,
                                              "username": "y", "submitted_at": ""},
                     model={"name": "SameModel", "url": ""})
        results = self.mod.check_duplicates([a, b])
        self.assertEqual(results[0]["status"], "warn")

    def test_distinct_ids_pass(self):
        a = make_sub()
        b = make_sub(id="post_2_z_0",
                     source={"post_number": 2, "post_id": 200, "username": "z",
                             "submitted_at": ""},
                     model={"name": "OtherModel", "url": ""})
        results = self.mod.check_duplicates([a, b])
        self.assertEqual(results[0]["status"], "pass")

    # --- check 5: vram reasonableness ---------------------------------------
    def test_zero_vram_hardware_fails(self):
        bad = make_sub(hardware={"description": "1x GPU 0GB", "vendor": "NVIDIA"})
        results = self.mod.check_vram_reasonable([bad], self.schema)
        self.assertEqual(results[0]["status"], "fail")

    def test_huge_vram_hardware_fails(self):
        bad = make_sub(hardware={"description": "1x GPU 5000GB", "vendor": "NVIDIA"})
        results = self.mod.check_vram_reasonable([bad], self.schema)
        self.assertEqual(results[0]["status"], "fail")

    def test_sensible_vram_passes(self):
        # 24GB VRAM + 128GB system RAM are both well within bounds.
        ok = make_sub(hardware={"description": "1x RTX 4090 24GB, 128GB DDR4",
                                "vendor": "NVIDIA"})
        results = self.mod.check_vram_reasonable([ok], self.schema)
        self.assertEqual(results[0]["status"], "pass")

    def test_t1_zero_floor_is_legit(self):
        # t1 is "≤16GB" = [0, 16]; a 0 floor must NOT be flagged (only the
        # ceiling is bounded). This is the exact case that tripped the first
        # validator draft on real data.
        results = self.mod.check_vram_reasonable([make_sub(tier="t1")],
                                                self.schema)
        self.assertEqual(results[0]["status"], "pass")

    # --- check 6: referential integrity -------------------------------------
    def test_non_integer_post_id_fails(self):
        bad = make_sub(source={"post_number": 1, "post_id": "not-an-int",
                               "username": "x", "submitted_at": ""})
        results = self.mod.check_referential_integrity([bad], self.schema)
        self.assertEqual(results[0]["status"], "fail")

    def test_missing_main_thread_fails(self):
        schema = {**self.schema, "monitored_threads": [
            {"id": "crucible", "url": "https://x", "name": "c", "type": "b",
             "description": "d"}]}
        results = self.mod.check_referential_integrity([make_sub()], schema)
        self.assertEqual(results[0]["status"], "fail")
        self.assertIn("main", results[0]["detail"])

    def test_non_url_model_is_not_a_hard_failure(self):
        # A "repo · Hugging Face" string is a data gap, not a contract break.
        ok = make_sub(model={"name": "M", "url": "SomeRepo · Hugging Face"})
        results = self.mod.check_referential_integrity([ok], self.schema)
        self.assertEqual(results[0]["status"], "pass")

    # --- check 7: data gaps (informational) ---------------------------------
    def test_data_gaps_are_warnings(self):
        results = self.mod.check_data_gaps([make_sub()], self.schema)
        self.assertEqual(results[0]["status"], "warn")
        self.assertIn("Apple", results[0]["detail"])


class TestExitCodeContract(unittest.TestCase):
    """End-to-end: valid data exits 0, invalid data exits 1."""

    @classmethod
    def setUpClass(cls):
        cls.mod = load_tool("tools/validate.py")

    def _workspace(self, submissions):
        """A temp workspace mirroring the repo layout, with the given rows."""
        tmp = Path(tempfile.mkdtemp(prefix="las_validate_"))
        (tmp / "data").mkdir()
        (tmp / "tools").mkdir()
        for rel in ("data/benchmarks.json", "data/hardware.json",
                    "data/category_threads.json", "data/last_seen.json",
                    "tools/schema.json", "tools/tags.json"):
            dst = tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, dst)
        payload = {
            "generated_at": "2026-01-01T00:00:00", "schema_version": "2.1",
            "source_thread": "https://forum.level1techs.com/t/256443",
            "total_submissions": len(submissions), "skipped_templates": 0,
            "submissions": submissions,
        }
        (tmp / "data" / "submissions.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8")
        return tmp

    def test_valid_dataset_exits_zero(self):
        tmp = self._workspace([make_sub()])
        try:
            _, valid = self.mod.validate(data_dir=tmp / "data", workspace=tmp,
                                         schema_path=tmp / "tools" / "schema.json")
            self.assertTrue(valid)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_invalid_dataset_is_not_valid(self):
        tmp = self._workspace([make_sub(tier="t9",
                                        hardware={"description": "x 9999GB",
                                                  "vendor": "Nope"})])
        try:
            _, valid = self.mod.validate(data_dir=tmp / "data", workspace=tmp,
                                         schema_path=tmp / "tools" / "schema.json")
            self.assertFalse(valid)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
