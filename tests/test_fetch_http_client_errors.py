import hashlib
import http.client
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog


URL = "https://example.org/source"


def truncated_response():
    result = mock.MagicMock(status=200, url=URL, headers={"Content-Type": "text/plain"})
    result.__enter__.return_value = result
    result.read.side_effect = http.client.IncompleteRead(b"partial", 100)
    return result


class FetchHttpClientErrorTests(unittest.TestCase):
    def setUp(self):
        self.cache = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(mock.patch.object(catalog, "CACHE", self.cache))
        self.sleep = self.enterContext(mock.patch("time.sleep"))
        self.key = hashlib.sha256(URL.encode()).hexdigest()

    def test_http_client_errors_become_failed_receipts(self):
        errors = {"IncompleteRead": http.client.IncompleteRead(b"partial", 100), "BadStatusLine": http.client.BadStatusLine("HTTP/9 ???"),
                  "LineTooLong": http.client.LineTooLong("header line"), "InvalidURL": http.client.InvalidURL("bad URL"),
                  "truncated body": truncated_response()}
        for name, outcome in errors.items():
            with self.subTest(name), mock.patch("urllib.request.urlopen", side_effect=[outcome]) as urlopen:
                info, body = catalog.fetch(URL, refresh=True)
                self.assertEqual((info["ok"], body, urlopen.call_count), (False, b"", 1))
                self.assertTrue(info["error"])
                self.assertEqual(catalog.read_json(self.cache / f"{self.key}.error.json")["error"], info["error"])
        self.sleep.assert_not_called()

    def test_failed_refresh_keeps_previous_successful_cache(self):
        catalog.write_json(self.cache / f"{self.key}.json", {"ok": True, "url": URL, "sha256": hashlib.sha256(b"old good snapshot").hexdigest()})
        (self.cache / f"{self.key}.body").write_bytes(b"old good snapshot")
        with mock.patch("urllib.request.urlopen", side_effect=[http.client.IncompleteRead(b"new", 50)]):
            info, body = catalog.fetch(URL, refresh=True)
        self.assertEqual((info["ok"], body), (False, b""))
        info, body = catalog.fetch(URL)
        self.assertEqual((info["ok"], body), (True, b"old good snapshot"))

    def test_url_with_whitespace_is_recorded_without_a_connection(self):
        with mock.patch("socket.create_connection", side_effect=AssertionError("no network")) as connect:
            info, body = catalog.fetch("https://example.org/a b", refresh=True)
        self.assertEqual((info["ok"], body), (False, b""))
        self.assertIn("control characters", info["error"])
        connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
