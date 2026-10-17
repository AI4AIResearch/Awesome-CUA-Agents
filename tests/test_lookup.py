import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build
import catalog
import lookup


class LookupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Real materialized records exercise version metadata, scoped licenses and nested receipts.
        rows = [json.loads(line) for line in (ROOT / 'data/catalog.jsonl').read_text().splitlines()]
        by_id = {row['id']: row for row in rows}
        cls.repo = by_id['github:bytedance/ui-tars']
        cls.paper = by_id['arxiv:2501.12326']
        cls.model = by_id['url:4d32ad3682ae2d71c178']
        cls.metadata = next(row for row in rows if row['review_status'] == 'metadata_verified')
        cls.excluded = next(d for d in json.loads((ROOT / 'data/exclusion-status.json').read_text())['decisions']
                            if d['status'] == 'excluded')

    def setUp(self):
        self.records = copy.deepcopy([self.repo, self.paper, self.model, self.metadata])
        self.decisions = copy.deepcopy([self.excluded])

    def cli(self, resource_id, *, related=False, as_json=True, records=None, decisions=None):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            rows = self.records if records is None else records
            ledger = self.decisions if decisions is None else decisions
            (data / 'catalog.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
            (data / 'exclusion-status.json').write_text(json.dumps({'schema_version': 1, 'decisions': ledger}))
            # Deliberately unusable reference data proves lookup never opens or promotes mentions.
            (data / 'references.jsonl').write_text('This is not a reviewed-relations input.\n')
            argv = ['get', resource_id]
            if related:
                argv.append('--related')
            if as_json:
                argv.append('--json')
            output = io.StringIO()
            with mock.patch.object(lookup, 'DATA', data), contextlib.redirect_stdout(output):
                code = catalog.main(argv)
            return code, json.loads(output.getvalue()) if as_json else output.getvalue()

    def test_exact_id_json_returns_the_whole_original_record(self):
        before = copy.deepcopy(self.records)
        code, result = self.cli(self.paper['id'])
        self.assertEqual(code, lookup.EXIT_OK)
        self.assertEqual(result, self.paper)
        self.assertNotIn('record', result)
        self.assertEqual(result['details']['arxiv_snapshot'], self.paper['details']['arxiv_snapshot'])
        self.assertEqual(self.records, before)

    def test_metadata_record_remains_unreviewed_with_nulls_and_all_evidence(self):
        code, result = self.cli(self.metadata['id'])
        self.assertEqual(code, 0)
        self.assertEqual(result, self.metadata)
        self.assertEqual(result['review_status'], 'metadata_verified')
        self.assertEqual(result['scope'], 'relevance_pending')
        self.assertIsNone(result['summary'])
        self.assertEqual(result['licenses'], self.metadata['licenses'])

    def test_unknown_titles_urls_partial_and_case_changed_ids_are_not_searches(self):
        for value in ['UI-TARS', self.repo['url'], 'github:bytedance', self.repo['id'].upper(), self.paper['id'] + 'v2']:
            with self.subTest(value=value):
                code, result = self.cli(value)
                self.assertEqual(code, lookup.EXIT_NOT_FOUND)
                self.assertEqual(result['status'], 'not_found')
                self.assertEqual(result['id'], value)
                self.assertNotIn('record', result)

    def test_injection_strings_are_literal_ids_and_cannot_create_files(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'must-not-exist'
            for value in ["' OR 1=1 --", f'$(touch {marker})', '<script>alert(1)</script>', '../../data/catalog.jsonl']:
                with self.subTest(value=value):
                    code, result = self.cli(value, related=True)
                    self.assertEqual(code, lookup.EXIT_NOT_FOUND)
                    self.assertEqual(result['id'], value)
                    self.assertFalse(marker.exists())

    def test_applied_exclusion_reports_reason_receipt_and_ledger_with_nonzero_exit(self):
        code, result = self.cli(self.excluded['id'], related=True)
        self.assertEqual(code, lookup.EXIT_EXCLUDED)
        self.assertEqual(result['status'], 'excluded')
        self.assertEqual(result['reason'], self.excluded['reason'])
        self.assertEqual(result['decision'], self.excluded)
        self.assertEqual(result['ledger_url'], lookup.EXCLUSION_LEDGER_URL)
        self.assertNotIn('record', result)
        self.assertNotIn('related', result)

    def test_pending_exclusion_does_not_hide_an_active_record_or_claim_exclusion(self):
        pending = {**self.excluded, 'id': self.metadata['id'], 'status': 'revalidation_pending'}
        code, result = self.cli(self.metadata['id'], decisions=[pending])
        self.assertEqual((code, result), (0, self.metadata))
        pending['id'] = 'arxiv:0000.00000'
        code, result = self.cli(pending['id'], decisions=[pending])
        self.assertEqual(code, lookup.EXIT_NOT_FOUND)
        self.assertEqual(result['status'], 'not_found')

    def test_related_records_are_bidirectional_and_preserve_edge_meaning_and_evidence(self):
        code, result = self.cli(self.repo['id'], related=True)
        self.assertEqual(code, 0)
        self.assertEqual(result['status'], 'active')
        self.assertEqual(result['record'], self.repo)
        edges = result['related']
        self.assertEqual(len(edges), 2)
        outgoing = next(e for e in edges if e['direction'] == 'outgoing')
        incoming = next(e for e in edges if e['direction'] == 'incoming')
        self.assertEqual((outgoing['source_id'], outgoing['target_id'], outgoing['type']),
                         (self.repo['id'], self.paper['id'], 'documented_by'))
        self.assertEqual((incoming['source_id'], incoming['target_id'], incoming['type']),
                         (self.model['id'], self.repo['id'], 'variant_of'))
        self.assertEqual(outgoing['resource'], self.paper)
        self.assertEqual(incoming['resource'], self.model)
        for edge, owner in [(outgoing, self.repo), (incoming, self.model)]:
            self.assertEqual(edge['evidence'], [r for r in owner['evidence']
                                              if r['url'] == edge['evidence_url']
                                              and r['role'] == 'primary' and 'relations' in r['supports']])

    def test_mentions_and_metadata_owned_edges_are_not_reviewed_relations(self):
        repo, paper, model, metadata = self.records
        repo['relations'].append({**repo['relations'][0], 'type': 'mentions'})
        metadata['relations'] = [{'type': 'uses', 'target_id': repo['id'], 'evidence_url': metadata['evidence'][0]['url']}]
        code, result = self.cli(repo['id'], related=True)
        self.assertEqual(code, 0)
        self.assertEqual({e['type'] for e in result['related']}, {'documented_by', 'variant_of'})
        self.assertEqual(len(result['related']), 2)

    def test_related_metadata_endpoint_is_not_promoted_to_curated(self):
        self.records[1].update(review_status='metadata_verified', scope='relevance_pending', summary=None)
        code, result = self.cli(self.repo['id'], related=True)
        self.assertEqual(code, 0)
        target = next(e['resource'] for e in result['related'] if e['direction'] == 'outgoing')
        self.assertEqual(target, self.records[1])
        self.assertIsNone(target['summary'])

    def test_active_excluded_overlap_and_duplicate_ids_report_data_errors(self):
        bad_decision = {**self.excluded, 'id': self.repo['id']}
        for rows, decisions in [(self.records, [bad_decision]), (self.records + [self.records[0]], [])]:
            with self.subTest(decisions=bool(decisions)):
                code, result = self.cli(self.repo['id'], records=rows, decisions=decisions)
                self.assertEqual(code, lookup.EXIT_DATA_ERROR)
                self.assertEqual(result['status'], 'data_error')
                self.assertNotIn('record', result)

    def test_related_missing_target_or_primary_receipt_is_not_silently_accepted(self):
        for broken in ['target', 'receipt']:
            rows = copy.deepcopy(self.records)
            relation = rows[0]['relations'][0]
            relation['target_id' if broken == 'target' else 'evidence_url'] = 'not-retained'
            code, result = self.cli(self.repo['id'], related=True, records=rows)
            self.assertEqual(code, lookup.EXIT_DATA_ERROR)
            self.assertEqual(result['status'], 'data_error')

    def test_missing_materialization_is_a_data_error_not_an_unknown_id(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(lookup, 'DATA', Path(directory)):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = catalog.main(['get', self.repo['id'], '--json'])
            self.assertEqual(code, lookup.EXIT_DATA_ERROR)
            self.assertEqual(json.loads(output.getvalue())['status'], 'data_error')

    def test_malformed_related_containers_return_structured_data_errors(self):
        for field, value in [('relations', [None]), ('relations', {}), ('evidence', [None])]:
            with self.subTest(field=field, value=value):
                rows = copy.deepcopy(self.records)
                rows[0][field] = value
                code, result = self.cli(self.repo['id'], related=True, records=rows)
                self.assertEqual(code, lookup.EXIT_DATA_ERROR)
                self.assertEqual(result['status'], 'data_error')

    def test_text_errors_escape_terminal_controls_and_show_the_exclusion_ledger(self):
        code, text = self.cli('unknown\x1b[31m\nID', as_json=False)
        self.assertEqual(code, lookup.EXIT_NOT_FOUND)
        self.assertNotIn('\x1b', text)
        code, text = self.cli(self.excluded['id'], as_json=False)
        self.assertEqual(code, lookup.EXIT_EXCLUDED)
        self.assertIn(lookup.EXCLUSION_LEDGER_URL, text)

    def test_old_commands_returning_none_still_exit_successfully(self):
        with mock.patch.object(build, 'search', return_value=None) as search:
            self.assertEqual(catalog.main(['search', 'grounding', '--json']), 0)
            search.assert_called_once()

    def test_real_cli_works_without_site_packages_and_propagates_exit_status(self):
        with tempfile.TemporaryDirectory() as directory:
            for resource_id, expected in [(self.metadata['id'], 0), (self.excluded['id'], lookup.EXIT_EXCLUDED),
                                          ("unknown' OR 1=1 --", lookup.EXIT_NOT_FOUND)]:
                with self.subTest(resource_id=resource_id):
                    run = subprocess.run([sys.executable, '-S', str(ROOT / 'scripts/catalog.py'),
                                          'get', resource_id, '--json'], cwd=directory,
                                         capture_output=True, text=True, check=False)
                    self.assertEqual(run.returncode, expected, run.stderr)
                    value = json.loads(run.stdout)
                    if expected == 0:
                        self.assertEqual(value, self.metadata)
                    else:
                        self.assertEqual(value['id'], resource_id)
                    self.assertEqual(run.stderr, '')


if __name__ == '__main__':
    unittest.main()
