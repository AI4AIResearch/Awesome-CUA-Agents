"""Offline materialized views, quality gates, and search for the CUA catalog."""
from __future__ import annotations

import collections
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import urllib.parse

from catalog import ROOT, DATA, KINDS, ENVIRONMENTS, STATUSES, canonical, read_json, read_jsonl, write_json, write_jsonl
from specifications import validate_profiles
from scope_review import resolve_exclusions, scope_report
from arxiv_metadata import validate_snapshot


def apply_license_reviews(editorial, primary, licenses, details):
    reviews=editorial.get('reviewed_licenses', {})
    if not isinstance(reviews, dict) or set(reviews)-set(licenses):
        raise ValueError('Invalid reviewed license scopes: '+editorial['name'])
    receipts=[primary,*editorial.get('additional_evidence',[])]
    for slot,decision in reviews.items():
        if not isinstance(decision,dict) or set(decision)!={'value','reason','evidence_urls'}:
            raise ValueError('License review needs value, reason, and evidence URLs: '+editorial['name'])
        if not isinstance(decision['reason'],str) or not decision['reason'].strip() or not decision['evidence_urls']:
            raise ValueError('License review lacks an explanation or evidence: '+editorial['name'])
        for url in decision['evidence_urls']:
            if not any(r['url']==url and ('licenses' in r['supports'] or 'licenses.'+slot in r['supports']) for r in receipts):
                raise ValueError('License review lacks a supporting receipt: '+url)
        value=decision['value']
        if value is not None and (not isinstance(value,dict) or value.get('url') not in decision['evidence_urls']):
            raise ValueError('Reviewed license must cite its retained evidence: '+editorial['name'])
        licenses[slot]=copy.deepcopy(value)
    if reviews:
        details['license_review']={slot:{k:copy.deepcopy(v) for k,v in decision.items() if k!='value'} for slot,decision in reviews.items()}


def source_records(with_scope=False):
    records = {r["id"]: copy.deepcopy(r) for r in read_jsonl(DATA / "papers.jsonl")}
    evidence = {r["id"]: r for r in read_jsonl(DATA / "primary-evidence.jsonl")}
    enrichment = {r["id"]: r for r in read_jsonl(DATA / "enrichment.jsonl")}
    pending = []
    for row in records.values():
        snapshot = row.get('details', {}).get('arxiv_snapshot')
        row.update(scope="relevance_pending", details={'arxiv_snapshot': snapshot} if snapshot else {})
    for editorial in read_json(DATA / "editorial.json", []):
        parsed = canonical(editorial["url"])
        if not parsed:
            raise ValueError(f"Invalid editorial URL: {editorial['url']}")
        rid = editorial.get("id", parsed[0])
        ev = evidence.get(rid)
        if not editorial.get("editorial_reviewed") or not ev or not ev.get("content_matched") or editorial.get("reviewed_sha256") != ev.get("sha256"):
            reason = editorial.get("review_note", "editorial review pending")
            if not ev or not ev.get("content_matched"):
                reason = "primary evidence unresolved: " + (ev or {}).get("error", "content mismatch")
            elif editorial.get("reviewed_sha256") != ev.get("sha256"):
                reason = "current source snapshot needs editorial review"
            pending.append({"id": rid, "name": editorial["name"], "url": editorial["url"], "reason": reason})
            continue
        base = records.get(rid, {})
        extra = enrichment.get(rid, {})
        if extra.get("evidence_sha256") != ev["sha256"]:
            extra = {}
        licenses = {"code": None, "data": None, "weights": None, "document": None}
        licenses.update(extra.get("licenses", {}))
        details = copy.deepcopy(base.get('details', {}))
        details.update(copy.deepcopy(editorial.get("details", {})))
        details.update(extra.get("details", {}))
        if editorial["kind"] == "dataset":
            for key, default in {"sample_count": None, "sample_unit": None, "modalities": [], "download_url": None, "languages": []}.items():
                details.setdefault(key, default)
        if editorial["kind"] == "benchmark":
            for key, default in {"task_count": None, "metrics": [], "evaluation_type": None, "leaderboard_url": None}.items():
                details.setdefault(key, default)
        relations = copy.deepcopy(editorial.get('reviewed_relations', []))
        for aid in editorial.get("paper_ids", []):
            target = "arxiv:" + aid
            relations.append({"type": "introduced_by", "target_id": target, "evidence_url": ev["url"]})
        for aid in editorial.get("documented_by", []):
            relations.append({"type": "documented_by", "target_id": "arxiv:" + aid, "evidence_url": ev["url"]})
        if editorial.get("publisher_id"):
            relations.append({"type": "published_by", "target_id": editorial["publisher_id"], "evidence_url": ev["url"]})
        if editorial.get("component_of"):
            relations.append({"type": "component_of", "target_id": canonical(editorial["component_of"])[0], "evidence_url": ev["url"]})
        if editorial.get("family_url"):
            relations.append({"type": "variant_of", "target_id": canonical(editorial["family_url"])[0], "evidence_url": ev["url"]})
        primary = {"role": "primary", "method": "editorial_primary_review", "supports": editorial.get("primary_supports", ["name", "kind", "summary", "environments", "topics", "scope", "relations"]),
            "url": ev["url"], "retrieved_at": ev["retrieved_at"], "sha256": ev["sha256"]}
        if editorial.get("details") and "primary_supports" not in editorial:
            primary["supports"].append("details")
        apply_license_reviews(editorial,primary,licenses,details)
        row = {"id": rid, "name": editorial["name"], "kind": editorial["kind"], "url": editorial["url"],
            "aliases": editorial.get("aliases", []), "environments": editorial["environments"], "topics": editorial["topics"],
            "scope": editorial.get("scope", "core"), "summary": editorial["summary"], "review_status": "curated",
            "published_at": base.get("published_at"), "updated_at": base.get("updated_at"), "authors": base.get("authors", []),
            "identifiers": base.get("identifiers", {}), "links": [{"rel": "primary", "url": editorial["url"]}],
            "relations": relations, "licenses": licenses, "evidence": base.get("evidence", []) + [primary] + editorial.get("additional_evidence", []) + extra.get("evidence", []),
            "last_verified_at": ev["retrieved_at"], "notes": editorial.get("notes", ""), "details": details}
        records[rid] = row
    changes = {row['id'] for row in read_jsonl(DATA/'metadata-updates.jsonl')}
    decisions = resolve_exclusions(records, read_json(DATA/'exclusions.json', []), changes)
    excluded = {row['id'] for row in decisions if row['status']=='excluded'}
    pending += [{'id':row['id'],'name':records[row['id']]['name'],'url':row['url'],'reason':row['status_reason']} for row in decisions if row['status']=='revalidation_pending']
    rows = sorted((row for rid,row in records.items() if rid not in excluded), key=lambda r:r['id'])
    return (rows,pending,decisions) if with_scope else (rows,pending)


def validate_records(rows):
    errors, seen = [], set()
    required = {"id", "name", "kind", "url", "aliases", "environments", "topics", "scope", "summary", "review_status", "published_at", "updated_at", "authors", "identifiers", "links", "relations", "licenses", "evidence", "last_verified_at", "notes", "details"}
    ids = {r.get("id") for r in rows}
    for r in rows:
        rid = r.get("id", "<missing>")
        def error(message):
            errors.append(f"{rid}: {message}")
        if rid in seen:
            error("duplicate identifier")
        seen.add(rid)
        if missing := required - r.keys():
            error("missing fields " + ", ".join(sorted(missing)))
        if r.get("kind") not in KINDS:
            error("invalid kind")
        if not r.get("name") or not canonical(r.get("url", "")):
            error("missing name or invalid URL")
        if r.get("review_status") not in STATUSES:
            error("invalid review status")
        if not r.get("environments") or set(r["environments"]) - ENVIRONMENTS:
            error("invalid environments")
        if r.get("scope") not in {"core", "adjacent", "relevance_pending"}:
            error("invalid scope")
        if r.get("review_status") == "curated" and (not r.get("summary") or r.get("scope") == "relevance_pending"):
            error("curated entry lacks an editorial summary/scope")
        for issue in validate_profiles(r):
            error(issue)
        for issue in validate_snapshot(r):
            error(issue)
        preferred = r.get("identifiers", {}).get("preferred_arxiv")
        if preferred and preferred != r.get("identifiers", {}).get("arxiv"):
            if "arxiv:" + preferred not in ids:
                error("preferred bibliographic identity is missing")
            if r.get("review_status") == "curated":
                error("known duplicate cannot be counted as an additional curated paper")
        if set(r.get("licenses", {})) != {"code", "data", "weights", "document"}:
            error("license scopes must be explicit")
        for scope, license_info in r.get("licenses", {}).items():
            if license_info is not None and (not isinstance(license_info, dict) or not license_info.get("url") or not license_info.get("declared")):
                error(f"{scope} license lacks a declaration or source")
        if not r.get("evidence"):
            error("missing primary evidence")
        for ev in r.get("evidence", []):
            parsed_url = urllib.parse.urlsplit(ev.get("url", ""))
            if ev.get("role") != "primary" or not re.fullmatch(r"[0-9a-f]{64}", ev.get("sha256", "")) or not ev.get("supports") or parsed_url.scheme != "https" or not parsed_url.netloc:
                error("invalid evidence receipt")
            try:
                dt.datetime.fromisoformat(ev["retrieved_at"].replace("Z", "+00:00"))
            except (ValueError, KeyError):
                error("invalid evidence timestamp")
        for relation in r.get("relations", []):
            if relation.get("target_id") not in ids:
                error(f"dangling reviewed relation {relation.get('target_id')}")
            if relation.get('evidence_url') not in {e.get('url') for e in r.get('evidence',[])}:
                error('reviewed relation lacks a retained primary evidence receipt')
        for key in ("published_at", "updated_at"):
            value = r.get(key)
            if value is not None:
                try:
                    dt.date.fromisoformat(value)
                    if value > r["last_verified_at"][:10]:
                        error(f"{key} is after its verification date")
                except (ValueError, KeyError):
                    error(f"invalid {key}")
    return errors


def coverage(rows, pending, scope_decisions):
    ids = {r["id"] for r in rows}
    by_id = {r["id"]: r for r in rows}
    candidates = read_jsonl(DATA / "candidates.jsonl")
    runs = {r["id"]: r for r in read_json(DATA / "discovery-runs.json", [])}
    sources = read_json(DATA / "sources.json", [])
    excluded = {row['id'] for row in scope_decisions if row['status']=='excluded'}
    source_rows = []
    for source in sources:
        population = {r["id"] for r in candidates if any(o["source_id"] == source["id"] for o in r["discovered_in"])}
        present = population & ids
        source_rows.append({"id": source["id"], "name": source["name"], "url": source["homepage"],
            "snapshot": runs.get(source["id"]), "discovered": len(population), "indexed": len(present),
            "curated": sum(by_id[i]["review_status"] == "curated" for i in present), "excluded":len(population & excluded), "unindexed": len(population - ids - excluded)})
    latest = max((e["retrieved_at"] for r in rows for e in r["evidence"]), default="")
    return {"as_of_utc": latest, "total_records": len(rows), "curated_records": sum(r["review_status"] == "curated" for r in rows),
        "bibliographic_records": sum(r["id"].startswith("arxiv:") for r in rows),
        "arxiv_archive_records":len(read_jsonl(DATA/'papers.jsonl')),
        "excluded_records":len(excluded),
        "exclusion_revalidation_pending":sum(row['status']=='revalidation_pending' for row in scope_decisions),
        "metadata_only_records": sum(r["review_status"] == "metadata_verified" for r in rows),
        "discovery_identifiers": len(candidates), "unindexed_candidates": len({r["id"] for r in candidates} - ids - excluded),
        "pending_editorial": pending, "by_kind": dict(sorted(collections.Counter(r["kind"] for r in rows).items())),
        "curated_by_environment": dict(sorted(collections.Counter(e for r in rows if r["review_status"] == "curated" for e in r["environments"]).items())),
        "curated_by_kind_and_environment": {kind: dict(sorted(collections.Counter(e for r in rows if r["review_status"] == "curated" and r["kind"] == kind for e in set(r["environments"])).items()))
            for kind in sorted({r["kind"] for r in rows if r["review_status"] == "curated"})},
        "license_declarations_by_scope": {slot: sum(r["licenses"][slot] is not None for r in rows) for slot in ("code", "data", "weights", "document")},
        "sources": source_rows, "primary_search": read_json(DATA / "arxiv-search.json", {}),
        "paper_discovery": read_json(DATA / 'paper-discovery-status.json', {}),
        "paper_query_registry": read_json(DATA / 'paper-discovery-queries.json', {}),
        "limits": ["Counts are resources, not distinct projects, companies, or independent discoveries.",
            "Metadata verification does not establish relevance, quality, reproducibility, availability, or endorsement.",
            "Source indexing measures only fetched source snapshots; incidental/out-of-scope links remain in discovery.",
            "Global completeness has no observed denominator and is not claimed.",
            "Environment facets overlap. Unknown license, size, price, or performance fields are not inferred."]}


def md(value):
    return str(value).replace("|", "\\|").replace("\n", " ").replace("[", "\\[").replace("]", "\\]")


def paper_cell(r, by_id):
    """Reviewed paper relations only; a mention in a README is not a paper link."""
    targets = list(dict.fromkeys(rel["target_id"] for rel in r["relations"] if rel["type"] in {"introduced_by", "documented_by"} and rel["target_id"].startswith("arxiv:")))
    cells = []
    for target in targets:
        paper = by_id.get(target)
        year = f" ({paper['published_at'][:4]})" if paper and paper.get("published_at") else ""
        cells.append(f"[{target.split(':', 1)[1]}](https://arxiv.org/abs/{target.split(':', 1)[1]}){year}")
    return ", ".join(cells) or "—"


def license_cell(r):
    """Declared licenses per scope; unknown scopes are omitted, never inferred."""
    parts = []
    for scope in ("code", "data", "weights", "document"):
        declared = (r["licenses"].get(scope) or {}).get("declared")
        if declared:
            parts.append(f"{scope} {md('/'.join(declared) if isinstance(declared, list) else declared)}")
    return " · ".join(parts) or "—"


def publisher_cell(r, by_id):
    publishers = [by_id[rel["target_id"]] for rel in r["relations"] if rel["type"] == "published_by" and rel["target_id"] in by_id]
    return ", ".join(f"[{md(p['name'])}]({p['url']})" for p in publishers) or "—"


EVIDENCE_NOTE = "*Evidence* links the reviewed first-party snapshot and its retrieval date."
# Columns per generated category page; facts that cannot apply to a kind are not shown as empty columns.
KIND_COLUMNS = {
    None: (("Resource", "Environments", "Paper", "License", "Description", "Evidence"),
        "*Paper* lists reviewed `introduced_by`/`documented_by` arXiv relations with the arXiv submission year. *License* lists publisher declarations by scope (code, data, weights, document). " + EVIDENCE_NOTE),
    # The arXiv abstract link is the reviewed source; its API receipt stays in data/catalog.jsonl.
    "paper": (("Date", "Resource", "Environments", "Description"), "*Date* is the arXiv first-submission date; newest first. Each title links the reviewed arXiv record; API receipts are in `data/catalog.jsonl`."),
    "survey": (("Date", "Resource", "Environments", "Description"), "*Date* is the arXiv first-submission date; newest first. Each title links the reviewed arXiv record; API receipts are in `data/catalog.jsonl`."),
    "product": (("Resource", "Publisher", "Environments", "Description", "Evidence"), "*Publisher* is a reviewed `published_by` relation. " + EVIDENCE_NOTE),
    "company": (("Resource", "Environments", "Description", "Evidence"), EVIDENCE_NOTE),
}


# Category-page sections; a resource spanning several families is cross-platform by definition.
ENVIRONMENT_FAMILIES = [("web", "Web", {"web"}), ("desktop", "Desktop", {"desktop", "windows", "macos", "linux"}),
    ("mobile", "Mobile", {"android", "ios", "harmonyos"}), ("cross-platform", "Cross-platform", {"cross-platform"}), ("unspecified", "Unspecified", {"unspecified"})]


def environment_family(r):
    families = {slug for slug, _, members in ENVIRONMENT_FAMILIES if members & set(r["environments"])}
    return families.pop() if len(families) == 1 else "cross-platform"


def table_row(r, columns, by_id):
    primary = next(e for e in r["evidence"] if e["method"] == "editorial_primary_review")
    cells = {"Resource": f"[{md(r['name'])}]({r['url']})", "Environments": ", ".join(r["environments"]),
        "Paper": paper_cell(r, by_id), "License": license_cell(r), "Publisher": publisher_cell(r, by_id),
        "Date": r.get("published_at") or "—", "Description": md(r["summary"]),
        "Evidence": f"[✓ {primary['retrieved_at'][:10]}]({primary['url']})"}
    return "| " + " | ".join(cells[column] for column in columns) + " |"


TOPIC_LABELS = {"safety-security": "Safety and security", "cross-app": "Cross-app workflows", "human-in-the-loop": "Human-in-the-loop",
    "long-horizon": "Long-horizon tasks", "ui-design": "UI design", "training-free": "Training-free methods", "self-reflection": "Self-reflection"}
TOPIC_KINDS = [("benchmark", "Benchmarks"), ("dataset", "Datasets"), ("model", "Models"), ("agent", "Agents"), ("framework", "Frameworks"),
    ("tool", "Tools"), ("infrastructure", "Infrastructure"), ("product", "Products"), ("company", "Publishers"), ("survey", "Surveys"), ("paper", "Papers")]


def topic_label(topic):
    return TOPIC_LABELS.get(topic, topic.replace("-", " ").capitalize())


def topic_pages(rows):
    """One generated hub per curated topic, listing every reviewed resource kind tagged with it."""
    by_id = {r["id"]: r for r in rows}
    tagged = collections.defaultdict(list)
    for r in rows:
        if r["review_status"] == "curated":
            for topic in sorted(set(r["topics"])):
                tagged[topic].append(r)
    order = sorted(tagged, key=lambda t: (-len(tagged[t]), t))
    files = {}
    index = ["# Reviewed research by topic", "", "[Home](../README.md) · [Full arXiv bibliography](papers.md) · [Methodology](methodology.md)", "",
        f"{sum(r['review_status'] == 'curated' for r in rows):,} source-reviewed resources across {len(order)} topics. Topic tags are catalog annotations from the editorial review, not author keywords; a resource appears under every topic it carries. Each hub lists benchmarks, data, models, systems, and papers together, newest papers first.", "",
        "| Topic | All | Benchmarks | Datasets | Models | Systems | Papers | Newest reviewed paper |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for topic in order:
        group = tagged[topic]
        kinds = collections.Counter(r["kind"] for r in group)
        papers = sorted((r for r in group if r["kind"] in {"paper", "survey"}), key=lambda r: (r.get("published_at") or "", r["name"]), reverse=True)
        systems = sum(kinds[k] for k in ("agent", "framework", "tool", "infrastructure", "product", "company"))
        newest = f"[{md(papers[0]['name'])}]({papers[0]['url']}) · {papers[0]['published_at'] or '—'}" if papers else "—"
        cell = lambda n: f"{n:,}" if n else "·"
        index.append(f"| [{topic_label(topic)}](topics/{topic}.md) | {len(group):,} | {cell(kinds['benchmark'])} | {cell(kinds['dataset'])} | {cell(kinds['model'])} | {cell(systems)} | {cell(len(papers))} | {newest} |")
        lines = [f"# {topic_label(topic)}", "", f"[Home](../../README.md) · [All topics](../topics.md) · [Full arXiv bibliography](../papers.md)", "",
            f"{len(group):,} source-reviewed resources tagged `{topic}`. Curated metadata, not a performance ranking; unknown facts are shown as —.", "",
            "**Contents:** " + " · ".join(f"[{label} ({kinds[kind]})](#{label.lower()})" for kind, label in TOPIC_KINDS if kinds[kind]), ""]
        for kind, label in TOPIC_KINDS:
            members = [r for r in group if r["kind"] == kind]
            if not members:
                continue
            columns = KIND_COLUMNS.get(kind, KIND_COLUMNS[None])[0]
            members.sort(key=lambda r: r["name"].casefold())
            if "Date" in columns:
                members.sort(key=lambda r: r.get("published_at") or "", reverse=True)
            lines += [f"## {label}", "", "| " + " | ".join(columns) + " |", "|" + " --- |" * len(columns), *(table_row(r, columns, by_id) for r in members), ""]
        files[f"docs/topics/{topic}.md"] = "\n".join(lines)
    files["docs/topics.md"] = "\n".join(index + [""])
    return files


MATRIX_ENVIRONMENTS = ["web", "desktop", "windows", "macos", "linux", "android", "ios", "harmonyos", "cross-platform", "unspecified"]


def matrix_lines(matrix):
    lines = ["| Kind | " + " | ".join(MATRIX_ENVIRONMENTS) + " |", "| --- |" + " ---: |" * len(MATRIX_ENVIRONMENTS)]
    for kind, counts in matrix.items():
        lines.append(f"| [{kind}]({'companies' if kind == 'company' else 'topics' if kind == 'paper' else kind + 's'}.md) | " + " | ".join(str(counts[e]) if counts.get(e) else "·" for e in MATRIX_ENVIRONMENTS) + " |")
    return lines


def documents(rows, report):
    files = {}
    by_id = {r["id"]: r for r in rows}
    grouped = collections.defaultdict(list)
    for r in rows:
        if r["review_status"] == "curated":
            grouped[r["kind"]].append(r)
    for kind, group in sorted(grouped.items()):
        if kind == "paper":
            # Reviewed papers are published by topic (docs/topics/); docs/papers.md is the full bibliography.
            continue
        columns, legend = KIND_COLUMNS.get(kind, KIND_COLUMNS[None])
        title = f"{kind.title()} catalog"
        sections = collections.defaultdict(list)
        for r in group:
            sections[environment_family(r)].append(r)
        present = [(slug, label) for slug, label, _ in ENVIRONMENT_FAMILIES if sections[slug]]
        lines = [f"# {title}", "", "[Home](../README.md) · [Methodology](methodology.md) · [Machine-readable catalog](../data/catalog.jsonl)", "",
            "Curated metadata, not a performance ranking. Each entry links its first-party evidence. Unknown facts are shown as —.", "", legend, "",
            f"**{len(group)} resources:** " + " · ".join(f"[{label} ({len(sections[slug])})](#{slug})" for slug, label in present), "",
            "Resources tagged with environments from more than one family are listed under *Cross-platform*; their exact environments stay in the table.", ""]
        for slug, label in present:
            ordered = sorted(sections[slug], key=lambda r: r["name"].casefold())
            if "Date" in columns:
                ordered.sort(key=lambda r: r.get("published_at") or "", reverse=True)
            lines += [f"## {label}", "", "| " + " | ".join(columns) + " |", "|" + " --- |" * len(columns), *(table_row(r, columns, by_id) for r in ordered),
                "", f"[↑ Back to top](#{title.lower().replace(' ', '-')})", ""]
        lines += ["Detailed notes and separate code/data/weights license declarations are in `data/catalog.jsonl`.", ""]
        filename = "companies" if kind == "company" else kind + "s"
        files[f"docs/{filename}.md"] = "\n".join(lines)
    paper_lines = ["# Research bibliography", "", "[Home](../README.md) · [Reviewed research by topic](topics.md) · [Curated surveys](surveys.md) · [Query examples](query-guide.md)", "",
        "Official arXiv bibliographic metadata. Most entries have **not** undergone a relevance or methodological review. Discovery includes historical references and adjacent work; this is not a count of confirmed CUA papers.",
        "Explicit scope exclusions are listed in the [scope-decision ledger](../data/exclusion-status.json); original records remain in the [metadata archive](../data/papers.jsonl).", ""]
    years = collections.defaultdict(list)
    for r in rows:
        if r["id"].startswith("arxiv:") or (r["kind"] == "paper" and r["review_status"] == "curated"):
            years[r["published_at"][:4] if r["published_at"] else "Undated"].append(r)
    order = sorted((y for y in years if y != "Undated"), reverse=True) + (["Undated"] if "Undated" in years else [])
    reviewed = lambda group: sum(r["review_status"] == "curated" for r in group)
    paper_lines += ["**Years:** " + " · ".join(f"[{y}](#{y.lower()}) ({len(years[y]):,}; {reviewed(years[y]):,} ⭐)" for y in order), "",
        "⭐ marks papers with an editorial relevance review; their topics link to the [topic hubs](topics.md). Other rows are arXiv metadata only.", ""]
    for year in order:
        paper_lines += [f"## {year}", "", "| Date | Paper | Review | Topics |", "| --- | --- | --- | --- |"]
        for r in sorted(years[year], key=lambda r: (r["published_at"] or "", r["name"]), reverse=True):
            curated = r["review_status"] == "curated"
            topics = ", ".join(f"[{t}](topics/{t}.md)" for t in sorted(set(r["topics"]))) if curated else ""
            paper_lines.append(f"| {r['published_at'] or '—'} | [{md(r['name'])}]({r['url']}) | {'⭐ reviewed' if curated else 'metadata'} | {topics} |")
        paper_lines.append("")
    files["docs/papers.md"] = "\n".join(paper_lines)
    hubs = topic_pages(rows)
    if hubs.keys() & files.keys():
        raise ValueError("Generated paths assigned twice: " + ", ".join(sorted(hubs.keys() & files.keys())))
    files.update(hubs)
    lines = ["# Coverage and quality ledger", "", f"Evidence snapshot through **{report['as_of_utc']}**. Generated from committed source receipts.", "",
        f"- {report['total_records']:,} resource records: {report['curated_records']:,} curated; {report['metadata_only_records']:,} bibliographic metadata only.",
        f"- {report['bibliographic_records']:,} arXiv records, including curated surveys. This count overlaps the status counts above.",
        f"- {report['arxiv_archive_records']:,} retained arXiv metadata records; {report['excluded_records']:,} explicit scope exclusions are outside the active catalog.",
        f"- {report['discovery_identifiers']:,} discovery identifiers; {report['unindexed_candidates']:,} remain unresolved after accounting for scope exclusions.",
        f"- {len(report['pending_editorial'])} editorial proposals await verification or review.", "",
        "These are distinct resource identifiers, not distinct research projects. Papers, repositories, datasets, products, and publisher entities have different grains.", "",
        "## Curated coverage by kind and environment", "", "Counts of source-reviewed resources. A resource tagged with several environments counts in each column; `·` marks an empty cell, which is where contributions are most needed.", "",
        *matrix_lines(report["curated_by_kind_and_environment"]), "",
        "## Source snapshot coverage", "", "The denominator is the normalized identifiers extracted from each fetched document, including incidental links. Sources overlap. These figures do not measure global completeness or editorial recall.", "",
        "| Source | Discovered | Indexed | Curated | Excluded | Unresolved | Fetch |", "| --- | ---: | ---: | ---: | ---: | ---: | --- |"]
    for s in report["sources"]:
        status = s["snapshot"] or {}
        lines.append(f"| [{md(s['name'])}]({s['url']}) | {s['discovered']} | {s['indexed']} | {s['curated']} | {s['excluded']} | {s['unindexed']} | {'OK' if status.get('ok') else 'FAILED'} · {status.get('retrieved_at', '')[:10]} |")
    search = report["primary_search"]
    discovery = report.get('paper_discovery', {})
    if discovery:
        lines += ['', '## Paper-discovery query coverage', '',
            f"Latest pass: {discovery.get('finished_at') or 'in progress'}; **{discovery.get('successful_query_count',0)}/{discovery.get('configured_query_count',0)}** query windows succeeded. {discovery.get('unique_identifiers',0):,} distinct identifiers; {discovery.get('new_candidate_count',0):,} new to the candidate queue.", '',
            'These are ranked search windows, not a field-wide denominator. New identifiers still require primary metadata verification and relevance review.', '',
            '| Area | Query | Returned / limit | State |', '| --- | --- | ---: | --- |']
        for item in discovery.get('queries', []):
            lines.append(f"| {md(item['area'])} | {md(item['query'])} | {item['returned_count']} / {item['limit']} | {md(item['state'])} |")
    lines += ["", "## Primary arXiv discovery", "", f"The recorded title query returned {search.get('unique_returned', 0):,} unique records out of {search.get('reported_total', 0):,} reported matches. Pagination complete: **{search.get('complete', False)}**. This query population overlaps the lists and is not the whole field.", "", "```text", search.get("query", ""), "```", "",
        "## License evidence", "", "| Scope | Recorded declarations |", "| --- | ---: |"]
    lines += [f"| {slot} | {n} |" for slot, n in report["license_declarations_by_scope"].items()]
    lines += ["", "A code license never fills a data or weights field. Hub declarations are publisher metadata, not independently audited legal conclusions. Missing values remain null.", "",
        "## Pending editorial proposals", "", "| Resource | Reason |", "| --- | --- |"]
    for p in report["pending_editorial"]:
        lines.append(f"| [{md(p['name'])}]({p['url']}) | {md(p['reason'])} |")
    lines += ["", "## Scope exclusions", "", f"{report['excluded_records']} records have an applied scope decision; {report['exclusion_revalidation_pending']} require another review after a change. See the [decision ledger](../data/exclusion-status.json) for each rationale and source fingerprint. These decisions concern catalog relevance, not research quality. Original bibliographic metadata is retained, and previous resource URLs explain the decision rather than silently disappearing.", "", "## Known gaps", "",
        "- Most bibliography records still require relevance review and detailed taxonomy.",
        "- Closed/private datasets, unpublished systems, regional products, and work absent from arXiv/lists are not exhaustively represented.",
        "- Asset sizes, model weights licenses, runtime requirements, and benchmark protocols need additional field-level curation.",
        "- Publisher entries cover selected brands; corporate ownership, funding, usage, revenue, and product pricing are not researched here.",
        "- Download links and available code do not establish that an asset is reproducible or still works.",
        "- Name changes, repository transfers, and related resource families need continuing entity resolution.", "",
        "See [methodology](methodology.md) for the inclusion boundary and [the review queue](../data/review-queue.jsonl) for actionable gaps.", ""]
    files["docs/coverage.md"] = "\n".join(lines)
    return files


def shield(label, message, color):
    escape = lambda text: urllib.parse.quote(str(text).replace("-", "--").replace("_", "__"), safe="")
    return f"https://img.shields.io/badge/{escape(label)}-{escape(message)}-{color}"


def badges(rows, report):
    curated = report["curated_records"]
    return ("\n" + " ".join([
        f"[![Resources]({shield('resources', format(report['total_records'], ','), '4f46e5')})](data/catalog.jsonl)",
        f"[![Curated]({shield('source-reviewed', format(curated, ','), '0e8a16')})](docs/coverage.md)",
        f"[![Evidence]({shield('evidence through', report['as_of_utc'][:10], '1d76db')})](docs/coverage.md)",
        "[![Catalog quality](https://github.com/reacher-z/Awesome-CUA/actions/workflows/catalog.yml/badge.svg)](https://github.com/reacher-z/Awesome-CUA/actions/workflows/catalog.yml)",
        f"[![License]({shield('license', 'MIT', 'blue')})](LICENSE)",
        f"[![Website]({shield('website', 'awesomecua.github.io', '6366f1')})](https://awesomecua.github.io/)"]) + "\n")


# README category layout: rows of (left, right) cells; each cell lists (label, generated page, kind). Counts are curated resources.
EXPLORE = [
    ([("Research by topic", "docs/topics.md", "paper"), ("Full bibliography", "docs/papers.md", "bibliography")], [("Agents", "docs/agents.md", "agent")]),
    ([("Surveys", "docs/surveys.md", "survey")], [("Frameworks", "docs/frameworks.md", "framework")]),
    ([("Datasets", "docs/datasets.md", "dataset")], [("Infrastructure", "docs/infrastructures.md", "infrastructure")]),
    ([("Benchmarks", "docs/benchmarks.md", "benchmark")], [("Tools", "docs/tools.md", "tool")]),
    ([("Models and checkpoint releases", "docs/models.md", "model")], [("Products", "docs/products.md", "product"), ("Publishers and brands", "docs/companies.md", "company")]),
]


def explore(rows, report):
    curated = collections.Counter(r["kind"] for r in rows if r["review_status"] == "curated")
    def link(label, path, kind):
        if kind == "paper":
            return f"[{label}]({path}) · **{curated[kind]:,}** reviewed papers"
        if kind == "bibliography":
            return f"[{label}]({path}) · {report['bibliographic_records']:,} arXiv records"
        return f"[{label}]({path}) · **{curated[kind]:,}**"
    lines = ["| Research and training | Engineering and industry |", "| --- | --- |"]
    lines += [f"| {' · '.join(link(*item) for item in left)} | {' · '.join(link(*item) for item in right)} |" for left, right in EXPLORE]
    return "\n" + "\n".join(lines) + "\n"


HIGHLIGHT_KINDS = [("benchmark", "Benchmarks", "docs/benchmarks.md"), ("model", "Models", "docs/models.md"), ("dataset", "Datasets", "docs/datasets.md"),
    ("framework", "Frameworks", "docs/frameworks.md"), ("agent", "Agents", "docs/agents.md")]


def highlights(rows, edges, limit=6):
    """Rank curated resources by distinct cataloged resources whose reviewed source mentions them; not a quality ranking."""
    by_id = {r["id"]: r for r in rows}
    cited_by = collections.defaultdict(set)
    for edge in edges:
        if edge["target_in_catalog"] and edge["source_id"] != edge["target_id"]:
            cited_by[edge["target_id"]].add(edge["source_id"])
    lines = [""]
    for kind, label, path in HIGHLIGHT_KINDS:
        curated = [r for r in rows if r["kind"] == kind and r["review_status"] == "curated"]
        ranked = sorted((r for r in curated if cited_by[r["id"]]), key=lambda r: (-len(cited_by[r["id"]]), r["name"].casefold()))[:limit]
        if not ranked:
            continue
        lines += [f"**{label}** · [all {len(curated)} →]({path})", "", "| Resource | Mentioned by | Environments | Paper | License | Description |", "| --- | ---: | --- | --- | --- | --- |"]
        lines += [f"| [{md(r['name'])}]({r['url']}) | {len(cited_by[r['id']])} | {', '.join(r['environments'])} | {paper_cell(r, by_id)} | {license_cell(r)} | {md(r['summary'])} |" for r in ranked]
        lines.append("")
    return "\n".join(lines) + "\n"


def recently_reviewed(rows, reviewed_at, limit=12):
    """Newest editorial approvals of non-paper resources; papers are listed by date in the topic hubs."""
    recent = sorted((r for r in rows if r["review_status"] == "curated" and r["kind"] not in {"paper", "survey"} and reviewed_at.get(r["id"])),
        key=lambda r: (reviewed_at[r["id"]], r["name"].casefold()), reverse=True)[:limit]
    lines = ["", "| Reviewed | Resource | Kind | Environments | Description |", "| --- | --- | --- | --- | --- |"]
    lines += [f"| {reviewed_at[r['id']][:10]} | [{md(r['name'])}]({r['url']}) | {r['kind']} | {', '.join(r['environments'])} | {md(r['summary'])} |" for r in recent]
    return "\n".join(lines) + "\n" if recent else "\n"


def write_sqlite(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.unlink(missing_ok=True)
    con = sqlite3.connect(temporary)
    con.executescript("""
        CREATE TABLE resources(id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL, url TEXT NOT NULL,
          review_status TEXT NOT NULL, scope TEXT NOT NULL, published_at TEXT, summary TEXT, record_json TEXT NOT NULL);
        CREATE TABLE facets(resource_id TEXT NOT NULL REFERENCES resources(id), facet TEXT NOT NULL, value TEXT NOT NULL,
          PRIMARY KEY(resource_id, facet, value));
        CREATE TABLE relations(source_id TEXT NOT NULL REFERENCES resources(id), relation TEXT NOT NULL, target_id TEXT NOT NULL,
          evidence_url TEXT NOT NULL, PRIMARY KEY(source_id, relation, target_id));
        CREATE VIRTUAL TABLE resource_search USING fts5(id UNINDEXED, name, summary, aliases, authors, topics);
        CREATE INDEX resources_kind ON resources(kind, review_status);
        CREATE INDEX facets_lookup ON facets(facet, value);
    """)
    for row in rows:
        con.execute("INSERT INTO resources VALUES(?,?,?,?,?,?,?,?,?)", (row["id"], row["name"], row["kind"], row["url"], row["review_status"], row["scope"], row["published_at"], row["summary"], json.dumps(row, ensure_ascii=False)))
        for facet in ("environments", "topics"):
            for value in sorted(set(row[facet])):
                con.execute("INSERT INTO facets VALUES(?,?,?)", (row["id"], facet, value))
        for relation in row["relations"]:
            con.execute("INSERT INTO relations VALUES(?,?,?,?)", (row["id"], relation["type"], relation["target_id"], relation["evidence_url"]))
        con.execute("INSERT INTO resource_search VALUES(?,?,?,?,?,?)", (row["id"], row["name"], row["summary"] or "", " ".join(row["aliases"]), " ".join(row["authors"]), " ".join(row["topics"])))
    con.commit()
    con.close()
    temporary.replace(path)


def build(args):
    rows, pending, scope_decisions = source_records(with_scope=True)
    errors = validate_records(rows)
    if errors:
        raise ValueError("\n".join(errors[:30]))
    report = coverage(rows, pending, scope_decisions)
    files = documents(rows, report)
    stats = (f"\n\n**{report['total_records']:,} resource records** · **{report['curated_records']:,} curated** · "
        f"**{report['bibliographic_records']:,} arXiv records** · **{len(report['sources'])} discovery documents**\n\n"
        f"Evidence through `{report['as_of_utc']}`. {report['metadata_only_records']:,} records have bibliographic verification only; "
        f"{report['unindexed_candidates']:,} discovered identifiers remain unresolved. "
        f"{report['excluded_records']:,} scope exclusions retain their original metadata in the archive. Counts overlap as explained below.\n\n")
    files["data/catalog.jsonl"] = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
    files["data/coverage.json"] = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    files['data/exclusion-status.json'] = json.dumps(scope_report(scope_decisions),ensure_ascii=False,indent=2)+'\n'
    ids = {r["id"] for r in rows}
    excluded = {row['id'] for row in scope_decisions if row['status']=='excluded'}
    candidates = read_jsonl(DATA / "candidates.jsonl")
    queue = [{**r, "review_status": "candidate", "reason": "discovered identifier; primary evidence and relevance need review"} for r in candidates if r["id"] not in ids and r['id'] not in excluded]
    editorial_pending = {r["id"]: r for r in pending}
    merged = {r["id"]: r for r in queue}
    for rid, item in editorial_pending.items():
        merged[rid] = {**merged.get(rid, {}), **item, "review_status": "candidate"}
    files["data/review-queue.jsonl"] = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in sorted(merged.values(), key=lambda r: r["id"]))
    edges = []
    row_map = {r["id"]: r for r in rows}
    for r in read_jsonl(DATA / "enrichment.jsonl"):
        if r["id"] not in ids or not any(e["sha256"] == r.get("evidence_sha256") for e in row_map[r["id"]]["evidence"]):
            continue
        for ref in r.get("references", []):
            edges.append({"id": hashlib.sha256((r["id"] + "\0" + ref["target_id"]).encode()).hexdigest()[:24], "source_id": r["id"], **ref, "target_in_catalog": ref["target_id"] in ids})
    files["data/references.jsonl"] = "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n" for e in sorted(edges, key=lambda e: e["id"]))
    reviewed_at = {(e.get("id") or canonical(e["url"])[0]): e.get("reviewed_at") for e in read_json(DATA / "editorial.json", []) if e.get("editorial_reviewed")}
    blocks = {"STATS": stats, "BADGES": badges(rows, report), "EXPLORE": explore(rows, report), "HIGHLIGHTS": highlights(rows, edges), "RECENT": recently_reviewed(rows, reviewed_at)}
    for filename in ("README.md", "README.zh-CN.md"):
        path = ROOT / filename
        if path.exists():
            content = path.read_text()
            for name, body in blocks.items():
                # A function replacement keeps backslashes in generated Markdown literal.
                content = re.sub(rf"(?<=<!-- {name}:START -->).*?(?=<!-- {name}:END -->)", lambda _: body, content, flags=re.S)
            files[filename] = content
    changed = []
    for relative, content in files.items():
        path = ROOT / relative
        if not path.exists() or path.read_text() != content:
            changed.append(relative)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
    if args.check:
        if changed:
            raise ValueError("Generated files are stale: " + ", ".join(changed))
        print(f"Generated views match {len(rows)} source-backed records.")
        return
    write_sqlite(rows, ROOT / "dist" / "catalog.sqlite")
    write_json(ROOT / "dist" / "catalog.json", rows)
    print(f"Built {len(rows)} records ({report['curated_records']} curated), {len(edges)} reference edges, {len(merged)} review items, and SQLite/JSON exports.")


def validate(args):
    rows = read_jsonl(DATA / "catalog.jsonl")
    if not rows:
        raise ValueError("No catalog. Run build first.")
    errors = validate_records(rows)
    # Full published JSON Schema validation is part of the release/CI gate.
    import jsonschema
    validator = jsonschema.Draft202012Validator(read_json(ROOT / "schemas" / "resource.schema.json"), format_checker=jsonschema.FormatChecker())
    for row in rows:
        errors.extend(f"{row['id']}: {error.message}" for error in validator.iter_errors(row))
    decisions = read_json(DATA/'exclusions.json', [])
    scope_validator = jsonschema.Draft202012Validator(read_json(ROOT/'schemas/scope-decision.schema.json'), format_checker=jsonschema.FormatChecker())
    scope_errors = ['Scope decisions: '+error.message for error in scope_validator.iter_errors(decisions)]
    errors.extend(scope_errors)
    if not scope_errors:
        retained = {row['id']:row for row in read_jsonl(DATA/'papers.jsonl')}
        retained.update({row['id']:row for row in rows})
        outcomes = resolve_exclusions(retained, decisions, {row['id'] for row in read_jsonl(DATA/'metadata-updates.jsonl')})
        published = {row['id'] for row in rows}
        for outcome in outcomes:
            if outcome['status']=='excluded' and outcome['id'] in published:
                errors.append(outcome['id']+': scope-excluded record remains in the active catalog')
            if outcome['status']=='revalidation_pending' and outcome['id'] not in published:
                errors.append(outcome['id']+': stale scope decision must not suppress a record')
    if errors:
        raise ValueError("\n".join(errors[:40]))
    print(f"Validated {len(rows)} records: JSON Schema, identifiers, dates, source receipts, scoped licenses, and reviewed relation targets.")


def search(args):
    # Literal AND search is intentionally safe and works without a generated database.
    terms = args.query.casefold().split()
    result = []
    for row in read_jsonl(DATA / "catalog.jsonl"):
        if args.kind and row["kind"] != args.kind:
            continue
        if args.status and row["review_status"] != args.status:
            continue
        if args.environment and args.environment not in row["environments"]:
            continue
        if args.topic and args.topic not in row["topics"]:
            continue
        haystack = " ".join([row["name"], row["summary"] or "", *row["aliases"], *row["authors"], *row["topics"]]).casefold()
        if all(term in haystack for term in terms):
            result.append(row)
    result.sort(key=lambda r: (r["review_status"] != "curated", r["name"].casefold()))
    limited = result[:args.limit] if args.limit else result
    if args.json:
        print(json.dumps({"total_matches": len(result), "returned": len(limited), "records": limited}, ensure_ascii=False, indent=2))
    else:
        print(f"{len(result)} matches; showing {len(limited)}")
        for r in limited:
            print(f"{r['name']} [{r['kind']} · {r['review_status']}]\n  {r['url']}")
