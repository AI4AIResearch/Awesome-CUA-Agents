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


def published_edition(parts=None, publication_type='conference-paper'):
    return {
        'type': publication_type, 'title': 'The Published GUI Study',
        'authors': ['Changed Author', 'Éva and 王 Research Team'],
        'date_parts': [2025] if parts is None else parts,
        'venue': 'Proceedings of the GUI Research Conference',
        'publisher': 'Example Research Publisher', 'pages': '101--120',
        'doi': '10.1234/published_gui', 'url': 'https://example.org/proceedings/gui-study',
        'evidence_urls': ['https://example.org/proceedings/gui-study'],
    }


def publisher_paper(parts=None, publication_type='conference-paper', status='curated'):
    pub = published_edition(parts, publication_type)
    record = paper(status=status)
    record.update(id='url:' + hashlib.sha256(pub['url'].encode()).hexdigest()[:20],
                  name=pub['title'], authors=list(pub['authors']), url=pub['url'],
                  identifiers={'doi': pub['doi']}, updated_at=None,
                  published_at='-'.join([f'{pub["date_parts"][0]:04d}',
                                         *(f'{p:02d}' for p in pub['date_parts'][1:])])
                  if len(pub['date_parts']) == 3 else None,
                  details={'publication': pub})
    return record


class CitationExportTests(unittest.TestCase):
    def test_preexisting_arxiv_format_remains_byte_identical_without_publication(self):
        record = paper()
        self.assertEqual(hashlib.sha256(citation_bibtex(record).encode()).hexdigest(),
                         'a099e979996062d242b537f321863c3f7ba88bbf87caa6b694e2f35233d727c3')
        self.assertEqual(hashlib.sha256(json.dumps(citation_csl(record), ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
                         '6379bb5c9ed248617d109c9de83837927fd093e143d91f0152eb89b0dedce9c2')

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
                                            'citations-all.csl.json', 'publication-citations.bib',
                                            'publication-citations.csl.json', 'citations-manifest.json'})
            self.assertEqual(first, json.loads((path / 'citations-manifest.json').read_bytes()))
            for export in first['exports']:
                body = (path / export['file']).read_bytes()
                self.assertEqual(body, payloads[export['file']])
                self.assertEqual(export['sha256'], hashlib.sha256(body).hexdigest())
                self.assertEqual(export['bytes'], len(body))
                count = len(json.loads(body)) if export['format'] == 'csl-json' else len(re.findall(rb'^@[a-z]+\{', body, re.M))
                self.assertEqual(export['records'], count)
                self.assertEqual(count, 0 if export['edition'] == 'publication' else 2 if export['includes_metadata_only'] else 1)

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
                pub = record.get('details', {}).get('publication') if not record['id'].startswith('arxiv:') else None
                self.assertEqual(item['title'], pub['title'] if pub else record['name'])
                self.assertEqual(item.get('author', []), [{'literal': name} for name in (pub['authors'] if pub else record['authors'])])
                self.assertEqual(item['URL'], pub['url'] if pub else (record['details'].get('arxiv_snapshot') or {}).get('versioned_url') or record['url'])
                self.assertEqual(item['custom']['identifiers'], record['identifiers'])
                if not pub:
                    self.assertNotIn('container-title', item)
            bib = encode_citations(rows, 'bibtex', include_metadata)
            self.assertEqual(len(re.findall(rb'^@[a-z]+\{', bib, re.M)), len(expected))

    def test_attached_publication_never_changes_default_arxiv_bibliographic_fields(self):
        record = paper()
        original = citation_csl(record)
        original_entry = citation_bibtex(record).split('\n', 1)[1]
        record['details']['publication'] = published_edition([2025, 7, 9])
        # Even a publisher DOI copied into generic identifiers is not a preprint DOI.
        record['identifiers']['doi'] = record['details']['publication']['doi']
        item = citation_csl(record)
        self.assertEqual({k: v for k, v in item.items() if k != 'custom'},
                         {k: v for k, v in original.items() if k != 'custom'})
        self.assertEqual(citation_bibtex(record).split('\n', 1)[1], original_entry)
        self.assertEqual(item['custom']['publication'], record['details']['publication'])
        self.assertEqual(item['custom']['citation_edition'], 'record')
        comment = json.loads(citation_bibtex(record).splitlines()[0].removeprefix('% AwesomeCUA: '))
        self.assertEqual(comment['publication'], record['details']['publication'])
        self.assertEqual(comment['catalog_id'], record['id'])

    def test_explicit_publication_uses_its_own_authors_date_type_url_and_identity(self):
        record = paper()
        pub = published_edition([2025, 7, 9])
        record['details']['publication'] = pub
        before = copy.deepcopy(record)
        item = citation_csl(record, edition='publication')
        self.assertEqual(item['id'], record['id'] + ':publication')
        self.assertEqual(item['citation-key'], 'arxiv_2404_07972_publication')
        self.assertEqual(item['custom']['catalog_id'], record['id'])
        self.assertEqual(item['custom']['citation_edition'], 'publication')
        self.assertEqual(item['title'], pub['title'])
        self.assertEqual(item['author'], [{'literal': name} for name in pub['authors']])
        self.assertEqual(item['issued'], {'date-parts': [[2025, 7, 9]]})
        self.assertEqual(item['type'], 'paper-conference')
        self.assertEqual(item['container-title'], pub['venue'])
        self.assertEqual(item['URL'], pub['url'])
        self.assertEqual(item['DOI'], pub['doi'])
        for field in ['archive', 'archive_location', 'version', 'genre']:
            self.assertNotIn(field, item)
        self.assertEqual(item['note'], 'Publication date: 2025-07-09.')
        self.assertEqual(item['custom']['arxiv_snapshot'], record['details']['arxiv_snapshot'])
        bib = citation_bibtex(record, edition='publication')
        self.assertIn('@inproceedings{arxiv_2404_07972_publication,', bib)
        self.assertIn('year = {2025}', bib)
        self.assertIn('month = jul', bib)
        self.assertIn('booktitle = {' + pub['venue'] + '}', bib)
        self.assertIn('{Changed Author} and {Éva and 王 Research Team}', bib)
        entry = bib.split('\n', 1)[1]
        for text in ['eprint =', 'archivePrefix =', '2024-04-11', '2026-10-01', 'Recorded arXiv version']:
            self.assertNotIn(text, entry)
        self.assertEqual(record, before)
        item['custom']['publication']['authors'].append('Must not mutate the source')
        self.assertEqual(record, before)

    def test_publisher_only_defaults_match_explicit_edition_at_all_date_precisions(self):
        for parts in [[2025], [2025, 7], [2025, 7, 9]]:
            with self.subTest(parts=parts):
                record = publisher_paper(parts)
                item = citation_csl(record)
                self.assertEqual(item, citation_csl(record, 'publication'))
                self.assertEqual(citation_bibtex(record), citation_bibtex(record, 'publication'))
                self.assertEqual(item['id'], record['id'])
                self.assertEqual(item['citation-key'], citation_key(record))
                self.assertFalse(item['citation-key'].endswith('_publication'))
                self.assertEqual(item['issued']['date-parts'], [parts])
                bib = citation_bibtex(record)
                self.assertIn('year = {2025}', bib)
                self.assertEqual('month = jul' in bib, len(parts) >= 2)
                expected_date = '-'.join([str(parts[0]), *(f'{p:02d}' for p in parts[1:])])
                self.assertEqual(item['note'], 'Publication date: ' + expected_date + '.')
                self.assertNotIn('2025-01-01', item['note'])

    def test_journal_and_unknown_publication_fields_are_not_invented(self):
        record = publisher_paper([2025, 7], 'journal-article')
        pub = record['details']['publication']
        pub.update(venue='Journal of GUI Research', volume='12', issue='3', pages='100–120', series='Research Series')
        item = citation_csl(record)
        self.assertEqual(item['type'], 'article-journal')
        for field, value in [('container-title', pub['venue']), ('volume', '12'), ('issue', '3'),
                             ('page', '100–120'), ('collection-title', 'Research Series')]:
            self.assertEqual(item[field], value)
        bib = citation_bibtex(record)
        self.assertIn('@article{', bib)
        self.assertIn('journal = {Journal of GUI Research}', bib)
        self.assertIn('number = {3}', bib)
        pub.update(date_parts=None, authors=[], doi=None, venue=None, publisher=None,
                   volume=None, issue=None, pages=None, series=None)
        record.update(published_at=None, authors=[], identifiers={})
        item = citation_csl(record)
        for field in ['issued', 'author', 'DOI', 'container-title', 'publisher', 'volume', 'issue', 'page', 'collection-title', 'note']:
            self.assertNotIn(field, item)
        entry = citation_bibtex(record).split('\n', 1)[1]
        for field in ['year', 'month', 'author', 'doi', 'journal', 'publisher', 'volume', 'number', 'pages', 'note']:
            self.assertNotRegex(entry, rf'\n  {field}\s*=')
        for publication_type, csl_type in [('report', 'report'), ('other', 'article')]:
            pub['type'] = publication_type
            self.assertEqual(citation_csl(record)['type'], csl_type)
            self.assertIn('@misc{', citation_bibtex(record))
            self.assertNotIn('institution =', citation_bibtex(record))

    def test_publication_selection_is_gated_and_missing_single_edition_is_an_error(self):
        missing = paper()
        present = paper('2501.00001')
        present['details']['publication'] = published_edition()
        pending = paper('2501.00002', status='metadata_verified')
        pending['details']['publication'] = published_edition()
        rows = [missing, present, pending]
        selected = json.loads(encode_citations(rows, 'csl-json', edition='publication'))
        self.assertEqual([r['custom']['catalog_id'] for r in selected], [present['id']])
        all_selected = json.loads(encode_citations(rows, 'csl-json', True, edition='publication'))
        self.assertEqual([r['custom']['catalog_id'] for r in all_selected], [present['id'], pending['id']])
        with self.assertRaisesRegex(ValueError, 'No recorded publication'):
            encode_citations(rows, record_id=missing['id'], edition='publication')
        with self.assertRaisesRegex(ValueError, '--include-metadata'):
            encode_citations(rows, record_id=pending['id'], edition='publication')
        with self.assertRaisesRegex(ValueError, 'No recorded publication'):
            citation_csl(missing, 'publication')
        with self.assertRaisesRegex(ValueError, 'Unsupported citation edition'):
            citation_bibtex(present, 'latest')

    def test_publication_comment_and_fields_escape_untrusted_literal_metadata(self):
        record = publisher_paper([2025])
        pub = record['details']['publication']
        pub.update(title='GUI } \\input{secret} & 50% ^^',
                   authors=['A} and B', '王 \\write18{x}'],
                   venue='Proceedings {test} #1',
                   notes='\n@misc{injected}\u2028next line')
        item = citation_csl(record)
        self.assertEqual(item['title'], pub['title'])
        self.assertEqual(item['author'], [{'literal': name} for name in pub['authors']])
        bib = citation_bibtex(record)
        comment, entry = bib.split('\n', 1)
        self.assertEqual(json.loads(comment.removeprefix('% AwesomeCUA: '))['publication'], pub)
        self.assertNotIn('@', comment)
        self.assertTrue(comment.isascii())
        self.assertNotIn(r'\input{', entry)
        self.assertNotIn(r'\write18{', entry)
        self.assertNotIn('^^', entry)
        self.assertNotIn('injected', entry)
        self.assertIn(r'\textbraceright{}', entry)
        self.assertIn(r'\& 50\%', entry)
        self.assertEqual(len(re.findall(r'^@[a-z]+\{', bib, re.M)), 1)

    def test_malformed_publication_facts_or_mixed_identity_fail_before_export(self):
        mutations = [lambda p: p.update(type='conference'), lambda p: p.update(authors='one author'),
                     lambda p: p.update(title=''), lambda p: p.update(url='javascript:alert(1)'),
                     lambda p: p.update(date_parts=[2025, 2, 30]), lambda p: p.update(date_parts=[True]),
                     lambda p: p.update(doi='https://doi.org/10.1234/x'), lambda p: p.pop('date_parts')]
        for mutate in mutations:
            record = publisher_paper()
            mutate(record['details']['publication'])
            with self.subTest(record=record), self.assertRaises(ValueError):
                citation_bibtex(record)
        record = publisher_paper()
        record['details']['arxiv_snapshot'] = paper()['details']['arxiv_snapshot']
        with self.assertRaisesRegex(ValueError, 'arXiv'):
            citation_csl(record)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            record = publisher_paper()
            record['details']['publication']['date_parts'] = [2025, 13]
            with self.assertRaises(ValueError):
                build_citation_exports([paper(), record], path, b'source')
            self.assertEqual(list(path.iterdir()), [])

    def test_publication_global_bundle_is_reviewed_only_and_hashes_match(self):
        linked = paper()
        linked['details']['publication'] = published_edition()
        native = publisher_paper([2025, 7])
        pending = paper('2501.00001', status='metadata_verified')
        pending['details']['publication'] = published_edition()
        rows = [linked, native, pending, paper('2501.00002')]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            manifest = build_citation_exports(rows, path, b'source')
            self.assertEqual(len(manifest['exports']), 6)
            pub_items = json.loads((path / 'publication-citations.csl.json').read_bytes())
            self.assertEqual({r['custom']['catalog_id'] for r in pub_items}, {linked['id'], native['id']})
            for export in manifest['exports']:
                body = (path / export['file']).read_bytes()
                expected = 2 if export['edition'] == 'publication' else 4 if export['includes_metadata_only'] else 3
                self.assertEqual(export['records'], expected)
                self.assertEqual(export['sha256'], hashlib.sha256(body).hexdigest())
                self.assertEqual(export['bytes'], len(body))
            self.assertIn(citation_bibtex(linked, 'publication').encode(), (path / 'publication-citations.bib').read_bytes())

    def test_cli_publication_edition_missing_record_and_metadata_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'catalog.jsonl'
            pending = paper('2501.00001', status='metadata_verified')
            pending['details']['publication'] = published_edition([2025, 7])
            path.write_text('\n'.join(json.dumps(r) for r in [paper(), pending]), encoding='utf-8')
            base = [sys.executable, '-S', str(ROOT / 'scripts/export_citations.py'), '--input', str(path), '--edition', 'publication', '--format', 'csl-json']
            for rid, message in [('arxiv:2404.07972', b'No recorded publication'), (pending['id'], b'--include-metadata')]:
                run = subprocess.run(base + ['--id', rid], capture_output=True)
                self.assertNotEqual(run.returncode, 0)
                self.assertEqual(run.stdout, b'')
                self.assertIn(message, run.stderr)
            run = subprocess.run(base + ['--include-metadata', '--id', pending['id']], capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr.decode())
            item = json.loads(run.stdout)[0]
            self.assertEqual(item['id'], pending['id'] + ':publication')
            self.assertEqual(item['issued']['date-parts'], [[2025, 7]])


if __name__ == '__main__':
    unittest.main()
