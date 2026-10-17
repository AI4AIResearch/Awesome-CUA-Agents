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

SOURCE = {"id": "src", "name": "S", "url": "https://raw.githubusercontent.com/o/awesome/main/README.md", "homepage": "https://github.com/o/awesome"}


def occurrence(source_id, line):
    return {"source_id": source_id, "line": line, "section": "Agents", "snapshot_sha256": "a" * 64}


class TrailingResidueTests(unittest.TestCase):
    def test_backticks_braces_and_backslashes_are_not_part_of_the_identity(self):
        cases = {
            "https://surf.new": ["https://surf.new`", "https://surf.new/`", "https://surf.new%60", "https://surf.new`."],
            "https://anonymous.4open.science/r/MemGUI-Bench-Anonymous": [
                "https://anonymous.4open.science/r/MemGUI-Bench-Anonymous%7D", "https://anonymous.4open.science/r/MemGUI-Bench-Anonymous%7d",
                "https://anonymous.4open.science/r/MemGUI-Bench-Anonymous}", "https://anonymous.4open.science/r/MemGUI-Bench-Anonymous},"],
            "https://huggingface.co/Hcompany/Holo1.5-72B": [
                "https://huggingface.co/Hcompany/Holo1.5-72B\\", "https://huggingface.co/Hcompany/Holo1.5-72B\\\\\\",
                "https://huggingface.co/Hcompany/Holo1.5-72B%5C", "https://huggingface.co/Hcompany/Holo1.5-72B{"],
        }
        for clean, inputs in cases.items():
            expected = catalog.canonical(clean)
            self.assertEqual(expected[1], clean)
            for url in inputs:
                with self.subTest(url=url):
                    self.assertEqual(catalog.canonical(url), expected)

    def test_balanced_parentheses_are_still_kept(self):
        mercury = "https://en.wikipedia.org/wiki/Mercury_(planet)"
        self.assertEqual(catalog.canonical(mercury + "`")[1], mercury)
        self.assertEqual(catalog.canonical("https://example.org/a)`"), catalog.canonical("https://example.org/a"))

    def test_extraction_stops_at_code_latex_and_escape_delimiters(self):
        text = ("Try `https://surf.new` or \\url{https://anonymous.4open.science/r/FingerTip-57B8}. "
                '{"href":"https://huggingface.co/Hcompany/Holo1.5-72B\\"} and "https://huggingface.co/Hcompany\\\\\\" '
                "plus {{https://example.org/a}} and [x](https://en.wikipedia.org/wiki/Mercury_(planet))")
        self.assertEqual(catalog.LINK_RE.findall(text), [
            "https://surf.new", "https://anonymous.4open.science/r/FingerTip-57B8", "https://huggingface.co/Hcompany/Holo1.5-72B",
            "https://huggingface.co/Hcompany", "https://example.org/a", "https://en.wikipedia.org/wiki/Mercury_(planet)"])
        self.assertEqual([url for _, _, url in catalog.source_links(SOURCE, ("## Agents\n- " + text).encode())], catalog.LINK_RE.findall(text))


class LocalHostTests(unittest.TestCase):
    def test_loopback_private_and_local_hosts_are_not_resources(self):
        for url in ["http://localhost:8000/x", "https://LOCALHOST", "http://app.localhost:3000/", "http://printer.local/",
                    "http://127.0.0.1:7860", "https://127.0.0.1//127.0.0.1:6801", "http://0.0.0.0:8080/v1", "http://10.1.2.3/",
                    "http://172.16.0.5", "http://192.168.1.10/x", "http://169.254.169.254/latest", "http://100.64.0.1/",
                    "http://[::1]:8080/", "http://[fe80::1]/", "http://[fd00::1]/", "http://[::ffff:127.0.0.1]/", "http://localhost:8000/x`"]:
            with self.subTest(url=url):
                self.assertIsNone(catalog.canonical(url))

    def test_public_hosts_still_parse(self):
        for url in ["https://8.8.8.8/", "http://[2606:4700:4700::1111]/", "https://localhost.example.com/",
                    "https://local.example.org/", "https://example.localhost.dev/", "https://172.32.0.1/"]:
            with self.subTest(url=url):
                self.assertEqual(catalog.canonical(url)[2], "url")


class StoredCandidateTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.path = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.stack.enter_context(mock.patch.object(catalog, "DATA", self.path))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))

    def candidate(self, url, *occurrences, first="2026-10-16T00:00:00Z", rid=None):
        rid = rid or "url:" + hashlib.sha256(url.encode()).hexdigest()[:20]
        return {"id": rid, "url": url, "provider": "url", "first_discovered_at": first, "discovered_in": list(occurrences)}

    def test_rerun_merges_or_drops_rows_whose_stored_url_no_longer_maps_to_their_id(self):
        clean = catalog.canonical("https://anonymous.4open.science/r/FingerTip-57B8")
        kept = {**self.candidate(clean[1], occurrence("other", 3), first="2026-10-15T00:00:00Z"), "id": clean[0]}
        rows = [
            self.candidate("https://surf.new`", occurrence("src", 1), occurrence("other", 9)),
            self.candidate("https://anonymous.4open.science/r/FingerTip-57B8%7D", occurrence("other", 3), occurrence("other", 4), first="2026-10-14T00:00:00Z"),
            kept,
            self.candidate("https://127.0.0.1", occurrence("other", 5)),
            self.candidate("https://web3.arxiv.org/abs/2408.07199v1", occurrence("other", 6)),
            {"id": "arxiv:2408.07199", "url": "https://arxiv.org/abs/2408.07199", "provider": "arxiv", "first_discovered_at": "2026-10-16T00:00:00Z",
             "discovered_in": [occurrence("arxiv-title-search", None)], "discovered_title": "Kept field"},
        ]
        catalog.write_jsonl(self.path / "candidates.jsonl", rows)
        catalog.write_json(self.path / "sources.json", [SOURCE])
        body = b"## Agents\n- `https://surf.new`\n- Run `http://localhost:8000/` locally\n"
        fetch = lambda url, refresh=False: ({"url": url, "ok": True, "status": 200, "retrieved_at": "2026-10-17T00:00:00Z", "sha256": hashlib.sha256(body).hexdigest()}, body)
        with mock.patch.object(catalog, "fetch", side_effect=fetch):
            catalog.discover(types.SimpleNamespace(refresh=True, accept_shrink=None))
        result = {r["id"]: r for r in catalog.read_jsonl(self.path / "candidates.jsonl")}
        surf = catalog.canonical("https://surf.new")
        self.assertEqual(sorted(result), sorted([surf[0], clean[0], "arxiv:2408.07199"]))
        self.assertEqual((result[surf[0]]["url"], result[surf[0]]["first_discovered_at"]), ("https://surf.new", "2026-10-16T00:00:00Z"))
        self.assertEqual([(o["source_id"], o["line"]) for o in result[surf[0]]["discovered_in"]], [("other", 9), ("src", 2)])
        self.assertEqual(result[clean[0]]["first_discovered_at"], "2026-10-14T00:00:00Z")
        self.assertEqual([o["line"] for o in result[clean[0]]["discovered_in"]], [3, 4])
        self.assertEqual(result["arxiv:2408.07199"]["discovered_title"], "Kept field")
        self.assertEqual([o["source_id"] for o in result["arxiv:2408.07199"]["discovered_in"]], ["arxiv-title-search", "other"])
        self.assertEqual(catalog.read_json(self.path / "discovery-runs.json")[0]["unique_resources"], 1)


class EnrichReferenceTests(unittest.TestCase):
    def test_escaped_readme_links_yield_clean_reference_targets(self):
        url = "https://example.org/project"
        readme = b'<script>{"models":["https://huggingface.co/Hcompany/Holo1.5-72B\\"]}</script> `https://huggingface.co/datasets/xlangai/ubuntu_osworld/resolve/main/Ubuntu.qcow2.zip`'
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(catalog, "DATA", Path(directory)), \
                mock.patch.object(catalog, "cached_body", return_value=readme), contextlib.redirect_stdout(io.StringIO()):
            catalog.write_json(catalog.DATA / "editorial.json", [{"url": url, "kind": "framework", "name": "P"}])
            catalog.write_jsonl(catalog.DATA / "primary-evidence.jsonl", [{"id": catalog.canonical(url)[0], "url": url, "content_matched": True,
                "sha256": hashlib.sha256(readme).hexdigest(), "retrieved_at": "2026-10-17T00:00:00Z"}])
            catalog.enrich(types.SimpleNamespace(refresh=False))
            references = catalog.read_jsonl(catalog.DATA / "enrichment.jsonl")[0]["references"]
        self.assertEqual([r["target_url"] for r in references], [
            "https://huggingface.co/Hcompany/Holo1.5-72B", "https://huggingface.co/datasets/xlangai/ubuntu_osworld/resolve/main/Ubuntu.qcow2.zip"])


if __name__ == "__main__":
    unittest.main()
