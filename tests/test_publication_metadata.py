import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build
from catalog import canonical, publication_identity, write_json, write_jsonl
from export_citations import citation_csl
from export_rag import documents as rag_documents
from paper_library import paper_library
from publication_metadata import (attach_publications, checked_date_parts, format_date_parts,
    publication_aliases, record_date_text, validate_publication)
from scope_review import metadata_fingerprint, resolve_exclusions
from search_pages import description, resource_path, resource_schema


def arxiv_record():
    identity='arxiv:2001.00001'
    return {'id':identity,'name':'Retained preprint title','kind':'paper',
        'url':'https://arxiv.org/abs/2001.00001','authors':['Original Author'],
        'published_at':'2020-01-02','updated_at':'2020-02-03','last_verified_at':'2024-01-01T00:00:00Z',
        'identifiers':{'arxiv':'2001.00001'},'aliases':[], 'environments':['unspecified'], 'topics':[],
        'scope':'relevance_pending','review_status':'metadata_verified','summary':None,
        'links':[{'rel':'primary','url':'https://arxiv.org/abs/2001.00001'}], 'relations':[],
        'licenses':{key:None for key in ('code','data','weights','document')},'notes':'',
        'evidence':[{'role':'primary','method':'arxiv_api','supports':['name','authors','published_at','identifiers.arxiv','details.arxiv_snapshot'],
                     'url':'https://export.arxiv.org/api/query?id_list=2001.00001','sha256':'a'*64,'retrieved_at':'2024-01-01T00:00:00Z'}],
        'details':{'arxiv_snapshot':{'version':2,'versioned_url':'https://arxiv.org/abs/2001.00001v2',
            'submitted_at':'2020-01-02T00:00:00Z','updated_at':'2020-02-03T00:00:00Z',
            'abstract_sha256':'b'*64,'abstract_hash_method':'sha256-utf8-whitespace-collapsed-v1'}}}


def observation(parts=None, *, url='https://publisher.example/paper', target=None, doi=None):
    parts=[2017] if parts is None else parts
    return {'id':target or publication_identity(url)[0],
        'publication':{'type':'conference-paper','title':'Published source title','authors':['Éva Example','Second Author'],
            'date_parts':parts,'venue':'Proceedings of Example Conference','publisher':'Example Publisher',
            'url':url,'pdf_url':url+'.pdf','doi':doi,'evidence_urls':[url]},
        'evidence':[{'role':'primary','method':'editorial_primary_review','supports':['details.publication'],
                     'url':url,'sha256':'c'*64,'retrieved_at':'2026-10-17T00:00:00Z'}],
        'last_verified_at':'2026-10-17T00:00:00Z'}


class PublicationMetadataTests(unittest.TestCase):
    def test_date_precision_and_actual_calendar_validation(self):
        for parts, rendered in [([2017],'2017'),([2017,8],'2017-08'),([2024,2,29],'2024-02-29')]:
            self.assertEqual(checked_date_parts(parts),parts)
            self.assertEqual(format_date_parts(parts),rendered)
        self.assertEqual(format_date_parts(None),'')
        for invalid in [[],[2024,0],[2024,13],[2023,2,29],[2024,1,0],[2024,None,2],[True],[2024,1,1,2],['2024']]:
            with self.subTest(parts=invalid),self.assertRaises(ValueError):checked_date_parts(invalid)

    def test_publisher_partial_dates_survive_record_library_schema_citations_and_rag(self):
        for parts in ([2017],[2017,8],[2017,8,10]):
            incoming=observation(parts)
            row=attach_publications({},[incoming],publication_identity)[incoming['id']]
            self.assertEqual(row['authors'],incoming['publication']['authors'])
            self.assertEqual(row['published_at'],'2017-08-10' if len(parts)==3 else None)
            self.assertEqual(row['review_status'],'metadata_verified')
            self.assertNotIn('arXiv',description(row))
            self.assertEqual(citation_csl(row)['issued']['date-parts'],[parts])
            self.assertEqual('datePublished' in resource_schema(row),len(parts)==3)
            row.update(review_status='curated',scope='core',summary='Original annotation.')
            markup,itemlist=paper_library([row],resource_path)
            self.assertIn('id="papers-2017"',markup)
            self.assertEqual(itemlist['numberOfItems'],1)
            self.assertNotIn('2017-01-01',markup)
            document=next(rag_documents([row]))
            self.assertEqual(document['metadata']['publication'],incoming['publication'])
            self.assertIn(format_date_parts(parts),document['text'])
            self.assertNotIn('2017-01-01',document['text'])

    def test_arxiv_attachment_changes_neither_canonical_facts_nor_review_state(self):
        original=arxiv_record();before=copy.deepcopy(original)
        incoming=observation([2025,7],target=original['id'],doi='10.1234/Published')
        row=attach_publications({original['id']:original},[incoming],publication_identity)[original['id']]
        self.assertEqual(original,before)
        for key in ('id','name','authors','published_at','updated_at','identifiers','review_status','scope'):
            self.assertEqual(row[key],before[key])
        self.assertEqual(row['details']['arxiv_snapshot'],before['details']['arxiv_snapshot'])
        self.assertEqual(record_date_text(row),'2020-01-02')
        self.assertFalse(validate_publication(row))  # Publication's 2026 receipt, not old arXiv check, bounds its date.
        retained,published=citation_csl(row),citation_csl(row,edition='publication')
        self.assertEqual(retained['title'],before['name'])
        self.assertEqual(retained['issued']['date-parts'],[[2020,1,2]])
        self.assertEqual(retained['URL'],'https://arxiv.org/abs/2001.00001v2')
        self.assertNotIn('DOI',retained)
        self.assertEqual(published['title'],incoming['publication']['title'])
        self.assertEqual(published['issued']['date-parts'],[[2025,7]])
        self.assertEqual(published['DOI'],'10.1234/Published')
        self.assertNotIn('version',published)

    def test_identity_collision_gates_use_the_entire_archive(self):
        old=arxiv_record();old['identifiers']['doi']='10.1234/EXAMPLE'
        with self.assertRaisesRegex(ValueError,'already represented'):
            attach_publications({old['id']:old},[observation(doi='10.1234/example')],publication_identity)
        with self.assertRaisesRegex(ValueError,'unretained'):
            attach_publications({},[observation(target=old['id'])],publication_identity)
        incoming=observation();incoming['publication']['pdf_url']='https://arxiv.org/pdf/2001.00001'
        with self.assertRaisesRegex(ValueError,'arXiv identity'):
            attach_publications({old['id']:old},[incoming],publication_identity)
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            attach_publications({},[observation(),observation()],publication_identity)

    def test_materializer_keeps_publication_facts_separate_from_editorial_approval(self):
        old=arxiv_record();attachment=observation([2025,7],target=old['id'])
        addition=observation([2017],url='https://publisher.example/survey')
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)
            write_jsonl(directory/'papers.jsonl',[old]);write_jsonl(directory/'publications.jsonl',[attachment,addition])
            with mock.patch.object(build,'DATA',directory):
                before,_=build.source_records()
                self.assertTrue(all(row['review_status']=='metadata_verified' for row in before))
                write_json(directory/'editorial.json',[{'name':addition['publication']['title'],'url':addition['publication']['url'],
                    'kind':'survey','editorial_reviewed':True,'reviewed_sha256':'c'*64,'summary':'Reviewed survey annotation.',
                    'scope':'core','environments':['web'],'topics':['survey']}])
                write_jsonl(directory/'primary-evidence.jsonl',[{'id':addition['id'],'content_matched':True,'sha256':'c'*64,
                    'url':addition['publication']['url'],'retrieved_at':'2026-10-17T00:00:00Z'}])
                after,_=build.source_records()
        indexed={row['id']:row for row in after}
        self.assertEqual(indexed[old['id']]['review_status'],'metadata_verified')
        self.assertEqual(indexed[old['id']]['authors'],old['authors'])
        self.assertEqual(indexed[addition['id']]['review_status'],'curated')
        self.assertEqual(indexed[addition['id']]['kind'],'survey')
        self.assertEqual(indexed[addition['id']]['authors'],addition['publication']['authors'])
        self.assertEqual(indexed[addition['id']]['details']['publication'],addition['publication'])
        self.assertFalse(build.validate_records(after))

    def test_excluded_work_cannot_reenter_through_an_editorial_publisher_alias(self):
        old=arxiv_record();incoming=observation(target=old['id'])
        receipt=old['evidence'][0]
        decision={'id':old['id'],'name':old['name'],'url':old['url'],'decision':'out_of_scope',
            'basis':'primary_abstract_review','reason':'Fixture scope exclusion.','reviewed_at':'2024-01-01T00:00:00Z',
            'metadata_fingerprint':metadata_fingerprint(old),'evidence':{key:receipt[key] for key in ('url','sha256','retrieved_at')}}
        attached=attach_publications({old['id']:old},[incoming],publication_identity)
        self.assertEqual(resolve_exclusions(attached,[decision],set())[0]['status'],'excluded')
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)
            write_jsonl(directory/'papers.jsonl',[old]);write_jsonl(directory/'publications.jsonl',[incoming])
            alias=publication_identity(incoming['publication']['url'])[0]
            write_json(directory/'editorial.json',[{'name':'Alias bypass','url':incoming['publication']['url'],
                'kind':'paper','editorial_reviewed':True,'reviewed_sha256':'c'*64,'summary':'A duplicate alias.',
                'scope':'core','environments':['web'],'topics':[]}])
            write_jsonl(directory/'primary-evidence.jsonl',[{'id':alias,'content_matched':True,'sha256':'c'*64}])
            write_json(directory/'exclusions.json',[decision])
            with mock.patch.object(build,'DATA',directory),self.assertRaisesRegex(ValueError,'canonical publication resource'):
                build.source_records()

    def test_doi_opt_in_and_openreview_query_identity(self):
        a='https://doi.org/10.1234/ABC(DEF)'
        b='http://dx.doi.org/10.1234/abc%28def%29'
        self.assertIsNone(canonical(a))
        self.assertEqual(publication_identity(a),publication_identity(b))
        self.assertTrue(publication_identity(a)[1].endswith('abc(def)'))
        for invalid in ['https://doi.org/not-a-doi','https://doi.org/10.1234/','https://user@doi.org/10.1234/x']:
            self.assertIsNone(publication_identity(invalid))
        entry=observation(url='https://openreview.net/forum?id=paper-a')
        entry['publication']['pdf_url']='https://openreview.net/pdf?id=paper-a'
        aliases=publication_aliases([entry],publication_identity)
        self.assertEqual(aliases[publication_identity(entry['publication']['pdf_url'])[0]],entry['id'])
        self.assertNotIn(publication_identity('https://openreview.net/forum?id=paper-b')[0],aliases)

    def test_same_source_multiple_scopes_and_malformed_shapes(self):
        entry=observation();row=attach_publications({},[entry],publication_identity)[entry['id']]
        row['evidence'].append({**row['evidence'][0],'supports':['summary']})
        self.assertFalse(validate_publication(row))
        for path,value in [('type',[]),('authors',None),('url',[]),('pdf_url',[])]:
            bad=copy.deepcopy(entry);bad['publication'][path]=value
            with self.subTest(field=path),self.assertRaises(ValueError):attach_publications({},[bad],publication_identity)
        bad=copy.deepcopy(entry);bad['evidence'][0]['url']=[]
        with self.assertRaises(ValueError):attach_publications({},[bad],publication_identity)

    def test_source_alias_coverage_and_generic_paper_relation(self):
        old=arxiv_record();entry=observation(target=old['id'])
        row=attach_publications({old['id']:old},[entry],publication_identity)[old['id']]
        row.update(review_status='curated',scope='core',summary='Reviewed annotation.')
        raw_ids=[publication_identity(entry['publication'][key])[0] for key in ('url','pdf_url')]
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)
            write_jsonl(directory/'papers.jsonl',[old]);write_jsonl(directory/'publications.jsonl',[entry])
            write_jsonl(directory/'candidates.jsonl',[{'id':identity,'discovered_in':[{'source_id':'fixture'}]} for identity in raw_ids])
            write_json(directory/'sources.json',[{'id':'fixture','name':'Fixture','homepage':'https://publisher.example'}])
            with mock.patch.object(build,'DATA',directory):report=build.coverage([row],[],[])
        source=report['sources'][0]
        self.assertEqual((source['discovered'],source['indexed'],source['indexed_resources'],source['unindexed']),(2,2,1,0))
        publisher=observation([2017]);paper=attach_publications({},[publisher],publication_identity)[publisher['id']]
        asset={'relations':[{'type':'documented_by','target_id':paper['id']}]}
        self.assertIn(paper['url'],build.paper_cell(asset,{paper['id']:paper}))
        self.assertIn('(2017)',build.paper_cell(asset,{paper['id']:paper}))


if __name__=='__main__':unittest.main()
