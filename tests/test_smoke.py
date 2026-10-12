"""Smoke tests: the foundation is intact.

The first assertions a new environment hits. They verify, without executing
any pipeline logic:

* every one of the 5 pipeline scripts parses and imports cleanly;
* every committed data file is valid JSON with its expected top-level shape.

If these fail, nothing else in the suite can be trusted.
"""

import unittest

from tests.util import DATA_FILES, PIPELINE_SCRIPTS, ROOT, load_json, load_tool


class TestPipelineImportable(unittest.TestCase):
    """Each of the 5 pipeline scripts must import without error."""

    def test_all_scripts_import(self):
        for relpath in PIPELINE_SCRIPTS:
            with self.subTest(script=relpath):
                module = load_tool(relpath)
                self.assertIsNotNone(module.__file__)
                self.assertTrue(module.__file__.endswith(relpath.split("/")[-1]))

    def test_scripts_are_runnable_entrypoints(self):
        # Every tool is a script (python tools/x.py): it must guard its
        # main() behind __main__ so importing it has no side effects.
        for relpath in PIPELINE_SCRIPTS:
            with self.subTest(script=relpath):
                text = (ROOT / relpath).read_text(encoding="utf-8")
                self.assertIn("__main__", text)

    def test_pipeline_scripts_are_pep8_compilable(self):
        # Byte-compiles every script; catches syntax errors on this
        # interpreter (Python 3.14) without running the tools.
        import py_compile

        for relpath in PIPELINE_SCRIPTS:
            with self.subTest(script=relpath):
                py_compile.compile(str(ROOT / relpath), doraise=True)


class TestDataFilesValid(unittest.TestCase):
    """Every committed data file must be valid JSON with its expected shape."""

    def test_all_data_files_parse(self):
        for relpath in DATA_FILES:
            with self.subTest(file=relpath):
                data = load_json(relpath)
                self.assertIsNotNone(data, f"{relpath} parsed to None")

    def test_submissions_top_level_shape(self):
        data = load_json("data/submissions.json")
        for key in (
            "generated_at",
            "schema_version",
            "source_thread",
            "total_submissions",
            "skipped_templates",
            "submissions",
        ):
            self.assertIn(key, data, f"submissions.json missing {key}")
        # The header count must match the rows actually present.
        self.assertEqual(
            data["total_submissions"], len(data["submissions"])
        )
        self.assertIsInstance(data["submissions"], list)
        self.assertGreater(len(data["submissions"]), 0)

    def test_dataset_schema_version_matches_schema(self):
        # parse.py stamps the schema version into the dataset; a mismatch
        # means the data was produced by a different schema generation.
        schema = load_json("tools/schema.json")
        data = load_json("data/submissions.json")
        self.assertEqual(data["schema_version"], schema["version"])

    def test_secondary_thread_outputs_have_expected_shape(self):
        for relpath, key in (
            ("data/benchmarks.json", "items"),
            ("data/hardware.json", "items"),
            ("data/category_threads.json", "items"),
        ):
            with self.subTest(file=relpath):
                data = load_json(relpath)
                self.assertIn("thread_id", data)
                self.assertIn("count", data)
                self.assertIn(key, data)
                self.assertEqual(data["count"], len(data[key]))


if __name__ == "__main__":
    unittest.main()
