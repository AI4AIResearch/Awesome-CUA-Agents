import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog
import build

ROWS = {r["id"]: r for r in catalog.read_jsonl(catalog.DATA / "catalog.jsonl")}


def record(rid):
    return {**copy.deepcopy(ROWS[rid]), "relations": []}


def identity_errors(rows):
    return [e for e in build.validate_records(rows) if "resolves to" in e or "identifiers.arxiv" in e]


class UrlIdentityTests(unittest.TestCase):
    def test_committed_catalog_urls_resolve_to_their_ids(self):
        self.assertEqual(identity_errors(list(ROWS.values())), [])

    def test_changed_url_no_longer_matching_the_id_fails(self):
        repository, paper = record("github:xlang-ai/osworld"), record("arxiv:2404.07972")
        repository["url"] = "https://github.com/someone-else/unrelated"
        other_paper = record("arxiv:2404.07972")
        other_paper["url"] = "https://arxiv.org/abs/2501.00001"
        page = record("url:00b1a3abf9bcb424b264")
        page["url"] = "https://huggingface.co/Tongyi-MAI/another-model"
        self.assertEqual(build.validate_records([repository, paper]), ["github:xlang-ai/osworld: url resolves to github:someone-else/unrelated, not to its id"])
        self.assertEqual(identity_errors([other_paper]), ["arxiv:2404.07972: url resolves to arxiv:2501.00001, not to its id"])
        self.assertEqual(len(identity_errors([page])), 1)

    def test_arxiv_identifier_must_match_the_id(self):
        paper = record("arxiv:2404.07972")
        paper["identifiers"] = {"arxiv": "2501.00001"}
        self.assertEqual(build.validate_records([paper]), ["arxiv:2404.07972: identifiers.arxiv does not match the arXiv id"])
        del paper["identifiers"]["arxiv"]
        self.assertEqual(identity_errors([paper]), ["arxiv:2404.07972: identifiers.arxiv does not match the arXiv id"])

    def test_equivalent_urls_and_documented_exceptions_pass(self):
        paper, repository = record("arxiv:2404.07972"), record("github:xlang-ai/osworld")
        paper["url"] = "https://arxiv.org/pdf/2404.07972v2"
        repository["url"] = "https://github.com/xlang-ai/OSWorld/tree/main"
        self.assertEqual(build.validate_records([paper, repository]), [])
        # Editor-assigned identities resolve elsewhere by design: a monorepo component and a publisher.
        exceptions = [record("component:google-research/android_control"), record("organization:openai")]
        self.assertNotEqual(catalog.canonical(exceptions[0]["url"])[0], exceptions[0]["id"])
        self.assertEqual(build.validate_records(exceptions), [])
        duplicate = record("arxiv:2505.13887")
        self.assertNotEqual(duplicate["identifiers"]["preferred_arxiv"], duplicate["identifiers"]["arxiv"])
        self.assertEqual(identity_errors([duplicate]), [])


if __name__ == "__main__":
    unittest.main()
