#!/usr/bin/env python3
"""Run one bounded public-source scan and persist an auditable update report."""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET

from catalog import ROOT, DATA, arxiv_entry, fetch, now, read_json, read_jsonl, write_json, write_jsonl


def counts():
    rows=read_jsonl(DATA/'catalog.jsonl')
    return {'resources':len(rows),'bibliographic_records':len(read_jsonl(DATA/'papers.jsonl')),
        'curated_papers':sum(r['kind'] in {'paper','survey'} and r['review_status']=='curated' for r in rows),
        'curated_resources':sum(r['kind'] not in {'paper','survey'} and r['review_status']=='curated' for r in rows),
        'candidates':len(read_jsonl(DATA/'candidates.jsonl'))}


def stage(name,command,timeout=600):
    started=now()
    try:
        result=subprocess.run([sys.executable,*command],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
        print(result.stdout[-6000:],flush=True)
        return {'name':name,'started_at':started,'finished_at':now(),'ok':result.returncode==0,'exit_code':result.returncode,
            'error':result.stdout[-1600:] if result.returncode else None}
    except subprocess.TimeoutExpired:
        return {'name':name,'started_at':started,'finished_at':now(),'ok':False,'error':f'Stage exceeded {timeout} seconds; last verified records retained.'}


def consider_paper(row,records,proposals,observed_at):
    """New metadata is publishable; changed existing identity is queued for review."""
    rid=row['id']
    if rid not in records:
        records[rid]=row
        return True
    fields=['name','authors','published_at','updated_at']
    changes={field:{'current':records[rid].get(field),'observed':row.get(field)} for field in fields if records[rid].get(field)!=row.get(field)}
    if changes:
        previous=proposals.get(rid,{})
        proposals[rid]={'id':rid,'url':row['url'],'review_status':'metadata_change_pending',
            'first_observed_at':previous.get('first_observed_at',observed_at),'last_observed_at':observed_at,
            'changes':changes,'evidence':row['evidence']}
    return False


def recent_papers(config):
    current=dt.datetime.now(dt.timezone.utc)
    begin=current-dt.timedelta(days=config['recent_lookback_days'])
    cutoff=current.strftime('%Y%m%d%H%M');since=begin.strftime('%Y%m%d%H%M')
    terms='ti:"computer use" OR ti:"computer-use" OR ti:"GUI agent" OR ti:"GUI agents" OR ti:"GUI grounding" OR ti:"web agent" OR ti:"browser agent"'
    query=f'({terms}) AND submittedDate:[{since} TO {cutoff}]'
    records={r['id']:r for r in read_jsonl(DATA/'papers.jsonl')}
    candidates={r['id']:r for r in read_jsonl(DATA/'candidates.jsonl')}
    proposals={r['id']:r for r in read_jsonl(DATA/'metadata-updates.jsonl')}
    start=0;total=None;seen=set();new_ids=[];pages=[];warnings=[]
    ceiling=config['recent_max_results']
    while start<ceiling and (total is None or start<total):
        url='https://export.arxiv.org/api/query?'+urllib.parse.urlencode({'search_query':query,'start':start,'max_results':min(200,ceiling-start),'sortBy':'submittedDate','sortOrder':'descending'})
        info,body=fetch(url,refresh=True)
        if not info['ok']:
            pages.append(info);warnings.append(info.get('error','arXiv fetch failed'));break
        try:
            root=ET.fromstring(body)
            total=int(root.findtext('{http://a9.com/-/spec/opensearch/1.1/}totalResults','0'))
            entries=root.findall('{http://www.w3.org/2005/Atom}entry')
            if any('/api/errors' in entry.findtext('{http://www.w3.org/2005/Atom}id','') for entry in entries):
                raise ValueError('arXiv returned an API error entry instead of search results')
        except (ET.ParseError,ValueError) as error:
            pages.append({**info,'ok':False,'error':str(error)});warnings.append(str(error));break
        pages.append({**info,'start':start,'returned':len(entries)})
        for entry in entries:
            row=arxiv_entry(entry,{k:info[k] for k in ('url','retrieved_at','sha256')})
            if not row:continue
            if not row.get('published_at') or row['published_at']>current.date().isoformat():
                warnings.append('Ignored a missing/future publication date: '+row['id']);continue
            if row['published_at']<begin.date().isoformat():
                warnings.append('Ignored an out-of-window search result: '+row['id']);continue
            seen.add(row['id'])
            if consider_paper(row,records,proposals,info['retrieved_at']):new_ids.append(row['id'])
            c=candidates.setdefault(row['id'],{'id':row['id'],'url':row['url'],'provider':'arxiv','first_discovered_at':info['retrieved_at'],'discovered_in':[]})
            c['discovered_in']=[o for o in c['discovered_in'] if o['source_id']!='arxiv-recent-scan']
            c['discovered_in'].append({'source_id':'arxiv-recent-scan','line':None,'section':'Recent title search; relevance awaits review','snapshot_sha256':info['sha256']})
        start+=len(entries)
        if not entries:break
        if start<min(total,ceiling):time.sleep(3.1)
    complete=total is not None and len(seen)==total and bool(pages) and all(p.get('ok') for p in pages)
    if total is not None and not complete:warnings.append(f'Recent search delivered {len(seen)} unique in-window records out of {total} reported; completeness is not claimed.')
    write_jsonl(DATA/'papers.jsonl',records.values());write_jsonl(DATA/'candidates.jsonl',candidates.values());write_jsonl(DATA/'metadata-updates.jsonl',proposals.values())
    report={'query':query,'since_utc':since,'cutoff_utc':cutoff,'reported_total':total,'unique_returned':len(seen),'complete':complete,'pages':pages,'new_ids':new_ids,'warnings':warnings}
    write_json(DATA/'recent-paper-search.json',report)
    return {'name':'recent_arxiv','ok':any(p.get('ok') for p in pages),'complete':complete,'new_count':len(new_ids),'warnings':warnings}


def summarize_phases(phases,source_runs,hf_runs,harvest_failures):
    problems=[]
    for phase in phases:
        if not phase.get('ok'):problems.append(phase['name']+': '+phase.get('error','failed'))
        problems.extend(phase.get('warnings',[]))
    failed_sources=[r['id'] for r in source_runs if not r.get('ok')]
    failed_queries=[r['id'] for r in hf_runs if not r.get('evidence',{}).get('ok') or r.get('parse_error')]
    if failed_sources:problems.append('Discovery sources failed: '+', '.join(failed_sources))
    if failed_queries:problems.append('Paper searches failed: '+', '.join(failed_queries))
    if harvest_failures:problems.append(f'{len(harvest_failures)} arXiv identifiers remain unresolved in this harvest.')
    phase_ok={p['name']:p.get('ok',False) for p in phases}
    usable=(phase_ok.get('discovery') and any(r.get('ok') for r in source_runs)) or (phase_ok.get('huggingface') and any(r.get('evidence',{}).get('ok') for r in hf_runs)) or phase_ok.get('recent_arxiv')
    fatal=not usable or any(p['name'] in {'build','validate'} and not p.get('ok') for p in phases)
    return ('failed' if fatal else 'partial' if problems else 'success'),problems


def run_scan():
    config=read_json(DATA/'scan-config.json')
    if not 1<=config['recent_lookback_days']<=31 or not 1<=config['recent_max_results']<=2000:raise ValueError('Unbounded recent-search configuration')
    started=now();before=counts();old_papers={r['id'] for r in read_jsonl(DATA/'papers.jsonl')};old_candidates={r['id'] for r in read_jsonl(DATA/'candidates.jsonl')}
    phases=[stage('discovery',['scripts/catalog.py','discover','--refresh'],900),stage('huggingface',['scripts/discover_papers.py','--refresh'],360)]
    try:phases.append(recent_papers(config))
    except Exception as error:phases.append({'name':'recent_arxiv','ok':False,'error':str(error)})
    phases.append(stage('harvest',['scripts/catalog.py','harvest','--limit',str(config['harvest_limit'])],600))
    phases.append(stage('build',['scripts/catalog.py','build']))
    phases.append(stage('validate',['scripts/catalog.py','validate']))
    source_runs=read_json(DATA/'discovery-runs.json',[]);hf_runs=read_json(DATA/'research-discovery.json',[])
    status,problems=summarize_phases(phases,source_runs,hf_runs,read_jsonl(DATA/'harvest-failures.jsonl'))
    papers=read_jsonl(DATA/'papers.jsonl');candidates=read_jsonl(DATA/'candidates.jsonl');finished=now()
    new_papers=[{'id':r['id'],'name':r['name'],'url':r['url'],'review_status':'metadata_verified'} for r in papers if r['id'] not in old_papers]
    repo=os.getenv('GITHUB_REPOSITORY','');run_id=os.getenv('GITHUB_RUN_ID','')
    run_url=f'https://github.com/{repo}/actions/runs/{run_id}' if repo and run_id else None
    report={'id':'scan:'+started,'schema_version':1,'status':status,'started_at':started,'finished_at':finished,'run_url':run_url,
        'schedule':{'timezone':config['timezone'],'times_local':config['scan_times_local']},'before':before,'after':counts(),
        'new_papers':new_papers,'new_candidate_count':sum(r['id'] not in old_candidates for r in candidates),
        'pending_metadata_changes':len(read_jsonl(DATA/'metadata-updates.jsonl')),'source_fetches':{'successful':sum(bool(r.get('ok')) for r in source_runs) if phases[0]['ok'] else 0,'total':len(source_runs)},
        'phases':phases,'warnings':problems,'policy':config['policy']}
    write_json(DATA/'scan-status.json',report)
    history=read_jsonl(DATA/'scan-history.jsonl');history.append({k:v for k,v in report.items() if k!='phases'})
    write_jsonl(DATA/'scan-history.jsonl',history[-config['history_limit']:])
    summary=f'Scan {status}: {len(new_papers)} new paper metadata records; {report["new_candidate_count"]} new candidates; {report["after"]["curated_papers"]} reviewed papers.'
    print(summary)
    summary_file=os.getenv('GITHUB_STEP_SUMMARY')
    if summary_file:
        with open(summary_file,'a') as f:
            f.write('## AwesomeCUA scan\n\n'+summary+'\n\n'+f'Scheduled at {", ".join(config["scan_times_local"])} {config["timezone"]}.\n\n')
            f.write('\n'.join('- '+p for p in problems)+'\n')
    return 1 if status=='failed' else 0


if __name__=='__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    raise SystemExit(run_scan())
