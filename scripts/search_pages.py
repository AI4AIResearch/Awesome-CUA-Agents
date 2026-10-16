"""Server-rendered, evidence-backed discovery pages for the static website."""
from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

SITE = "https://awesomecua.github.io"
REPO = "https://github.com/AwesomeCUA/awesomecua.github.io"
KINDS = {"paper":"Research papers", "survey":"Surveys", "model":"Models and checkpoints", "dataset":"Datasets", "benchmark":"Benchmarks", "agent":"Agents", "framework":"Frameworks", "infrastructure":"Infrastructure", "tool":"Tools", "product":"Products", "company":"Publishers"}


def esc(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def resource_path(record):
    # IDs, rather than mutable display names, keep permalinks stable through renames.
    slug = re.sub(r"[^a-z0-9]+", "-", record["id"].lower()).strip("-")
    return f"/resources/{slug}/"


def eligible(record):
    return record["review_status"] == "curated" and record["scope"] in {"core", "adjacent"}


def description(record):
    return record.get("summary") or f"Bibliographic record for {record['name']}. Title, authors and dates checked against arXiv; relevance and findings await editorial review."


def jsonld(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def organization():
    return {"@type":"Organization", "@id":SITE+"/#organization", "name":"AwesomeCUA", "url":SITE+"/", "sameAs":["https://github.com/AwesomeCUA", REPO]}


def page(title, summary, path, body, main=None, index=True, lang="en", alternatives=False):
    url=SITE+path
    graph=[organization(), {"@type":"WebPage", "@id":url+"#page", "url":url, "name":title, "description":summary, "inLanguage":lang, "isPartOf":{"@id":SITE+"/#website"}, "publisher":{"@id":SITE+"/#organization"}}]
    if main:
        main={"@id":url+"#entity", **main}
        graph.append(main);graph[1]["mainEntity"]={"@id":main["@id"]}
    if path!="/":
        graph.append({"@type":"BreadcrumbList", "itemListElement":[{"@type":"ListItem","position":1,"name":"AwesomeCUA","item":SITE+"/"},{"@type":"ListItem","position":2,"name":title,"item":url}]})
    alternate=f'<link rel="alternate" hreflang="en" href="{SITE}/"><link rel="alternate" hreflang="zh-CN" href="{SITE}/zh/"><link rel="alternate" hreflang="x-default" href="{SITE}/">' if alternatives else ""
    robots="index,follow,max-image-preview:large" if index else "noindex,follow"
    return f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} | AwesomeCUA</title><meta name="description" content="{esc(summary[:300])}"><meta name="robots" content="{robots}"><link rel="canonical" href="{url}">{alternate}<meta property="og:title" content="{esc(title)} | AwesomeCUA"><meta property="og:description" content="{esc(summary[:300])}"><meta property="og:url" content="{url}"><meta property="og:type" content="website"><meta property="og:image" content="{SITE}/social.svg"><meta name="twitter:card" content="summary_large_image"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/pages.css"><link rel="alternate" type="application/atom+xml" href="/feed.xml" title="AwesomeCUA research updates"><script type="application/ld+json">{jsonld({"@context":"https://schema.org","@graph":graph})}</script></head><body><a class="skip-link" href="#content">Skip to content</a><header class="site-header"><div class="header-inner"><a class="brand" href="/"><img src="/favicon.svg" width="32" height="32" alt=""><span>Awesome<span class="brand-cua">CUA</span></span></a><nav aria-label="Main navigation"><a href="/catalog/">Catalog</a><a href="/papers/">Papers</a><a href="/guides/">Guides</a><a href="/data/">Data</a></nav><a class="github-link" href="{REPO}">GitHub ↗</a></div></header><main id="content" class="reading-shell"><div class="breadcrumbs"><a href="/">AwesomeCUA</a> / <a href="/catalog/">Catalog</a></div>{body}</main><footer class="shell"><a class="brand" href="/">AwesomeCUA</a><a href="/about/">Editorial policy</a><a href="/coverage/">Coverage</a><a href="/data/">Download data</a><a href="/llms.txt">Machine-readable guide</a><a href="https://github.com/AwesomeCUA">GitHub organization ↗</a></footer></body></html>'''


def resource_schema(record):
    entity={"@type":"ScholarlyArticle" if record["kind"] in {"paper","survey"} else "CreativeWork", "name":record["name"], "description":description(record), "url":SITE+resource_path(record), "sameAs":record["url"], "identifier":record["id"]}
    if record["authors"]:entity["author"]=[{"@type":"Person","name":name} for name in record["authors"]]
    if record["published_at"]:entity["datePublished"]=record["published_at"]
    if record["updated_at"]:entity["dateModified"]=record["updated_at"]
    if record["topics"]:entity["keywords"]=record["topics"]
    if record["kind"]=="dataset" and len(description(record))>=50:entity["@type"]="Dataset"
    return entity


def listing(rows):
    return '<div class="reading-list">'+"".join(f'<article><div class="list-overline">{esc(KINDS[r["kind"]])} · {esc(r["review_status"])}</div><h2><a href="{resource_path(r)}">{esc(r["name"])}</a></h2><p>{esc(description(r))}</p><small>{esc(r.get("published_at") or "Release date not recorded")} · {esc(", ".join(r["environments"]))}</small></article>' for r in rows)+'</div>'


def incoming_relations(rows):
    incoming=defaultdict(list)
    for source in rows:
        for relation in source['relations']:
            incoming[relation['target_id']].append({'source_id':source['id'],**relation})
    return incoming


def resource_body(record, lookup, incoming=None):
    r=record
    status="AI-assisted editorial review against a primary source" if eligible(r) else "Bibliographic metadata verified; topic relevance and research findings have not been reviewed"
    body=f'<div class="eyebrow">{esc(KINDS[r["kind"]])}</div><h1>{esc(r["name"])}</h1><p class="answer-lead">{esc(description(r))}</p><p class="review-notice">{esc(status)}. This is a catalog annotation, not an independent reproduction or endorsement.</p><div class="page-actions"><a class="button primary" href="{esc(r["url"])}">Original source ↗</a><a class="button secondary" href="{resource_path(r)}index.md">Read as Markdown</a></div>'
    facts=[("Resource type",KINDS[r["kind"]]),("Environment",", ".join(r["environments"])),("Topics",", ".join(r["topics"]) or "Not assigned"),("Publication date",r["published_at"] or "Not recorded"),("Evidence retrieved",r["last_verified_at"]),("Resource ID",r["id"])]
    body+='<h2>What is this resource?</h2><dl class="page-facts">'+''.join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k,v in facts)+'</dl>'
    if r["authors"]:body+='<h2>Authors</h2><p>'+esc(', '.join(r["authors"]))+'</p>'
    if r["kind"] not in {"paper","survey"}:
        body+='<h2>What licenses are recorded?</h2><p>Code, training data, weights, and documents can have different terms. A blank declaration means unknown, not unrestricted use.</p><dl class="page-facts">'
        for slot,l in r["licenses"].items():
            value=f'<a href="{esc(l["url"])}">{esc(l["declared"] if isinstance(l["declared"],str) else ", ".join(l["declared"]))}</a> ({esc(l["basis"])})' if l else "Not recorded"
            body+=f'<div><dt>{esc(slot.title())}</dt><dd>{value}</dd></div>'
        body+='</dl>'
    details=[(k,v) for k,v in r["details"].items() if v is not None and v!=[] and v!=""]
    if details:
        body+='<h2>Recorded specifications</h2><dl class="page-facts">'+''.join(f'<div><dt>{esc(k.replace("_"," "))}</dt><dd>{esc(json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list,bool)) else v)}</dd></div>' for k,v in details)+'</dl>'
    if r["notes"]:body+='<h2>Scope and limitations</h2><p>'+esc(r["notes"])+'</p>'
    if r["relations"]:
        body+='<h2>Related resources</h2><ul>'+''.join(f'<li>{esc(rel["type"].replace("_"," "))}: <a href="{resource_path(lookup[rel["target_id"]])}">{esc(lookup[rel["target_id"]]["name"])}</a></li>' for rel in r["relations"] if rel["target_id"] in lookup)+'</ul>'
    backlinks=(incoming or {}).get(r['id'],[])
    if backlinks:
        labels={'documented_by':'Documented resource','introduced_by':'Introduced resource','published_by':'Published resource','variant_of':'Model variant','component_of':'Component'}
        body+='<h2>Connected assets</h2><p>These links come from reviewed resource records. A documentation link does not imply a training-data or evaluation dependency.</p><ul>'
        for rel in backlinks:
            source=lookup[rel['source_id']]
            body+=f'<li>{esc(labels.get(rel["type"],rel["type"].replace("_"," ")))}: <a href="{resource_path(source)}">{esc(source["name"])}</a> · {esc(KINDS[source["kind"]])} · <a href="{esc(rel["evidence_url"])}">relationship evidence</a></li>'
        body+='</ul>'
    body+='<h2>Primary evidence and verification</h2><p>Source retrieval is separate from experiment reproduction. Use the original publication or publisher page when citing claims about the resource.</p><ol class="source-list">'
    for ev in r["evidence"]:
        body+=f'<li><a href="{esc(ev["url"])}">{esc(ev["method"].replace("_"," "))}</a><p>Retrieved {esc(ev["retrieved_at"])}. Supports: {esc(", ".join(ev["supports"]))}.</p><details><summary>Content fingerprint</summary><code>{esc(ev["sha256"])}</code></details></li>'
    body+='</ol><h2>Suggest a correction</h2><p><a href="'+REPO+'/issues/new?template=resource.yml">Open a source-backed correction</a>. Include this record ID and the original source. Read our <a href="/about/">editorial policy</a> and <a href="/coverage/">coverage boundaries</a>.</p>'
    return body


def resource_markdown(r):
    lines=[f'# {r["name"]}', '', description(r), '', f'- Catalog URL: {SITE}{resource_path(r)}', f'- Original source: {r["url"]}', f'- Kind: {r["kind"]}', f'- Review: {r["review_status"]}', f'- Scope: {r["scope"]}', f'- Environments: {", ".join(r["environments"])}', f'- Topics: {", ".join(r["topics"])}', f'- Evidence checked: {r["last_verified_at"]}', f'- ID: {r["id"]}', '', '## Limitations', '', r["notes"] or 'Inclusion does not establish reproducibility or endorsement.']
    if r["authors"]:lines+=['','## Authors','',', '.join(r["authors"])]
    lines+=['','## License declarations','']
    for slot,license in r["licenses"].items():lines.append(f'- {slot}: '+(f'{license["declared"]} — {license["url"]}' if license else 'not recorded'))
    lines+=['','## Primary evidence','']+[f'- {ev["url"]} (retrieved {ev["retrieved_at"]}; SHA-256 {ev["sha256"]})' for ev in r["evidence"]]
    return '\n'.join(line.rstrip() for line in lines)+'\n'


def build_search_pages(destination, rows, coverage, root):
    lookup={r["id"]:r for r in rows}
    incoming=incoming_relations(rows)
    reviewed=[r for r in rows if eligible(r)]
    latest=coverage["as_of_utc"]
    manifest=[]
    def emit(path,content,index=True):
        target=destination/path.lstrip('/')/'index.html' if path.endswith('/') else destination/path.lstrip('/')
        target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content)
        manifest.append({"path":path,"indexable":index,"sha256":hashlib.sha256(content.encode()).hexdigest()})
    for r in rows:
        path=resource_path(r)
        emit(path,page(r["name"],description(r),path,resource_body(r,lookup,incoming),resource_schema(r),eligible(r)),eligible(r))
        (destination/path.lstrip('/')/'index.md').write_text(resource_markdown(r))
    category_links='<ul class="category-directory">'+''.join(f'<li><a href="/categories/{kind}/">{esc(name)}</a><span>{sum(r["kind"]==kind for r in rows):,} resources</span></li>' for kind,name in KINDS.items())+'</ul>'
    overview=f'<div class="eyebrow">COMPUTER-USE AGENT DIRECTORY</div><h1>Explore the computer-use agent ecosystem</h1><p class="answer-lead">AwesomeCUA connects research papers, GUI models, training datasets, benchmarks, engineering tools, products, and publishers with their original sources.</p><p>This snapshot has {len(rows):,} resource records, including {len(reviewed):,} reviewed entries. Counts are resources, not independent projects.</p><a class="button primary" href="/#catalog">Search and filter all resources</a><h2>Browse by resource type</h2>{category_links}<h2>Research and practical guides</h2><ul><li><a href="/papers/">Reviewed computer-use and GUI-agent research papers</a></li><li><a href="/guides/">Guides to agents, benchmarks, and training data</a></li><li><a href="/data/">Download the source-backed catalog</a></li><li><a href="/coverage/">Inspect coverage and unresolved gaps</a></li></ul>'
    emit('/catalog/',page('Computer-use agent resource directory','Browse source-backed computer-use agent papers, models, datasets, benchmarks, tools, products, and publishers.','/catalog/',overview,{"@type":"CollectionPage","name":"AwesomeCUA resource directory"}))
    for kind,label in KINDS.items():
        selected=sorted([r for r in reviewed if r['kind']==kind],key=lambda r:r['name'].lower())
        body=f'<div class="eyebrow">RESOURCE CATEGORY</div><h1>Computer-use agent {esc(label.lower())}</h1><p class="answer-lead">Browse {len(selected)} reviewed {esc(label.lower())} connected to computer-use, GUI, web, and mobile agents. Each entry links to primary evidence and records its scope.</p><p>Review means AI-assisted editorial inspection, not independent reproduction. Unknown licenses and specifications remain unknown.</p>'
        if kind=='paper':body+='<p>The complete bibliography includes metadata-only discoveries awaiting relevance review. They remain accessible in the <a href="/?kind=paper#catalog">interactive catalog</a> and data downloads.</p>'
        body+=listing(selected)+f'<p><a href="/?kind={kind}#catalog">Search all records in this category</a> · <a href="/catalog/">All categories</a></p>'
        schema={"@type":"ItemList","name":f'Computer-use agent {label.lower()}',"numberOfItems":len(selected),"itemListElement":[{"@type":"ListItem","position":i+1,"url":SITE+resource_path(r),"name":r['name']} for i,r in enumerate(selected)]}
        emit(f'/categories/{kind}/',page(f'Computer-use agent {label.lower()}',f'Reviewed {label.lower()} for computer-use and GUI agents, with original sources, platform tags, and license evidence.',f'/categories/{kind}/',body,schema))
    papers=sorted([r for r in reviewed if r['kind'] in {'paper','survey'}],key=lambda r:r.get('published_at') or '',reverse=True)
    body='<div class="eyebrow">RESEARCH LIBRARY</div><h1>Computer-use agent papers and surveys</h1><p class="answer-lead">A reading list covering GUI grounding, desktop and mobile evaluation, browser agents, training data, planning, and safety. Annotations are based on primary publications, with original author and date metadata.</p><p>The date shown is the paper publication date, not the date we added it. These annotations do not independently reproduce reported experiments.</p>'+listing(papers)
    emit('/papers/',page('Computer-use agent papers and surveys','Read source-backed annotations of computer-use and GUI-agent research, including OSWorld, AndroidWorld, UI-TARS, OpenCUA, grounding, planning, and safety.','/papers/',body,{"@type":"CollectionPage","name":"Reviewed computer-use agent research"}))
    linked_papers=[r for r in papers if any(e['type'] in {'documented_by','introduced_by'} for e in incoming.get(r['id'],[]))]
    body='<div class="eyebrow">FOLLOW THE RESEARCH TO THE ASSETS</div><h1>Computer-use papers, code, and datasets</h1><p class="answer-lead">Find the implementations, benchmarks, and datasets connected to reviewed research papers. Every relationship below has a primary-source evidence link.</p><p>Connections describe publication documentation or introduction. They do not automatically mean that a model was trained on a dataset or evaluated on a benchmark.</p><div class="reading-list">'
    for paper in linked_papers:
        body+=f'<article><h2><a href="{resource_path(paper)}">{esc(paper["name"])}</a></h2><p>{esc(description(paper))}</p><ul>'
        for rel in incoming[paper['id']]:
            source=lookup[rel['source_id']]
            body+=f'<li><a href="{resource_path(source)}">{esc(source["name"])}</a> — {esc(KINDS[source["kind"]])} · <a href="{esc(rel["evidence_url"])}">source evidence</a></li>'
        body+='</ul></article>'
    body+='</div><p><a href="/downloads/relationships.json">Download reviewed relationships as JSON</a> · <a href="/about/">Editorial policy</a></p>'
    emit('/connections/',page('Computer-use papers, code, and datasets','Trace computer-use agent papers to documented implementations, GUI benchmarks, and training datasets using reviewed primary-source relationships.','/connections/',body))
    edges=[{'source_id':r['id'],'source_name':r['name'],'source_kind':r['kind'],**rel} for r in rows for rel in r['relations']]
    (destination/'downloads/relationships.json').write_text(json.dumps({'relation_count':len(edges),'semantics':'Reviewed semantic links only. Documentation does not establish training or evaluation dependency.','relations':edges},ensure_ascii=False,indent=2)+'\n')
    sources=''.join(f'<tr><td><a href="{esc(s["url"])}">{esc(s["name"])}</a></td><td>{s["discovered"]}</td><td>{s["indexed"]}</td><td>{s["curated"]}</td></tr>' for s in coverage['sources'])
    body=f'<h1>Coverage and verification ledger</h1><p class="answer-lead">{len(rows):,} resource records: {len(reviewed):,} curated and {coverage["metadata_only_records"]:,} with bibliographic metadata verification only.</p><p>Evidence snapshot: {esc(latest)}. Resource types can refer to different parts of the same project. Source populations overlap and cannot be summed into a global field size.</p><h2>Discovery-source coverage</h2><div class="table-scroll"><table class="coverage-table"><thead><tr><th>Source</th><th>Found</th><th>Indexed</th><th>Curated</th></tr></thead><tbody>{sources}</tbody></table></div><h2>What remains unverified?</h2><p>Most bibliography entries still require relevance review. Closed datasets, unpublished systems, and regional resources are not exhaustively represented. Asset sizes, model licenses, availability, and experiment protocols need continuing curation. Global completeness has not been established.</p><p>{coverage["unindexed_candidates"]} discovered identifiers currently have no catalog record.</p><p><a href="/downloads/coverage.json">Download the complete coverage ledger</a> · <a href="/about/">Editorial policy</a></p>'
    emit('/coverage/',page('Coverage and verification ledger','Inspect AwesomeCUA source populations, editorial review states, bibliographic verification, unresolved identifiers, and explicit coverage gaps.','/coverage/',body))
    scan_config=json.loads((root/'data/scan-config.json').read_text())
    scan_path=root/'data/scan-status.json'
    scan=json.loads(scan_path.read_text()) if scan_path.exists() else None
    schedule=', '.join(scan_config['scan_times_local'])+' '+scan_config['timezone']
    publication=', '.join(scan_config['publish_times_local'])+' '+scan_config['timezone']
    body=f'<div class="eyebrow">DISCOVERY ACTIVITY</div><h1>Twice-daily catalog updates</h1><p class="answer-lead">Public sources are scanned twice a day. New paper identities are checked against arXiv; editorial annotations and approvals remain separate.</p><dl class="page-facts"><div><dt>Configured scan times</dt><dd>{esc(schedule)}</dd></div><div><dt>Website rebuild times</dt><dd>{esc(publication)}</dd></div></dl><p>GitHub scheduling can be delayed. The completion times below record what actually ran, rather than assuming that a scheduled job executed.</p>'
    body+=f'<h2>Current published catalog</h2><dl class="page-facts"><div><dt>Reviewed papers and surveys</dt><dd>{len(papers):,}</dd></div><div><dt>Other reviewed resources</dt><dd>{len(reviewed)-len(papers):,}</dd></div><div><dt>Total resource records</dt><dd>{len(rows):,}</dd></div></dl><p>These counts include editorial work completed after the scan below. <a href="/papers/">Browse reviewed research</a> or <a href="/coverage/">inspect full coverage</a>.</p>'
    if scan:
        body+=f'<h2>Latest completed scan</h2><dl class="page-facts"><div><dt>Status</dt><dd>{esc(scan["status"])}</dd></div><div><dt>Started</dt><dd>{esc(scan["started_at"])}</dd></div><div><dt>Finished</dt><dd>{esc(scan["finished_at"])}</dd></div><div><dt>Discovery documents fetched</dt><dd>{scan["source_fetches"]["successful"]} / {scan["source_fetches"]["total"]}</dd></div><div><dt>New paper metadata</dt><dd>{len(scan["new_papers"])}</dd></div><div><dt>New candidate identifiers</dt><dd>{scan["new_candidate_count"]}</dd></div><div><dt>Reviewed papers at scan completion</dt><dd>{scan["after"]["curated_papers"]}</dd></div><div><dt>Pending metadata changes</dt><dd>{scan["pending_metadata_changes"]}</dd></div></dl>'
        if scan.get('run_url'):body+=f'<p><a href="{esc(scan["run_url"])}">Inspect the workflow run and logs</a></p>'
        if scan['warnings']:body+='<h3>Recorded gaps</h3><ul>'+''.join('<li>'+esc(w)+'</li>' for w in scan['warnings'])+'</ul>'
        if scan['new_papers']:
            body+='<h2>New to the bibliography</h2><p>These are newly discovered bibliographic records. Relevance and findings still require editorial review.</p><ul>'+''.join(f'<li><a href="{resource_path(r)}">{esc(r["name"])}</a> · metadata verified</li>' for r in scan['new_papers'][:30])+'</ul>'
        (destination/'downloads/scan-status.json').write_text(json.dumps(scan,ensure_ascii=False,indent=2)+'\n')
        body+='<p><a href="/downloads/scan-status.json">Download the full scan receipt</a></p>'
    else:
        body+='<h2>First scan pending</h2><p>The schedule is configured in the source repository. No completed automated-scan receipt has been recorded yet.</p>'
    body+='<h2>What automation does and does not establish</h2><p>A scan can discover a source or verify bibliographic fields. It does not reproduce experiments, approve a resource’s relevance, establish dataset permissions, or add editorial summaries. Existing reviewed snapshots are preserved; observed metadata changes are queued for review.</p><p><a href="https://github.com/reacher-z/Awesome-CUA/actions/workflows/scan.yml">Discovery workflow</a> · <a href="'+REPO+'/actions/workflows/publish.yml">Publication workflow</a> · <a href="/coverage/">Coverage ledger</a></p>'
    emit('/updates/',page('Twice-daily catalog updates','Inspect the actual completion, discoveries, and source gaps from the AwesomeCUA twice-daily public-source scans.','/updates/',body))
    badge_papers=sum(r['kind'] in {'paper','survey'} for r in reviewed)
    (destination/'badges').mkdir(exist_ok=True)
    badge=f'<svg xmlns="http://www.w3.org/2000/svg" width="590" height="30" role="img" aria-label="{len(rows)} resources, {len(reviewed)} reviewed resources, {badge_papers} reviewed papers"><rect width="590" height="30" rx="5" fill="#4856df"/><g fill="#fff" font-family="Arial,sans-serif" font-size="12" text-anchor="middle"><text x="85" y="20">{len(rows):,} resources</text><text x="270" y="20">{len(reviewed):,} reviewed resources</text><text x="485" y="20">{badge_papers:,} reviewed papers</text></g></svg>'
    (destination/'badges/catalog.svg').write_text(badge)
    body='<h1>About AwesomeCUA and its editorial policy</h1><p class="answer-lead">AwesomeCUA is a source-backed catalog of resources for agents that operate computer interfaces. Its purpose is to make research and engineering assets easier to find, compare, and trace to their original publishers.</p><h2>Who maintains the catalog?</h2><p>The AwesomeCUA project publishes the catalog through its <a href="https://github.com/AwesomeCUA">GitHub organization</a>. Annotations and taxonomy are produced with AI-assisted editorial review. This is not a claim of independent peer review, benchmark reproduction, or affiliation with listed publishers.</p><h2>What is included?</h2><p>GUI and hybrid GUI/code agents, visual grounding, web and mobile navigation, training data, evaluation environments, execution infrastructure, safety research, and relevant products. Supporting tools may be marked adjacent.</p><h2>How are claims checked?</h2><p>Community lists and semantic searches discover candidates. arXiv verifies bibliographic metadata. Official papers, repositories, documentation, and model/dataset cards support curated annotations. Every record retains source URLs, retrieval timestamps, and content hashes. Source refreshes do not silently inherit editorial approval.</p><h2>What do review states mean?</h2><ul><li><strong>Curated:</strong> a primary source was inspected for identity, scope, and the concise annotation.</li><li><strong>Metadata verified:</strong> bibliographic fields were checked; relevance, taxonomy, and findings are still pending.</li><li><strong>Candidate:</strong> an identifier was discovered but is not a published catalog record.</li></ul><h2>Licenses and corrections</h2><p>Code, data, weights, and document licenses are separate. Public availability does not establish reuse rights. Original catalog annotations and code use MIT; upstream resources keep their own terms. Report errors through <a href="'+REPO+'/issues/new?template=resource.yml">a source-backed correction</a>.</p><h2>Indexing policy</h2><p>Reviewed resource pages and useful collection pages are eligible for indexing. Metadata-only resource pages remain accessible, with <code>noindex,follow</code> until their relevance is reviewed. The full bibliography remains searchable and downloadable.</p><p><a href="/coverage/">Coverage ledger</a> · <a href="/data/">Data and provenance</a></p>'
    emit('/about/',page('About AwesomeCUA and editorial policy','Learn what AwesomeCUA includes, how primary-source review works, what verification does and does not mean, and how to suggest corrections.','/about/',body))
    desc='A structured catalog of computer-use agent research papers, models, datasets, benchmarks, tools, products, and publishers, including original annotations, review states, source evidence, scoped license declarations, and resource relationships.'
    dataset={"@type":"Dataset","name":"AwesomeCUA computer-use agent resource catalog","description":desc,"url":SITE+'/data/',"creator":{"@id":SITE+'/#organization'},"license":REPO+'/blob/main/LICENSE',"dateModified":latest,"keywords":["computer-use agents","GUI agents","browser agents","datasets","benchmarks"],"distribution":[{"@type":"DataDownload","encodingFormat":"application/x-ndjson","contentUrl":SITE+'/downloads/catalog.jsonl'},{"@type":"DataDownload","encodingFormat":"application/vnd.sqlite3","contentUrl":SITE+'/downloads/catalog.sqlite'}],"isAccessibleForFree":True}
    body=f'<h1>Download the AwesomeCUA data catalog</h1><p class="answer-lead">{desc}</p><p>This snapshot contains {len(rows):,} resource records. A record is a resource, not necessarily an independent project. Evidence snapshot: {esc(latest)}.</p><h2>Data downloads</h2><ul><li><a href="/downloads/catalog.jsonl">Complete resource catalog — JSONL</a></li><li><a href="/downloads/catalog.sqlite">Queryable database — SQLite</a></li><li><a href="/downloads/coverage.json">Coverage and verification ledger — JSON</a></li><li><a href="/downloads/sources.json">Discovery-source registry — JSON</a></li></ul><h2>What does a record contain?</h2><p>Stable identifier, resource name, kind, platform and topic facets, concise annotation, review state, bibliographic dates and authors where available, separate code/data/weights/document licenses, source URLs, retrieval times, content fingerprints, and reviewed relationships.</p><h2>What does this download exclude?</h2><p>It does not contain upstream model weights, training datasets, paper PDFs, or copied full abstracts. Follow each resource’s original source for those assets and their licensing terms.</p><h2>License and attribution</h2><p>Original catalog code and annotations use <a href="/LICENSE">MIT</a>. Third-party titles, bibliographic facts, and linked assets retain their original attribution and applicable terms; the catalog does not relicense the underlying papers, data, or weights.</p><h2>Quality and reuse</h2><p>Retain review status and provenance when redistributing or analyzing records. Missing data is unknown, not zero. Do not interpret metadata-only papers as editorially confirmed CUA research or combine scores across incompatible experiment protocols.</p><p><a href="/about/">Editorial method</a> · <a href="/coverage/">Coverage limits</a></p>'
    emit('/data/',page('AwesomeCUA computer-use agent dataset and downloads',desc,'/data/',body,dataset))
    guides=json.loads((root/'data/site-guides.json').read_text())
    for guide in guides:
        emit('/guides/'+guide['slug']+'/',page(guide['title'],guide['description'],'/guides/'+guide['slug']+'/',guide['body'],{"@type":"Article","headline":guide['title'],"description":guide['description'],"author":{"@id":SITE+'/#organization'}}))
    body='<h1>Guides to computer-use agents</h1><p class="answer-lead">Practical reading guides with direct answers and primary research references. These guides help distinguish interface grounding, task execution, training data, and evaluation.</p><div class="reading-list">'+''.join(f'<article><h2><a href="/guides/{esc(g["slug"])}/">{esc(g["title"])}</a></h2><p>{esc(g["description"])}</p></article>' for g in guides)+'</div>'
    emit('/guides/',page('Computer-use agent guides','Understand computer-use agents, choose GUI-agent benchmarks, and find training datasets with clearly scoped primary-source references.','/guides/',body))
    zh=f'<div class="eyebrow">COMPUTER-USE AGENT 资源指南</div><h1>AwesomeCUA：可追溯的智能体资源目录</h1><p class="answer-lead">连接论文、模型、数据集、评测基准、框架、工具、产品与发布方。每条资源保留一手来源与审阅状态。</p><p>当前有 {len(rows):,} 条资源，{len(reviewed):,} 条经过 AI 辅助编辑审阅。数量以资源为单位，不代表独立项目总数。</p><div class="page-actions"><a class="button primary" href="/?lang=zh#catalog">打开中文搜索目录</a><a class="button secondary" href="/data/">下载数据</a></div><h2>研究与训练</h2><ul><li><a href="/papers/">论文与综述阅读列表</a></li><li><a href="/categories/dataset/">训练数据集</a></li><li><a href="/categories/benchmark/">GUI、桌面、网页与手机评测基准</a></li><li><a href="/categories/model/">模型与权重版本</a></li></ul><h2>产业与工程</h2><ul><li><a href="/categories/agent/">智能体</a></li><li><a href="/categories/framework/">开发与训练框架</a></li><li><a href="/categories/product/">产品</a></li><li><a href="/catalog/">浏览全部分类</a></li></ul><h2>如何理解“已核验”？</h2><p>已审阅条目经过一手来源编辑检查。论文元数据仅核实标题、作者和日期，不代表研究结论或实验已复现。代码、数据、权重与文档许可分别记录，未知信息保留为空。</p><h2>是否已经全球最全？</h2><p>全面覆盖是目标，目前没有足够证据证明已达到全球最全。请查看<a href="/coverage/">覆盖台账</a>和<a href="/about/">编辑方法</a>了解边界与缺口。</p>'
    emit('/zh/',page('AwesomeCUA 中文主页：Computer-Use Agent 资源目录','浏览可搜索、可追溯的 Computer-Use Agent 论文、模型、数据集、基准、框架与产品，查看来源证据并下载结构化目录。','/zh/',zh,lang='zh-CN',alternatives=True))
    # A static, visible directory is useful to visitors even when JavaScript is unavailable.
    home=(destination/'index.html').read_text()
    extra=f'<link rel="canonical" href="{SITE}/"><meta name="robots" content="index,follow,max-image-preview:large"><meta property="og:url" content="{SITE}/"><link rel="alternate" hreflang="en" href="{SITE}/"><link rel="alternate" hreflang="zh-CN" href="{SITE}/zh/"><link rel="alternate" hreflang="x-default" href="{SITE}/"><link rel="alternate" type="application/atom+xml" href="{SITE}/feed.xml" title="AwesomeCUA research updates"><link rel="stylesheet" href="./pages.css">'
    home=home.replace('</head>',extra+f'<script type="application/ld+json">{jsonld({"@context":"https://schema.org","@graph":[organization(),{"@type":"WebSite","@id":SITE+"/#website","url":SITE+"/","name":"AwesomeCUA","description":"Source-backed computer-use and GUI-agent resource catalog","publisher":{"@id":SITE+"/#organization"}}]})}</script></head>')
    for identity,value in [('stat-resources',len(rows)),('stat-curated',len(reviewed)),('stat-kinds',len(KINDS)),('stat-sources',len(coverage['sources']))]:
        home=re.sub(f'(id="{identity}">).*?(</span>)',lambda m:m.group(1)+format(value,',')+m.group(2),home)
    home=home.replace('id="snapshot-date">—','id="snapshot-date">'+latest[:10])
    static='<section class="shell static-directory" aria-labelledby="static-directory-title"><div class="eyebrow">READ, EXPLORE, AND CITE</div><h2 id="static-directory-title">Computer-use agent research and resources</h2><p>Browse source-backed pages directly, with or without JavaScript. Reviewed entries include concise annotations, provenance, and separate license declarations.</p><div class="directory-links"><a href="/catalog/">Resource directory</a><a href="/papers/">Research papers</a><a href="/connections/">Papers → code & data</a><a href="/updates/">Twice-daily updates</a><a href="/categories/model/">Models</a><a href="/categories/dataset/">Datasets</a><a href="/categories/benchmark/">Benchmarks</a><a href="/categories/framework/">Frameworks</a><a href="/categories/product/">Products</a><a href="/guides/">Guides</a><a href="/data/">Download data</a><a href="/coverage/">Coverage</a><a href="/about/">Editorial policy</a><a href="/zh/">中文指南</a></div><h3>Where should I start?</h3><p><a href="/guides/what-are-computer-use-agents/">Understand computer-use agents</a>, <a href="/guides/gui-agent-benchmarks/">choose a benchmark for the capability you need</a>, or <a href="/guides/gui-agent-training-data/">find training data with the right supervision and license</a>.</p></section>'
    home=home.replace('</main>',static+'</main>')
    emit('/',home)
    feed=ET.Element('feed',xmlns='http://www.w3.org/2005/Atom')
    for key,value in [('title','AwesomeCUA research reading list'),('id',SITE+'/papers/'),('updated',latest)]:ET.SubElement(feed,key).text=value
    ET.SubElement(feed,'link',href=SITE+'/feed.xml',rel='self');ET.SubElement(feed,'link',href=SITE+'/papers/')
    for r in papers[:50]:
        entry=ET.SubElement(feed,'entry')
        for key,value in [('title',r['name']),('id',SITE+resource_path(r)),('updated',r['last_verified_at']),('summary',description(r))]:ET.SubElement(entry,key).text=value
        ET.SubElement(entry,'link',href=SITE+resource_path(r));author=ET.SubElement(entry,'author');ET.SubElement(author,'name').text='AwesomeCUA'
    (destination/'feed.xml').write_bytes(ET.tostring(feed,encoding='utf-8',xml_declaration=True))
    llms=['# AwesomeCUA','', '> A source-backed computer-use agent resource catalog. Distinguish curated entries from metadata-only bibliography records.','', 'Resource counts are not independent project counts. Primary-source retrieval does not establish reproducibility. Code, data, weights, and document licenses are separate.','', '## Start here','',f'- [Catalog]({SITE}/catalog/): resource categories',f'- [Research]({SITE}/papers/): reviewed papers and surveys',f'- [Guides]({SITE}/guides/): definitions and practical reading guides',f'- [Editorial policy]({SITE}/about/): review states and limits',f'- [Coverage]({SITE}/coverage/): source populations and known gaps',f'- [Data downloads]({SITE}/data/): structured catalog with provenance','', '## Machine-readable access','',f'- [Full catalog JSONL]({SITE}/downloads/catalog.jsonl)',f'- [Curated annotations in Markdown]({SITE}/llms-full.txt)',f'- [Research Atom feed]({SITE}/feed.xml)','', 'Resource HTML pages have a companion `index.md` at the same path. This file is an optional navigation aid, not an indexing requirement or a request to rank this site.']
    (destination/'llms.txt').write_text('\n'.join(llms)+'\n')
    (destination/'llms-full.txt').write_text('# AwesomeCUA curated resource annotations\n\n'+f'Evidence snapshot: {latest}. These records were reviewed with AI assistance; experiments are not independently reproduced.\n\n'+'\n---\n\n'.join(resource_markdown(r) for r in reviewed))
    robots='User-agent: *\nAllow: /\n\n'+''.join(f'User-agent: {bot}\nAllow: /\n\n' for bot in ['Googlebot','bingbot','OAI-SearchBot','PerplexityBot','Claude-SearchBot'])+f'Sitemap: {SITE}/sitemap.xml\nSitemap: {SITE}/sitemap.txt\n'
    (destination/'robots.txt').write_text(robots)
    sitemap=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for item in sorted(manifest,key=lambda x:x['path']):
        if item['indexable']:
            node=ET.SubElement(sitemap,'url');ET.SubElement(node,'loc').text=SITE+item['path']
            # No synthetic build-time lastmod; upstream evidence time is not page modification time.
    ET.indent(sitemap,space='  ')
    (destination/'sitemap.xml').write_bytes(ET.tostring(sitemap,encoding='utf-8',xml_declaration=True))
    (destination/'sitemap.txt').write_text(''.join(SITE+item['path']+'\n' for item in sorted(manifest,key=lambda x:x['path']) if item['indexable']))
    (destination/'data/search-manifest.json').write_text(json.dumps({'site_url':SITE,'indexable_pages':sum(x['indexable'] for x in manifest),'metadata_only_pages':sum(not x['indexable'] for x in manifest),'pages':manifest},ensure_ascii=False,indent=2)+'\n')
    config=json.loads((root/'data/site-discovery.json').read_text())
    key=config['indexnow_key'];(destination/(key+'.txt')).write_text(key)
    return manifest
