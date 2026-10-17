"""Previously reviewed PDFs retain approval only for the exact reviewed bytes."""
import contextlib
import copy
import hashlib
import io
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import catalog


PRIMARY = 'https://example.org/paper.pdf'
SUPPORT_A = 'https://example.org/publication'
SUPPORT_B = 'https://example.org/project'
# Compressed/non-UTF-8-looking bytes intentionally contain no verification term.
# The verifier checks a previously reviewed byte fingerprint, not PDF syntax.
PDF = b'%PDF-1.7\n%\xff\xfe\x00\x81\n1 0 obj\nstream\n\x9c\x00\xff\nendstream\n%%EOF\n'


def digest(body):
    return hashlib.sha256(body).hexdigest()


def receipt(url, body, **updates):
    return {'url': url, 'final_url': url, 'ok': True, 'status': 200,
            'sha256': digest(body), 'retrieved_at': '2026-10-17T12:00:00Z', **updates}


def reviewed_row():
    return {'url': 'https://example.org/paper', 'name': 'Reviewed GUI Paper',
            'verify_terms': ['Reviewed GUI Paper'], 'evidence_urls': [PRIMARY],
            'editorial_reviewed': True, 'reviewed_sha256': digest(PDF)}


class PdfEvidenceTests(unittest.TestCase):
    def verify(self, row, responses, previous=None):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(catalog, 'DATA', Path(directory)):
            catalog.write_json(Path(directory) / 'editorial.json', [row])
            if previous:
                catalog.write_jsonl(Path(directory) / 'primary-evidence.jsonl', [previous])

            def fake_fetch(url, refresh=False):
                self.assertTrue(refresh)
                self.assertIn(url, responses, 'Unexpected request; fixtures never use the network')
                return copy.deepcopy(responses[url])

            with mock.patch.object(catalog, 'fetch', side_effect=fake_fetch) as fetch, \
                    contextlib.redirect_stdout(io.StringIO()):
                catalog.verify_editorial(types.SimpleNamespace(refresh=True))
            results = catalog.read_jsonl(Path(directory) / 'primary-evidence.jsonl')
            self.assertEqual(len(results), 1)
            return results[0], fetch.call_args_list

    def test_unchanged_reviewed_binary_pdf_matches_without_decoded_title(self):
        result, calls = self.verify(reviewed_row(), {
            PRIMARY: (receipt(PRIMARY, PDF, content_type='application/octet-stream'), PDF)})
        self.assertTrue(result['content_matched'])
        self.assertEqual(result['content_match_method'], 'reviewed_pdf_sha256')
        self.assertEqual(result['matched_terms'], [])
        self.assertEqual(result['sha256'], digest(PDF))
        self.assertEqual(result['url'], PRIMARY)
        self.assertEqual(result['retrieved_at'], '2026-10-17T12:00:00Z')
        self.assertEqual(len(calls), 1)

    def test_new_or_unreviewed_pdf_cannot_match_even_with_plaintext_title(self):
        body = PDF + b'Reviewed GUI Paper'
        for changes in [{'editorial_reviewed': False}, {'editorial_reviewed': 'true'},
                        {'editorial_reviewed': None}, {'reviewed_sha256': None}]:
            with self.subTest(changes=changes):
                row = reviewed_row()
                row['reviewed_sha256'] = digest(body)
                row.update(changes)
                result, _ = self.verify(row, {PRIMARY: (receipt(PRIMARY, body), body)})
                self.assertFalse(result['content_matched'])

    def test_changed_pdf_requires_review_despite_embedded_title(self):
        changed = PDF + b'\nReviewed GUI Paper\nchanged experimental content'
        result, _ = self.verify(reviewed_row(), {PRIMARY: (receipt(PRIMARY, changed), changed)})
        self.assertFalse(result['content_matched'])
        self.assertEqual(result['sha256'], digest(changed))

    def test_receipt_digest_cannot_approve_different_pdf_body(self):
        # A corrupted cache/body must not inherit approval from stale metadata.
        changed = PDF + b'changed'
        result, _ = self.verify(reviewed_row(), {PRIMARY: (receipt(PRIMARY, PDF), changed)})
        self.assertFalse(result['content_matched'])

    def test_html_challenge_at_pdf_url_does_not_use_fingerprint_approval(self):
        challenge = b'<html><h1>Reviewed GUI Paper</h1>Checking your browser</html>'
        row = reviewed_row()
        row['reviewed_sha256'] = digest(challenge)
        result, _ = self.verify(row, {
            PRIMARY: (receipt(PRIMARY, challenge, content_type='application/pdf'), challenge)})
        self.assertFalse(result['content_matched'])

    def test_non_pdf_matching_digest_does_not_replace_text_verification(self):
        body = b'<html>Unrelated landing page</html>'
        row = reviewed_row()
        row['reviewed_sha256'] = digest(body)
        result, _ = self.verify(row, {PRIMARY: (receipt(PRIMARY, body), body)})
        self.assertFalse(result['content_matched'])
        text = b'<html>Reviewed GUI Paper</html>'
        result, _ = self.verify(row, {PRIMARY: (receipt(PRIMARY, text), text)})
        self.assertTrue(result['content_matched'])
        self.assertEqual(result['content_match_method'], 'text_terms')
        self.assertEqual(result['matched_terms'], ['Reviewed GUI Paper'])

    def test_all_required_supporting_sources_still_gate_pdf_match(self):
        a, b = b'publication metadata', b'project description'
        row = reviewed_row()
        row['additional_evidence'] = [
            {'url': SUPPORT_A, 'sha256': digest(a)},
            {'url': SUPPORT_B, 'sha256': digest(b)},
        ]
        for state in ['unchanged', 'changed', 'unavailable']:
            with self.subTest(state=state):
                supporting_body = b if state != 'changed' else b'new project description'
                supporting_info = receipt(SUPPORT_B, supporting_body)
                if state == 'unavailable':
                    supporting_info.update(ok=False, status=503)
                result, calls = self.verify(row, {
                    PRIMARY: (receipt(PRIMARY, PDF), PDF),
                    SUPPORT_A: (receipt(SUPPORT_A, a), a),
                    SUPPORT_B: (supporting_info, supporting_body),
                })
                self.assertEqual([call.args[0] for call in calls], [PRIMARY, SUPPORT_A, SUPPORT_B])
                self.assertEqual(result['content_matched'], state == 'unchanged')
                self.assertEqual(result['content_match_method'], 'reviewed_pdf_sha256')
                if state != 'unchanged':
                    self.assertIn('supporting source unavailable or changed', result['error'])

    def test_failed_fetch_cannot_preserve_previous_pdf_match(self):
        row = reviewed_row()
        rid = catalog.canonical(row['url'])[0]
        previous = {'id': rid, **receipt(PRIMARY, PDF), 'content_matched': True}
        result, _ = self.verify(row, {
            PRIMARY: (receipt(PRIMARY, PDF, ok=False, status=503), PDF)}, previous)
        self.assertFalse(result['content_matched'])
        self.assertEqual(result['status'], 503)


if __name__ == '__main__':
    unittest.main()
