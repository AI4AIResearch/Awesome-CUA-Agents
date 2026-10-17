import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from export_citations import (build_citation_exports, citation_bibtex, citation_csl,
                              citation_key, encode_citations)


def paper(rid='2404.07972', status='curated', kind='paper'):
    return {
        'id': 'arxiv:' + rid, 'kind': kind, 'review_status': status,
        'scope': 'core' if status == 'curated' else 'relevance_pending',
        'name': 'GUI Agents: A Complete Title',
        'authors': ['Jean de la Fontaine', '王小明', 'Research and Development Team', 'Smith, Jr., John'],
        'url': 'https://arxiv.org/abs/' + rid,
        'identifiers': {'arxiv': rid},
        'published_at': '2024-04-11', 'updated_at': '2026-10-01',
        'details': {'arxiv_snapshot': {
            'version': 3, 'versioned_url': f'https://arxiv.org/abs/{rid}v3',
            'submitted_at': '2024-04-11T09:10:11Z', 'updated_at': '2026-10-01T01:02:03Z',
            'abstract_sha256': 'a' * 64,
            'abstract_hash_method': 'sha256-utf8-whitespace-collapsed-v1',
        }},
    }


class CitationExportTests(unittest.TestCase):
    def test_full_literal_names_and_original_title_are_preserved(self):
        record = paper()
        before = copy.deepcopy(record)
        item = citation_csl(record)
        self.assertEqual(item['title'], record['name'])
        self.assertEqual(item['author'], [{'literal': name} for name in record['authors']])
        self.assertEqual(item['type'], 'article')
        self.assertEqual(item['genre'], 'preprint')
        bib = citation_bibtex(record)
        self.assertIn('title = {{GUI Agents: A Complete Title}}', bib)
        self.assertIn('author = {{Jean de la Fontaine} and {王小明} and {Research and Development Team} and {Smith, Jr., John}}', bib)
        self.assertEqual(record, before)
        # Returned metadata cannot mutate the catalog through a nested alias.
        item['custom']['arxiv_snapshot']['version'] = 99
        item['custom']['identifiers']['arxiv'] = '2501.00001'
        self.assertEqual(record, before)

    def test_versioned_source_and_first_publication_date_remain_distinct(self):
        record = paper()
        item = citation_csl(record)
        self.assertEqual(item['issued'], {'date-parts': [[2024, 4, 11]]})
        self.assertEqual(item['URL'], 'https://arxiv.org/abs/2404.07972v3')
        self.assertEqual(item['version'], '3')
        self.assertEqual(item['custom']['arxiv_snapshot'], record['details']['arxiv_snapshot'])
        self.assertEqual(item['custom']['first_published_at'], '2024-04-11')
        self.assertEqual(item['custom']['record_updated_at'], '2026-10-01')
        self.assertIn('Recorded version updated: 2026-10-01T01:02:03Z', item['note'])
        bib = citation_bibtex(record)
        self.assertIn('year = {2024}', bib)
        self.assertNotIn('year = {2026}', bib)
        self.assertIn('First published: 2024-04-11', bib)
        self.assertIn('url = {https://arxiv.org/abs/2404.07972v3}', bib)
        self.assertIn('eprint = {2404.07972v3}', bib)

    def test_unknown_facts_are_omitted_instead_of_inferred(self):
        record = paper()
        record['published_at'] = None
        record['authors'] = []
        record['details'] = {}
        item = citation_csl(record)
        self.assertEqual(item['URL'], record['url'])
        for field in ['issued', 'submitted', 'original-date', 'version', 'author', 'DOI', 'container-title', 'publisher']:
            self.assertNotIn(field, item)
        bib = citation_bibtex(record)
        for field in ['year', 'month', 'author', 'doi', 'journal', 'booktitle', 'publisher']:
            self.assertNotRegex(bib, rf'\n  {field}\s*=')
        self.assertNotIn('v1', bib)
        self.assertIn('Recorded version updated: 2026-10-01', bib)

    def test_only_an_explicit_recorded_doi_is_exported(self):
        record = paper()
        record['identifiers']['doi'] = '10.1234/known_identifier'
        self.assertEqual(citation_csl(record)['DOI'], '10.1234/known_identifier')
        self.assertIn(r'doi = {10.1234/known\_identifier}', citation_bibtex(record))
        del record['identifiers']['doi']
        self.assertNotIn('DOI', citation_csl(record))

    def test_unknown_version_stays_unknown(self):
        record = paper()
        record['details']['arxiv_snapshot']['version'] = None
        record['details']['arxiv_snapshot']['versioned_url'] = None
        item = citation_csl(record)
        self.assertNotIn('version', item)
        self.assertEqual(item['URL'], record['url'])
        self.assertIn('eprint = {2404.07972}', citation_bibtex(record))

    def test_keys_follow_identity_and_not_mutable_metadata(self):
        record = paper()
        key = citation_key(record)
        self.assertEqual(key, 'arxiv_2404_07972')
        record['name'] = 'Revised title'
        record['authors'].reverse()
        record['published_at'] = '2023-01-01'
        record['details']['arxiv_snapshot'].update(version=4, versioned_url=record['url'] + 'v4')
        self.assertEqual(key, citation_csl(record)['citation-key'])
        old = paper('cs/9901001')
        other = paper('cs/9901002')
        self.assertRegex(citation_key(old), r'^cua_[0-9a-f]{24}$')
        self.assertNotEqual(citation_key(old), citation_key(other))

    def test_safe_tex_escaping_does_not_execute_input_or_break_entries(self):
        record = paper()
        record['name'] = 'Café 王: $x_1$ & 50% #tag ~ ^^ {unmatched \\input{secret}\n@misc{forged'
        record['authors'] = ['A} and B', 'Someone \\write18{command}']
        bib = citation_bibtex(record)
        self.assertIn('Café 王', bib)
        for escaped in [r'\$x\_1\$', r'\&', r'50\%', r'\#tag', r'\textasciitilde{}',
                        r'\textasciicircum{}\textasciicircum{}', r'\textbraceleft{}unmatched',
                        r'\textbackslash{}input\textbraceleft{}secret\textbraceright{}',
                        r'{A\textbraceright{} and B}']:
            self.assertIn(escaped, bib)
        self.assertNotIn(r'\input{', bib)
        self.assertNotIn(r'\write18{', bib)
        self.assertNotIn('^^', bib)
        self.assertEqual(len(re.findall(r'^@misc\{', bib, re.M)), 1)
        # A BibTeX reader counts lexical braces even in TeX escape sequences.
        depth = 0
        for char in bib:
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
            self.assertGreaterEqual(depth, 0)
        self.assertEqual(depth, 0)
        self.assertEqual(citation_csl(record)['title'], record['name'])

    def test_preferred_archive_is_explicit_without_replacing_duplicate_facts(self):
        duplicate = paper('2505.13887', status='metadata_verified')
        duplicate['identifiers']['preferred_arxiv'] = '2502.17110'
        duplicate['name'] = 'Original archive title'
        original = copy.deepcopy(duplicate)
        item = citation_csl(duplicate)
        self.assertEqual(item['id'], 'arxiv:2505.13887')
        self.assertEqual(item['title'], 'Original archive title')
        self.assertEqual(item['URL'], 'https://arxiv.org/abs/2505.13887v3')
        self.assertEqual(item['issued']['date-parts'], [[2024, 4, 11]])
        self.assertEqual(item['custom']['identifiers']['preferred_arxiv'], '2502.17110')
        self.assertEqual(item['custom']['preferred_record_id'], 'arxiv:2502.17110')
        self.assertIn('Preferred arXiv record recorded by catalog: arXiv:2502.17110', item['note'])
        self.assertEqual(item['custom']['catalog_review_status'], 'metadata_verified')
        self.assertNotIn('metadata_verified', item['note'])
        bib = citation_bibtex(duplicate)
        metadata = json.loads(bib.splitlines()[0].removeprefix('% AwesomeCUA: '))
        self.assertEqual(metadata['catalog_id'], duplicate['id'])
        self.assertEqual(metadata['catalog_review_status'], 'metadata_verified')
        self.assertEqual(metadata['catalog_scope'], 'relevance_pending')
        self.assertEqual(metadata['identifiers']['preferred_arxiv'], '2502.17110')
        self.assertEqual(metadata['preferred_record_id'], 'arxiv:2502.17110')
        self.assertIn('@misc{arxiv_2505_13887,', bib)
        self.assertIn('this citation retains arxiv:2505.13887', bib)
        self.assertIn('2502.17110', bib)
        self.assertEqual(json.loads(encode_citations([duplicate], 'csl-json')), [])
        self.assertEqual(len(json.loads(encode_citations([duplicate], 'csl-json', True))), 1)
        self.assertEqual(duplicate, original)

    def test_selection_includes_surveys_but_never_nonpapers(self):
        reviewed = paper()
        survey = paper('2501.00001', kind='survey')
        metadata = paper('2501.00002', status='metadata_verified')
        tool = paper('2501.00003', kind='tool')
        records = [metadata, tool, survey, reviewed]
        default = json.loads(encode_citations(records, 'csl-json'))
        all_papers = json.loads(encode_citations(records, 'csl-json', True))
        self.assertEqual([r['id'] for r in default], [reviewed['id'], survey['id']])
        self.assertEqual([r['id'] for r in all_papers], [reviewed['id'], survey['id'], metadata['id']])
        self.assertEqual(default[1]['type'], 'article')  # a survey is not a book review
        self.assertEqual(default[0]['custom']['catalog_review_status'], 'curated')
        self.assertEqual(all_papers[-1]['custom']['catalog_review_status'], 'metadata_verified')
        for item in all_papers:
            self.assertNotIn('Catalog status', item.get('note', ''))
            self.assertNotIn('editorial', item.get('note', ''))
        for record in [reviewed, metadata]:
            bib = citation_bibtex(record)
            metadata_line, entry = bib.split('\n', 1)
            state = json.loads(metadata_line.removeprefix('% AwesomeCUA: '))
            self.assertEqual(state['catalog_review_status'], record['review_status'])
            self.assertNotIn('Catalog status', entry)
            self.assertNotIn('editorial', entry)

    def test_bibtex_metadata_comments_are_single_line_json_and_never_typeset(self):
        record = paper()
        record['scope'] = 'core\n}\n@misc{injected\u2028line'
        record['identifiers']['literal_provenance'] = 'Café\r\n%text'
        bib = citation_bibtex(record)
        comment, entry = bib.split('\n', 1)
        self.assertTrue(comment.startswith('% AwesomeCUA: '))
        metadata = json.loads(comment.removeprefix('% AwesomeCUA: '))
        self.assertEqual(metadata['catalog_scope'], record['scope'])
        self.assertEqual(metadata['identifiers'], record['identifiers'])
        self.assertNotIn('\u2028', comment)
        self.assertNotIn('@', comment)  # classic BibTeX scans for @ even after %
        self.assertIn(r'\u0040misc', comment)
        self.assertTrue(comment.isascii())
        self.assertEqual(len(re.findall(r'^@misc\{', bib, re.M)), 1)
        self.assertNotIn('injected', entry)
        self.assertNotIn('catalog_review_status', entry)

    def test_single_record_selection_never_silently_exports_an_ineligible_id(self):
        records = [paper(), paper('2501.00001', status='metadata_verified'), paper('2501.00002', kind='tool')]
        for rid, message in [('arxiv:0000.00000', 'Unknown'), ('arxiv:2501.00001', '--include-metadata'),
                             ('arxiv:2501.00002', 'paper or survey')]:
            with self.subTest(rid=rid), self.assertRaisesRegex(ValueError, message):
                encode_citations(records, record_id=rid)
        output = json.loads(encode_citations(records, 'csl-json', True, 'arxiv:2501.00001'))
        self.assertEqual([r['id'] for r in output], ['arxiv:2501.00001'])

    def test_malformed_dates_identity_versions_and_controls_are_rejected(self):
        variants = []
        for field, value in [('published_at', '2024-02-30'), ('published_at', '2024-4-1'),
                             ('updated_at', 'yesterday'), ('name', 'bad\x00title'), ('review_status', 'auto_approved')]:
            record = paper()
            record[field] = value
            variants.append(record)
        record = paper()
        record['details']['arxiv_snapshot']['versioned_url'] = 'https://arxiv.org/abs/2501.00001v3'
        variants.append(record)
        record = paper()
        record['details']['arxiv_snapshot']['version'] = True
        variants.append(record)
        record = paper()
        record['identifiers']['arxiv'] = '2501.00001'
        variants.append(record)
        for record in variants:
            with self.subTest(record=record), self.assertRaises(ValueError):
                citation_bibtex(record)

    def test_manifest_matches_final_bytes_and_is_order_independent(self):
        records = [paper(), paper('2501.00001', status='metadata_verified'), paper('2501.00002', kind='tool')]
        source = b'exact input catalog bytes\n'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            first = build_citation_exports(iter(records), path, source)
            payloads = {file.name: file.read_bytes() for file in path.iterdir()}
            second = build_citation_exports(reversed(records), path, source)
            self.assertEqual(first, second)
            self.assertEqual(first['catalog_sha256'], hashlib.sha256(source).hexdigest())
            self.assertEqual(set(payloads), {'citations.bib', 'citations.csl.json', 'citations-all.bib',
                                            'citations-all.csl.json', 'citations-manifest.json'})
            self.assertEqual(first, json.loads((path / 'citations-manifest.json').read_bytes()))
            for export in first['exports']:
                body = (path / export['file']).read_bytes()
                self.assertEqual(body, payloads[export['file']])
                self.assertEqual(export['sha256'], hashlib.sha256(body).hexdigest())
                self.assertEqual(export['bytes'], len(body))
                count = len(json.loads(body)) if export['format'] == 'csl-json' else len(re.findall(rb'^@misc\{', body, re.M))
                self.assertEqual(export['records'], count)
                self.assertEqual(count, 2 if export['includes_metadata_only'] else 1)

    def test_invalid_input_cannot_leave_partial_or_replace_existing_exports(self):
        records = [paper(), paper('2501.00001', status='metadata_verified')]
        records[1]['published_at'] = 'invalid'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            target = path / 'citations.bib'
            target.write_bytes(b'previous complete export')
            with self.assertRaises(ValueError):
                build_citation_exports(records, path, b'input')
            self.assertEqual(target.read_bytes(), b'previous complete export')
            self.assertEqual(list(path.iterdir()), [target])
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                build_citation_exports([paper(), paper()], path, b'input')

    def test_cli_single_record_metadata_gate_and_input_overwrite_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'catalog.jsonl'
            original = '\n'.join(json.dumps(r, ensure_ascii=False) for r in [paper(), paper('2501.00001', status='metadata_verified')])
            path.write_text(original, encoding='utf-8')
            base = [sys.executable, '-S', str(ROOT / 'scripts/export_citations.py'), '--input', str(path)]
            result = subprocess.run(base + ['--id', 'arxiv:2501.00001', '--include-metadata', '--format', 'csl-json'], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            self.assertEqual([r['id'] for r in json.loads(result.stdout)], ['arxiv:2501.00001'])
            result = subprocess.run(base + ['--id', 'arxiv:2501.00001'], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, b'')
            self.assertIn(b'--include-metadata', result.stderr)
            result = subprocess.run(base + ['--output', str(path)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b'must not overwrite', result.stderr)
            self.assertEqual(path.read_text(encoding='utf-8'), original)

    def test_current_catalog_exports_preserve_each_selected_paper(self):
        rows = [json.loads(line) for line in (ROOT / 'data/catalog.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
        for include_metadata in [False, True]:
            expected = {r['id']: r for r in rows if r['kind'] in {'paper', 'survey'}
                        and (include_metadata or r['review_status'] == 'curated')}
            output = json.loads(encode_citations(rows, 'csl-json', include_metadata))
            self.assertEqual({r['id'] for r in output}, set(expected))
            self.assertEqual(len(output), len(expected))
            for item in output:
                record = expected[item['id']]
                self.assertEqual(item['title'], record['name'])
                self.assertEqual(item.get('author', []), [{'literal': name} for name in record['authors']])
                self.assertEqual(item['URL'], (record['details'].get('arxiv_snapshot') or {}).get('versioned_url') or record['url'])
                self.assertEqual(item['custom']['identifiers'], record['identifiers'])
                self.assertNotIn('container-title', item)
            bib = encode_citations(rows, 'bibtex', include_metadata)
            self.assertEqual(len(re.findall(rb'^@misc\{', bib, re.M)), len(expected))


if __name__ == '__main__':
    unittest.main()
