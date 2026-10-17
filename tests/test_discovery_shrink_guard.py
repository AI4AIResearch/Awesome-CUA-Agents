import contextlib
import hashlib
import io
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog
import scan

SOURCE = {"id": "src", "name": "S", "url": "https://raw.githubusercontent.com/o/awesome/main/README.md", "homepage": "https://github.com/o/awesome"}


def readme(count):
    return ("## Benchmarks\n" + "".join(f"- https://github.com/o/repo{i}\n" for i in range(count))).encode()


class ShrinkGuardTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.path = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.stack.enter_context(mock.patch.object(catalog, "DATA", self.path))
        self.stack.enter_context(mock.patch.object(catalog, "fetch", side_effect=self.fetch))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        catalog.write_json(self.path / "sources.json", [SOURCE])
        self.bodies = []

    def fetch(self, url, refresh=False):
        body = self.bodies.pop(0)
        return {"url": url, "ok": True, "status": 200, "retrieved_at": "2026-10-17T00:00:00Z", "sha256": hashlib.sha256(body).hexdigest()}, body

    def discover(self, body, accept=None):
        self.bodies.append(body)
        catalog.discover(types.SimpleNamespace(refresh=True, accept_shrink=accept))
        return catalog.read_json(self.path / "discovery-runs.json")[0]

    def provenance(self):
        return sum(len(r["discovered_in"]) for r in catalog.read_jsonl(self.path / "candidates.jsonl"))

    def test_empty_success_keeps_provenance_and_is_reported_as_a_failed_source(self):
        self.discover(readme(4))
        candidates = catalog.read_jsonl(self.path / "candidates.jsonl")
        for _ in range(2):  # The rejected run's manifest must not lower the next run's baseline.
            run = self.discover(b"")
            self.assertEqual(catalog.read_jsonl(self.path / "candidates.jsonl"), candidates)
            self.assertFalse(run["ok"])
            self.assertEqual(run["state"], "failed")
            self.assertTrue(run["error"].startswith("suspicious shrink: 4 -> 0; previous provenance retained"))
        _, problems = scan.summarize_phases([{"name": "discovery", "ok": True}], [run], [], [])
        self.assertIn("Discovery sources failed: src", problems)

    def test_drop_below_half_is_held_but_half_is_applied(self):
        self.discover(readme(4))
        run = self.discover(readme(1))
        self.assertFalse(run["ok"])
        self.assertIn("4 -> 1", run["error"])
        self.assertEqual(self.provenance(), 4)
        run = self.discover(readme(2))
        self.assertTrue(run["ok"])
        self.assertEqual((run["unique_resources"], self.provenance()), (2, 2))

    def test_explicitly_accepted_shrink_is_applied(self):
        self.discover(readme(4))
        run = self.discover(b"", accept=["other"])
        self.assertFalse(run["ok"])
        run = self.discover(b"", accept=["src"])
        self.assertTrue(run["ok"])
        self.assertEqual(run["state"], "success")
        self.assertEqual(self.provenance(), 0)
        self.assertEqual(len(catalog.read_jsonl(self.path / "candidates.jsonl")), 4)

    def test_cli_accepts_repeated_shrink_flags(self):
        with mock.patch.object(catalog, "discover") as discover, mock.patch.object(sys, "argv", ["catalog.py", "discover", "--accept-shrink", "a", "--accept-shrink", "b"]):
            catalog.main()
        self.assertEqual(discover.call_args.args[0].accept_shrink, ["a", "b"])


if __name__ == "__main__":
    unittest.main()
