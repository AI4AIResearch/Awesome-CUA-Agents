import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog
import build


def record(slug, name, kind, status="curated", environments=("desktop",), **fields):
    url = "https://example.org/" + slug
    return {"id": catalog.canonical(url)[0], "url": url, "name": name, "kind": kind, "review_status": status, "environments": list(environments),
        "summary": None, "aliases": [], "authors": [], "topics": [], "identifiers": {}, **fields}


# File order differs from result order, and the names' case differs from their case-folded order.
ROWS = [
    record("item-1", "Zeta Grounder", "model", environments=["android"], summary="Grounds GUI\nelements on phone screens.", topics=["gui-grounding"]),
    record("item-2", "Beta Agent", "paper", status="metadata_verified", authors=["Ada Lovelace"], topics=["gui-grounding"]),
    record("item-3", "aardvark Assistant", "product", status="metadata_verified", environments=["android", "ios"], summary="A phone assistant."),
    record("item-4", "alpha Navigator", "benchmark", environments=["web"], summary="Multi-step GUI tasks on live websites.", aliases=["WebNav Suite"], topics=["web-navigation"]),
]
ZETA, BETA, AARDVARK, ALPHA = (row["id"] for row in ROWS)


class SearchCliTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.data = Path(directory.name)
        catalog.write_jsonl(self.data / "catalog.jsonl", ROWS)
        patcher = mock.patch.object(build, "DATA", self.data)
        patcher.start()
        self.addCleanup(patcher.stop)

    def search(self, query="", limit=0, **filters):
        args = types.SimpleNamespace(query=query, kind=None, status=None, environment=None, topic=None, limit=limit, json=True)
        vars(args).update(filters)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            build.search(args)
        return json.loads(out.getvalue())

    def ids(self, query="", **filters):
        return [row["id"] for row in self.search(query, **filters)["records"]]

    def test_terms_are_case_insensitive_and_all_must_match(self):
        self.assertEqual(self.ids("gui"), [ALPHA, ZETA, BETA])
        self.assertEqual(self.ids("GUI grounding"), [ZETA, BETA])
        self.assertEqual(self.ids("grounding GUI"), self.ids("gui GROUNDING"))
        self.assertEqual(self.ids("gui grounding websites"), [])
        self.assertEqual(self.ids("lovelace BETA"), [BETA])

    def test_whitespace_in_query_and_record_text_only_separates_terms(self):
        self.assertEqual(self.ids("  grounds \n gui  "), [ZETA])
        self.assertEqual(self.ids("gui elements"), [ZETA])
        self.assertEqual(self.ids("gui-elements"), [])

    def test_each_text_field_is_searchable(self):
        for query, expected in [("navigator", ALPHA), ("websites", ALPHA), ("webnav", ALPHA), ("lovelace", BETA), ("web-navigation", ALPHA), ("aardvark", AARDVARK)]:
            with self.subTest(query=query):
                self.assertEqual(self.ids(query), [expected])

    def test_environment_and_kind_are_filters_not_search_terms(self):
        # The CLI haystack leaves out environments and kind, unlike the site search in web/app.js.
        self.assertEqual(self.ids("android"), [])
        self.assertEqual(self.ids(environment="android"), [ZETA, AARDVARK])
        self.assertEqual(self.ids("benchmark"), [])
        self.assertEqual(self.ids(kind="benchmark"), [ALPHA])

    def test_each_filter_narrows_matches_on_its_own(self):
        self.assertEqual(self.ids(kind="model"), [ZETA])
        self.assertEqual(self.ids(kind="dataset"), [])
        self.assertEqual(self.ids(status="curated"), [ALPHA, ZETA])
        self.assertEqual(self.ids(status="metadata_verified"), [AARDVARK, BETA])
        self.assertEqual(self.ids(environment="ios"), [AARDVARK])
        self.assertEqual(self.ids(topic="gui-grounding"), [ZETA, BETA])
        self.assertEqual(self.ids(topic="gui"), [], "topic filters are exact facet values")

    def test_filters_combine_with_terms_and_each_other(self):
        self.assertEqual(self.ids("gui", status="curated"), [ALPHA, ZETA])
        self.assertEqual(self.ids("phone", environment="android", status="metadata_verified"), [AARDVARK])
        self.assertEqual(self.ids("gui", kind="paper", topic="gui-grounding"), [BETA])
        self.assertEqual(self.ids("gui", kind="product"), [])

    def test_curated_records_come_first_then_case_folded_name(self):
        self.assertEqual(self.ids(), [ALPHA, ZETA, AARDVARK, BETA])

    def test_json_envelope_counts_all_matches_and_returns_full_records(self):
        result = self.search("gui", limit=1)
        self.assertEqual(list(result), ["total_matches", "returned", "records"])
        self.assertEqual((result["total_matches"], result["returned"]), (3, 1))
        self.assertEqual(result["records"], [ROWS[3]])
        self.assertEqual(self.search("nothing-matches"), {"total_matches": 0, "returned": 0, "records": []})

    def test_cli_defaults_to_twenty_matches_and_zero_returns_all(self):
        catalog.write_jsonl(self.data / "catalog.jsonl", [record(f"filler-{i}", f"Filler {i:02d}", "tool") for i in range(25)])

        def cli(*argv):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(catalog.main(["search", *argv]), 0)
            return out.getvalue()

        output = cli("filler")
        self.assertTrue(output.startswith("25 matches; showing 20\n"))
        self.assertEqual(output.count(" [tool · curated] "), 20)
        self.assertIn("Filler 19 [tool", output)
        self.assertNotIn("Filler 20 [tool", output)
        self.assertTrue(cli("filler", "--limit", "0").startswith("25 matches; showing 25\n"))
        self.assertEqual(json.loads(cli("filler", "--json"))["returned"], 20)
        self.assertEqual(json.loads(cli("filler", "--limit", "0", "--json"))["returned"], 25)


if __name__ == "__main__":
    unittest.main()
