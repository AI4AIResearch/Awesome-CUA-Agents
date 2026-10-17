import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import backfill_arxiv_snapshots as backfill
import catalog
from arxiv_metadata import ATOM, ABSTRACT_HASH_METHOD


def entry(aid="2501.00001", version=2, title="A GUI paper", authors=("Ada Author", "Bo Author")):
    node = ET.Element(ATOM + "entry")
    for key, value in {
        "id": f"http://arxiv.org/abs/{aid}v{version}",
        "title": title,
        "published": "2025-01-01T12:34:56Z",
        "updated": "2025-02-03T23:45:01Z",
        "summary": " A retained\n  GUI abstract. ",
    }.items():
        ET.SubElement(node, ATOM + key).text = value
    for name in authors:
        ET.SubElement(ET.SubElement(node, ATOM + "author"), ATOM + "name").text = name
    return node


def feed(*entries):
    root = ET.Element(ATOM + "feed")
    root.extend(entries)
    return ET.tostring(root, encoding="utf-8")


def paper(aid, body, *, title="A GUI paper", url="https://export.arxiv.org/api/query?id_list=test"):
    return {
        "id": "arxiv:" + aid,
        "name": title,
        "authors": ["Ada Author", "Bo Author"],
        "published_at": "2025-01-01",
        "updated_at": "2025-02-03",
        "identifiers": {"arxiv": aid, "preferred_arxiv": "2401.12345"},
        "url": "https://arxiv.org/abs/" + aid,
        "kind": "paper",
        "notes": "Retain this duplicate-submission explanation exactly.",
        "review_status": "metadata_verified",
        "last_verified_at": "2025-02-05T01:02:03Z",
        "details": {"unrelated": {"items": [1, "keep", None]}},
        "evidence": [{
            "method": "arxiv_api", "role": "primary", "url": url,
            "sha256": hashlib.sha256(body).hexdigest(),
            "retrieved_at": "2025-02-05T01:02:03Z",
            "supports": ["name", "authors", "published_at", "updated_at", "identifiers.arxiv"],
            "original_extra": {"keep": True},
        }, {
            "method": "editorial_primary_review", "url": "https://example.org/note",
            "sha256": "b" * 64, "retrieved_at": "2025-02-04T00:00:00Z",
            "supports": ["identifiers.preferred_arxiv", "notes"],
        }],
    }


def write_archive(path, records):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8")
    return path.read_bytes()


class ArxivBackfillTests(unittest.TestCase):
    def setUp(self):
        self.network = mock.patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden"))
        self.network.start()
        self.addCleanup(self.network.stop)
        self.fetch = mock.patch.object(catalog, "fetch", side_effect=AssertionError("fetch forbidden"))
        self.fetch.start()
        self.addCleanup(self.fetch.stop)

    def test_only_snapshot_and_original_receipt_support_are_added(self):
        body = feed(entry(title=" A\n GUI paper ", authors=(" Ada  Author ", "Bo Author")))
        row = paper("2501.00001", body)
        original = copy.deepcopy(row)
        loader = mock.Mock(return_value=body)
        result = backfill.prepare_backfill([row], load_body=loader)
        expected = copy.deepcopy(original)
        expected["details"]["arxiv_snapshot"] = {
            "version": 2,
            "versioned_url": "https://arxiv.org/abs/2501.00001v2",
            "submitted_at": "2025-01-01T12:34:56Z",
            "updated_at": "2025-02-03T23:45:01Z",
            "abstract_sha256": hashlib.sha256(b"A retained GUI abstract.").hexdigest(),
            "abstract_hash_method": ABSTRACT_HASH_METHOD,
        }
        expected["evidence"][0]["supports"].append(backfill.SNAPSHOT_PATH)
        self.assertEqual(result.records, [expected])
        self.assertEqual(row, original)
        self.assertEqual(result.records[0]["identifiers"]["preferred_arxiv"], "2401.12345")
        loader.assert_called_once_with(row["evidence"][0]["url"])
        self.assertEqual((result.changed_records, result.snapshots_added, result.receipts_updated), (1, 1, 1))

    def test_same_feed_matches_each_id_and_is_parsed_once(self):
        body = feed(entry(), entry("2501.00002", version=7, title="Second paper"))
        rows = [paper("2501.00002", body, title="Second paper"), paper("2501.00001", body)]
        loader = mock.Mock(return_value=body)
        with mock.patch.object(backfill.ET, "fromstring", wraps=ET.fromstring) as parse:
            result = backfill.prepare_backfill(rows, load_body=loader)
        self.assertEqual([r["id"] for r in result.records], [r["id"] for r in rows])
        self.assertEqual([r["details"]["arxiv_snapshot"]["version"] for r in result.records], [7, 2])
        self.assertEqual(result.feeds_parsed, 1)
        loader.assert_called_once()
        parse.assert_called_once()

    def test_all_original_receipts_must_agree_and_only_their_supports_change(self):
        body = feed(entry())
        row = paper("2501.00001", body)
        another = copy.deepcopy(row["evidence"][0])
        another["url"] += "&source=second"
        another["retrieved_at"] = "2025-02-06T00:00:00Z"
        row["evidence"].append(another)
        result = backfill.prepare_backfill([row], load_body=lambda url: body)
        self.assertEqual(result.receipts_updated, 2)
        self.assertEqual(result.records[0]["evidence"][1], row["evidence"][1])
        self.assertEqual(result.records[0]["evidence"][2]["retrieved_at"], another["retrieved_at"])

    def test_missing_details_and_supports_can_be_added(self):
        body = feed(entry())
        row = paper("2501.00001", body)
        del row["details"]
        del row["evidence"][0]["supports"]
        result = backfill.prepare_backfill([row], load_body=lambda url: body)
        self.assertEqual(result.records[0]["evidence"][0]["supports"], [backfill.SNAPSHOT_PATH])
        self.assertIn("arxiv_snapshot", result.records[0]["details"])

    def test_default_cli_is_dry_run(self):
        body = feed(entry())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "papers.jsonl"
            original = write_archive(path, [paper("2501.00001", body)])
            output = io.StringIO()
            with mock.patch.object(catalog, "cached_body", return_value=body), contextlib.redirect_stdout(output):
                self.assertEqual(backfill.main(["--papers", str(path)]), 0)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(json.loads(output.getvalue())["mode"], "dry-run")
            self.assertFalse(json.loads(output.getvalue())["written"])

    def test_explicit_write_preserves_order_count_permissions_and_is_idempotent(self):
        body = feed(entry(), entry("2501.00002", version=7, title="Second paper"))
        rows = [paper("2501.00002", body, title="Second paper"), paper("2501.00001", body)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "papers.jsonl"
            write_archive(path, rows)
            path.chmod(0o640)
            with mock.patch.object(catalog, "cached_body", return_value=body), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(backfill.main(["--papers", str(path), "--write"]), 0)
            after = path.read_bytes()
            written = [json.loads(line) for line in after.splitlines()]
            self.assertEqual([r["id"] for r in written], [r["id"] for r in rows])
            self.assertEqual(len(written), 2)
            self.assertEqual(path.stat().st_mode & 0o777, 0o640)
            with mock.patch.object(backfill.os, "replace", side_effect=AssertionError("no second write")):
                second = backfill.backfill_file(path, write=True, load_body=lambda url: body)
            self.assertFalse(second.written)
            self.assertEqual(second.changed_records, 0)
            self.assertEqual(second.receipts_updated, 0)
            self.assertEqual(path.read_bytes(), after)

    def test_any_bad_record_blocks_whole_file_without_partial_write(self):
        good_body = feed(entry())
        other_body = feed(entry("2501.00002"))
        cases = ["missing_cache", "hash", "xml", "entry_id", "name", "authors",
                 "published_at", "updated_at", "identifier", "no_receipt"]
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                good = paper("2501.00001", good_body, url="https://export.arxiv.org/api/query?good")
                bad = paper("2501.00002", other_body, url="https://export.arxiv.org/api/query?bad")
                loaded = other_body
                if case == "missing_cache":
                    loaded = b""
                elif case == "hash":
                    bad["evidence"][0]["sha256"] = "0" * 64
                elif case == "xml":
                    loaded = b"<broken"
                    bad["evidence"][0]["sha256"] = hashlib.sha256(loaded).hexdigest()
                elif case == "entry_id":
                    loaded = good_body
                    bad["evidence"][0]["sha256"] = hashlib.sha256(loaded).hexdigest()
                elif case == "authors":
                    bad["authors"].reverse()
                elif case in ["name", "published_at", "updated_at"]:
                    bad[case] = "different retained fact"
                elif case == "identifier":
                    bad["identifiers"]["arxiv"] = "9999.99999"
                elif case == "no_receipt":
                    bad["evidence"] = bad["evidence"][1:]
                path = Path(directory) / "papers.jsonl"
                original = write_archive(path, [good, bad])
                def loader(url):
                    return good_body if url.endswith("?good") else loaded
                with self.assertRaises(backfill.BackfillError):
                    backfill.backfill_file(path, write=True, load_body=loader)
                self.assertEqual(path.read_bytes(), original)
                self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_existing_conflicting_snapshot_is_not_overwritten(self):
        body = feed(entry())
        row = backfill.prepare_backfill([paper("2501.00001", body)], load_body=lambda url: body).records[0]
        row["details"]["arxiv_snapshot"]["abstract_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "papers.jsonl"
            original = write_archive(path, [row])
            with self.assertRaisesRegex(backfill.BackfillError, "refusing to overwrite"):
                backfill.backfill_file(path, write=True, load_body=lambda url: body)
            self.assertEqual(path.read_bytes(), original)

    def test_existing_snapshot_still_requires_original_evidence(self):
        body = feed(entry())
        row = backfill.prepare_backfill([paper("2501.00001", body)], load_body=lambda url: body).records[0]
        with self.assertRaisesRegex(backfill.BackfillError, "missing"):
            backfill.prepare_backfill([row], load_body=lambda url: b"")

    def test_cache_key_includes_receipt_hash(self):
        body = feed(entry(), entry("2501.00002"))
        rows = [paper("2501.00001", body), paper("2501.00002", body)]
        rows[1]["evidence"][0]["sha256"] = "0" * 64
        loader = mock.Mock(return_value=body)
        with self.assertRaisesRegex(backfill.BackfillError, "SHA-256"):
            backfill.prepare_backfill(rows, load_body=loader)
        self.assertEqual(loader.call_count, 2)

    def test_conflicting_original_receipts_and_duplicate_entries_are_rejected(self):
        first = feed(entry())
        later = feed(entry(version=3))
        row = paper("2501.00001", first)
        extra = copy.deepcopy(row["evidence"][0])
        extra.update(url="https://export.arxiv.org/api/query?later", sha256=hashlib.sha256(later).hexdigest())
        row["evidence"].append(extra)
        with self.assertRaisesRegex(backfill.BackfillError, "receipts disagree"):
            backfill.prepare_backfill([row], load_body=lambda url: later if url.endswith("?later") else first)
        ambiguous = feed(entry(), entry(version=3))
        with self.assertRaisesRegex(backfill.BackfillError, "2 matching entries"):
            backfill.prepare_backfill([paper("2501.00001", ambiguous)], load_body=lambda url: ambiguous)

    def test_incomplete_snapshot_is_rejected(self):
        for field in ["summary", "published", "updated", "id"]:
            with self.subTest(field=field):
                node = entry()
                node.find(ATOM + field).text = "" if field != "id" else "http://arxiv.org/abs/2501.00001"
                body = feed(node)
                with self.assertRaises(backfill.BackfillError):
                    backfill.prepare_backfill([paper("2501.00001", body)], load_body=lambda url: body)

    def test_source_changed_during_validation_is_not_overwritten(self):
        body = feed(entry())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "papers.jsonl"
            write_archive(path, [paper("2501.00001", body)])
            changed = b"concurrent edit\n"
            def loader(url):
                path.write_bytes(changed)
                return body
            with self.assertRaisesRegex(backfill.BackfillError, "changed during validation"):
                backfill.backfill_file(path, write=True, load_body=loader)
            self.assertEqual(path.read_bytes(), changed)
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_replace_failure_leaves_original_and_cleans_temporary(self):
        body = feed(entry())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "papers.jsonl"
            original = write_archive(path, [paper("2501.00001", body)])
            with mock.patch.object(backfill.os, "replace", side_effect=OSError("replace failed")):
                with self.assertRaisesRegex(OSError, "replace failed"):
                    backfill.backfill_file(path, write=True, load_body=lambda url: body)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_cli_failure_returns_nonzero_and_preserves_input(self):
        body = feed(entry())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "papers.jsonl"
            original = write_archive(path, [paper("2501.00001", body)])
            errors = io.StringIO()
            with mock.patch.object(catalog, "cached_body", return_value=b""), contextlib.redirect_stderr(errors):
                self.assertEqual(backfill.main(["--papers", str(path), "--write"]), 1)
            self.assertIn("missing", errors.getvalue())
            self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
