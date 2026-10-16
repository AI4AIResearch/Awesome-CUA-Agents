#!/usr/bin/env python3
"""Prepare existing public website/profile checkouts. Does not commit, push, or change visibility."""
from pathlib import Path
import json
import shutil
from search_pages import KINDS, SITE, REPO, resource_path

ROOT=Path(__file__).resolve().parents[1]


def main():
    site=ROOT/'.cache/github-pages-publish';profile=ROOT/'.cache/github-profile'
    if not (site/'.git').exists() or not (profile/'.git').exists():
        raise SystemExit('Clone AwesomeCUA/awesomecua.github.io and AwesomeCUA/.github into the documented .cache checkout paths first.')
    build=ROOT/'dist/site'
    incoming=json.loads((build/'data/search-manifest.json').read_text())
    old_path=site/'data/search-manifest.json'
    if old_path.exists():
        old=json.loads(old_path.read_text());new_paths={p['path'] for p in incoming['pages']}
        for item in old.get('pages',[]):
            if item['path'] in new_paths or not item['path'].startswith(('/resources/','/categories/','/guides/')):continue
            folder=site/item['path'].lstrip('/')
            for filename in ['index.html','index.md']:(folder/filename).unlink(missing_ok=True)
    shutil.copytree(build,site,dirs_exist_ok=True)
    (site/'.github/ISSUE_TEMPLATE').mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'.github/ISSUE_TEMPLATE/resource.yml',site/'.github/ISSUE_TEMPLATE/resource.yml')
    (site/'schemas').mkdir(exist_ok=True);shutil.copy2(ROOT/'schemas/resource.schema.json',site/'schemas/resource.schema.json')
    report=json.loads((ROOT/'data/coverage.json').read_text())
    rows=[json.loads(l) for l in (ROOT/'data/catalog.jsonl').read_text().splitlines()]
    readme=['# Awesome Computer-Use Agents · AwesomeCUA','', '**A source-backed catalog of computer-use, GUI, browser, and mobile agents.**','', f'[Website]({SITE}/) · [Research papers]({SITE}/papers/) · [中文指南]({SITE}/zh/) · [GitHub organization](https://github.com/AwesomeCUA)','',f'**{report["total_records"]:,} resource records** · **{report["curated_records"]:,} curated** · **{report["bibliographic_records"]:,} arXiv records** · **{len(report["sources"])} discovery documents**','',f'Evidence snapshot: {report["as_of_utc"]}. Bibliography counts overlap review-state counts. Resources are not independent projects.','', '## What is a computer-use agent?','', 'A computer-use agent observes software interfaces, chooses and executes actions, and checks progress toward a user goal. It may operate a browser, desktop application, or phone, sometimes combining graphical interaction with code and tools. See [the primary-source introduction]('+SITE+'/guides/what-are-computer-use-agents/) and [reviewed research]('+SITE+'/papers/).','', '## Explore the ecosystem','', '| Category | Records | Browse |','| --- | ---: | --- |']
    for kind,name in KINDS.items():readme.append(f'| {name} | {report["by_kind"].get(kind,0):,} | [Open directory]({SITE}/categories/{kind}/) |')
    readme+=['','Category pages highlight reviewed resources; the [interactive catalog]('+SITE+'/#catalog) and downloads also expose metadata-only records with their review state.','', '## Research reading list','']
    selected=sorted([r for r in rows if r['kind']=='paper' and r['review_status']=='curated'],key=lambda r:r['published_at'] or '',reverse=True)
    for r in selected[:10]:readme.append(f'- [{r["name"]}]({SITE}{resource_path(r)}) — {r["summary"]} [Original paper]({r["url"]}).')
    readme+=['',f'[All reviewed papers and surveys]({SITE}/papers/). Annotations do not independently reproduce experimental findings.','', '## Choose a benchmark or training dataset','', f'- [GUI-agent benchmark guide]({SITE}/guides/gui-agent-benchmarks/): distinguish grounding, web tasks, mobile interaction, and desktop execution.', f'- [Training-data guide]({SITE}/guides/gui-agent-training-data/): compare supervision types, platform, splits, count units, and licenses.',f'- [Editorial policy]({SITE}/about/) and [coverage ledger]({SITE}/coverage/): understand what was verified and what is still missing.','', '## Download and reuse the data','',f'- [Full resource catalog — JSONL]({SITE}/downloads/catalog.jsonl)',f'- [Queryable database — SQLite]({SITE}/downloads/catalog.sqlite)',f'- [Data documentation]({SITE}/data/) · [JSON Schema](schemas/resource.schema.json)',f'- [Coverage JSON]({SITE}/downloads/coverage.json) · [Source registry]({SITE}/downloads/sources.json)',f'- [Machine-readable navigation]({SITE}/llms.txt) · [Curated Markdown]({SITE}/llms-full.txt) · [Research feed]({SITE}/feed.xml)','', 'The downloads contain metadata and original catalog annotations, not upstream training data, model weights, or paper PDFs. Code, data, weights, and document licenses remain separate.','', '## Website and contributions','', 'This repository hosts the published static website and metadata snapshot. Complete resource pages and guides work without JavaScript; interactive search adds filtering, pagination, and detail dialogs. No API keys, account, paid backend, or external analytics are required.','', '```bash','python3 -m http.server 4173 --bind 127.0.0.1','```','', 'GitHub Pages serves the `main` branch root. Original code and annotations use [MIT](LICENSE); linked assets retain their own terms.', '',f'[Suggest a resource or correction]({REPO}/issues/new?template=resource.yml). Supply a primary source and explain uncertain facts. Global completeness is a goal, not a verified claim.','']
    (site/'README.md').write_text('\n'.join(readme))
    profile_path=profile/'profile/README.md';profile_path.parent.mkdir(exist_ok=True)
    profile_path.write_text(f'''# AwesomeCUA\n\n### The computer-use agent ecosystem, with sources.\n\nResearch papers, GUI models, training datasets, evaluation benchmarks, frameworks, tools, and products — searchable and traceable in one catalog.\n\n**[Explore the website →]({SITE}/)** · **[Research papers →]({SITE}/papers/)** · **[中文指南 →]({SITE}/zh/)**\n\n| Research & training | Engineering & industry |\n| --- | --- |\n| [Papers]({SITE}/papers/) · [Surveys]({SITE}/categories/survey/) | [Agents]({SITE}/categories/agent/) · [Frameworks]({SITE}/categories/framework/) |\n| [Models]({SITE}/categories/model/) · [Datasets]({SITE}/categories/dataset/) | [Tools]({SITE}/categories/tool/) · [Infrastructure]({SITE}/categories/infrastructure/) |\n| [Benchmarks]({SITE}/categories/benchmark/) | [Products]({SITE}/categories/product/) · [Publishers]({SITE}/categories/company/) |\n\n**{report['total_records']:,} resource records** · **{report['curated_records']:,} reviewed** · **11 categories**\n\n[Download data]({SITE}/data/) · [Practical guides]({SITE}/guides/) · [Coverage]({SITE}/coverage/) · [Contribute]({REPO}/issues/new?template=resource.yml)\n\n每条资源保留一手来源与审阅状态。支持论文检索、分类筛选、来源追溯与结构化数据下载。\n\nCurated means AI-assisted editorial review; metadata verification does not establish research quality or reproducibility. Counts refer to resources, not distinct projects. Comprehensive global coverage is a goal, not a verified claim.\n\n<sub>Evidence snapshot: {report['as_of_utc'][:10]}. Original annotations and code: MIT. Linked assets retain their own terms.</sub>\n''')
    print(f'Prepared {incoming["indexable_pages"]} indexable pages and updated public README/profile. Review diffs before committing.')


if __name__=='__main__':main()
