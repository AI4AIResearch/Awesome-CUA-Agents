import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build
from catalog import read_jsonl, write_json, write_jsonl

OLD, NEW = "https://github.com/deepmind/android_env", "https://github.com/google-deepmind/android_env"


def record(url, **fields):
    return {"id": "github:" + url.split("github.com/", 1)[1].lower(), "url": url, "name": "AndroidEnv", "kind": "infrastructure", "review_status": "curated",
        "environments": ["android"], "summary": "Android device control.", "aliases": [], "authors": [], "topics": [], "identifiers": {}, "evidence": [],
        "licenses": dict.fromkeys(("code", "data", "weights", "document")), **fields}


def alias_errors(rows):
    return [error for error in build.validate_records(rows) if "alias" in error]


class RepositoryAliasTests(unittest.TestCase):
    def test_only_alias_urls_name_another_identity(self):
        survivor = record(NEW, aliases=["Android Env", OLD, NEW + "/tree/main"])
        self.assertEqual(build.identity_aliases([survivor]), {"github:deepmind/android_env": "github:google-deepmind/android_env"})
        self.assertEqual(alias_errors([survivor]), [])

    def test_alias_cannot_hide_a_second_active_record(self):
        errors = alias_errors([record(NEW, aliases=[OLD]), record(OLD)])
        self.assertEqual(errors, [f"github:google-deepmind/android_env: alias {OLD} is the active record github:deepmind/android_env; keep one record"])

    def test_two_records_cannot_claim_one_former_address(self):
        errors = alias_errors([record(NEW, aliases=[OLD]), record("https://github.com/example/android_env", aliases=[OLD + "/"])])
        self.assertEqual(errors, [f"github:example/android_env: alias {OLD}/ already resolves to github:google-deepmind/android_env"])

    def test_discovery_and_search_resolve_the_former_address(self):
        survivor = record(NEW, aliases=[OLD])
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            write_jsonl(data / "catalog.jsonl", [survivor])
            write_jsonl(data / "publications.jsonl", [])
            write_jsonl(data / "papers.jsonl", [])
            write_jsonl(data / "candidates.jsonl", [{"id": "github:deepmind/android_env", "discovered_in": [{"source_id": "fixture"}]}])
            write_json(data / "sources.json", [{"id": "fixture", "name": "Fixture", "homepage": "https://example.org"}])
            with mock.patch.object(build, "DATA", data):
                report = build.coverage([survivor], [], [])
                args = types.SimpleNamespace(query=OLD + "/tree/main", kind=None, status=None, environment=None, topic=None, limit=0, json=True)
                with contextlib.redirect_stdout(io.StringIO()) as out:
                    build.search(args)
        source = report["sources"][0]
        self.assertEqual((source["indexed"], source["indexed_resources"], source["resolved_aliases"], source["unindexed"]), (1, 1, 1, 0))
        self.assertEqual(report["unindexed_candidates"], 0)
        self.assertEqual([row["id"] for row in json.loads(out.getvalue())["records"]], [survivor["id"]])

    def test_android_env_is_one_record_under_its_current_owner(self):
        rows = read_jsonl(ROOT / "data" / "catalog.jsonl")
        matches = [row for row in rows if row["name"] == "AndroidEnv"]
        self.assertEqual([row["id"] for row in matches], ["github:google-deepmind/android_env"])
        self.assertIn(OLD, matches[0]["aliases"])
        self.assertIn("deepmind/android_env", matches[0]["notes"])
        queued = {row["id"] for row in read_jsonl(ROOT / "data" / "review-queue.jsonl")}
        self.assertNotIn("github:deepmind/android_env", queued)


if __name__ == "__main__":
    unittest.main()
