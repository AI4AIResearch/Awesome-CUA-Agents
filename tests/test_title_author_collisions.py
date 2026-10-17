import contextlib
import io
from pathlib import Path
import sys
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build

AUTHORS = ["Jikai Chen", "Long Chen", "Dong Wang"]


def paper(aid, title="V2P: Visual Attention Calibration for GUI Grounding", authors=AUTHORS, status="metadata_verified", **identifiers):
    return {"id": "arxiv:" + aid, "url": "https://arxiv.org/abs/" + aid, "name": title, "kind": "paper", "review_status": status,
        "authors": list(authors), "aliases": [], "environments": ["unspecified"], "topics": [], "identifiers": {"arxiv": aid, **identifiers}}


def groups(rows):
    return [[r["id"] for r in group] for group in build.title_author_collisions(rows)]


def collision_errors(rows):
    return [error for error in build.validate_records(rows) if "title and authors match" in error]


class TitleAuthorCollisionTests(unittest.TestCase):
    def test_same_title_and_authors_without_a_decision_are_reported(self):
        rows = [paper("2508.13634", status="curated"), paper("2601.06899", title="v2p -  visual attention calibration for GUI grounding")]
        self.assertEqual(groups(rows), [["arxiv:2508.13634", "arxiv:2601.06899"]])
        self.assertEqual(collision_errors(rows), [])

    def test_preferred_arxiv_decides_the_pair(self):
        self.assertEqual(groups([paper("2508.13634", status="curated"), paper("2601.06899", preferred_arxiv="2508.13634")]), [])
        rows = [paper("2508.13634"), paper("2601.06899", preferred_arxiv="2508.13634"), paper("2602.00001")]
        self.assertEqual(groups(rows), [["arxiv:2508.13634", "arxiv:2602.00001"]])

    def test_a_preferred_arxiv_outside_the_group_decides_nothing(self):
        self.assertEqual(groups([paper("2508.13634"), paper("2601.06899", preferred_arxiv="2401.00001")]), [["arxiv:2508.13634", "arxiv:2601.06899"]])

    def test_different_authors_or_kinds_are_not_collisions(self):
        self.assertEqual(groups([paper("2508.13634"), paper("2601.06899", authors=AUTHORS[::-1])]), [])
        self.assertEqual(groups([paper("2508.13634"), paper("2601.06899", authors=AUTHORS[:2])]), [])
        model = {**paper("2601.06899"), "kind": "model"}
        self.assertEqual(groups([paper("2508.13634"), model]), [])

    def test_a_second_curated_copy_fails_validation(self):
        rows = [paper("2508.13634", status="curated"), paper("2601.06899", status="curated")]
        self.assertEqual(collision_errors(rows), ["arxiv:2601.06899: title and authors match curated arxiv:2508.13634; record identifiers.preferred_arxiv on the duplicate"])

    def test_validate_reports_the_v2p_pair_without_its_decision(self):
        real = build.read_jsonl

        def without_decision(path):
            rows = real(path)
            if Path(path).name == "catalog.jsonl":
                for row in rows:
                    if row["id"] == "arxiv:2601.06899":
                        row["identifiers"].pop("preferred_arxiv")
            return rows

        with mock.patch.object(build, "read_jsonl", side_effect=without_decision), contextlib.redirect_stdout(io.StringIO()) as out:
            build.validate(types.SimpleNamespace())
        self.assertIn("Undecided duplicate: arxiv:2508.13634, arxiv:2601.06899 share a title and author list", out.getvalue())
        with contextlib.redirect_stdout(io.StringIO()) as out:
            build.validate(types.SimpleNamespace())
        self.assertNotIn("Undecided duplicate", out.getvalue())


if __name__ == "__main__":
    unittest.main()
