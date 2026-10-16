#!/usr/bin/env python3
"""Discover paper candidates with Hugging Face Papers; arXiv harvest remains authoritative."""
import argparse
import json
import re
import urllib.parse
from catalog import DATA, canonical, fetch, read_json, read_jsonl, write_json, write_jsonl

DEFAULT_QUERIES=['computer use agents','GUI grounding benchmark','mobile GUI agent reinforcement learning','web agent dataset benchmark','computer use agent safety','GUI agent memory planning']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--query',action='append',help='Repeat for multiple discovery queries.')
    parser.add_argument('--limit',type=int,default=30)
    parser.add_argument('--refresh',action='store_true')
    args=parser.parse_args()
    if not 1<=args.limit<=120:parser.error('--limit must be 1..120')
    rows={r['id']:r for r in read_jsonl(DATA/'candidates.jsonl')}
    papers={r['id'] for r in read_jsonl(DATA/'papers.jsonl')}
    runs={r['id']:r for r in read_json(DATA/'research-discovery.json',[])}
    found=set()
    for query in args.query or DEFAULT_QUERIES:
        if len(query)>250:parser.error('Query must not exceed 250 characters.')
        sid='hf-search-'+re.sub('[^a-z0-9]+','-',query.lower())
        endpoint='https://huggingface.co/api/papers/search?'+urllib.parse.urlencode({'q':query,'limit':args.limit})
        info,body=fetch(endpoint,args.refresh)
        run={'id':sid,'query':query,'provider':'huggingface_papers_search','limit':args.limit,'scope':'ranked search window, not exhaustive','evidence':info,'identifiers':[]}
        if info['ok']:
            try:
                for hit in json.loads(body):
                    paper=hit.get('paper',hit);parsed=canonical('https://arxiv.org/abs/'+paper.get('id',''))
                    if not parsed or parsed[2]!='arxiv':continue
                    rid,url,_=parsed;found.add(rid);run['identifiers'].append(rid)
                    row=rows.setdefault(rid,{'id':rid,'url':url,'provider':'arxiv','first_discovered_at':info['retrieved_at'],'discovered_in':[]})
                    row['discovered_in']=[o for o in row['discovered_in'] if o['source_id']!=sid]
                    row['discovered_in'].append({'source_id':sid,'line':None,'section':query,'snapshot_sha256':info['sha256']})
            except (ValueError,AttributeError,TypeError) as error:run['parse_error']=str(error)
        runs[sid]=run
        print(f'{query}: {len(run["identifiers"])} discovery results',flush=True)
    write_jsonl(DATA/'candidates.jsonl',rows.values());write_json(DATA/'research-discovery.json',sorted(runs.values(),key=lambda x:x['id']))
    print(f'{len(found)} unique hits; {len(found-papers)} lack arXiv metadata. Run scripts/catalog.py harvest next.')


if __name__=='__main__':main()
