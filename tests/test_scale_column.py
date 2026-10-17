from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build


def count(value, unit, qualifier="exact", population="release", reference=None):
    row = {"value": value, "unit": unit, "qualifier": qualifier, "basis": "reported", "population": population, "evidence_url": "https://example.com/readme"}
    if reference is not None:
        row["reference_url"] = reference
    return row


class ScaleColumnTests(unittest.TestCase):
    def test_first_count_per_unit_keeps_qualifier_and_source(self):
        record = {"kind": "benchmark", "details": {"benchmark_protocol": {"counts": [
            count(340, "tasks", population="complete collection"), count(300, "tasks", population="single-app subset"),
            count(15000, "demonstrations", "more-than", reference="https://example.com/paper"), count(66, "applications", "approximately")]}}}
        self.assertEqual(build.scale_cell(record), "[340 tasks](https://example.com/readme) · [> 15,000 demonstrations](https://example.com/paper) · [≈ 66 applications](https://example.com/readme)")

    def test_dataset_profiles_and_missing_counts(self):
        self.assertEqual(build.scale_cell({"kind": "dataset", "details": {"dataset_profile": {"counts": [count(1.5, "hours")]}}}), "[1.5 hours](https://example.com/readme)")
        self.assertEqual(build.scale_cell({"kind": "dataset", "details": {"dataset_profile": {"counts": []}}}), "—")
        self.assertEqual(build.scale_cell({"kind": "benchmark", "details": {}}), "—")
        self.assertEqual(build.scale_cell({"kind": "model", "details": {}}), "—")

    def test_benchmark_and_dataset_pages_show_scale(self):
        for kind in ("benchmark", "dataset"):
            self.assertIn("Scale", build.KIND_COLUMNS[kind][0])
        self.assertNotIn("Scale", build.KIND_COLUMNS[None][0])


if __name__ == "__main__":
    unittest.main()
