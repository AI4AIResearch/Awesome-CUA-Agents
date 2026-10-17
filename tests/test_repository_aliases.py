import contextlib
import io
import json
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build
import catalog
from catalog import read_jsonl

OLD, NEW = "https://github.com/deepmind/android_env", "https://github.com/google-deepmind/android_env"


def record(url, **fields):
    return {"id": "github:" + url.split("github.com/", 1)[1].lower(), "url": url, "name": "AndroidEnv", "kind": "infrastructure", "review_status": "curated",
        "environments": ["android"], "summary": "Android device control.", "aliases": [], "authors": [], "topics": [], "identifiers": {}, "evidence": [],
        "licenses": dict.fromkeys(("code", "data", "weights", "document")), **fields}


def alias_errors(rows):
    return [error for error in build.validate_records(rows) if "alias" in error]


class RepositoryAliasTests(unittest.TestCase):
    def test_alias_cannot_hide_a_second_active_record(self):
        errors = alias_errors([record(NEW, aliases=[OLD]), record(OLD)])
        self.assertEqual(errors, [f"github:google-deepmind/android_env: alias {OLD} is the active record github:deepmind/android_env; keep one record"])

    def test_two_records_cannot_claim_one_former_address(self):
        errors = alias_errors([record(NEW, aliases=[OLD]), record("https://github.com/example/android_env", aliases=[OLD + "/"])])
        self.assertEqual(errors, [f"github:example/android_env: alias {OLD}/ already resolves to github:google-deepmind/android_env"])

    def test_the_former_address_resolves_through_the_repository_alias_registry(self):
        rows = read_jsonl(ROOT / "data" / "catalog.jsonl")
        self.assertEqual(build.source_aliases(rows)["github:deepmind/android_env"], "github:google-deepmind/android_env")
        args = types.SimpleNamespace(query=OLD + "/tree/main", kind=None, status=None, environment=None, topic=None, limit=0, json=True)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            build.search(args)
        self.assertEqual([row["id"] for row in json.loads(out.getvalue())["records"]], ["github:google-deepmind/android_env"])
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(catalog.main(["get", "github:deepmind/android_env", "--json"]), 0)
        self.assertEqual(json.loads(out.getvalue())["id"], "github:google-deepmind/android_env")

    def test_android_env_is_one_record_under_its_current_owner(self):
        rows = read_jsonl(ROOT / "data" / "catalog.jsonl")
        matches = [row for row in rows if row["name"] == "AndroidEnv"]
        self.assertEqual([row["id"] for row in matches], ["github:google-deepmind/android_env"])
        self.assertIn(OLD, matches[0]["aliases"])
        self.assertEqual({e["url"] for e in matches[0]["evidence"] if e["method"] == "github_repository_identity"},
                         {"https://api.github.com/repos/deepmind/android_env", "https://api.github.com/repos/google-deepmind/android_env"})
        self.assertIn("deepmind/android_env", matches[0]["notes"])
        queued = {row["id"] for row in read_jsonl(ROOT / "data" / "review-queue.jsonl")}
        self.assertNotIn("github:deepmind/android_env", queued)


if __name__ == "__main__":
    unittest.main()
