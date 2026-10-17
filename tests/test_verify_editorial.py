"""Offline checks for which fetched page counts as an editorial entry's primary evidence."""
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


REPO = "https://github.com/Example/Repo"
RAW = "https://raw.githubusercontent.com/Example/Repo/HEAD/"
GITHUB_CHAIN = [RAW + "README.md", RAW + "README.MD", RAW + "readme.md", REPO]


def page(url, body, ok=True, status=200):
    return {"url": url, "final_url": url, "ok": ok, "status": status, "sha256": hashlib.sha256(body).hexdigest(), "retrieved_at": "2026-10-17T12:00:00Z"}, body


def missing(url, status=404):
    return page(url, b"", ok=False, status=status)


class VerifyEditorialTests(unittest.TestCase):
    def verify(self, row, responses):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(catalog, "DATA", Path(directory)):
            catalog.write_json(Path(directory) / "editorial.json", [row])

            def fake_fetch(url, refresh=False):
                self.assertIn(url, responses, "Unexpected request; fixtures never use the network")
                return responses[url]

            with mock.patch.object(catalog, "fetch", side_effect=fake_fetch) as fetch, contextlib.redirect_stdout(io.StringIO()):
                catalog.verify_editorial(types.SimpleNamespace(refresh=True))
            results = catalog.read_jsonl(Path(directory) / "primary-evidence.jsonl")
        self.assertEqual(len(results), 1)
        return results[0], [call.args[0] for call in fetch.call_args_list]

    def test_terms_match_regardless_of_case_and_whitespace(self):
        url = "https://example.org/tool"
        row = {"url": url, "name": "Example Tool", "verify_terms": ["GUI  Grounding Benchmark", "Absent Term"]}
        result, calls = self.verify(row, {url: page(url, b"<h1>gui\n  grounding\tBENCHMARK</h1>")})
        self.assertEqual(calls, [url])
        self.assertTrue(result["content_matched"])
        self.assertEqual(result["matched_terms"], ["GUI  Grounding Benchmark"])
        self.assertEqual((result["content_match_method"], result["attempts"], result["source_url"]), ("text_terms", 1, url))

    def test_name_is_the_default_term(self):
        url = "https://example.org/tool"
        for body, expected in [(b"<title>EXAMPLE\ntool</title>", True), (b"<title>Example</title>", False)]:
            with self.subTest(body=body):
                result, _ = self.verify({"url": url, "name": "Example Tool"}, {url: page(url, body)})
                self.assertEqual(result["content_matched"], expected)

    def test_challenge_pages_never_match_despite_the_term(self):
        url = "https://example.org/tool"
        for marker in ["Just a moment...", "Checking your browser before accessing", "Please verify you are human", "JUST A MOMENT..."]:
            with self.subTest(marker=marker):
                body = f"<title>{marker}</title><h1>Example Tool</h1>".encode()
                result, calls = self.verify({"url": url, "name": "Example Tool"}, {url: page(url, body)})
                self.assertEqual(calls, [url])
                self.assertFalse(result["content_matched"])
                self.assertEqual(result["status"], 200)

    def test_github_falls_back_through_readme_variants_and_records_the_matching_one(self):
        row = {"url": REPO, "name": "Example Repo"}
        result, calls = self.verify(row, {
            GITHUB_CHAIN[0]: missing(GITHUB_CHAIN[0]),
            GITHUB_CHAIN[1]: page(GITHUB_CHAIN[1], b"Unrelated readme"),
            GITHUB_CHAIN[2]: page(GITHUB_CHAIN[2], b"# Example Repo"),
        })
        self.assertEqual(calls, GITHUB_CHAIN[:3])
        self.assertTrue(result["content_matched"])
        self.assertEqual((result["id"], result["url"], result["source_url"], result["attempts"]), ("github:example/repo", GITHUB_CHAIN[2], REPO, 3))

    def test_github_repository_page_is_the_last_fallback(self):
        responses = {url: missing(url) for url in GITHUB_CHAIN[:3]}
        responses[REPO] = page(REPO, b"<strong>Example Repo</strong>")
        result, calls = self.verify({"url": REPO, "name": "Example Repo"}, responses)
        self.assertEqual(calls, GITHUB_CHAIN)
        self.assertTrue(result["content_matched"])
        self.assertEqual((result["url"], result["attempts"]), (REPO, 4))

    def test_explicit_evidence_urls_replace_the_default_chain(self):
        docs, paper = "https://example.org/docs", "https://example.org/paper"
        row = {"url": REPO, "name": "Example Repo", "evidence_urls": [docs, paper]}
        result, calls = self.verify(row, {docs: page(docs, b"Example Repo docs"), paper: page(paper, b"Example Repo paper")})
        self.assertEqual(calls, [docs])
        self.assertEqual((result["url"], result["source_url"], result["attempts"]), (docs, REPO, 1))

    def test_hugging_face_urls_are_read_through_the_hub_api(self):
        for url, api in [("https://huggingface.co/datasets/Example/Data", "https://huggingface.co/api/datasets/Example/Data"),
                ("https://huggingface.co/Example/Model-7B", "https://huggingface.co/api/models/Example/Model-7B"),
                ("https://huggingface.co/collections/Example/agents-123", "https://huggingface.co/collections/Example/agents-123")]:
            with self.subTest(url=url):
                result, calls = self.verify({"url": url, "name": "Example"}, {api: page(api, b'{"id": "Example"}')})
                self.assertEqual(calls, [api])
                self.assertTrue(result["content_matched"])
                self.assertEqual((result["url"], result["source_url"]), (api, url))

    def test_all_attempts_failing_reports_the_last_attempt(self):
        responses = {GITHUB_CHAIN[0]: missing(GITHUB_CHAIN[0]), GITHUB_CHAIN[1]: page(GITHUB_CHAIN[1], b"<title>Just a moment...</title>Example Repo"),
            GITHUB_CHAIN[2]: page(GITHUB_CHAIN[2], b"Unrelated readme"), REPO: missing(REPO, status=503)}
        result, calls = self.verify({"url": REPO, "name": "Example Repo"}, responses)
        self.assertEqual(calls, GITHUB_CHAIN)
        self.assertFalse(result["content_matched"])
        self.assertEqual((result["attempts"], result["url"], result["status"], result["ok"]), (4, REPO, 503, False))


if __name__ == "__main__":
    unittest.main()
