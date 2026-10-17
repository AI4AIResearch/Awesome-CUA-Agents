import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_site import compact_facts

ROOT = Path(__file__).resolve().parents[1]
ROWS = {row["id"]: row for row in map(json.loads, (ROOT / "data/catalog.jsonl").read_text().splitlines())}


class CompactFactsTests(unittest.TestCase):
    def test_documented_resource_gets_its_paper_and_declared_license(self):
        self.assertEqual(compact_facts(ROWS["github:xlang-ai/osworld"]), {"paper_arxiv": "2404.07972", "declared_licenses": {"code": "Apache-2.0"}})

    def test_paper_keeps_its_own_arxiv_id(self):
        self.assertEqual(compact_facts(ROWS["arxiv:2404.07972"])["paper_arxiv"], "2404.07972")

    def test_introducing_paper_wins_and_licenses_keep_slot_order(self):
        row = copy.deepcopy(ROWS["github:xlang-ai/osworld"])
        row["relations"] = [{"type": "documented_by", "target_id": "arxiv:2501.00001", "evidence_url": "https://example.org/"},
                            {"type": "documented_by", "target_id": "url:abc", "evidence_url": "https://example.org/"},
                            {"type": "introduced_by", "target_id": "arxiv:2401.00002", "evidence_url": "https://example.org/"}]
        row["licenses"] = {"document": None, "weights": {"declared": ["MIT", "CC-BY-4.0"]}, "data": {"declared": ""}, "code": {"declared": "Apache-2.0"}}
        self.assertEqual(compact_facts(row), {"paper_arxiv": "2401.00002", "declared_licenses": {"code": "Apache-2.0", "weights": "MIT, CC-BY-4.0"}})

    def test_unrecorded_facts_stay_empty(self):
        row = copy.deepcopy(ROWS["github:xlang-ai/osworld"])
        row["relations"] = [{"type": "documented_by", "target_id": "url:abc", "evidence_url": "https://example.org/"}]
        row["licenses"] = dict.fromkeys(("code", "data", "weights", "document"))
        self.assertEqual(compact_facts(row), {"paper_arxiv": None, "declared_licenses": {}})

    def test_catalog_facts_are_strings(self):
        for row in ROWS.values():
            facts = compact_facts(row)
            self.assertTrue(facts["paper_arxiv"] is None or facts["paper_arxiv"].strip(), row["id"])
            self.assertTrue(all(isinstance(v, str) and v.strip() for v in facts["declared_licenses"].values()), row["id"])


if __name__ == "__main__":
    unittest.main()
