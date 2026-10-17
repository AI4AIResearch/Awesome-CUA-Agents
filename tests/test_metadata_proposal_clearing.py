import copy
import datetime as dt
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import arxiv_metadata
import build
import catalog
import test_arxiv_metadata as fixtures
from test_arxiv_metadata import entry, feed, paper


def incomplete(row):
    """A transient Atom entry whose abstract digest is missing."""
    row = copy.deepcopy(row)
    row["details"]["arxiv_snapshot"]["abstract_sha256"] = None
    return row


class ProposalClearingTests(unittest.TestCase):
    def observe(self, retained, observations, proposals=None):
        records, proposals = {retained["id"]: copy.deepcopy(retained)}, proposals or {}
        statuses = []
        for day, observed in enumerate(observations, 17):
            arxiv_metadata.consider_paper(observed, records, proposals, f"2026-10-{day}T00:00:00Z")
            statuses.append(proposals.get(retained["id"], {}).get("review_status"))
        self.assertEqual(records[retained["id"]], retained)
        return statuses, proposals

    def test_matching_observation_clears_incomplete_and_reverted_proposals(self):
        old = paper()
        cases = {
            "incomplete then clean": incomplete(old),
            "new version then reverted": paper(version=2, updated="2026-10-05T12:00:00Z"),
            "abstract change then reverted": paper(abstract="A different GUI method."),
        }
        for label, first in cases.items():
            with self.subTest(label):
                statuses, proposals = self.observe(old, [first, copy.deepcopy(old)])
                self.assertIsNotNone(statuses[0])
                self.assertIsNone(statuses[1])
                self.assertEqual(proposals, {})

    def test_repeated_difference_or_uncertainty_keeps_the_proposal(self):
        old = paper()
        for label, observed in {"change": paper(version=2, updated="2026-10-05T12:00:00Z"), "uncertainty": incomplete(old)}.items():
            with self.subTest(label):
                _, proposals = self.observe(old, [observed, copy.deepcopy(observed)])
                proposal = proposals[old["id"]]
                self.assertEqual((proposal["first_observed_at"], proposal["last_observed_at"]), ("2026-10-17T00:00:00Z", "2026-10-18T00:00:00Z"))

    def test_incomplete_baseline_is_not_cleared_by_a_complete_observation(self):
        old = incomplete(paper())
        statuses, proposals = self.observe(old, [paper(), paper()])
        self.assertEqual(statuses, ["metadata_revalidation_pending"] * 2)
        self.assertEqual(proposals[old["id"]]["reason"], "snapshot_baseline_requires_review")

    def test_an_older_cached_observation_keeps_a_newer_proposal(self):
        old = paper()
        records, proposals = {old["id"]: copy.deepcopy(old)}, {}
        arxiv_metadata.consider_paper(paper(version=2, updated="2026-10-05T12:00:00Z"), records, proposals, "2026-10-18T00:00:00Z")
        arxiv_metadata.consider_paper(copy.deepcopy(old), records, proposals, "2026-10-16T00:00:00Z")
        self.assertEqual(proposals[old["id"]]["review_status"], "metadata_change_pending")
        arxiv_metadata.consider_paper(copy.deepcopy(old), records, proposals, "2026-10-18T00:00:00Z")
        self.assertEqual(proposals, {})

    def test_other_papers_proposals_are_untouched(self):
        other = {"id": "arxiv:2610.00002", "review_status": "metadata_change_pending"}
        _, proposals = self.observe(paper(), [paper()], {other["id"]: other})
        self.assertEqual(proposals, {other["id"]: other})


class ExclusionReopeningTests(unittest.TestCase):
    # Reuse the offline IngestionTests harness without re-running its tests here.
    setUp, fetch, seed, ingest = (fixtures.IngestionTests.setUp, fixtures.IngestionTests.fetch,
                                  fixtures.IngestionTests.seed, fixtures.IngestionTests.ingest)

    def test_excluded_paper_closes_again_once_the_source_matches(self):
        for name in ("harvest", "search", "recent"):
            for label, first in {"changed": entry(version=2, updated="2026-10-05T12:00:00Z"), "incomplete": entry(abstract=None)}.items():
                with self.subTest(entrypoint=name, first=label):
                    fixtures.FrozenDateTime.current = dt.datetime(2026, 10, 17, 12, tzinfo=dt.timezone.utc)
                    old = self.seed(protection="excluded")
                    self.responses = [feed([first], total=1)]
                    self.ingest(name)
                    self.assertEqual(len(catalog.read_jsonl(self.path / "metadata-updates.jsonl")), 1)
                    self.assertEqual(build.source_records(with_scope=True)[2][0]["status"], "revalidation_pending")
                    # A later UTC day, so the recent scan cannot reuse the first snapshot.
                    fixtures.FrozenDateTime.current = dt.datetime(2026, 10, 18, 12, tzinfo=dt.timezone.utc)
                    self.responses = [feed([entry()], total=1)]
                    self.ingest(name)
                    self.assertEqual(catalog.read_jsonl(self.path / "metadata-updates.jsonl"), [])
                    self.assertEqual(catalog.read_jsonl(self.path / "papers.jsonl"), [old])
                    rows, pending, decisions = build.source_records(with_scope=True)
                    self.assertEqual(decisions[0]["status"], "excluded")
                    self.assertEqual((rows, pending), ([], []))


if __name__ == "__main__":
    unittest.main()
