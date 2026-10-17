from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from paper_library import paper_library
from search_pages import page, resource_path, SITE


class LibraryParser(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.records = []
        self.ids = []
        self.links = []
        self.alternates = {}
        self.record_links = {}
        self.current_record = None
        self.feed(markup)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get('data-resource-id'):
            self.records.append(attrs['data-resource-id'])
            self.current_record = attrs['data-resource-id']
            self.record_links[self.current_record] = []
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'a':
            self.links.append(attrs.get('href', ''))
            if self.current_record:
                self.record_links[self.current_record].append(attrs.get('href', ''))
        if tag == 'link' and 'hreflang' in attrs:
            self.alternates[attrs['hreflang']] = attrs['href']

    def handle_endtag(self, tag):
        if tag == 'article':
            self.current_record = None


def record(rid, date, **changes):
    return {'id': rid, 'name': rid, 'kind': 'paper', 'review_status': 'curated',
            'scope': 'core', 'published_at': date, 'url': 'https://example.org/' + rid,
            'authors': ['First Author', 'Second Author', 'Third Author'],
            'summary': 'An original annotation.', 'topics': ['grounding'],
            'environments': ['web'], 'details': {}, 'relations': [], 'evidence': [], **changes}


class PaperLibraryTests(unittest.TestCase):
    def test_both_languages_show_the_same_reviewed_records_and_schema_in_date_order(self):
        rows = [record('old', '2020-01-02'), record('new', '2025-03-04'),
                record('undated', None, kind='survey'),
                record('metadata', '2026-01-01', review_status='metadata_verified'),
                record('pending', '2025-01-01', scope='unreviewed'),
                record('model', '2026-01-01', kind='model')]
        for language in ('en', 'zh'):
            markup, schema = paper_library(rows, resource_path, language=language)
            parsed = LibraryParser(markup)
            self.assertEqual(parsed.records, ['new', 'old', 'undated'])
            self.assertEqual(schema['numberOfItems'], 3)
            self.assertEqual([x['url'] for x in schema['itemListElement']],
                             [SITE + '/resources/' + key + '/' for key in parsed.records])
            for link in parsed.links:
                if link.startswith('#'):
                    self.assertIn(link[1:], parsed.ids)
            self.assertEqual(len(parsed.ids), len(set(parsed.ids)))
            self.assertIn('papers-undated', parsed.ids)
            self.assertNotIn('<time datetime="None"', markup)
            for rid, kind in [('new', 'paper'), ('undated', 'survey')]:
                topic_links = [parse_qs(urlsplit(link).query) for link in parsed.record_links[rid]
                               if 'topic=' in link]
                self.assertTrue(topic_links)
                self.assertTrue(all(query['kind'] == [kind] for query in topic_links))
            category_links = [parse_qs(urlsplit(link).query) for link in parsed.links
                              if 'review=curated' in link and 'topic=' not in link]
            self.assertEqual({query['kind'][0] for query in category_links}, {'paper', 'survey'})

    def test_source_version_and_safe_text_survive_without_inventing_unknowns(self):
        row = record('arxiv:2404.07972', '2024-04-11', name='<script>unsafe</script> & original',
                     summary='An annotation <with> & punctuation.',
                     details={'arxiv_snapshot': {'version': 2, 'versioned_url': 'https://arxiv.org/abs/2404.07972v2'}})
        markup, schema = paper_library([row], resource_path)
        parsed = LibraryParser(markup)
        self.assertNotIn('<script>unsafe</script>', markup)
        self.assertIn('&lt;script&gt;unsafe&lt;/script&gt;', markup)
        self.assertEqual(schema['itemListElement'][0]['name'], row['name'])
        self.assertIn('https://arxiv.org/abs/2404.07972v2', parsed.links)
        self.assertIn('/resources/arxiv-2404-07972/citation.bib', parsed.links)
        self.assertIn('2024-04-11', markup)
        self.assertIn('First Author, Second Author + 1 author', markup)
        for link in parsed.links:
            query = parse_qs(urlsplit(link).query)
            if query.get('topic'):
                self.assertEqual(query['review'], ['curated'])
                self.assertEqual(query['topic'], ['grounding'])

    def test_language_alternates_point_to_the_library_pair_and_chinese_navigation(self):
        alternatives = {'en': '/papers/', 'zh-CN': '/zh/papers/', 'x-default': '/papers/'}
        for lang, path in [('en', '/papers/'), ('zh-CN', '/zh/papers/')]:
            markup = page('Library', 'Reviewed papers', path, '<h1>Library</h1>',
                          lang=lang, alternatives=alternatives)
            parsed = LibraryParser(markup)
            self.assertEqual(parsed.alternates, {key: SITE + val for key, val in alternatives.items()})
            self.assertIn(f'<link rel="canonical" href="{SITE}{path}">', markup)
            if lang == 'zh-CN':
                self.assertIn('<a href="/zh/papers/">论文</a>', markup)


if __name__ == '__main__':
    unittest.main()
