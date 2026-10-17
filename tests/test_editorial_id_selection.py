"""Offline checks that `verify --id` and `enrich --id` touch only the named editorial entries."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog


A, B = "https://example.org/alpha", "https://example.org/beta"
REPO = "https://github.com/example/repo"
README = "https://raw.githubusercontent.com/example/repo/HEAD/README.md"
TOOL = "component:example/repo/tool"


def sha(body):
    return hashlib.sha256(body).hexdigest()


def page(url, body):
    return {"url": url, "final_url": url, "ok": True, "status": 200, "sha256": sha(body), "retrieved_at": "2026-10-17T12:00:00Z"}, body


def receipt(rid, url, body, retrieved_at="2026-01-01T00:00:00Z"):
    return {"id": rid, "source_url": url, "url": url, "final_url": url, "ok": True, "status": 200, "sha256": sha(body),
            "retrieved_at": retrieved_at, "content_matched": True, "matched_terms": ["Alpha"], "content_match_method": "text_terms", "attempts": 1}


class EditorialIdSelectionTests(unittest.TestCase):
    def setUp(self):
        directory = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(mock.patch.object(catalog, "DATA", directory / "data"))
        self.enterContext(mock.patch.object(catalog, "CACHE", directory / "cache"))
        self.alpha, self.beta = catalog.canonical(A)[0], catalog.canonical(B)[0]
        catalog.write_json(catalog.DATA / "editorial.json", [
            {"url": A, "name": "Alpha", "kind": "framework"},
            {"url": B, "name": "Beta", "kind": "framework"},
            {"id": TOOL, "url": REPO, "name": "Tool", "kind": "tool"},
        ])
        self.old = {rid: f"{rid} cites https://arxiv.org/abs/2404.07972".encode() for rid in (self.alpha, self.beta, TOOL)}
        catalog.write_jsonl(catalog.DATA / "primary-evidence.jsonl", [receipt(self.alpha, A, self.old[self.alpha]), receipt(self.beta, B, self.old[self.beta]),
            receipt(TOOL, README, self.old[TOOL]), receipt("url:orphan", "https://example.org/gone", b"gone")])

    def lines(self, name):
        return {json.loads(line)["id"]: line for line in (catalog.DATA / name).read_bytes().splitlines()}

    def run_cli(self, argv, responses=None, bodies=None):
        fetched = []

        def fake_fetch(url, refresh=False):
            fetched.append(url)
            self.assertIn(url, responses or {}, "Unexpected request; fixtures never use the network")
            return responses[url]

        with mock.patch.object(catalog, "fetch", side_effect=fake_fetch), \
                mock.patch.object(catalog, "cached_body", side_effect=lambda url: (bodies or {}).get(url, b"")), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            catalog.main(argv)
        return fetched, out.getvalue()

    def test_verify_fetches_and_rewrites_only_the_named_entry(self):
        before = self.lines("primary-evidence.jsonl")
        body = b"<h1>Alpha</h1>"
        fetched, out = self.run_cli(["verify", "--id", self.alpha], {A: page(A, body)})
        self.assertEqual(fetched, [A])
        self.assertEqual(out.split(), ["MATCH", self.alpha, "200"])
        after = self.lines("primary-evidence.jsonl")
        self.assertEqual(sorted(after), sorted(before))
        self.assertEqual((json.loads(after[self.alpha])["retrieved_at"], json.loads(after[self.alpha])["sha256"]), ("2026-10-17T12:00:00Z", sha(body)))
        self.assertEqual({rid: line for rid, line in after.items() if rid != self.alpha}, {rid: line for rid, line in before.items() if rid != self.alpha})

    def test_verify_id_is_repeatable_and_uses_an_explicit_entry_id(self):
        before = self.lines("primary-evidence.jsonl")
        fetched, _ = self.run_cli(["verify", "--id", TOOL, "--id", self.beta], {B: page(B, b"Beta"), README: page(README, b"# Tool")})
        self.assertEqual(sorted(fetched), sorted([B, README]))
        after = self.lines("primary-evidence.jsonl")
        self.assertEqual(after[self.alpha], before[self.alpha])
        self.assertEqual(after["url:orphan"], before["url:orphan"])
        self.assertNotEqual(after[TOOL], before[TOOL])
        self.assertNotEqual(after[self.beta], before[self.beta])

    def test_enrich_updates_only_the_named_entry(self):
        catalog.write_jsonl(catalog.DATA / "enrichment.jsonl", [{"id": rid, "evidence_sha256": sha(body), "licenses": {}, "details": {}, "references": [], "evidence": []}
            for rid, body in self.old.items()])
        before = self.lines("enrichment.jsonl")
        # Every body is cached and cites a paper: enriching beta or the tool would add a reference, and the tool would request its LICENSE.
        fetched, out = self.run_cli(["enrich", "--id", self.alpha], bodies={A: self.old[self.alpha], B: self.old[self.beta], README: self.old[TOOL]})
        self.assertEqual(fetched, [])
        self.assertIn("0 skipped", out)
        after = self.lines("enrichment.jsonl")
        self.assertEqual(sorted(after), sorted(before))
        self.assertEqual([r["target_id"] for r in json.loads(after[self.alpha])["references"]], ["arxiv:2404.07972"])
        self.assertEqual({rid: line for rid, line in after.items() if rid != self.alpha}, {rid: line for rid, line in before.items() if rid != self.alpha})

    def test_unknown_ids_fail_before_any_request_or_write(self):
        for command in ("verify", "enrich"):
            for ids in (["url:missing"], [self.alpha, "url:missing", "github:example/repo"]):
                with self.subTest(command=command, ids=ids):
                    before = {name: (catalog.DATA / name).read_bytes() if (catalog.DATA / name).exists() else None for name in ("primary-evidence.jsonl", "enrichment.jsonl")}
                    argv = [command] + [arg for rid in ids for arg in ("--id", rid)]
                    with self.assertRaises(SystemExit) as raised:
                        self.run_cli(argv)
                    message = str(raised.exception.code)
                    self.assertIn("UNKNOWN url:missing", message)
                    # An entry with an explicit id is keyed by it, not by its URL's identity.
                    self.assertEqual("UNKNOWN github:example/repo" in message, "github:example/repo" in ids)
                    self.assertNotIn(self.alpha, message)
                    self.assertEqual({name: (catalog.DATA / name).read_bytes() if (catalog.DATA / name).exists() else None for name in before}, before)


if __name__ == "__main__":
    unittest.main()
