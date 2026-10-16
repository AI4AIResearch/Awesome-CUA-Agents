#!/usr/bin/env python3
"""Build the portable AwesomeCUA site from the committed catalog; no network required."""
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build import validate_records, write_sqlite


def build_site(output=None):
    destination=Path(output) if output else ROOT/'dist'/'site'
    rows=[json.loads(line) for line in (ROOT/'data/catalog.jsonl').read_text().splitlines() if line.strip()]
    coverage=json.loads((ROOT/'data/coverage.json').read_text())
    errors=validate_records(rows)
    if errors:raise ValueError('\n'.join(errors[:10]))
    if len(rows)!=coverage['total_records']:raise ValueError('Catalog/coverage count mismatch; rebuild catalog first.')
    destination.mkdir(parents=True,exist_ok=True)
    for path in (ROOT/'web').iterdir():
        if path.is_file():shutil.copy2(path,destination/path.name)
    (destination/'data').mkdir(exist_ok=True)
    (destination/'downloads').mkdir(exist_ok=True)
    keys=['id','name','kind','url','aliases','environments','topics','summary','review_status','published_at','authors','scope','last_verified_at']
    index={'coverage':{k:coverage[k] for k in ['as_of_utc','total_records','curated_records','metadata_only_records','by_kind','unindexed_candidates','sources']},'records':[{k:row[k] for k in keys} for row in rows]}
    for filename,payload in [('index.json',index),('records.json',rows)]:
        (destination/'data'/filename).write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n')
    for name in ['catalog.jsonl','coverage.json','sources.json']:
        shutil.copy2(ROOT/'data'/name,destination/'downloads'/name)
    write_sqlite(rows,destination/'downloads'/'catalog.sqlite')
    shutil.copy2(ROOT/'LICENSE',destination/'LICENSE')
    (destination/'.nojekyll').write_text('')
    (destination/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: https://awesomecua.github.io/sitemap.xml\n')
    (destination/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://awesomecua.github.io/</loc><lastmod>'+coverage['as_of_utc'][:10]+'</lastmod></url></urlset>\n')
    print(f'Built {len(rows):,} searchable resources → {destination}')
    return destination


if __name__=='__main__':build_site(sys.argv[1] if len(sys.argv)>1 else None)
