import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build
from catalog import editorial_identity

# Flat keys that only an editor sets; profiles hold the counts with their units and populations.
LEGACY = {"dataset": ("sample_count", "sample_unit"), "benchmark": ("task_count", "task_unit", "metrics", "evaluation_type", "leaderboard_url")}


def editorial(name, kind, details=None):
    entry = {"name": name, "kind": kind, "url": f"https://github.com/example/{name}", "summary": f"{name} summary.",
        "environments": ["web"], "topics": [], "editorial_reviewed": True, "reviewed_sha256": "a" * 64, "reviewed_at": "2026-10-02T00:00:00Z"}
    if details is not None:
        entry["details"] = details
    return entry


class LegacyDetailFieldTests(unittest.TestCase):
    def build_fixture(self, entries, enrichment=()):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(build, "DATA", Path(directory)):
            data = Path(directory)
            (data / "editorial.json").write_text(json.dumps(entries))
            evidence = [{"id": f"github:example/{e['name'].lower()}", "url": e["url"], "retrieved_at": "2026-10-01T00:00:00Z", "sha256": "a" * 64, "content_matched": True} for e in entries]
            (data / "primary-evidence.jsonl").write_text("".join(json.dumps(row) + "\n" for row in evidence))
            (data / "enrichment.jsonl").write_text("".join(json.dumps(row) + "\n" for row in enrichment))
            for name in ("papers.jsonl", "publications.jsonl", "metadata-updates.jsonl"):
                (data / name).write_text("")
            rows, pending = build.source_records()
        self.assertEqual(pending, [])
        return {row["name"]: row for row in rows}

    def test_build_emits_no_placeholder_for_unset_flat_fields(self):
        rows = self.build_fixture([editorial("Data", "dataset"), editorial("Bench", "benchmark")])
        self.assertEqual(rows["Data"]["details"], {})
        self.assertEqual(rows["Bench"]["details"], {})

    def test_editorial_and_hub_values_are_kept_as_given(self):
        rows = self.build_fixture([editorial("Data", "dataset", {"sample_count": None, "sample_unit": "episodes"}),
            editorial("Bench", "benchmark", {"task_count": 12, "metrics": ["task success"]})],
            [{"id": "github:example/data", "evidence_sha256": "a" * 64, "details": {"languages": [], "modalities": ["image"]}}])
        self.assertEqual(rows["Data"]["details"], {"sample_count": None, "sample_unit": "episodes", "languages": [], "modalities": ["image"]})
        self.assertEqual(rows["Bench"]["details"], {"task_count": 12, "metrics": ["task success"]})

    def test_published_catalog_has_no_unset_flat_placeholders(self):
        entries = {(e.get("id") or editorial_identity(e)[0]): e.get("details", {}) for e in json.loads((ROOT / "data" / "editorial.json").read_text(encoding="utf-8"))}
        for line in (ROOT / "data" / "catalog.jsonl").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            for key in LEGACY.get(row["kind"], ()):
                if key in row["details"]:
                    with self.subTest(row["id"], key=key):
                        self.assertIn(key, entries[row["id"]])


if __name__ == "__main__":
    unittest.main()
