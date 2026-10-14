"""Schema validation: ``tools/schema.json`` is the contract.

The pipeline, the generator, the client filters, and the (future) guides all
depend on this file's shape. These tests lock its structure in place:

* a version string in ``major.minor`` form;
* exactly 6 VRAM tiers, ordered, with contiguous ranges;
* every enum non-empty and string-typed;
* well-formed, unique, https ``monitored_threads`` (with the ``main``
  submissions thread present, since ``parse.py`` depends on it);
* the E2 token lists (known_gpus / known_model_families / known_models /
  vendor_keywords / model_author_prefixes) non-empty and properly formatted,
  and parse.py / site utils building their regexes from them — adding a new
  GPU or model is a schema edit, not a code change.
"""

import re
import sys
import unittest

from tests.util import ROOT, load_json, load_tool

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

    def test_six_disjoint_tiers_are_contiguous(self):
        # A3: the tiers are DISJOINT bands — each starts exactly where the
        # previous one ends, so every VRAM amount has exactly one tier
        # home (a 16GB card is t2, a 24GB card t3, a 32GB 5090 t4, ...).
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
        for prev, cur in zip(tiers, tiers[1:]):
            self.assertEqual(
                cur["range"][0], prev["range"][1],
                f"{cur['id']} must start exactly where {prev['id']} ends "
                "(disjoint bands: no gaps, no overlaps)",
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


class TestFieldsRegistry(unittest.TestCase):
    """``fields`` (schema v2.4) is the single source of truth for what the
    forum template asks for and what parse.py extracts. This class locks the
    registry's shape and enforces that it stays in sync with the parser.
    """

    @classmethod
    def setUpClass(cls):
        cls.schema = load_json("tools/schema.json")
        cls.parse = load_tool("tools/parse.py")

    def test_fields_registry_present(self):
        fields = self.schema.get("fields")
        self.assertIsInstance(fields, dict, "schema is missing the fields registry")
        for key in ("canonical", "aliases", "optional"):
            self.assertIn(key, fields, f"fields.{key} missing")

    def test_all_canonical_fields_registered(self):
        # Every field parse.py maps into the dataset entry must be declared.
        canonical = set(self.schema["fields"]["canonical"])
        for required in (
            "tier", "hardware", "backend", "os_driver", "model_name",
            "quant_package", "weight_precision", "download_url",
            "primary_use_case", "stable_context_tested", "kv_cache_setting",
            "engine_mode", "throughput_tps", "prefill_tps", "ttft_cold",
            "power_draw", "setup_notes",
        ):
            self.assertIn(required, canonical, f"{required} not registered")

    def test_speed_is_a_tracked_field(self):
        # The user-requested speed / tokens-per-second field: canonical name
        # plus every friendly spelling the community uses.
        self.assertIn("throughput_tps", self.schema["fields"]["canonical"])
        aliases = self.schema["fields"]["aliases"]
        for alias in ("speed", "tok_s", "tokens_per_second", "tps"):
            self.assertEqual(aliases.get(alias), "throughput_tps",
                             f"alias {alias} must target throughput_tps")

    def test_aliases_match_parser_exactly(self):
        # Drift guard: schema.json "fields.aliases" must equal parse.py's
        # FIELD_ALIASES, so the registry and the code can never disagree.
        self.assertEqual(
            self.schema["fields"]["aliases"],
            dict(self.parse.FIELD_ALIASES),
            "schema fields.aliases and parse.py FIELD_ALIASES have drifted",
        )

    def test_alias_targets_are_registered_canonical(self):
        canonical = set(self.schema["fields"]["canonical"])
        for alias, target in self.schema["fields"]["aliases"].items():
            self.assertIn(target, canonical, f"alias {alias} -> unregistered {target}")

    def test_optional_fields_are_registered(self):
        canonical = set(self.schema["fields"]["canonical"])
        for opt in self.schema["fields"]["optional"]:
            self.assertIn(opt, canonical, f"optional field {opt} not registered")
        # Speed is tracked but optional (not every submission reports it).
        self.assertIn("throughput_tps", self.schema["fields"]["optional"])

    def test_required_minimum_is_three_fields(self):
        # B10: the site's submit form enforces ONLY tier + hardware +
        # model_name — the minimum for a useful entry (the "30 seconds"
        # promise). backend / quant_package / primary_use_case are optional
        # (encouraged), and the registry must say exactly that.
        canonical = set(self.schema["fields"]["canonical"])
        optional = set(self.schema["fields"]["optional"])
        self.assertEqual(
            canonical - optional,
            {"tier", "hardware", "model_name"},
            "the required minimum must be exactly tier + hardware + model_name")
        for encouraged in ("backend", "quant_package", "primary_use_case"):
            self.assertIn(
                encouraged, optional,
                f"{encouraged} must be optional (encouraged) per B10")


class TestTokenLists(unittest.TestCase):
    """E2: the GPU / model / vendor token lists live in schema.json.

    These tests lock the token lists' SHAPE (non-empty, string-typed, no
    blanks, no duplicates) so a bad edit is caught here instead of silently
    degrading the parser's signal detection — and they verify the code side
    (parse.py / site utils) actually builds from the schema, so the two can
    never drift.
    """

    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        cls.schema = load_json("tools/schema.json")
        cls.parse = load_tool("tools/parse.py")

    def _strings(self, values):
        self.assertIsInstance(values, list)
        self.assertTrue(values, "token list is empty")
        self.assertTrue(
            all(isinstance(v, str) and v.strip() for v in values),
            "token list contains non-string/blank entries")
        self.assertEqual(len(values), len(set(values)), "token list has duplicates")

    # --- shape ------------------------------------------------------------
    def test_known_gpus_well_formed(self):
        self._strings(self.schema["known_gpus"])

    def test_known_model_families_well_formed(self):
        self._strings(self.schema["known_model_families"])

    def test_known_models_well_formed(self):
        self._strings(self.schema["known_models"])

    def test_model_author_prefixes_well_formed(self):
        self._strings(self.schema["model_author_prefixes"])

    def test_vendor_keywords_well_formed(self):
        vk = self.schema["vendor_keywords"]
        self.assertIsInstance(vk, dict)
        self.assertTrue(vk, "vendor_keywords is empty")
        # Every vendor key is a schema vendor (Mixed is an outcome, not a
        # signal source), and each carries a non-empty token list.
        vendors = set(self.schema["hardware_vendors"])
        for vendor, tokens in vk.items():
            with self.subTest(vendor=vendor):
                self.assertIn(vendor, vendors, f"unknown vendor {vendor!r}")
                self.assertNotEqual(vendor, "Mixed",
                                    "Mixed is never a signal source")
                self._strings(tokens)

    # --- the code builds from the schema (drift guard) ---------------------
    def test_parse_gpu_tokens_built_from_schema(self):
        expected = {self.parse._gpu_token(n): n for n in self.schema["known_gpus"]}
        self.assertEqual(self.parse._GPU_TOKENS, expected,
                         "parse._GPU_TOKENS must be derived from schema known_gpus")

    def test_parse_model_tokens_built_from_schema(self):
        self.assertEqual(tuple(self.parse._MODEL_TOKENS),
                         tuple(self.schema["known_models"]),
                         "parse._MODEL_TOKENS must equal schema known_models")

    def test_parse_vendor_signals_built_from_schema(self):
        vk = self.schema["vendor_keywords"]
        for vendor, tokens in vk.items():
            with self.subTest(vendor=vendor):
                if vendor == "Apple":
                    # M-series chips match word-bounded, not as substrings.
                    expected = tuple(t for t in tokens
                                     if not re.fullmatch(r"m[1-4]", t))
                else:
                    expected = tuple(tokens)
                self.assertEqual(self.parse._VENDOR_SUBSTRINGS.get(vendor), expected,
                                 f"parse._VENDOR_SUBSTRINGS[{vendor}] must equal "
                                 "schema vendor_keywords")

    def test_parse_hardware_signal_re_covers_schema(self):
        pat = self.parse.HARDWARE_SIGNAL_RE.pattern
        for name in self.schema["known_gpus"]:
            self.assertRegex(pat, re.escape(name),
                             f"hardware signal regex missing GPU {name!r}")
        for fam in self.schema["known_model_families"]:
            self.assertRegex(pat, re.escape(fam),
                             f"hardware signal regex missing family {fam!r}")

    def test_utils_family_prefix_built_from_schema(self):
        from tools.site import utils
        self.assertIsNotNone(utils.FAMILY_AUTHOR_PREFIX,
                             "FAMILY_AUTHOR_PREFIX must be built from the schema")
        for prefix in self.schema["model_author_prefixes"]:
            with self.subTest(prefix=prefix):
                self.assertTrue(
                    utils.FAMILY_AUTHOR_PREFIX.match(f"{prefix}-SomeModel"),
                    f"utils.FAMILY_AUTHOR_PREFIX does not match {prefix!r}")
                self.assertEqual(
                    utils.model_family(f"{prefix}-SomeModel-27B-GGUF"),
                    "SomeModel-27B",
                    f"model_family does not strip the {prefix!r} author prefix")


if __name__ == "__main__":
    unittest.main()
