import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
import unittest
from unittest import mock
import urllib.error
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog
import build


def paper():
    element = ET.fromstring('''<entry xmlns="http://www.w3.org/2005/Atom">
      <id>http://arxiv.org/abs/2404.07972v3</id>
      <title>OSWorld: Benchmarking\n Multimodal Agents</title>
      <published>2024-04-11T00:00:00Z</published><updated>2024-05-01T00:00:00Z</updated>
      <author><name>A Researcher</name></author><summary>This must not become a reviewed summary.</summary>
    </entry>''')
    row = catalog.arxiv_entry(element, {"url": "https://export.arxiv.org/api/query?id_list=2404.07972", "retrieved_at": "2026-10-16T00:00:00Z", "sha256": "a" * 64})
    row.update(scope="relevance_pending", details={})
    return row


class IdentityTests(unittest.TestCase):
    def test_arxiv_versions_and_mirrors_share_identity(self):
        expected = ("arxiv:2404.07972", "https://arxiv.org/abs/2404.07972", "arxiv")
        for url in ["http://arxiv.org/pdf/2404.07972v3.pdf", "https://arxiv.org/html/2404.07972v2", "https://huggingface.co/papers/2404.07972"]:
            self.assertEqual(catalog.canonical(url), expected)

    def test_repository_case_and_paths_fold(self):
        for url in ["https://github.com/Xlang-AI/OSWorld.git", "https://github.com/xlang-ai/OSWorld/tree/main", "https://github.com/xlang-ai/OSWorld/blob/main/README.md"]:
            self.assertEqual(catalog.canonical(url)[0], "github:xlang-ai/osworld")

    def test_incidental_urls_are_not_resources(self):
        for url in ["https://github.com/topics/gui", "https://github.com/user-attachments/assets/123", "https://github.com/xlang-ai/OSWorld/issues/1", "https://img.shields.io/badge/test-blue", "javascript:alert(1)"]:
            self.assertIsNone(catalog.canonical(url))

    def test_host_spoof_does_not_become_arxiv(self):
        self.assertEqual(catalog.canonical("https://notarxiv.org/abs/2404.07972")[2], "url")

    def test_tracking_and_anchor_do_not_create_new_resource(self):
        self.assertEqual(catalog.canonical("https://example.org/item/?utm_source=test#intro"), catalog.canonical("https://example.org/item"))


class SourceTests(unittest.TestCase):
    def test_metadata_verification_does_not_imply_editorial_review(self):
        row = paper()
        self.assertEqual(row["review_status"], "metadata_verified")
        self.assertEqual(row["name"], "OSWorld: Benchmarking Multimodal Agents")
        self.assertIsNone(row["summary"])
        self.assertTrue(all(v is None for v in row["licenses"].values()))

    def test_api_error_entry_is_not_a_paper(self):
        entry = ET.fromstring('<entry xmlns="http://www.w3.org/2005/Atom"><id>http://arxiv.org/api/errors#bad</id><title>Error</title></entry>')
        self.assertIsNone(catalog.arxiv_entry(entry, {}))

    def test_failed_refresh_keeps_good_cache_but_reports_failure(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(catalog, "CACHE", Path(directory)):
            url = "https://example.org/source"
            key = hashlib.sha256(url.encode()).hexdigest()
            catalog.write_json(Path(directory) / f"{key}.json", {"ok": True, "url": url, "sha256": "a" * 64})
            (Path(directory) / f"{key}.body").write_bytes(b"old good snapshot")
            error = urllib.error.HTTPError(url, 429, "rate limited", {}, None)
            with mock.patch("urllib.request.urlopen", side_effect=error):
                info, body = catalog.fetch(url, refresh=True)
            self.assertFalse(info["ok"])
            self.assertEqual(body, b"")
            cached_info, cached_body = catalog.fetch(url)
            self.assertTrue(cached_info["ok"])
            self.assertEqual(cached_body, b"old good snapshot")

    def test_changed_source_cannot_keep_curated_status(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(build, "DATA", Path(directory)):
            row = {"name": "Example", "kind": "framework", "url": "https://example.org/", "environments": ["web"], "topics": [], "summary": "Example.", "editorial_reviewed": True, "reviewed_sha256": "a" * 64}
            catalog.write_json(Path(directory) / "editorial.json", [row])
            rid = catalog.canonical(row["url"])[0]
            ev = {"id": rid, "url": row["url"], "content_matched": True, "sha256": "b" * 64, "retrieved_at": "2026-10-16T00:00:00Z"}
            catalog.write_jsonl(Path(directory) / "primary-evidence.jsonl", [ev])
            rows, pending = build.source_records()
            self.assertEqual(rows, [])
            self.assertIn("snapshot", pending[0]["reason"])
            ev["sha256"] = "a" * 64
            catalog.write_jsonl(Path(directory) / "primary-evidence.jsonl", [ev])
            rows, pending = build.source_records()
            self.assertEqual(len(rows), 1)
            self.assertEqual(pending, [])

    def test_hub_card_licenses_are_scoped_and_require_a_metadata_declaration(self):
        cases = [
            ("dataset", "https://huggingface.co/datasets/example/data", "---\nlicense: cc-by-4.0\n---\nDataset card", {"data": "cc-by-4.0"}),
            ("model", "https://huggingface.co/example/model", "---\nlicense: apache-2.0\n---\nModel card", {"weights": "apache-2.0"}),
            ("framework", "https://huggingface.co/example/framework", "---\nlicense: mit\n---\nFramework", {}),
            ("dataset", "https://huggingface.co/datasets/example/prose", "# Card\nRelated code has license: MIT", {}),
        ]
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(catalog, "DATA", Path(directory)):
            rows, evidence, bodies = [], [], {}
            for kind, url, content, expected in cases:
                rid = catalog.canonical(url)[0]
                primary = url + "/raw/main/README.md"
                bodies[primary] = content.encode()
                rows.append({"url": url, "kind": kind})
                evidence.append({"id": rid, "url": primary, "content_matched": True, "sha256": hashlib.sha256(content.encode()).hexdigest(), "retrieved_at": "2026-10-16T00:00:00Z"})
            catalog.write_json(Path(directory) / "editorial.json", rows)
            catalog.write_jsonl(Path(directory) / "primary-evidence.jsonl", evidence)
            with mock.patch.object(catalog, "cached_body", side_effect=lambda url: bodies[url]), contextlib.redirect_stdout(io.StringIO()):
                catalog.enrich(types.SimpleNamespace(refresh=False))
            enriched = {r["id"]: r for r in catalog.read_jsonl(Path(directory) / "enrichment.jsonl")}
            for kind, url, content, expected in cases:
                result = enriched[catalog.canonical(url)[0]]
                self.assertEqual({scope: value["declared"] for scope, value in result["licenses"].items()}, expected)
                for receipt in result["evidence"]:
                    self.assertEqual(receipt["url"], url + "/raw/main/README.md")

    def test_supporting_source_change_revokes_primary_review_match(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(catalog, "DATA", Path(directory)):
            primary = "https://example.org/primary"
            supporting = "https://example.org/description"
            row = {"name": "Example", "url": primary, "additional_evidence": [{"url": supporting, "sha256": "b" * 64}]}
            catalog.write_json(Path(directory) / "editorial.json", [row])
            for support_digest, expected in [("b" * 64, True), ("c" * 64, False)]:
                def fake_fetch(url, refresh=False):
                    return {"url": url, "ok": True, "status": 200, "sha256": "a" * 64 if url == primary else support_digest}, b"Example"
                with mock.patch.object(catalog, "fetch", side_effect=fake_fetch), contextlib.redirect_stdout(io.StringIO()):
                    catalog.verify_editorial(types.SimpleNamespace(refresh=True))
                result = catalog.read_jsonl(Path(directory) / "primary-evidence.jsonl")[0]
                self.assertEqual(result["content_matched"], expected)
                if not expected:
                    self.assertIn("supporting source", result["error"])


class QualityTests(unittest.TestCase):
    def test_confirmed_duplicate_remains_provenance_not_an_extra_reviewed_work(self):
        original = paper()
        duplicate = copy.deepcopy(original)
        duplicate.update(id="arxiv:2505.13887", url="https://arxiv.org/abs/2505.13887")
        duplicate["identifiers"] = {"arxiv": "2505.13887", "preferred_arxiv": original["identifiers"]["arxiv"]}
        self.assertEqual(build.validate_records([original, duplicate]), [])
        duplicate.update(review_status="curated", scope="core", summary="A duplicate publication.")
        self.assertTrue(any("known duplicate" in e for e in build.validate_records([original, duplicate])))

    def test_duplicate_and_dangling_relationship_rejected(self):
        row = paper()
        row["relations"] = [{"type": "uses", "target_id": "missing", "evidence_url": row["url"]}]
        errors = build.validate_records([row, copy.deepcopy(row)])
        self.assertTrue(any("duplicate" in e for e in errors))
        self.assertTrue(any("dangling" in e for e in errors))

    def test_future_publication_and_unscoped_license_rejected(self):
        row = paper()
        row["published_at"] = "2099-01-01"
        row["licenses"] = {"code": "MIT"}
        errors = build.validate_records([row])
        self.assertTrue(any("after" in e for e in errors))
        self.assertTrue(any("license" in e for e in errors))

    def test_sqlite_preserves_json_and_search(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.sqlite"
            row = paper()
            build.write_sqlite([row], path)
            con = sqlite3.connect(path)
            self.assertEqual(con.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(con.execute("SELECT id FROM resource_search WHERE resource_search MATCH ?", ("OSWorld",)).fetchone()[0], row["id"])
            self.assertEqual(json.loads(con.execute("SELECT record_json FROM resources").fetchone()[0]), row)
            con.close()

    def test_published_schema_accepts_real_catalog(self):
        import jsonschema
        validator = jsonschema.Draft202012Validator(catalog.read_json(catalog.ROOT / "schemas/resource.schema.json"), format_checker=jsonschema.FormatChecker())
        rows = catalog.read_jsonl(catalog.DATA / "catalog.jsonl")
        self.assertGreater(len(rows), 0)
        for row in rows:
            self.assertEqual(list(validator.iter_errors(row)), [], row["id"])

    def test_committed_generated_views_are_reproducible(self):
        with contextlib.redirect_stdout(io.StringIO()):
            build.build(types.SimpleNamespace(check=True))


if __name__ == "__main__":
    unittest.main()
