from pathlib import Path
import sys
import unittest
import urllib.parse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog


# Papers behind curated resources that were still relevance_pending (#105), with the scope their reviewed abstract supports.
REVIEWED = {"arxiv:2310.10634": "adjacent", "arxiv:2605.28534": "core", "arxiv:2507.21071": "core"}
LINKED_FROM = {"component:xlang-ai/openagents/web_agent": "arxiv:2310.10634", "github:wuzheng02/gui-cider": "arxiv:2605.28534",
    "url:d0300db5ba754b1a64fa": "arxiv:2605.28534"}


class LinkedPaperCurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = {r["id"]: r for r in catalog.read_jsonl(catalog.DATA / "catalog.jsonl")}
        cls.receipts = {r["id"]: r for r in catalog.read_jsonl(catalog.DATA / "primary-evidence.jsonl")}
        cls.editorial = {catalog.editorial_identity(r)[0]: r for r in catalog.read_json(catalog.DATA / "editorial.json")}
        cls.topics = set(catalog.read_json(catalog.DATA / "topics.json"))

    def test_papers_are_curated_with_a_scope_decision(self):
        for rid, scope in REVIEWED.items():
            with self.subTest(rid):
                record = self.records[rid]
                self.assertEqual((record["kind"], record["review_status"], record["scope"]), ("paper", "curated", scope))
                self.assertTrue(record["environments"])
                self.assertTrue(record["topics"])
                self.assertLessEqual(set(record["topics"]), self.topics)
                self.assertLessEqual(len(record["summary"]), 200)
                self.assertTrue(record["summary"].endswith("."))

    def test_approval_cites_the_retained_arxiv_receipt(self):
        for rid in REVIEWED:
            with self.subTest(rid):
                entry, receipt = self.editorial[rid], self.receipts[rid]
                self.assertIs(entry["editorial_reviewed"], True)
                self.assertTrue(receipt["content_matched"])
                self.assertEqual(entry["reviewed_sha256"], receipt["sha256"])
                self.assertEqual(entry["evidence_urls"], [receipt["url"]])
                parts = urllib.parse.urlsplit(receipt["url"])
                self.assertEqual((parts.hostname, parts.path), ("export.arxiv.org", "/api/query"))
                primary = next(ev for ev in self.records[rid]["evidence"] if ev["method"] == "editorial_primary_review")
                self.assertEqual((primary["url"], primary["sha256"]), (receipt["url"], receipt["sha256"]))
                self.assertIn("details.arxiv_snapshot", next(ev for ev in self.records[rid]["evidence"] if ev["method"] == "arxiv_api")["supports"])

    def test_linking_resources_point_at_curated_papers(self):
        for rid, target in LINKED_FROM.items():
            with self.subTest(rid):
                record = self.records[rid]
                self.assertEqual(record["review_status"], "curated")
                self.assertIn(target, {rel["target_id"] for rel in record["relations"] if rel["type"] in {"documented_by", "introduced_by"}})
                self.assertEqual(self.records[target]["review_status"], "curated")


if __name__ == "__main__":
    unittest.main()
