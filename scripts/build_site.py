#!/usr/bin/env python3
"""Build the portable AwesomeCUA site from the committed catalog; no network required."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build import validate_records, write_sqlite
from search_pages import build_search_pages, resource_path
from export_rag import build_exports
from export_citations import build_citation_exports
from site_files import reconcile_generated_pages
from publication_metadata import record_date_parts, record_date_text, publication_search_text


def version_script_imports(destination):
    # Version dependencies before hashing their consumers for the generated HTML.
    core_version=hashlib.sha256((destination/'catalog-core.js').read_bytes()).hexdigest().encode()
    pattern=rb"(\bfrom\s*)(['\"])\./catalog-core\.js(?:\?[^'\"\r\n]*)?\2"
    for name in ('app.js','compare.js'):
        target=destination/name
        content=re.sub(pattern,lambda m:m[1]+m[2]+b'./catalog-core.js?v='+core_version+m[2],target.read_bytes())
        target.write_bytes(content)


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
    version_script_imports(destination)
    (destination/'data').mkdir(exist_ok=True)
    (destination/'downloads').mkdir(exist_ok=True)
    (destination/'schemas').mkdir(exist_ok=True)
    for contract in ('resource.schema.json','scope-decision.schema.json','publication-observation.schema.json'):
        shutil.copy2(ROOT/'schemas'/contract,destination/'schemas'/contract)
    keys=['id','name','kind','url','aliases','environments','topics','summary','review_status','published_at','authors','scope','last_verified_at']
    related={row['id']:set() for row in rows}
    incoming={row['id']:[] for row in rows}
    for row in rows:
        for relation in row['relations']:
            if relation['target_id'] in related:
                related[relation['target_id']].add(row['id']);related[row['id']].add(relation['target_id'])
                incoming[relation['target_id']].append({'source_id':row['id'],'type':relation['type'],'evidence_url':relation['evidence_url']})
    index={'coverage':{k:coverage[k] for k in ['as_of_utc','total_records','curated_records','metadata_only_records','by_kind','unindexed_candidates','sources','excluded_records','arxiv_archive_records']},'records':[{**{k:row[k] for k in keys},'page_url':resource_path(row),
        'paper_version':row.get('details',{}).get('arxiv_snapshot',{}).get('version'),
        'paper_source_url':row.get('details',{}).get('arxiv_snapshot',{}).get('versioned_url'),
        'paper_date':record_date_text(row),
        'paper_date_precision':{1:'year',2:'month',3:'day'}.get(len(record_date_parts(row) or [])),
        'publication_search_text':publication_search_text(row),
        'related_count':len(related[row['id']]),'incoming_relations':incoming[row['id']]} for row in rows]}
    for filename,payload in [('index.json',index),('records.json',rows)]:
        (destination/'data'/filename).write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n')
    for name in ['catalog.jsonl','coverage.json','sources.json']:
        shutil.copy2(ROOT/'data'/name,destination/'downloads'/name)
    shutil.copy2(ROOT/'data/exclusion-status.json',destination/'downloads/exclusions.json')
    shutil.copy2(ROOT/'data/papers.jsonl',destination/'downloads/arxiv-archive.jsonl')
    (destination/'downloads/publications.jsonl').write_bytes((ROOT/'data/publications.jsonl').read_bytes() if (ROOT/'data/publications.jsonl').exists() else b'')
    write_sqlite(rows,destination/'downloads'/'catalog.sqlite')
    build_exports(rows,destination/'downloads',(ROOT/'data/catalog.jsonl').read_bytes())
    build_citation_exports(rows,destination/'downloads',(ROOT/'data/catalog.jsonl').read_bytes())
    shutil.copy2(ROOT/'AGENTS.md',destination/'AGENTS.md')
    for name in ('paper-discovery-queries.json','paper-discovery-status.json','conference-discovery.json'):
        if (ROOT/'data'/name).exists():shutil.copy2(ROOT/'data'/name,destination/'downloads'/name)
    shutil.copy2(ROOT/'LICENSE',destination/'LICENSE')
    (destination/'.nojekyll').write_text('')
    manifest=build_search_pages(destination,rows,coverage,ROOT)
    reconcile_generated_pages(destination,manifest)
    print(f'Built {len(rows):,} searchable resources and {sum(x["indexable"] for x in manifest)} indexable HTML pages → {destination}')
    return destination


if __name__=='__main__':build_site(sys.argv[1] if len(sys.argv)>1 else None)
