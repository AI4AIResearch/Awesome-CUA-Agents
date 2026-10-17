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

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build
import catalog
import scope_review
from test_catalog import paper


def decision(row):
    return {'id':row['id'],'name':row['name'],'url':row['url'],'decision':'out_of_scope',
        'basis':'primary_abstract_review','reason':'An explicitly reviewed test scope decision.',
        'reviewed_at':'2026-10-16T01:00:00Z','metadata_fingerprint':scope_review.metadata_fingerprint(row),
        'evidence':{key:row['evidence'][0][key] for key in ['url','sha256','retrieved_at']}}


class ScopeDecisionTests(unittest.TestCase):
    def test_no_keyword_based_exclusion_and_no_input_mutation(self):
        row=paper();row['name']='Quantum computing using a GUI agent';records={row['id']:row};original=copy.deepcopy(records)
        self.assertEqual(scope_review.resolve_exclusions(records,[]),[])
        result=scope_review.resolve_exclusions(records,[decision(row)])
        self.assertEqual(result[0]['status'],'excluded')
        self.assertEqual(records,original)

    def test_changed_metadata_evidence_or_observation_reopens_review(self):
        for change in ['title','receipt','observed']:
            with self.subTest(change=change):
                row=paper();d=decision(row);observed=set()
                if change=='title':row['name']='New primary title'
                if change=='receipt':row['evidence'][0]['sha256']='b'*64
                if change=='observed':observed.add(row['id'])
                result=scope_review.resolve_exclusions({row['id']:row},[d],observed)
                self.assertEqual(result[0]['status'],'revalidation_pending')

    def test_curated_inclusion_and_retained_relationships_cannot_be_silently_removed(self):
        row=paper();d=decision(row);row['review_status']='curated'
        with self.assertRaisesRegex(ValueError,'curated inclusion'):
            scope_review.resolve_exclusions({row['id']:row},[d])
        row['review_status']='metadata_verified'
        dependent={'id':'github:example/agent','review_status':'curated','relations':[{'target_id':row['id']}],'identifiers':{}}
        with self.assertRaisesRegex(ValueError,'relationships depend'):
            scope_review.resolve_exclusions({row['id']:row,dependent['id']:dependent},[d])

    def test_invalid_review_missing_record_and_duplicate_decisions_fail(self):
        row=paper();d=decision(row)
        for bad in [{**d,'reason':''},{**d,'reviewed_at':'2026-10-15T00:00:00Z'},{**d,'basis':'keyword_match'}]:
            with self.assertRaises(ValueError):scope_review.resolve_exclusions({row['id']:row},[bad])
        with self.assertRaisesRegex(ValueError,'no retained'):scope_review.resolve_exclusions({},[d])
        with self.assertRaisesRegex(ValueError,'duplicate'):scope_review.resolve_exclusions({row['id']:row},[d,d])

    def test_materialization_preserves_archive_and_stale_decisions_return(self):
        with tempfile.TemporaryDirectory() as directory,mock.patch.object(build,'DATA',Path(directory)):
            row=paper();archive=Path(directory)/'papers.jsonl'
            catalog.write_jsonl(archive,[row]);original=archive.read_bytes()
            catalog.write_json(Path(directory)/'exclusions.json',[decision(row)])
            rows,pending,outcomes=build.source_records(with_scope=True)
            self.assertEqual(rows,[]);self.assertEqual(pending,[]);self.assertEqual(outcomes[0]['status'],'excluded')
            self.assertEqual(archive.read_bytes(),original)
            catalog.write_jsonl(Path(directory)/'metadata-updates.jsonl',[{'id':row['id']}])
            rows,pending,outcomes=build.source_records(with_scope=True)
            self.assertEqual([r['id'] for r in rows],[row['id']])
            self.assertEqual(pending[0]['id'],row['id'])
            self.assertEqual(outcomes[0]['status'],'revalidation_pending')
            self.assertEqual(archive.read_bytes(),original)

    def test_coverage_distinguishes_excluded_from_unresolved(self):
        with tempfile.TemporaryDirectory() as directory,mock.patch.object(build,'DATA',Path(directory)):
            row=paper();catalog.write_jsonl(Path(directory)/'papers.jsonl',[row])
            catalog.write_json(Path(directory)/'sources.json',[{'id':'source','name':'Test','homepage':'https://example.org'}])
            catalog.write_jsonl(Path(directory)/'candidates.jsonl',[{'id':row['id'],'discovered_in':[{'source_id':'source'}]},{'id':'arxiv:9999.99999','discovered_in':[{'source_id':'source'}]}])
            outcomes=scope_review.resolve_exclusions({row['id']:row},[decision(row)])
            report=build.coverage([],[],outcomes)
            self.assertEqual(report['excluded_records'],1)
            self.assertEqual(report['arxiv_archive_records'],1)
            self.assertEqual(report['unindexed_candidates'],1)
            self.assertEqual(report['sources'][0]['excluded'],1)
            self.assertEqual(report['sources'][0]['unindexed'],1)


if __name__=='__main__':unittest.main()
