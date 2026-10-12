"""Data API tests (P4-4) — the versioned JSON contract is real and valid.

Runs the generator into a temp workspace (full inputs: dataset, schema,
shared assets, the whole ``content/`` dir, and the secondary-thread
datasets) and verifies:

* ``data.json`` carries the API ``version`` field (== ``api.API_VERSION``);
* ``data/api/v1/{submissions,benchmarks,hardware}.json`` are published,
  valid, and version-stamped (submissions identical to ``data.json``);
* ``data/api/v1/schema.json`` exists, is a well-formed JSON Schema
  (draft 2020-12) document, and is **not** rewritten by the generator
  (it is authored, not generated);
* the published ``data.json`` **conforms** to the schema — checked with a
  small stdlib validator (the project has no test dependencies);
* the ``/api/`` documentation page renders (structure, one h1, balanced
  tags, no template leaks).
"""

import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from html.parser import HTMLParser

from tests.util import ROOT
from tests.test_generate import TagChecker

API_V1 = "data/api/v1"
SCHEMA_PATH = f"{API_V1}/schema.json"

#: Everything the full-site build needs (mirrors the a11y/perf setup, plus
#: the secondary datasets the API publishes versioned copies of).
REQUIRED_INPUTS = (
    "data/submissions.json",
    "data/benchmarks.json",
    "data/hardware.json",
    "tools/schema.json",
    "css/style.css",
    "js/main.js",
)


# ---------------------------------------------------------------------------
# A small stdlib JSON Schema validator — exactly the keyword subset the
# project's schema uses (type incl. unions, enum, pattern, minimum,
# required, properties, additionalProperties:false, items, $defs/$ref).
# `format` is intentionally ignored (informational in our usage).
# ---------------------------------------------------------------------------

def _type_ok(value, tname: str) -> bool:
    if tname == "object":
        return isinstance(value, dict)
    if tname == "array":
        return isinstance(value, list)
    if tname == "string":
        return isinstance(value, str)
    if tname == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if tname == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if tname == "boolean":
        return isinstance(value, bool)
    if tname == "null":
        return value is None
    raise ValueError(f"unknown JSON Schema type: {tname}")


def validate(instance, schema: dict, root: dict, path: str = "$") -> list[str]:
    """Validate ``instance`` against ``schema``; return error strings."""
    errors: list[str] = []
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/$defs/"):
            errors.append(f"{path}: unsupported $ref target {ref!r}")
            return errors
        schema = root["$defs"][ref[len("#/$defs/"):]]

    t = schema.get("type")
    if t is not None:
        names = t if isinstance(t, list) else [t]
        if not any(_type_ok(instance, n) for n in names):
            errors.append(
                f"{path}: expected type {names}, got "
                f"{type(instance).__name__} ({instance!r})")
            return errors  # wrong type → deeper checks are meaningless

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} not in enum {schema['enum']}")

    if isinstance(instance, str) and "pattern" in schema:
        if not re.search(schema["pattern"], instance):
            errors.append(
                f"{path}: {instance!r} does not match "
                f"pattern {schema['pattern']!r}")

    if (isinstance(instance, int) and not isinstance(instance, bool)
            and "minimum" in schema and instance < schema["minimum"]):
        errors.append(f"{path}: {instance} < minimum {schema['minimum']}")

    if isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                errors.append(f"{path}: missing required key {req!r}")
        props = schema.get("properties", {})
        for key, val in instance.items():
            if key in props:
                errors.extend(validate(val, props[key], root, f"{path}.{key}"))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected key {key!r}")

    if isinstance(instance, list) and "items" in schema:
        for i, val in enumerate(instance):
            errors.extend(validate(val, schema["items"], root, f"{path}[{i}]"))

    return errors


VALID_TYPES = {"object", "array", "string", "integer", "number",
               "boolean", "null"}


def schema_structure_errors(schema: dict) -> list[str]:
    """Well-formedness check of the schema document itself (no validator lib).

    Verifies the draft marker, the top-level shape, that every ``required``
    key is defined in ``properties``, that type names are legal, and that
    every ``$ref`` resolves into ``$defs``.
    """
    errors: list[str] = []
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append(f"unexpected $schema: {schema.get('$schema')!r}")
    if schema.get("type") != "object":
        errors.append("top-level schema must be type 'object'")
    props = schema.get("properties", {})
    for req in schema.get("required", []):
        if req not in props:
            errors.append(f"required key {req!r} not defined in properties")

    def walk(node, path):
        if not isinstance(node, dict):
            errors.append(f"{path}: schema node is not an object")
            return
        if "$ref" in node:
            target = node["$ref"]
            if not target.startswith("#/$defs/") or \
                    target[len("#/$defs/"):] not in schema.get("$defs", {}):
                errors.append(f"{path}: unresolvable $ref {target!r}")
        t = node.get("type")
        if t is not None:
            names = t if isinstance(t, list) else [t]
            for n in names:
                if n not in VALID_TYPES:
                    errors.append(f"{path}: illegal type name {n!r}")
        if "enum" in node and not isinstance(node["enum"], list):
            errors.append(f"{path}: enum must be a list")
        for key, child in node.get("properties", {}).items():
            walk(child, f"{path}.properties.{key}")
        if "items" in node:
            walk(node["items"], f"{path}.items")
        for req in node.get("required", []):
            if "properties" in node and req not in node["properties"]:
                errors.append(f"{path}: required {req!r} not in properties")

    for key, node in props.items():
        walk(node, f"properties.{key}")
    for key, node in schema.get("$defs", {}).items():
        walk(node, f"$defs.{key}")
    return errors


# ---------------------------------------------------------------------------
# The tests
# ---------------------------------------------------------------------------

class TestDataApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        cls.tmp = Path(tempfile.mkdtemp(prefix="las_api_"))
        for rel in REQUIRED_INPUTS:
            src = ROOT / rel
            dst = cls.tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        # The full authored content dir (api.md + recommend.md + submit.md
        # + the guides) so every page renders, exactly like a real build.
        shutil.copytree(ROOT / "content", cls.tmp / "content",
                        dirs_exist_ok=True)
        # Snapshot the authored schema BEFORE the run — the generator must
        # never modify it.
        cls.schema_before = (ROOT / SCHEMA_PATH).read_bytes()

        from tools.site import api
        cls.api_module = api
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

    def _load(self, rel: str):
        with open(self.tmp / rel, encoding="utf-8") as f:
            return json.load(f)

    # --- versioning ---------------------------------------------------------

    def test_data_json_carries_api_version(self):
        from tools.site import api
        data = self._load("data.json")
        self.assertIn("version", data, "data.json is missing the version field")
        self.assertEqual(data["version"], api.API_VERSION)
        # version is first (the contract generation is visible up front)
        self.assertEqual(next(iter(data)), "version")

    def test_version_is_major_minor(self):
        from tools.site import api
        self.assertRegex(api.API_VERSION, r"^[0-9]+\.[0-9]+$")

    def test_v1_submissions_matches_data_json(self):
        self.assertEqual(
            self._load(f"{API_V1}/submissions.json"),
            self._load("data.json"),
            "v1/submissions.json must be the same payload as data.json")

    def test_secondary_datasets_are_versioned(self):
        for name in ("benchmarks.json", "hardware.json"):
            with self.subTest(file=name):
                data = self._load(f"{API_V1}/{name}")
                self.assertEqual(
                    data["version"], self.api_module.API_VERSION)
                # The original dataset fields are preserved.
                for key in ("thread_id", "count", "items"):
                    self.assertIn(key, data)

    # --- the JSON Schema ----------------------------------------------------

    def test_schema_is_well_formed(self):
        schema = json.loads(
            (ROOT / SCHEMA_PATH).read_text(encoding="utf-8"))
        self.assertEqual(
            schema_structure_errors(schema), [],
            "the JSON Schema document is not well-formed")
        self.assertIn("submission", schema["$defs"])

    def test_schema_is_authored_not_generated(self):
        # The generator must leave the authored schema byte-identical.
        self.assertEqual(
            (ROOT / SCHEMA_PATH).read_bytes(), self.schema_before,
            "the generator modified the authored JSON Schema")

    def test_data_json_conforms_to_schema(self):
        schema = json.loads(
            (ROOT / SCHEMA_PATH).read_text(encoding="utf-8"))
        data = self._load("data.json")
        self.assertEqual(
            validate(data, schema, schema), [],
            "data.json does not conform to data/api/v1/schema.json")

    # --- the /api/ documentation page ----------------------------------------

    def test_api_page_renders(self):
        path = self.tmp / "api" / "index.html"
        self.assertTrue(path.exists(), "/api/ page was not written")
        text = path.read_text(encoding="utf-8")
        self.assertIn("<h1>", text)
        self.assertEqual(text.count("<h1>"), 1, "expected exactly one <h1>")
        self.assertIn("<nav", text)
        self.assertIn("<footer", text)
        self.assertIn('property="og:title"', text)
        self.assertNotIn("{{", text)
        self.assertNotIn("}}", text)
        checker = TagChecker()
        checker.feed(text)
        checker.close()
        self.assertEqual(checker.finished(), [], "tag imbalance on /api/")

    def test_api_page_links_to_contract(self):
        text = (self.tmp / "api" / "index.html").read_text(encoding="utf-8")
        self.assertIn("v1/schema.json", text,
                      "the /api/ page must link the JSON Schema")
        self.assertIn("data.json", text,
                      "the /api/ page must reference the canonical payload")


if __name__ == "__main__":
    unittest.main()
