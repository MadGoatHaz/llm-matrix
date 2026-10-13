"""Dataset validation: ``data/submissions.json`` invariants.

The dataset is what the entire site renders. These tests catch parser
regressions and template leaks:

* the header count matches the row count;
* every row carries the full canonical key set;
* tier / vendor are schema-valid;
* every raw backend string normalizes (via the generator's
  ``normalize_backend``) to a schema-known backend;
* no unfilled-template rows leaked into the dataset.
"""

import unittest

from tests.util import load_json, load_tool

#: Canonical keys every parsed submission must carry (schema v2.1 contract).
REQUIRED_KEYS = (
    "id",
    "source",
    "type",
    "raw",
    "tier",
    "hardware",
    "backend",
    "model",
    "quant",
    "weight_precision",
    "use_cases",
    "context",
    "performance",
    "engine_mode",
    "notes",
    "confidence",
    "lifecycle",
    "highlight",
    "tags",
)




class TestSubmissionsInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_json("data/submissions.json")
        cls.schema = load_json("tools/schema.json")
        cls.subs = cls.data["submissions"]
        # The generator's normalizer is the single source of truth for
        # backend canonicalization (parse.py stores raw strings).
        cls.generator = load_tool("tools/generate_site.py")

    def test_row_count_matches_header(self):
        self.assertEqual(len(self.subs), self.data["total_submissions"])
        self.assertGreater(len(self.subs), 0)

    def test_every_row_has_required_keys(self):
        for sub in self.subs:
            with self.subTest(id=sub.get("id")):
                missing = [k for k in REQUIRED_KEYS if k not in sub]
                self.assertEqual(missing, [], f"missing keys: {missing}")

    def test_tiers_within_schema(self):
        valid = {t["id"] for t in self.schema["tiers"]}
        for sub in self.subs:
            with self.subTest(id=sub["id"]):
                self.assertIn(sub["tier"], valid)

    def test_vendors_within_schema(self):
        valid = set(self.schema["hardware_vendors"])
        for sub in self.subs:
            with self.subTest(id=sub["id"]):
                self.assertIn(sub["hardware"]["vendor"], valid)

    def test_backends_normalize_to_schema_values(self):
        valid = set(self.schema["backends"])
        for sub in self.subs:
            with self.subTest(id=sub["id"]):
                raw = (sub["backend"] or "").strip()
                if not raw:
                    continue  # unreported backend is a data gap, not a violation
                normalized = self.generator.normalize_backend(raw, self.schema)
                self.assertIn(
                    normalized, valid,
                    f"backend {raw!r} -> {normalized!r} not in schema",
                )

    def test_no_template_rows_leaked(self):
        # The production detector (single source of truth): a row is a
        # leaked unfilled template only if ALL of its key fields are
        # placeholders. parse.py must have filtered every such row out.
        for sub in self.subs:
            with self.subTest(id=sub["id"]):
                self.assertTrue(
                    (sub["model"]["name"] or "").strip(), "empty model name"
                )
                self.assertFalse(
                    self.generator.is_template_submission(sub),
                    "unfilled template row leaked into the dataset",
                )

    def test_source_fields_present(self):
        # Forum deep links depend on post_number/post_id being captured.
        for sub in self.subs:
            with self.subTest(id=sub["id"]):
                for key in ("post_number", "post_id", "username"):
                    self.assertIn(key, sub["source"])

    def test_speed_is_tracked_on_every_row(self):
        # Speed (tokens/second) is a tracked, optional field: every row
        # carries the decode_tps key (empty when not reported) so the
        # template -> parser -> data -> site chain has no orphan fields.
        for sub in self.subs:
            with self.subTest(id=sub["id"]):
                self.assertIn("decode_tps", sub["performance"])
        reported = [
            s for s in self.subs
            if (s["performance"].get("decode_tps") or "").strip()
        ]
        self.assertGreater(
            len(reported), 0,
            "no submission reports a decode speed — the Speed column is empty",
        )


if __name__ == "__main__":
    unittest.main()
