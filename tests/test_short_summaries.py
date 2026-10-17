from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog

# Their reviewed receipts are too thin for a specific summary: the WebUI Hub card names only the project,
# and openai.com refuses the Operator announcement to the catalog's fetcher.
THIN_SOURCES = {"url:13b9442bcb6a8b984c4f", "url:f0584842138a52158f51"}


class ShortSummaryTests(unittest.TestCase):
    def test_curated_non_paper_summaries_are_specific(self):
        short = {row["id"]: row["summary"] for row in catalog.read_jsonl(catalog.DATA / "catalog.jsonl")
                 if row.get("review_status") == "curated" and row["kind"] not in {"paper", "survey"} and len(row["summary"]) < 60}
        self.assertEqual({k: v for k, v in short.items() if k not in THIN_SOURCES}, {})


if __name__ == "__main__":
    unittest.main()
