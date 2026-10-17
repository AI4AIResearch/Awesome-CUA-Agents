from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog


# Curated repositories whose reviewed README links the same-named paper (#92).
PAIRS = {"github:microsoft/ufo": "2402.07939", "github:emergenceai/agent-e": "2407.13032", "github:meituan/evocua": "2601.15876",
    "github:llamatouch/llamatouch": "2404.16054", "github:hitsz-tmg/windowsworld": "2604.27776", "github:yjyddq/riosworld": "2506.00618",
    "github:unipat-ai/saas-bench": "2605.15777", "github:os-copilot/os-sentinel": "2510.24411", "github:uitron-hub/treecua": "2602.09662",
    "github:zju-real/clawgui": "2604.11784", "github:madeagents/mobile-use": "2507.16853", "github:open-compass/mmbench-gui": "2507.19478",
    "github:os-copilot/scienceboard": "2505.19897", "github:thudm/mobilerl": "2509.18119", "github:x-lance/mobile-env": "2305.08144",
    "github:xlang-ai/spider2-v": "2407.10956", "github:zju-real/gui-g2": "2507.15846"}


class DocumentedByPairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = {r["id"]: r for r in catalog.read_jsonl(catalog.DATA / "catalog.jsonl")}
        cls.enrichment = {r["id"]: r for r in catalog.read_jsonl(catalog.DATA / "enrichment.jsonl")}

    def primary(self, record):
        return next(ev for ev in record["evidence"] if ev["method"] == "editorial_primary_review")

    def test_repository_is_documented_by_its_paper(self):
        for rid, aid in PAIRS.items():
            with self.subTest(rid):
                record = self.records[rid]
                self.assertEqual(record["review_status"], "curated")
                self.assertIn("relations", self.primary(record)["supports"])
                self.assertIn({"type": "documented_by", "target_id": "arxiv:" + aid, "evidence_url": self.primary(record)["url"]}, record["relations"])
                self.assertEqual(self.records["arxiv:" + aid]["kind"], "paper")

    def test_reviewed_snapshot_links_the_paper(self):
        for rid, aid in PAIRS.items():
            with self.subTest(rid):
                sha = self.primary(self.records[rid])["sha256"]
                row = self.enrichment[rid]
                self.assertEqual(row["evidence_sha256"], sha)
                self.assertIn("arxiv:" + aid, {ref["target_id"] for ref in row["references"] if ref["source_sha256"] == sha})


if __name__ == "__main__":
    unittest.main()
