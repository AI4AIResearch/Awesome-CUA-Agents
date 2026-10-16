#!/usr/bin/env python3
"""Submit published, indexable URLs to IndexNow. Default is a dry run, not a submission."""
import argparse
import datetime as dt
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--submit',action='store_true');args=parser.parse_args()
    config=json.loads((ROOT/'data/site-discovery.json').read_text());site=config['site_url'].rstrip('/');key=config['indexnow_key']
    ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    urls=[e.text for e in ET.parse(ROOT/'dist/site/sitemap.xml').findall('s:url/s:loc',ns)]
    host=urllib.parse.urlsplit(site).netloc
    if not urls or len(urls)>10000 or any(urllib.parse.urlsplit(u).netloc!=host for u in urls):raise ValueError('Invalid or unbounded submission population')
    if not args.submit:
        print(f'Dry run: {len(urls)} indexable URLs on {host}. Use --submit only after this exact build is live.');return
    with urllib.request.urlopen(site+'/'+key+'.txt',timeout=30) as response:
        if response.read().decode().strip()!=key:raise ValueError('Public ownership key does not match')
    with urllib.request.urlopen(site+'/data/search-manifest.json',timeout=30) as response:live=json.load(response)
    local=json.loads((ROOT/'dist/site/data/search-manifest.json').read_text())
    if live!=local:raise ValueError('Live site does not match the verified local build; refusing to submit stale URLs')
    payload={'host':host,'key':key,'keyLocation':site+'/'+key+'.txt','urlList':urls}
    request=urllib.request.Request('https://api.indexnow.org/indexnow',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json; charset=utf-8','User-Agent':'AwesomeCUA-indexing/1.0'},method='POST')
    status=None;body=''
    try:
        with urllib.request.urlopen(request,timeout=40) as response:status=response.status;body=response.read(2000).decode(errors='replace')
    except urllib.error.HTTPError as error:status=error.code;body=error.read(2000).decode(errors='replace')
    except urllib.error.URLError as error:body=str(error)
    receipt={'submitted_at':dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),'provider':'IndexNow','endpoint':'https://api.indexnow.org/indexnow','site':site,'status':status,'url_count':len(urls),'urls':urls,'response':body,'meaning':{200:'Submission accepted; indexing is not guaranteed.',202:'URLs received; ownership-key validation pending.'}.get(status,'Submission not confirmed; inspect the response before retrying.')}
    path=ROOT/'data/search-submissions.json';receipts=json.loads(path.read_text()) if path.exists() else [];receipts.append(receipt);path.write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n')
    print(f'IndexNow HTTP {status}: {len(urls)} URLs. {receipt["meaning"]}')
    if status not in {200,202}:raise SystemExit(1)


if __name__=='__main__':main()
