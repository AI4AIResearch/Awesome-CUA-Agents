from collections import defaultdict
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog


class CuratedSummaryTests(unittest.TestCase):
    def test_no_two_curated_records_share_a_summary(self):
        groups = defaultdict(list)
        for row in catalog.read_jsonl(catalog.DATA / "catalog.jsonl"):
            if row.get("review_status") == "curated":
                groups[" ".join(row["summary"].split()).casefold()].append(row["id"])
        self.assertEqual({text: ids for text, ids in groups.items() if len(ids) > 1}, {})


if __name__ == "__main__":
    unittest.main()
