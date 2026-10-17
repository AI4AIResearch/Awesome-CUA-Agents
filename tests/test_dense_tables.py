from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build


def row(name, environments, published_at="2025-01-02"):
    return {"name": name, "url": "https://example.com/" + name, "environments": environments, "summary": name + ".", "published_at": published_at,
        "relations": [], "licenses": {"code": None, "data": None, "weights": None, "document": None},
        "evidence": [{"method": "editorial_primary_review", "url": "https://example.com/" + name, "retrieved_at": "2026-10-16T00:00:00Z"}]}


class DenseTableTests(unittest.TestCase):
    def test_uniform_environments_are_stated_once(self):
        lines = build.section_table([row("A", ["web"]), row("B", ["web"])], build.KIND_COLUMNS[None][0], {})
        self.assertEqual(lines[0], "All entries in this section: web.")
        self.assertEqual(lines[2], "| Resource | Paper | License | Description | Evidence |")
        self.assertTrue(all(line.count("|") == 6 for line in lines[2:]))

    def test_mixed_environments_keep_the_column(self):
        lines = build.section_table([row("A", ["android"]), row("B", ["android", "ios"])], build.KIND_COLUMNS[None][0], {})
        self.assertEqual(lines[0], "| Resource | Environments | Paper | License | Description | Evidence |")
        self.assertIn("| android, ios |", lines[3])

    def test_dates_do_not_wrap(self):
        line = build.table_row(row("A", ["web"]), build.KIND_COLUMNS["survey"][0], {})
        self.assertTrue(line.startswith("| 2025‑01‑02 |"))
        self.assertIn("[✓ 2026‑10‑16]", build.table_row(row("A", ["web"]), build.KIND_COLUMNS[None][0], {}))
        self.assertNotIn("-", build.nowrap("2026-10-16"))


if __name__ == "__main__":
    unittest.main()
