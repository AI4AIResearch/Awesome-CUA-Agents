import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog
import build


def record(rid, url, name, kind="paper", **fields):
    return {"id": rid, "url": url, "name": name, "kind": kind, "review_status": "curated", "environments": ["desktop"],
        "summary": None, "aliases": [], "authors": [], "topics": [], "identifiers": {}, **fields}


ROWS = [
    record("arxiv:2404.07972", "https://arxiv.org/abs/2404.07972", "OSWorld: Benchmarking Multimodal Agents", identifiers={"arxiv": "2404.07972"}),
    record("arxiv:2505.13887", "https://arxiv.org/abs/2505.13887", "A republished paper", review_status="metadata_verified", identifiers={"arxiv": "2505.13887", "preferred_arxiv": "2502.17110"}),
    record("github:xlang-ai/osworld", "https://github.com/xlang-ai/OSWorld", "OSWorld", kind="benchmark", summary="Desktop tasks."),
    record(catalog.canonical("https://example.com/agent")[0], "https://example.com/agent", "Example agent", kind="product"),
]


class SearchLookupTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        catalog.write_jsonl(Path(directory.name) / "catalog.jsonl", ROWS)
        patcher = mock.patch.object(build, "DATA", Path(directory.name))
        patcher.start()
        self.addCleanup(patcher.stop)

    def cli(self, *argv):
        with mock.patch.object(sys, "argv", ["catalog.py", "search", *argv]), contextlib.redirect_stdout(io.StringIO()) as out:
            catalog.main()
        return out.getvalue()

    def ids(self, query):
        return [r["id"] for r in json.loads(self.cli(query, "--limit", "0", "--json"))["records"]]

    def test_negative_limit_is_a_usage_error(self):
        for value in ("-1", "-5"):
            with contextlib.redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit) as exit:
                self.cli("osworld", "--limit", value)
            self.assertEqual(exit.exception.code, 2)
            self.assertIn("--limit", err.getvalue())

    def test_zero_limit_returns_every_match(self):
        self.assertEqual(json.loads(self.cli("--limit", "0", "--json"))["returned"], len(ROWS))
        limited = json.loads(self.cli("--limit", "1", "--json"))
        self.assertEqual((limited["total_matches"], limited["returned"]), (len(ROWS), 1))

    def test_identifiers_find_records(self):
        self.assertEqual(self.ids("2404.07972"), ["arxiv:2404.07972"])
        self.assertEqual(self.ids("arxiv:2404.07972"), ["arxiv:2404.07972"])
        self.assertEqual(self.ids("2502.17110"), ["arxiv:2505.13887"])
        self.assertEqual(self.ids("github:xlang-ai/osworld"), ["github:xlang-ai/osworld"])
        self.assertEqual(self.ids("xlang-ai"), ["github:xlang-ai/osworld"])
        self.assertEqual(self.ids(ROWS[3]["id"]), [ROWS[3]["id"]])

    def test_urls_find_records_by_canonical_identity(self):
        self.assertEqual(self.ids("https://github.com/xlang-ai/OSWorld"), ["github:xlang-ai/osworld"])
        self.assertEqual(self.ids("https://github.com/xlang-ai/OSWorld/tree/main"), ["github:xlang-ai/osworld"])
        self.assertEqual(self.ids("http://arxiv.org/pdf/2404.07972v3.pdf"), ["arxiv:2404.07972"])
        self.assertEqual(self.ids("https://example.com/agent/?utm_source=feed"), [ROWS[3]["id"]])

    def test_text_output_shows_record_id(self):
        output = self.cli("osworld", "--kind", "benchmark")
        self.assertIn("OSWorld [benchmark · curated] github:xlang-ai/osworld\n  https://github.com/xlang-ai/OSWorld", output)


if __name__ == "__main__":
    unittest.main()
