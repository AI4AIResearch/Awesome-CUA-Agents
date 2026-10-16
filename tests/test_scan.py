import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import scan
from catalog import write_jsonl


class ScanSafetyTests(unittest.TestCase):
    def row(self,name='Primary title'):
        return {'id':'arxiv:2610.00001','url':'https://arxiv.org/abs/2610.00001','name':name,'authors':['Researcher'],
            'published_at':'2026-10-01','updated_at':'2026-10-02','evidence':[],'review_status':'metadata_verified'}
    def test_new_metadata_does_not_gain_editorial_approval(self):
        records={};proposals={};row=self.row()
        self.assertTrue(scan.consider_paper(row,records,proposals,'2026-10-16T00:00:00Z'))
        self.assertEqual(records[row['id']]['review_status'],'metadata_verified');self.assertEqual(proposals,{})
    def test_changed_existing_metadata_is_queued_without_rewriting_approved_snapshot(self):
        old=self.row();old['review_status']='curated';records={old['id']:copy.deepcopy(old)};proposals={}
        observed=self.row('Updated primary title')
        self.assertFalse(scan.consider_paper(observed,records,proposals,'2026-10-16T00:00:00Z'))
        self.assertEqual(records[old['id']],old)
        self.assertEqual(proposals[old['id']]['review_status'],'metadata_change_pending')
        self.assertEqual(proposals[old['id']]['changes']['name']['observed'],'Updated primary title')
    def test_all_failed_phases_cannot_borrow_old_success_receipts(self):
        phases=[{'name':x,'ok':False} for x in ['discovery','huggingface','recent_arxiv']]
        status,problems=scan.summarize_phases(phases,[{'id':'old','ok':True}],[{'id':'old','evidence':{'ok':True}}],[])
        self.assertEqual(status,'failed');self.assertTrue(problems)
    def test_partial_source_failure_is_reported_separately(self):
        phases=[{'name':'discovery','ok':True},{'name':'validate','ok':True}]
        status,problems=scan.summarize_phases(phases,[{'id':'good','ok':True},{'id':'bad','ok':False}],[],[])
        self.assertEqual(status,'partial');self.assertIn('bad',' '.join(problems))
    def test_validation_failure_prevents_successful_scan_status(self):
        phases=[{'name':'discovery','ok':True},{'name':'validate','ok':False,'error':'invalid record'}]
        status,_=scan.summarize_phases(phases,[{'id':'good','ok':True}],[],[])
        self.assertEqual(status,'failed')
    def test_arxiv_error_feed_cannot_be_counted_as_successful_empty_search(self):
        body=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/api/errors#bad_query</id><title>Error</title></entry></feed>'
        info={'ok':True,'url':'https://export.arxiv.org/api/query','retrieved_at':'2026-10-16T00:00:00Z','sha256':'a'*64}
        with tempfile.TemporaryDirectory() as directory,mock.patch.object(scan,'DATA',Path(directory)),mock.patch.object(scan,'fetch',return_value=(info,body)):
            existing=self.row();write_jsonl(Path(directory)/'papers.jsonl',[existing])
            result=scan.recent_papers({'recent_lookback_days':14,'recent_max_results':100})
            self.assertFalse(result['ok'])
            rows=[json.loads(line) for line in (Path(directory)/'papers.jsonl').read_text().splitlines()]
            self.assertEqual(rows,[existing])


if __name__=='__main__':unittest.main()
