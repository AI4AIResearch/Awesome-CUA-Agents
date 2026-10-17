import copy
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build import apply_license_reviews


class LicenseReviewTests(unittest.TestCase):
    def fixture(self):
        card={'url':'https://example.org/model-card','sha256':'a'*64,'retrieved_at':'2026-10-17T00:00:00Z','supports':['licenses.weights']}
        license={'declared':'MIT','url':card['url'],'retrieved_at':card['retrieved_at'],'basis':'Hub header'}
        second={**card,'url':'https://example.org/component-license','sha256':'b'*64}
        editorial={'name':'Mixed bundle','additional_evidence':[second],
            'reviewed_licenses':{'weights':{'value':None,'reason':'The header and component-specific declarations disagree.',
                'evidence_urls':[card['url'],second['url']]}}}
        return editorial,card,{'code':None,'data':None,'weights':license,'document':None}
    def test_conflict_null_overrides_extracted_label_and_retains_evidence(self):
        editorial,receipt,licenses=self.fixture();details={}
        apply_license_reviews(editorial,receipt,licenses,details)
        self.assertIsNone(licenses['weights'])
        self.assertEqual(details['license_review']['weights']['evidence_urls'],editorial['reviewed_licenses']['weights']['evidence_urls'])
        self.assertIn('disagree',details['license_review']['weights']['reason'])
    def test_composite_label_is_bound_to_the_reviewed_component_source(self):
        editorial,receipt,licenses=self.fixture();details={}
        editorial['reviewed_licenses']['weights']['value']={**licenses['weights'],'declared':'Component-specific MIT and AGPL-3.0 terms',
            'url':'https://example.org/component-license','basis':'Separate component licenses; no single license for the bundle.'}
        apply_license_reviews(editorial,receipt,licenses,details)
        self.assertIn('Component-specific',licenses['weights']['declared'])
    def test_missing_or_wrong_scope_receipts_and_unsupported_sources_are_rejected(self):
        for scenario in ['missing','wrong-scope','wrong-value-source','unknown-slot']:
            editorial,receipt,licenses=self.fixture()
            if scenario=='missing':editorial['additional_evidence']=[]
            elif scenario=='wrong-scope':editorial['additional_evidence'][0]['supports']=['licenses.code']
            elif scenario=='wrong-value-source':editorial['reviewed_licenses']['weights']['value']={**licenses['weights'],'url':'https://unreviewed.example/license'}
            else:editorial['reviewed_licenses']['other']=editorial['reviewed_licenses'].pop('weights')
            with self.subTest(scenario=scenario),self.assertRaises(ValueError):apply_license_reviews(editorial,receipt,licenses,{})


if __name__=='__main__':unittest.main()
