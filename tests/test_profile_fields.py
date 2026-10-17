import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from specifications import PROFILE_KEYS, validate_profiles, resource_profile_html, comparison_body
from search_pages import resource_path, resource_markdown

ROWS = [json.loads(line) for line in (Path(__file__).resolve().parents[1] / "data/catalog.jsonl").read_text().splitlines()]


def fixture(rid):
    return copy.deepcopy(next(row for row in ROWS if row["id"] == rid))


FIXTURES = {"benchmark": "github:xlang-ai/osworld", "dataset": "github:dongping-chen/gui-world"}
FIELDS = {"benchmark": ["focus", "setting", "observations", "actions", "evaluation", "notes", "counts"], "dataset": ["supervision", "modalities", "formats", "splits", "notes", "counts"]}
BAD_VALUES = {
    "benchmark": [("focus", "gui"), ("focus", []), ("focus", [""]), ("focus", ["gui", "gui"]), ("setting", "banana"), ("setting", ["interactive"]), ("observations", "screenshots"), ("actions", [None]), ("evaluation", None), ("notes", 5)],
    "dataset": [("supervision", "trajectories"), ("supervision", []), ("modalities", "text"), ("formats", [" "]), ("splits", ["train", "train"]), ("notes", None)],
}


def render(row):
    resource_profile_html(row)
    comparison_body([row], row["kind"], resource_path)
    resource_markdown(row)


class ProfileFieldTests(unittest.TestCase):
    def test_missing_rendered_fields_are_rejected(self):
        for kind, rid in FIXTURES.items():
            for field in FIELDS[kind]:
                with self.subTest(kind=kind, missing=field):
                    row = fixture(rid)
                    del row["details"][PROFILE_KEYS[kind]][field]
                    self.assertTrue(validate_profiles(row))

    def test_wrong_field_types_are_rejected(self):
        for kind, rid in FIXTURES.items():
            for field, value in BAD_VALUES[kind]:
                with self.subTest(kind=kind, field=field, value=value):
                    row = fixture(rid)
                    row["details"][PROFILE_KEYS[kind]][field] = value
                    self.assertTrue(validate_profiles(row))

    def test_unhashable_count_labels_are_errors_not_crashes(self):
        for field in ["qualifier", "basis"]:
            with self.subTest(field=field):
                row = fixture(FIXTURES["benchmark"])
                row["details"]["benchmark_protocol"]["counts"][0][field] = ["exact"]
                self.assertTrue(any("precision qualifier or counting basis" in error for error in validate_profiles(row)))

    def test_duplicate_evidence_urls_are_rejected(self):
        row = fixture(FIXTURES["benchmark"])
        sources = row["details"]["benchmark_protocol"]["evidence_urls"]
        sources.append(sources[0])
        self.assertIn("benchmark_protocol has duplicate evidence receipts", validate_profiles(row))

    def test_current_profiles_validate_and_render(self):
        profiled = [row for row in ROWS if any(row["details"].get(key) for key in PROFILE_KEYS.values())]
        self.assertGreater(len(profiled), 0)
        for row in profiled:
            with self.subTest(id=row["id"]):
                self.assertEqual(validate_profiles(row), [])
                render(row)


if __name__ == "__main__":
    unittest.main()
