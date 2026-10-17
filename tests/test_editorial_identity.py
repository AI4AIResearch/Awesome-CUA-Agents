import contextlib
import io
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog


class EditorialIdentityTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(mock.patch.object(catalog, "DATA", self.directory))

    def test_url_without_identity_stops_verify_and_enrich_before_network(self):
        rows = [{"name": "Good", "url": "https://example.org/good"},
                {"name": "Demo", "url": "https://www.youtube.com/watch?v=abc"},
                {"name": "Paper DOI", "url": "https://doi.org/10.1000/example"}]
        catalog.write_json(self.directory / "editorial.json", rows)
        for command, output in [(catalog.verify_editorial, "primary-evidence.jsonl"), (catalog.enrich, "enrichment.jsonl")]:
            with self.subTest(command=command.__name__):
                with mock.patch.object(catalog, "fetch", side_effect=AssertionError("Unexpected network request")), \
                        mock.patch.object(catalog, "cached_body", side_effect=AssertionError("Unexpected cache read")), \
                        contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as stopped:
                    command(types.SimpleNamespace(refresh=False))
                message = str(stopped.exception.code)
                self.assertIn("INVALID Demo: https://www.youtube.com/watch?v=abc has no canonical identity", message)
                self.assertIn("INVALID Paper DOI: https://doi.org/10.1000/example", message)
                self.assertNotIn("Good", message)
                self.assertFalse((self.directory / output).exists())

    def test_canonical_urls_still_verify(self):
        catalog.write_json(self.directory / "editorial.json", [{"name": "Good", "url": "https://example.org/good"}])
        fake = lambda url, refresh=False: ({"url": url, "ok": True, "status": 200, "sha256": "a" * 64, "retrieved_at": "t"}, b"Good")
        with mock.patch.object(catalog, "fetch", side_effect=fake), contextlib.redirect_stdout(io.StringIO()):
            catalog.verify_editorial(types.SimpleNamespace(refresh=False))
        self.assertTrue(catalog.read_jsonl(self.directory / "primary-evidence.jsonl")[0]["content_matched"])


if __name__ == "__main__":
    unittest.main()
