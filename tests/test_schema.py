"""Schema validation: ``tools/schema.json`` is the contract.

The pipeline, the generator, the client filters, and the (future) guides all
depend on this file's shape. These tests lock its structure in place:

* a version string in ``major.minor`` form;
* exactly 6 VRAM tiers, ordered, with contiguous ranges;
* every enum non-empty and string-typed;
* well-formed, unique, https ``monitored_threads`` (with the ``main``
  submissions thread present, since ``parse.py`` depends on it).
"""

import unittest

from tests.util import load_json

ENUM_KEYS = (
    "hardware_vendors",
    "backends",
    "os_drivers",
    "quant_formats",
    "kv_cache_types",
    "use_cases",
    "engine_modes",
    "confidence_levels",
    "lifecycle_statuses",
)


class TestSchemaStructure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_json("tools/schema.json")

    def test_version_present_and_well_formed(self):
        version = self.schema.get("version")
        self.assertIsInstance(version, str)
        parts = version.split(".")
        self.assertEqual(len(parts), 2, f"version {version!r} is not major.minor")
        self.assertTrue(all(p.isdigit() for p in parts))

    def test_six_tiers_in_strict_ascending_order(self):
        tiers = self.schema["tiers"]
        self.assertEqual(len(tiers), 6, "expected exactly 6 tiers")
        self.assertEqual(
            [t["id"] for t in tiers], [f"t{i}" for i in range(1, 7)],
            "tiers must be ordered t1..t6",
        )
        for tier in tiers:
            self.assertIn("label", tier)
            self.assertEqual(len(tier["range"]), 2)
            self.assertLess(tier["range"][0], tier["range"][1])
        # Strictly ascending. (Gaps are intentional: e.g. no 32–48GB
        # consumer hardware class exists, so t4 starts at 48.)
        for prev, cur in zip(tiers, tiers[1:]):
            self.assertGreater(
                cur["range"][0], prev["range"][0],
                f"{cur['id']} must start above {prev['id']}",
            )
            self.assertGreater(
                cur["range"][1], prev["range"][1],
                f"{cur['id']} must end above {prev['id']}",
            )

    def test_all_enums_non_empty(self):
        for key in ENUM_KEYS:
            with self.subTest(enum=key):
                values = self.schema[key]
                self.assertIsInstance(values, list)
                self.assertTrue(values, f"{key} is empty")
                self.assertTrue(
                    all(isinstance(v, str) and v.strip() for v in values),
                    f"{key} contains non-string/blank entries",
                )
                self.assertEqual(len(values), len(set(values)), f"{key} has duplicates")

    def test_monitored_threads_well_formed(self):
        threads = self.schema["monitored_threads"]
        self.assertGreaterEqual(len(threads), 1)
        required = {"id", "url", "name", "type", "description"}
        seen = set()
        for thread in threads:
            with self.subTest(thread=thread.get("id")):
                self.assertTrue(
                    required.issubset(thread),
                    f"thread missing keys: {required - set(thread)}",
                )
                self.assertTrue(
                    thread["url"].startswith("https://"),
                    f"thread url not https: {thread['url']}",
                )
                self.assertNotIn(thread["id"], seen, "duplicate thread id")
                seen.add(thread["id"])
        # parse.py reads data/raw/main_latest.json; the main thread must exist.
        self.assertIn("main", seen)


if __name__ == "__main__":
    unittest.main()
