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

#: Canonical keys every parsed submission must carry (schema v2.2 contract).
REQUIRED_KEYS = (
    "id",
    "source",
    "type",
    "raw",
    "tier",
    "hardware",
    "backend",
    "os_driver",
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
        # A non-None tier must be schema-legal. None is legitimate missing
        # data (e.g. a CPU-only rig with no VRAM tier), not a contract break —
        # the same rule the validator applies.
        valid = {t["id"] for t in self.schema["tiers"]}
        for sub in self.subs:
            with self.subTest(id=sub["id"]):
                if sub["tier"] is not None:
                    self.assertIn(sub["tier"], valid)

    def test_vendors_within_schema(self):
        valid = set(self.schema["hardware_vendors"])
        for sub in self.subs:
            with self.subTest(id=sub["id"]):
                vendor = sub["hardware"]["vendor"]
                # "" = no GPU vendor signal (e.g. a CPU-only rig) — missing
                # data, not a contract break. A non-empty vendor must be
                # schema-legal.
                if vendor:
                    self.assertIn(vendor, valid)

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

    def test_no_placeholder_instructions_in_dataset(self):
        # P0-1 data-tree guard (the `grep -r "if measured" data/` contract):
        # no string value anywhere in the dataset — including the verbatim
        # raw blocks — may carry unfilled-template instruction text.
        from tools.site.utils import TEMPLATE_CONTENT_RE, OPTION_LIST_RE
        bad = []

        def walk(o, path):
            if isinstance(o, str):
                s = o.strip()
                if not s:
                    return
                bracketed = s.startswith("[") and s.endswith("]")
                body = s[1:-1].strip() if bracketed else s
                if (bracketed and OPTION_LIST_RE.search(body)) or \
                        TEMPLATE_CONTENT_RE.search(body):
                    bad.append(f"{path}: {o!r}")
            elif isinstance(o, dict):
                for k, v in o.items():
                    walk(v, f"{path}.{k}")
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    walk(v, f"{path}[{i}]")

        for sub in self.subs:
            walk(sub, sub.get("id", "?"))
        self.assertEqual(bad, [], "placeholder instruction text leaked into the dataset")

    def test_no_sentinels_in_field_values(self):
        # B8 data-tree guard (the `grep -i "N/A|TBD|unknown" data/` contract):
        # no field value anywhere in the dataset — including the verbatim raw
        # blocks — may START with a no-measurement sentinel ("N/A (bench.sh
        # planned)", "TBD", "unknown", "none", "-", "—"). Those are the
        # ABSENCE of a measurement, not data, and would render in the detail
        # panel as if they were values. Prose comments are exempt: ``notes``
        # (submitter prose) and the curation ``highlight_reason`` may mention
        # the words mid-text.
        import re
        sentinel = re.compile(r"^(?:n/a|tbd|unknown|none|-|—)", re.IGNORECASE)
        exempt = {"notes", "highlight_reason"}
        bad = []

        def walk(o, path):
            if isinstance(o, str):
                s = o.strip()
                if s and sentinel.match(s):
                    bad.append(f"{path}: {o!r}")
            elif isinstance(o, dict):
                for k, v in o.items():
                    if k in exempt:
                        continue
                    walk(v, f"{path}.{k}")
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    walk(v, f"{path}[{i}]")

        for sub in self.subs:
            walk(sub, sub.get("id", "?"))
        self.assertEqual(
            bad, [],
            "no-measurement sentinels leaked into field values")

    def test_speed_fields_are_decomposed(self):
        # P0-2 data guard: decode_tps must never carry a prefill figure.
        # A "PP ... TG ..." / "prefill ... decode ..." compound string is
        # split at parse time; what remains in decode_tps is the decode
        # number (or a single unlabeled figure, as before).
        for sub in self.subs:
            with self.subTest(id=sub["id"]):
                decode = (sub["performance"].get("decode_tps") or "").lower()
                self.assertNotIn("pp ", f" {decode}",
                                 f"{sub['id']}: prefill figure leaked into decode_tps")
                self.assertNotIn("tg ", f" {decode}",
                                 f"{sub['id']}: compound speed string not split")

    def test_os_driver_key_present_and_populated(self):
        # P0-3 contract: every row carries the os_driver key (empty when not
        # reported) and at least one submission exposes a real value.
        for sub in self.subs:
            with self.subTest(id=sub["id"]):
                self.assertIn("os_driver", sub)
        populated = [s for s in self.subs if (s.get("os_driver") or "").strip()]
        self.assertGreaterEqual(
            len(populated), 1,
            "no submission exposes an OS/driver value",
        )


if __name__ == "__main__":
    unittest.main()
