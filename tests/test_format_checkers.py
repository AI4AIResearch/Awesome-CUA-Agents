import copy
from pathlib import Path
import sys
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog
import build


def record():
    return copy.deepcopy(next(row for row in catalog.read_jsonl(catalog.DATA / "catalog.jsonl") if row["id"] == "arxiv:2404.07972"))


class FormatCheckerTests(unittest.TestCase):
    def test_stdlib_gate_rejects_invalid_last_verified_at(self):
        self.assertNotIn("arxiv:2404.07972: invalid last_verified_at", build.validate_records([record()]))
        for value in ["not-a-timestamp", "2026-01-01T00:00:00", "2026-01-01", None, 20260101]:
            with self.subTest(value=value):
                row = record()
                row["last_verified_at"] = value
                self.assertIn("arxiv:2404.07972: invalid last_verified_at", build.validate_records([row]))

    def test_schema_enforces_date_time_and_uri_formats(self):
        import jsonschema
        self.assertLessEqual({"date-time", "uri"}, set(jsonschema.FormatChecker().checkers), "install requirements-dev.txt")
        validator = jsonschema.Draft202012Validator(catalog.read_json(catalog.ROOT / "schemas/resource.schema.json"), format_checker=jsonschema.FormatChecker())
        self.assertEqual(list(validator.iter_errors(record())), [])
        for path, value in [(("last_verified_at",), "not-a-timestamp"), (("evidence", 0, "retrieved_at"), "yesterday"), (("url",), "https://exa mple.org/x")]:
            with self.subTest(path=path):
                row = target = record()
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                self.assertTrue(any(error.validator == "format" for error in validator.iter_errors(row)))

    def test_validate_aborts_without_format_checkers(self):
        import jsonschema
        reduced = {name: check for name, check in jsonschema.FormatChecker.checkers.items() if name != "uri"}
        with mock.patch.object(jsonschema.FormatChecker, "checkers", reduced), mock.patch.object(build, "validate_records") as records:
            with self.assertRaisesRegex(ValueError, "format checkers unavailable: .*uri"):
                build.validate(types.SimpleNamespace())
        records.assert_not_called()


if __name__ == "__main__":
    unittest.main()
