from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog
import test_arxiv_metadata as fixtures
from test_arxiv_metadata import entry, feed

NAIVE = "2026-10-04T10:00:00"  # A published timestamp without a timezone.


class EntryErrorTests(unittest.TestCase):
    # Reuse the offline IngestionTests harness without re-running its tests here.
    setUp, fetch, ingest = fixtures.IngestionTests.setUp, fixtures.IngestionTests.fetch, fixtures.IngestionTests.ingest

    def test_harvest_limits_a_malformed_entry_to_its_own_identifier(self):
        ids = ["2610.00001", "2610.00002", "2610.00003"]
        catalog.write_jsonl(self.path / "candidates.jsonl", [
            {"id": "arxiv:" + aid, "url": "https://arxiv.org/abs/" + aid, "provider": "arxiv", "discovered_in": []} for aid in ids])
        self.responses = [feed([entry(aid=ids[0]), entry(aid=ids[1], published=NAIVE), entry(aid=ids[2])], total=3)]
        self.ingest("harvest")
        self.assertEqual([r["id"] for r in catalog.read_jsonl(self.path / "papers.jsonl")], ["arxiv:2610.00001", "arxiv:2610.00003"])
        failures = catalog.read_jsonl(self.path / "harvest-failures.jsonl")
        self.assertEqual([(r["id"], r["error"]) for r in failures],
                         [("arxiv:2610.00002", "invalid Atom entry: arXiv entry timestamp requires a timezone")])

    def test_search_lists_malformed_entries_keeps_paginating_and_stays_incomplete(self):
        self.responses = [feed([entry(aid="2610.00001"), entry(aid="2610.00002", published=NAIVE)], total=3),
                          feed([entry(aid="2610.00003")], total=3)]
        self.ingest("search")
        self.assertEqual(self.responses, [])
        report = catalog.read_json(self.path / "arxiv-search.json")
        self.assertFalse(report["complete"])
        self.assertEqual(report["unique_returned"], 2)
        self.assertEqual(report["pages"][0]["entry_errors"], [
            {"id": "http://arxiv.org/abs/2610.00002v1", "error": "arXiv entry timestamp requires a timezone"}])
        self.assertNotIn("entry_errors", report["pages"][1])
        self.assertEqual([r["id"] for r in catalog.read_jsonl(self.path / "papers.jsonl")], ["arxiv:2610.00001", "arxiv:2610.00003"])

    def test_search_with_only_valid_entries_remains_complete(self):
        self.responses = [feed([entry(aid="2610.00001"), entry(aid="2610.00002")], total=2)]
        self.ingest("search")
        report = catalog.read_json(self.path / "arxiv-search.json")
        self.assertTrue(report["complete"])
        self.assertNotIn("entry_errors", report["pages"][0])


if __name__ == "__main__":
    unittest.main()
