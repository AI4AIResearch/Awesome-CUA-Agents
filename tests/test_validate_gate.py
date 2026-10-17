import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build
import catalog
from test_catalog import paper
from test_scope_review import decision


def other_paper():
    return json.loads(json.dumps(paper()).replace("2404.07972", "2404.07973"))


class ValidateGateTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.data = Path(directory.name)
        patcher = mock.patch.object(build, "DATA", self.data)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, catalog_rows, papers=(), decisions=None, updates=()):
        catalog.write_jsonl(self.data / "catalog.jsonl", catalog_rows)
        catalog.write_jsonl(self.data / "papers.jsonl", papers)
        catalog.write_jsonl(self.data / "metadata-updates.jsonl", [{"id": rid} for rid in updates])
        if decisions is not None:
            catalog.write_json(self.data / "exclusions.json", decisions)

    def validate(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            build.validate(types.SimpleNamespace())
        return out.getvalue()

    def errors(self):
        with self.assertRaises(ValueError) as raised:
            self.validate()
        return str(raised.exception).splitlines()

    def test_missing_or_empty_catalog_requires_a_build(self):
        with self.assertRaisesRegex(ValueError, "^No catalog. Run build first.$"):
            self.validate()
        self.write([])
        with self.assertRaisesRegex(ValueError, "^No catalog. Run build first.$"):
            self.validate()

    def test_valid_catalog_and_applied_exclusion_pass(self):
        self.write([paper()])
        self.assertTrue(self.validate().startswith("Validated 1 records: JSON Schema"))
        excluded = other_paper()
        self.write([paper()], papers=[excluded], decisions=[decision(excluded)])
        self.assertTrue(self.validate().startswith("Validated 1 records: JSON Schema"))

    def test_scope_excluded_record_cannot_remain_in_the_active_catalog(self):
        row = paper()
        self.write([row], papers=[row], decisions=[decision(row)])
        self.assertEqual(self.errors(), ["arxiv:2404.07972: scope-excluded record remains in the active catalog"])

    def test_stale_scope_decision_cannot_suppress_a_record(self):
        stale = other_paper()
        self.write([paper()], papers=[stale], decisions=[decision(stale)], updates=[stale["id"]])
        self.assertEqual(self.errors(), ["arxiv:2404.07973: stale scope decision must not suppress a record"])
        self.write([paper(), stale], papers=[stale], decisions=[decision(stale)], updates=[stale["id"]])
        self.assertTrue(self.validate().startswith("Validated 2 records: JSON Schema"))

    def test_schema_invalid_decision_is_reported_without_cross_checks(self):
        row = paper()
        invalid = decision(row)
        del invalid["reason"]
        self.write([row], papers=[row], decisions=[invalid])
        self.assertEqual(self.errors(), ["Scope decisions: 'reason' is a required property"])

    def test_error_report_is_capped_at_forty_lines(self):
        invalid = decision(paper())
        del invalid["reason"]
        self.write([paper()], decisions=[invalid] * 45)
        self.assertEqual(self.errors(), ["Scope decisions: 'reason' is a required property"] * 40)


if __name__ == "__main__":
    unittest.main()
