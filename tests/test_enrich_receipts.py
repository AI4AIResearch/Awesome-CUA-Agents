import contextlib
import hashlib
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


README = b"See https://arxiv.org/abs/2404.07972 and https://github.com/xlang-ai/OSWorld"
MIT = b"MIT License\n\nCopyright (c) 2026 Example"


def sha(body):
    return hashlib.sha256(body).hexdigest()


class EnrichReceiptTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(mock.patch.object(catalog, "DATA", self.directory / "data"))
        self.enterContext(mock.patch.object(catalog, "CACHE", self.directory / "cache"))

    def run_enrich(self, rows, bodies, fetch=None):
        """rows: (editorial row, primary URL, receipt digest); bodies: cached body per primary URL."""
        catalog.write_json(catalog.DATA / "editorial.json", [row for row, _, _ in rows])
        catalog.write_jsonl(catalog.DATA / "primary-evidence.jsonl", [{"id": catalog.canonical(row["url"])[0], "url": primary,
            "content_matched": True, "sha256": digest, "retrieved_at": "2026-10-17T00:00:00Z"} for row, primary, digest in rows])
        out = io.StringIO()
        with mock.patch.object(catalog, "cached_body", side_effect=lambda url: bodies.get(url, b"")), \
                mock.patch.object(catalog, "fetch", side_effect=fetch or AssertionError("Unexpected network request")), \
                contextlib.redirect_stdout(out):
            catalog.enrich(types.SimpleNamespace(refresh=False))
        return {r["id"]: r for r in catalog.read_jsonl(catalog.DATA / "enrichment.jsonl")}, out.getvalue()

    def test_missing_or_mismatched_body_keeps_previous_row(self):
        url = "https://example.org/project"
        row, rid = {"url": url, "kind": "framework", "name": "P"}, catalog.canonical(url)[0]
        enriched, _ = self.run_enrich([(row, url, sha(README))], {url: README})
        self.assertEqual(len(enriched[rid]["references"]), 2)
        before = (catalog.DATA / "enrichment.jsonl").read_bytes()
        for body in (None, b"unrelated body https://github.com/evil/repo"):
            with self.subTest(body=body):
                enriched, out = self.run_enrich([(row, url, sha(README))], {url: body} if body else {})
                self.assertEqual((catalog.DATA / "enrichment.jsonl").read_bytes(), before)
                self.assertIn(f"STALE {rid}", out)
                self.assertIn("1 skipped", out)

    def test_real_cache_lookup_treats_absent_body_as_stale(self):
        url = "https://example.org/project"
        catalog.write_json(catalog.DATA / "editorial.json", [{"url": url, "kind": "framework", "name": "P"}])
        catalog.write_jsonl(catalog.DATA / "primary-evidence.jsonl", [{"id": catalog.canonical(url)[0], "url": url,
            "content_matched": True, "sha256": sha(README), "retrieved_at": "2026-10-17T00:00:00Z"}])
        with mock.patch.object(catalog, "fetch", side_effect=AssertionError("Unexpected network request")), contextlib.redirect_stdout(io.StringIO()) as out:
            catalog.enrich(types.SimpleNamespace(refresh=False))
        self.assertEqual(catalog.read_jsonl(catalog.DATA / "enrichment.jsonl"), [])
        self.assertIn("STALE", out.getvalue())

    def test_license_outage_keeps_recorded_code_license(self):
        url = "https://github.com/example/repo"
        primary = "https://raw.githubusercontent.com/example/repo/HEAD/README.md"
        row, rid = {"url": url, "kind": "framework", "name": "Repo"}, catalog.canonical(url)[0]
        license_url = "https://raw.githubusercontent.com/example/repo/HEAD/LICENSE"
        ok = lambda u, refresh=False: ({"url": u, "ok": True, "status": 200, "sha256": sha(MIT), "retrieved_at": "2026-10-16T00:00:00Z"}, MIT if u == license_url else b"")
        def failing(status):
            def fetch(u, refresh=False):
                requested.append(u.rsplit("/", 1)[1])
                return {"url": u, "ok": False, "status": status, "error": "HTTP Error"}, b""
            return fetch
        enriched, _ = self.run_enrich([(row, primary, sha(README))], {primary: README}, ok)
        recorded = enriched[rid]
        self.assertEqual(recorded["licenses"]["code"]["declared"], "MIT")
        receipt = [e for e in recorded["evidence"] if e["method"] == "license_header"]
        for status in (503, 429, None):
            with self.subTest(status=status):
                requested = []
                enriched, _ = self.run_enrich([(row, primary, sha(README))], {primary: README}, failing(status))
                # LICENSE takes precedence, so LICENSE.md and LICENSE.txt cannot stand in for it while it is unknown.
                self.assertEqual(requested, ["LICENSE"])
                self.assertEqual(enriched[rid]["licenses"]["code"], recorded["licenses"]["code"])
                self.assertEqual([e for e in enriched[rid]["evidence"] if e["method"] == "license_header"], receipt)
                self.assertEqual(enriched[rid]["references"], recorded["references"])
        requested = []
        enriched, _ = self.run_enrich([(row, primary, sha(README))], {primary: README}, failing(404))
        self.assertEqual(requested, ["LICENSE", "LICENSE.md", "LICENSE.txt"])
        self.assertNotIn("code", enriched[rid]["licenses"])
        self.assertEqual([e for e in enriched[rid]["evidence"] if e["method"] == "license_header"], [])

    def test_invalid_hub_api_body_is_skipped_without_aborting_other_rows(self):
        url, primary = "https://huggingface.co/datasets/org/data", "https://huggingface.co/api/datasets/org/data"
        other = "https://example.org/project"
        hub_id, other_id = catalog.canonical(url)[0], catalog.canonical(other)[0]
        for body in (b"", b"<html>502 Bad Gateway</html>", b"[]", b'{"cardData": []}'):
            with self.subTest(body=body):
                rows = [({"url": url, "kind": "dataset", "name": "D"}, primary, sha(body)), ({"url": other, "kind": "framework", "name": "P"}, other, sha(README))]
                enriched, out = self.run_enrich(rows, {primary: body, other: README})
                self.assertEqual(len(enriched[other_id]["references"]), 2)
                if body == b'{"cardData": []}':
                    self.assertEqual(enriched[hub_id]["details"]["languages"], [])
                    continue
                self.assertEqual(enriched[hub_id]["details"], {})
                self.assertEqual(enriched[hub_id]["licenses"], {})
                self.assertEqual(enriched[hub_id]["evidence"], [])
                self.assertIn(f"INVALID {hub_id}", out)

    def test_hub_list_fields_are_normalised(self):
        url, primary = "https://huggingface.co/datasets/org/data", "https://huggingface.co/api/datasets/org/data"
        rid = catalog.canonical(url)[0]
        cases = [
            ({"language": "en", "size_categories": "1K<n<10K"}, ["en"], ["1K<n<10K"]),
            ({"language": ["en", 3, "zh"], "size_categories": ["1K<n<10K"]}, ["en", "zh"], ["1K<n<10K"]),
            ({"license": {"name": "mit"}}, [], None),
            ({"license": 3}, [], None),
            ({"license": " "}, [], None),
            ({"license": []}, [], None),
        ]
        for card, languages, sizes in cases:
            with self.subTest(card=card):
                body = json.dumps({"id": "org/data", "tags": ["modality:image", 7, "task:x"], "cardData": card}).encode()
                enriched, _ = self.run_enrich([({"url": url, "kind": "dataset", "name": "D"}, primary, sha(body))], {primary: body})
                details = enriched[rid]["details"]
                self.assertEqual(details["languages"], languages)
                self.assertEqual(details["size_category_reported"], sizes)
                self.assertEqual(details["modalities"], ["image"])
                self.assertNotIn("data", enriched[rid]["licenses"])

    def test_hub_license_keeps_a_single_or_listed_declaration(self):
        import jsonschema
        schema = catalog.read_json(catalog.ROOT / "schemas/resource.schema.json")["properties"]["licenses"]["properties"]["weights"]
        url, primary = "https://huggingface.co/example/model", "https://huggingface.co/api/models/example/model"
        rid = catalog.canonical(url)[0]
        for license_name, declared in [("apache-2.0", "apache-2.0"), (["mit", "apache-2.0"], ["mit", "apache-2.0"]), (["mit", 3], ["mit"])]:
            with self.subTest(license=license_name):
                body = json.dumps({"id": "example/model", "cardData": {"license": license_name}}).encode()
                enriched, _ = self.run_enrich([({"url": url, "kind": "model", "name": "M"}, primary, sha(body))], {primary: body})
                self.assertEqual(enriched[rid]["licenses"]["weights"]["declared"], declared)
                jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(enriched[rid]["licenses"]["weights"])
                self.assertEqual(enriched[rid]["evidence"][0]["supports"], ["details", "licenses.weights"])


if __name__ == "__main__":
    unittest.main()
