import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
import urllib.parse
import urllib.robotparser
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_site import build_site
from search_pages import SITE, eligible, resource_path, resource_schema, page, incoming_relations

ROOT=Path(__file__).resolve().parents[1]


class PageParser(HTMLParser):
    def __init__(self,text):
        super().__init__();self.canonical=[];self.robots=[];self.links=[];self.heading_count=0
        self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a['href'])
        if tag=='meta' and a.get('name')=='robots':self.robots.append(a['content'])
        if tag=='a' and 'href' in a:self.links.append(a['href'])
        if tag=='h1':self.heading_count+=1


class SearchPagesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.dest=build_site(cls.temp.name)
        cls.rows=[json.loads(x) for x in (ROOT/'data/catalog.jsonl').read_text().splitlines()]
        cls.manifest=json.loads((cls.dest/'data/search-manifest.json').read_text())
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_permalink_identity_survives_display_name_change(self):
        r=self.rows[0];self.assertEqual(resource_path(r),resource_path({**r,'name':'A renamed resource'}))
        self.assertEqual(len({resource_path(r) for r in self.rows}),len(self.rows))
    def test_every_page_has_matching_canonical_robots_and_visible_heading(self):
        for item in self.manifest['pages']:
            text=(self.dest/item['path'].lstrip('/')/'index.html').read_text();p=PageParser(text)
            self.assertEqual(p.canonical,[SITE+item['path']],item['path'])
            self.assertEqual(p.heading_count,1,item['path'])
            self.assertEqual('noindex' in p.robots[0],not item['indexable'],item['path'])
            for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>',text,re.S):
                value=json.loads(block);self.assertEqual(value['@context'],'https://schema.org')
    def test_sitemap_excludes_unreviewed_pages_and_has_no_synthetic_lastmod(self):
        root=ET.parse(self.dest/'sitemap.xml').getroot();ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls=[x.text for x in root.findall('s:url/s:loc',ns)]
        expected={SITE+p['path'] for p in self.manifest['pages'] if p['indexable']}
        self.assertEqual(set(urls),expected);self.assertEqual(len(urls),len(set(urls)))
        self.assertFalse(root.findall('s:url/s:lastmod',ns))
        for row in self.rows:self.assertEqual(SITE+resource_path(row) in urls,eligible(row))
        self.assertEqual((self.dest/'sitemap.txt').read_text().splitlines(),urls)
    def test_static_pages_link_to_real_local_destinations(self):
        for item in self.manifest['pages']:
            p=PageParser((self.dest/item['path'].lstrip('/')/'index.html').read_text())
            for link in p.links:
                u=urllib.parse.urlsplit(link)
                if u.scheme or u.netloc:continue
                path=urllib.parse.urlsplit(urllib.parse.urljoin(SITE+item['path'],link)).path
                target=self.dest/path.lstrip('/')
                if path.endswith('/'):target=target/'index.html'
                self.assertTrue(target.exists(),f'{item["path"]} -> {link}')
    def test_homepage_is_useful_without_javascript(self):
        text=(self.dest/'index.html').read_text();p=PageParser(text)
        self.assertIn('/papers/',p.links);self.assertIn('/catalog/',p.links);self.assertIn('/data/',p.links)
        self.assertIn(f'id="stat-resources">{len(self.rows):,}</span>',text)
        self.assertIn('Computer-use agent research and resources',text)
    def test_machine_navigation_and_verified_files_exist(self):
        config=json.loads((ROOT/'data/site-discovery.json').read_text())
        self.assertEqual((self.dest/(config['indexnow_key']+'.txt')).read_text(),config['indexnow_key'])
        self.assertEqual((self.dest/config['google_verification_file']).read_bytes(),(ROOT/'web'/config['google_verification_file']).read_bytes())
        self.assertIn('/papers/',(self.dest/'llms.txt').read_text())
        ET.parse(self.dest/'feed.xml')
        robots=urllib.robotparser.RobotFileParser();robots.parse((self.dest/'robots.txt').read_text().splitlines())
        for bot in ['Googlebot','bingbot','OAI-SearchBot','PerplexityBot','Claude-SearchBot']:
            self.assertTrue(robots.can_fetch(bot,SITE+'/papers/'))
    def test_resource_schema_uses_original_authorship_not_catalog_authorship(self):
        for r in self.rows:
            schema=resource_schema(r)
            self.assertEqual(schema['sameAs'],r['url'])
            if r['authors']:self.assertEqual([a['name'] for a in schema['author']],r['authors'])
            if schema['@type']=='Dataset':self.assertGreaterEqual(len(schema['description']),50)
    def test_reviewed_relationships_are_navigable_in_both_directions(self):
        incoming=incoming_relations(self.rows)
        paper=next(r for r in self.rows if r['id']=='arxiv:2508.09123')
        assets={r['source_id'] for r in incoming[paper['id']]}
        self.assertIn('github:xlang-ai/opencua',assets)
        self.assertTrue(any(r['name']=='AgentNet' and r['id'] in assets for r in self.rows))
        text=(self.dest/resource_path(paper).lstrip('/')/'index.html').read_text()
        self.assertIn('Connected assets',text);self.assertIn('AgentNet',text)
        export=json.loads((self.dest/'downloads/relationships.json').read_text())
        self.assertEqual(export['relation_count'],sum(len(r['relations']) for r in self.rows))
        self.assertTrue(any(e['type']=='documented_by' for e in export['relations']))
        self.assertNotIn('mentions',{e['type'] for e in export['relations']})
    def test_jsonld_and_titles_escape_untrusted_text(self):
        text=page('</script><script>alert(1)</script>','x','/test/','<h1>Test</h1>',{'@type':'CreativeWork','name':'</script><script>alert(1)</script>'})
        blocks=re.findall(r'<script type="application/ld\+json">(.*?)</script>',text,re.S)
        self.assertEqual(len(blocks),1);json.loads(blocks[0])
        self.assertNotIn('<script>alert(1)</script>',text)

    def test_scope_exclusions_keep_traceable_nonindexed_pages_and_archive(self):
        report=json.loads((self.dest/'downloads/exclusions.json').read_text())
        active={row['id'] for row in self.rows}
        archive={json.loads(line)['id'] for line in (self.dest/'downloads/arxiv-archive.jsonl').read_text().splitlines()}
        pages={item['path']:item for item in self.manifest['pages']}
        excluded=[row for row in report['decisions'] if row['status']=='excluded']
        self.assertEqual(len(excluded),report['excluded_records'])
        for row in excluded:
            self.assertNotIn(row['id'],active)
            self.assertIn(row['id'],archive)
            path=resource_path(row);item=pages[path]
            self.assertFalse(item['indexable']);self.assertTrue(item['scope_excluded'])
            content=(self.dest/path.lstrip('/')/'index.html').read_text()
            parsed=PageParser(content)
            self.assertIn('noindex',parsed.robots[0]);self.assertIn(row['url'],parsed.links)
            self.assertIn(html.escape(row['reason'],quote=True),content)
            self.assertIn('excluded from the active CUA catalog',(self.dest/path.lstrip('/')/'index.md').read_text())
        self.assertEqual(self.manifest['excluded_pages'],len(excluded))
        self.assertEqual(self.manifest['metadata_only_pages'],sum(row['review_status']=='metadata_verified' for row in self.rows))


if __name__=='__main__':unittest.main()
