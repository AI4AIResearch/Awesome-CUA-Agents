import copy
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from repository_identity import attach_repository_aliases, github_name, repository_aliases
import build
import catalog
import lookup
from export_rag import encode_documents


def declaration(alias='Former-Owner/Project', target='Current-Owner/Project', repository_id=101):
    return {
        'alias_id': 'github:' + alias.casefold(),
        'target_id': 'github:' + target.casefold(),
        'repository_id': repository_id,
        'basis': 'official_github_repository_id',
        'reviewed_at': '2026-10-17T00:02:00Z',
        'observations': [
            {'url': 'https://api.github.com/repos/' + name,
             'resolved_url': ('https://api.github.com/repositories/' + str(repository_id)
                              if name == alias else 'https://api.github.com/repos/' + target),
             'repository_id': repository_id, 'full_name': target,
             'html_url': 'https://github.com/' + target,
             'retrieved_at': '2026-10-17T00:01:00Z', 'sha256': digest * 64}
            for name, digest in [(alias, 'a'), (target, 'b')]
        ],
    }


def target_record(item=None):
    item = declaration() if item is None else item
    return {
        'id': item['target_id'], 'name': 'Reviewed project', 'kind': 'agent',
        'url': 'https://github.com/' + item['target_id'].removeprefix('github:'),
        'review_status': 'curated', 'scope': 'core', 'aliases': ['Existing short name'],
        'summary': 'Existing source-reviewed annotation.',
        'published_at': None, 'updated_at': None, 'authors': [],
        'identifiers': {}, 'environments': ['unspecified'], 'topics': ['automation'],
        'licenses': {'code': None, 'data': None, 'weights': None, 'document': None},
        'details': {'artifact_inspection': 'No runtime reproduction.'},
        'relations': [{'type': 'introduced_by', 'target_id': 'arxiv:2501.00001',
                       'evidence_url': 'https://example.org/project-paper'}],
        'evidence': [{'url': 'https://example.org/project-paper', 'sha256': 'c' * 64,
                      'retrieved_at': '2026-10-01T00:00:00Z', 'role': 'primary',
                      'method': 'editorial_primary_review', 'supports': ['summary', 'scope']}],
        'last_verified_at': '2026-10-01T00:00:00Z',
        'links': [{'rel': 'primary', 'url': 'https://github.com/' + item['target_id'].removeprefix('github:')}],
        'notes': '',
    }


class RepositoryIdentityTests(unittest.TestCase):
    def test_paired_official_observations_resolve_case_preserving_names(self):
        item = declaration()
        before = copy.deepcopy(item)
        self.assertEqual(repository_aliases([item], [target_record(item)]),
                         {item['alias_id']: item['target_id']})
        item['observations'][0]['resolved_url'] = item['observations'][1]['url']
        self.assertEqual(repository_aliases([item]), {item['alias_id']: item['target_id']})
        self.assertEqual(before['observations'][0]['full_name'], 'Current-Owner/Project')
        self.assertEqual(github_name('https://github.com/Current-Owner/Project'), 'Current-Owner/Project')

    def test_rejects_different_numeric_ids_and_non_integer_ids(self):
        for value in (102, True, '101', 101.0, None):
            with self.subTest(observed_id=value):
                item = declaration()
                item['observations'][0]['repository_id'] = value
                with self.assertRaises(ValueError):
                    repository_aliases([item])
        for value in (0, -1, True, '101', 101.0):
            with self.subTest(declared_id=value):
                item = declaration()
                item['repository_id'] = value
                with self.assertRaises(ValueError):
                    repository_aliases([item])

    def test_rejects_wrong_owner_in_payload_html_url_or_resolved_url(self):
        changes = {
            'full_name': 'Other-Owner/Project',
            'html_url': 'https://github.com/Other-Owner/Project',
            'resolved_url': 'https://api.github.com/repos/Other-Owner/Project',
        }
        for field, value in changes.items():
            with self.subTest(field=field):
                item = declaration()
                item['observations'][0][field] = value
                with self.assertRaises(ValueError):
                    repository_aliases([item])
        item = declaration()
        item['observations'][0]['resolved_url'] = 'https://api.github.com/repositories/102'
        with self.assertRaises(ValueError):
            repository_aliases([item])

    def test_both_requested_names_are_required_not_two_canonical_responses(self):
        for observations in ([], declaration()['observations'][:1],
                             [declaration()['observations'][1]] * 2):
            with self.subTest(observations=observations):
                item = declaration()
                item['observations'] = observations
                with self.assertRaises(ValueError):
                    repository_aliases([item])
        item = declaration()
        item['observations'][0]['url'] = 'https://api.github.com/repos/Unrelated/Project'
        with self.assertRaises(ValueError):
            repository_aliases([item])

    def test_missing_or_extra_fields_and_wrong_basis_are_rejected(self):
        for field in declaration():
            with self.subTest(missing=field):
                item = declaration()
                del item[field]
                with self.assertRaises(ValueError):
                    repository_aliases([item])
        for field in declaration()['observations'][0]:
            with self.subTest(missing_observation=field):
                item = declaration()
                del item['observations'][0][field]
                with self.assertRaises(ValueError):
                    repository_aliases([item])
        for mutate in (lambda item: item.update(guessed=True),
                       lambda item: item.update(basis='similar_title'),
                       lambda item: item['observations'][0].update(unverified=True)):
            item = declaration()
            mutate(item)
            with self.assertRaises(ValueError):
                repository_aliases([item])

    def test_targets_must_exist_and_be_curated_in_scope_with_the_same_primary_url(self):
        item = declaration()
        with self.assertRaises(ValueError):
            repository_aliases([item], [])
        for status, scope in [('metadata_verified', 'relevance_pending'),
                              ('metadata_verified', 'core'), ('curated', 'relevance_pending')]:
            with self.subTest(status=status, scope=scope):
                target = target_record(item)
                target.update(review_status=status, scope=scope)
                with self.assertRaises(ValueError):
                    repository_aliases([item], [target])
        target = target_record(item)
        target['url'] = 'https://github.com/Other-Owner/Project'
        with self.assertRaises(ValueError):
            repository_aliases([item], [target])
        target = target_record(item)
        target['scope'] = 'adjacent'
        self.assertEqual(repository_aliases([item], [target]), {item['alias_id']: item['target_id']})

    def test_active_alias_and_duplicate_catalog_ids_are_rejected(self):
        item = declaration()
        target = target_record(item)
        alias = {**copy.deepcopy(target), 'id': item['alias_id'],
                 'url': 'https://github.com/Former-Owner/Project', 'review_status': 'metadata_verified'}
        with self.assertRaises(ValueError):
            repository_aliases([item], [target, alias])
        with self.assertRaises(ValueError):
            repository_aliases([item], [target, copy.deepcopy(target)])

    def test_self_duplicate_noncanonical_and_component_ids_are_rejected(self):
        item = declaration()
        with self.assertRaises(ValueError):
            repository_aliases([item, copy.deepcopy(item)])
        for bad in (item['target_id'], 'github:Former-Owner/Project',
                    'component:former-owner/project/agent', 'https://github.com/former-owner/project'):
            with self.subTest(alias=bad):
                changed = declaration()
                changed['alias_id'] = bad
                with self.assertRaises(ValueError):
                    repository_aliases([changed])

    def test_numeric_repository_and_target_ownership_cannot_conflict(self):
        first = declaration()
        for second in (declaration('Second/Project', 'Another/Project', 101),
                       declaration('Second/Project', 'Current-Owner/Project', 202)):
            with self.subTest(second=second['target_id']):
                with self.assertRaises(ValueError):
                    repository_aliases([first, second])

    def test_direct_multiple_former_names_for_one_repository_are_allowed(self):
        first = declaration()
        second = declaration('Earlier-Owner/OldName', 'Current-Owner/Project', 101)
        self.assertEqual(repository_aliases([first, second], [target_record(first)]),
                         {first['alias_id']: first['target_id'], second['alias_id']: first['target_id']})

    def test_chains_and_cycles_are_rejected_in_either_order(self):
        first = declaration('Owner/A', 'Owner/B', 101)
        for second in (declaration('Owner/B', 'Owner/C', 202), declaration('Owner/B', 'Owner/A', 202)):
            for items in ([first, second], [second, first]):
                with self.subTest(target=second['target_id'], reverse=items[0] is second):
                    with self.assertRaises(ValueError):
                        repository_aliases(items)

    def test_unsafe_and_non_repository_urls_are_rejected(self):
        urls = [
            'http://github.com/Owner/Repo', 'https://github.com.evil.test/Owner/Repo',
            'https://github.com@evil.test/Owner/Repo', 'https://user@github.com/Owner/Repo',
            'https://github.com:443/Owner/Repo', 'https://github.com/Owner/Repo?x=1',
            'https://github.com/Owner/Repo#readme', 'https://github.com/Owner/Repo/tree/main',
            'https://github.com/Owner/Repo.git', 'https://github.com/Owner/Repo/',
            'https://github.com/Owner/..', 'https://github.com/Owner/.',
            'https://github.com/Owner%2FRepo/Other', 'https://github.com/Owner/%2e%2e',
            'https://api.github.com/repos/Owner/Repo',
        ]
        for url in urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    github_name(url)
        for field in ('url', 'resolved_url'):
            item = declaration()
            item['observations'][0][field] = 'https://api.github.com.evil.test/repos/Current-Owner/Project'
            with self.assertRaises(ValueError):
                repository_aliases([item])

    def test_literal_whitespace_and_control_characters_are_not_normalized_into_evidence_urls(self):
        urls = [' https://github.com/Owner/Repo', '\x00https://github.com/Owner/Repo',
                'https://github.com/Owner/Repo\n', 'https://github.com/Owner/\tRepo',
                'https://git\rhub.com/Owner/Repo']
        for url in urls:
            with self.subTest(url=repr(url)):
                with self.assertRaises(ValueError):
                    github_name(url)
        item = declaration()
        item['observations'][0]['url'] += '\n'
        with self.assertRaises(ValueError):
            repository_aliases([item])

    def test_timestamps_are_aware_and_compared_as_instants(self):
        for value in ('2026-10-17', '2026-10-17T00:02:00', 'not-a-date', None):
            with self.subTest(value=value):
                item = declaration()
                item['reviewed_at'] = value
                with self.assertRaises(ValueError):
                    repository_aliases([item])
        item = declaration()
        item['reviewed_at'] = '2026-10-17T02:02:00+02:00'
        self.assertEqual(repository_aliases([item]), {item['alias_id']: item['target_id']})
        item['reviewed_at'] = '2026-10-17T01:59:00+02:00'
        with self.assertRaises(ValueError):
            repository_aliases([item])

    def test_receipts_require_real_sha256_shapes(self):
        for value in ('a' * 63, 'A' * 64, 'z' * 64, '', None):
            with self.subTest(value=value):
                item = declaration()
                item['observations'][1]['sha256'] = value
                with self.assertRaises(ValueError):
                    repository_aliases([item])

    def test_attachment_is_immutable_idempotent_and_does_not_create_resources(self):
        item = declaration()
        records = [target_record(item), target_record(declaration('Other/Before', 'Other/After', 303))]
        original_records = copy.deepcopy(records)
        original_declarations = copy.deepcopy([item])
        result = attach_repository_aliases(records, [item])
        self.assertEqual(records, original_records)
        self.assertEqual([item], original_declarations)
        self.assertEqual([r['id'] for r in result], [r['id'] for r in records])
        self.assertEqual(result[1], records[1])
        for key, value in records[0].items():
            if key not in ('aliases', 'evidence'):
                self.assertEqual(result[0][key], value, key)
        self.assertEqual(result[0]['aliases'], ['Existing short name', item['alias_id'],
                                               'Former-Owner/Project', 'https://github.com/Former-Owner/Project'])
        self.assertEqual(result[0]['evidence'][:len(records[0]['evidence'])], records[0]['evidence'])
        self.assertEqual(len(result[0]['evidence']), len(records[0]['evidence']) + 2)
        for receipt in result[0]['evidence'][-2:]:
            self.assertEqual(receipt['supports'], ['aliases'])
            self.assertEqual(receipt['method'], 'github_repository_identity')
            self.assertEqual(receipt['role'], 'primary')
        self.assertEqual(attach_repository_aliases(result, [item]), result)
        result[0]['details']['artifact_inspection'] = 'Changed only in returned value'
        self.assertEqual(records, original_records)

    def test_failed_attachment_does_not_partially_mutate_inputs(self):
        item = declaration()
        invalid = declaration('Other/Old', 'Unknown/New', 404)
        records = [target_record(item)]
        before = copy.deepcopy(records)
        with self.assertRaises(ValueError):
            attach_repository_aliases(records, [item, invalid])
        self.assertEqual(records, before)


class RepositoryIdentityIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / 'data'
        self.data.mkdir()
        self.item = declaration()
        self.target = target_record(self.item)
        self.paper = copy.deepcopy(self.target)
        self.paper.update(id='arxiv:2501.00001', name='Retained paper', kind='paper',
                          url='https://arxiv.org/abs/2501.00001', aliases=[],
                          review_status='metadata_verified', scope='relevance_pending',
                          summary=None, published_at='2025-01-01', updated_at='2025-01-01',
                          identifiers={'arxiv': '2501.00001'}, topics=[], relations=[], details={},
                          links=[{'rel': 'primary', 'url': 'https://arxiv.org/abs/2501.00001'}])
        self.paper['evidence'] = [{**self.target['evidence'][0], 'method': 'arxiv_api',
                                   'url': 'https://export.arxiv.org/api/query?id_list=2501.00001'}]
        self.editorial = {key: copy.deepcopy(self.target[key]) for key in
                          ('name', 'kind', 'url', 'aliases', 'summary', 'scope', 'environments', 'topics', 'details')}
        self.editorial.update(editorial_reviewed=True, reviewed_sha256='c' * 64,
                              reviewed_at='2026-10-01T00:00:00Z',
                              reviewed_relations=copy.deepcopy(self.target['relations']))
        self.primary = {'id': self.target['id'], 'url': self.target['evidence'][0]['url'],
                        'retrieved_at': self.target['last_verified_at'], 'sha256': 'c' * 64,
                        'content_matched': True}
        self.write_json('editorial.json', [self.editorial])
        self.write_json('repository-aliases.json', [self.item])
        self.write_json('exclusions.json', [])
        self.write_json('sources.json', [{'id': 'fixture', 'name': 'Fixture collection',
                                         'homepage': 'https://example.org/collection'}])
        self.write_jsonl('papers.jsonl', [self.paper])
        self.write_jsonl('primary-evidence.jsonl', [self.primary])
        self.write_jsonl('publications.jsonl', [])
        self.write_jsonl('metadata-updates.jsonl', [])
        self.write_jsonl('enrichment.jsonl', [{
            'id': self.target['id'], 'evidence_sha256': 'c' * 64,
            'references': [{'type': 'mentions', 'target_id': self.item['alias_id'],
                            'evidence_url': self.primary['url']}],
        }])
        self.candidates = [{'id': identity, 'url': url, 'discovered_in': [{'source_id': 'fixture'}]}
                           for identity, url in [
                               (self.item['alias_id'], 'https://github.com/Former-Owner/Project'),
                               (self.item['target_id'], self.target['url']),
                               ('github:missing/repo', 'https://github.com/missing/repo'),
                           ]]
        self.write_jsonl('candidates.jsonl', self.candidates)
        for module, name, value in ((build, 'DATA', self.data), (build, 'ROOT', self.root),
                                    (lookup, 'DATA', self.data)):
            patcher = mock.patch.object(module, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def write_json(self, name, value):
        (self.data / name).write_text(json.dumps(value) + '\n')

    def write_jsonl(self, name, rows):
        (self.data / name).write_text(''.join(json.dumps(row) + '\n' for row in rows))

    def materialize_fixture(self):
        rows, pending, decisions = build.source_records(with_scope=True)
        self.assertEqual(pending, [])
        self.write_jsonl('catalog.jsonl', rows)
        self.write_json('exclusion-status.json', {'schema_version': 1, 'decisions': decisions})
        return rows

    def cli_json(self, arguments):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = catalog.main(arguments)
        return code, json.loads(stream.getvalue())

    def test_source_records_derives_only_aliases_and_identity_receipts(self):
        sources = {p.name: p.read_bytes() for p in self.data.iterdir()}
        rows, pending, decisions = build.source_records(with_scope=True)
        target = next(row for row in rows if row['id'] == self.target['id'])
        self.assertEqual(len(rows), 2)
        self.assertEqual(pending, [])
        self.assertEqual(decisions, [])
        self.assertIn(self.item['alias_id'], target['aliases'])
        self.assertEqual(target['relations'], self.target['relations'])
        self.assertEqual(target['licenses'], self.target['licenses'])
        self.assertEqual(target['last_verified_at'], self.target['last_verified_at'])
        identities = [e for e in target['evidence'] if e['method'] == 'github_repository_identity']
        self.assertEqual(len(identities), 2)
        self.assertTrue(all(e['supports'] == ['aliases'] for e in identities))
        self.assertEqual({p.name: p.read_bytes() for p in self.data.iterdir()}, sources)
        self.assertEqual(build.source_records(with_scope=True), (rows, pending, decisions))

    def test_source_records_fails_closed_when_alias_owner_loses_content_review(self):
        self.editorial['editorial_reviewed'] = False
        self.write_json('editorial.json', [self.editorial])
        with self.assertRaises(ValueError):
            build.source_records()

    def test_lookup_cli_returns_complete_canonical_record_and_canonical_relations(self):
        rows = self.materialize_fixture()
        target = next(row for row in rows if row['id'] == self.target['id'])
        code, result = self.cli_json(['get', self.item['alias_id'], '--json'])
        self.assertEqual(code, lookup.EXIT_OK)
        self.assertEqual(result, target)
        code, related = self.cli_json(['get', self.item['alias_id'], '--json', '--related'])
        self.assertEqual(code, lookup.EXIT_OK)
        self.assertEqual(related['record'], target)
        self.assertEqual(len(related['related']), 1)
        edge = related['related'][0]
        self.assertEqual(edge['source_id'], self.target['id'])
        self.assertEqual(edge['target_id'], self.paper['id'])
        self.assertEqual(edge['resource']['review_status'], 'metadata_verified')
        code, result = self.cli_json(['get', self.item['alias_id'].upper(), '--json'])
        self.assertEqual(code, lookup.EXIT_NOT_FOUND)
        self.assertEqual(result['id'], self.item['alias_id'].upper())

    def test_alias_identity_receipts_cannot_prove_reviewed_paper_or_evaluation_relations(self):
        rows = self.materialize_fixture()
        self.assertEqual(build.validate_records(rows), [])
        for relation_type in ('introduced_by', 'evaluates'):
            with self.subTest(relation_type=relation_type):
                changed = copy.deepcopy(rows)
                owner = next(row for row in changed if row['id'] == self.target['id'])
                target_id = self.paper['id']
                if relation_type == 'evaluates':
                    benchmark = target_record(declaration('Fixture/Before', 'Fixture/Benchmark', 303))
                    benchmark.update(kind='benchmark', name='Fixture benchmark', relations=[],
                                     details={'task_count': None, 'metrics': [],
                                              'evaluation_type': None, 'leaderboard_url': None})
                    changed.append(benchmark)
                    target_id = benchmark['id']
                identity = next(e for e in owner['evidence'] if e['method'] == 'github_repository_identity')
                self.assertEqual(identity['supports'], ['aliases'])
                owner['relations'] = [{'type': relation_type, 'target_id': target_id,
                                       'evidence_url': identity['url']}]
                errors = build.validate_records(changed)
                self.assertTrue(any('scoped to relations' in error for error in errors), errors)
                self.write_jsonl('catalog.jsonl', changed)
                code, result = self.cli_json(['get', self.item['alias_id'], '--json', '--related'])
                self.assertEqual(code, lookup.EXIT_DATA_ERROR)
                self.assertEqual(result['status'], 'data_error')
                self.assertIn('scoped to relations', result['message'])

    def test_metadata_owned_alias_receipt_edges_are_not_promoted_as_reviewed_relations(self):
        rows = self.materialize_fixture()
        owner = next(row for row in rows if row['id'] == self.target['id'])
        metadata = next(row for row in rows if row['id'] == self.paper['id'])
        identity = copy.deepcopy(next(e for e in owner['evidence'] if e['method'] == 'github_repository_identity'))
        metadata['evidence'].append(identity)
        metadata['relations'] = [{'type': 'evaluates', 'target_id': owner['id'],
                                  'evidence_url': identity['url']}]
        self.write_jsonl('catalog.jsonl', rows)
        code, result = self.cli_json(['get', self.item['alias_id'], '--json', '--related'])
        self.assertEqual(code, lookup.EXIT_OK)
        self.assertEqual(len(result['related']), 1)
        edge = result['related'][0]
        self.assertEqual(edge['source_id'], owner['id'])
        self.assertEqual(edge['target_id'], metadata['id'])
        self.assertEqual(edge['resource']['review_status'], 'metadata_verified')
        self.assertIsNone(edge['resource']['summary'])

    def test_search_cli_resolves_old_name_id_and_repository_file_url_with_filters(self):
        rows = self.materialize_fixture()
        target = next(row for row in rows if row['id'] == self.target['id'])
        for query in (self.item['alias_id'], 'Former-Owner/Project',
                      'https://github.com/Former-Owner/Project/tree/main/README.md'):
            with self.subTest(query=query):
                code, result = self.cli_json(['search', query, '--json', '--limit', '0'])
                self.assertEqual(code, 0)
                self.assertEqual(result['total_matches'], 1)
                self.assertEqual(result['records'], [target])
        _, result = self.cli_json(['search', self.item['alias_id'], '--kind', 'paper', '--json'])
        self.assertEqual(result['total_matches'], 0)
        _, result = self.cli_json(['search', self.item['alias_id'], '--status', 'metadata_verified', '--json'])
        self.assertEqual(result['total_matches'], 0)

    def test_search_rejects_repository_aliases_with_inactive_or_unreviewed_owners(self):
        rows = self.materialize_fixture()
        for state in ('missing', 'metadata_verified'):
            with self.subTest(state=state):
                changed = copy.deepcopy(rows)
                if state == 'missing':
                    changed = [row for row in changed if row['id'] != self.target['id']]
                else:
                    target = next(row for row in changed if row['id'] == self.target['id'])
                    target.update(review_status='metadata_verified', scope='relevance_pending',
                                  summary=None, aliases=[])
                self.write_jsonl('catalog.jsonl', changed)
                with self.assertRaises(ValueError):
                    self.cli_json(['search', 'https://github.com/Former-Owner/Project', '--json'])

    def test_source_aliases_preserves_publication_and_repository_mapping_namespaces(self):
        url = 'https://example.org/proceedings/retained-paper'
        self.write_jsonl('publications.jsonl', [{
            'id': self.paper['id'], 'publication': {
                'type': 'conference-paper', 'title': 'Publication edition',
                'authors': ['Edition Author'], 'date_parts': [2025], 'url': url,
                'doi': '10.1234/fixture', 'evidence_urls': [url],
            },
            'evidence': [{'url': url, 'sha256': 'd' * 64, 'retrieved_at': '2026-10-01T00:00:00Z',
                          'role': 'primary', 'method': 'editorial_primary_review',
                          'supports': ['details.publication']}],
            'last_verified_at': '2026-10-01T00:00:00Z',
        }])
        rows = self.materialize_fixture()
        aliases = build.source_aliases(rows)
        self.assertEqual(aliases[self.item['alias_id']], self.target['id'])
        self.assertEqual(aliases[catalog.publication_identity(url)[0]], self.paper['id'])
        self.assertEqual(aliases[catalog.publication_identity('https://doi.org/10.1234/fixture')[0]], self.paper['id'])
        _, result = self.cli_json(['search', 'https://doi.org/10.1234/fixture', '--json'])
        self.assertEqual([r['id'] for r in result['records']], [self.paper['id']])

    def test_coverage_resolves_two_identifiers_to_one_resource(self):
        rows = self.materialize_fixture()
        report = build.coverage(rows, [], [])
        self.assertEqual(report['total_records'], 2)
        self.assertEqual(report['curated_records'], 1)
        self.assertEqual(report['unindexed_candidates'], 1)
        source = report['sources'][0]
        self.assertEqual((source['discovered'], source['indexed'], source['indexed_resources'],
                          source['resolved_aliases'], source['unindexed']), (3, 2, 1, 1, 1))

    def test_real_build_queue_resolves_alias_without_rewriting_raw_mentions(self):
        original_candidates = (self.data / 'candidates.jsonl').read_bytes()
        original_enrichment = (self.data / 'enrichment.jsonl').read_bytes()
        with mock.patch.object(build, 'documents', return_value={}), contextlib.redirect_stdout(io.StringIO()):
            build.build(types.SimpleNamespace(check=False))
        queue = [json.loads(line) for line in (self.data / 'review-queue.jsonl').read_text().splitlines()]
        self.assertEqual([item['id'] for item in queue], ['github:missing/repo'])
        references = [json.loads(line) for line in (self.data / 'references.jsonl').read_text().splitlines()]
        self.assertEqual(len(references), 1)
        self.assertEqual(references[0]['target_id'], self.item['alias_id'])
        self.assertEqual(references[0]['type'], 'mentions')
        self.assertEqual((self.data / 'candidates.jsonl').read_bytes(), original_candidates)
        self.assertEqual((self.data / 'enrichment.jsonl').read_bytes(), original_enrichment)
        self.assertEqual(len((self.data / 'catalog.jsonl').read_text().splitlines()), 2)

    def test_rag_text_and_metadata_retain_proven_former_names(self):
        rows = self.materialize_fixture()
        documents = [json.loads(line) for line in encode_documents(rows).splitlines()]
        self.assertEqual(len(documents), 1)
        doc = documents[0]
        self.assertEqual(doc['id'], self.target['id'])
        self.assertIn(self.item['alias_id'], doc['metadata']['aliases'])
        self.assertIn('Recorded aliases:', doc['text'])
        self.assertIn('Former-Owner/Project', doc['text'])
        self.assertEqual(doc['metadata']['review_status'], 'curated')


if __name__ == '__main__':
    unittest.main()
