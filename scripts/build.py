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


def source_records():
    records = {r["id"]: copy.deepcopy(r) for r in read_jsonl(DATA / "papers.jsonl")}
    evidence = {r["id"]: r for r in read_jsonl(DATA / "primary-evidence.jsonl")}
    enrichment = {r["id"]: r for r in read_jsonl(DATA / "enrichment.jsonl")}
    pending = []
    for row in records.values():
        row.update(scope="relevance_pending", details={})
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
        details = copy.deepcopy(editorial.get("details", {}))
        details.update(extra.get("details", {}))
        if editorial["kind"] == "dataset":
            for key, default in {"sample_count": None, "sample_unit": None, "modalities": [], "download_url": None, "languages": []}.items():
                details.setdefault(key, default)
        if editorial["kind"] == "benchmark":
            for key, default in {"task_count": None, "metrics": [], "evaluation_type": None, "leaderboard_url": None}.items():
                details.setdefault(key, default)
        relations = []
        for aid in editorial.get("paper_ids", []):
            target = "arxiv:" + aid
            relations.append({"type": "introduced_by", "target_id": target, "evidence_url": ev["url"]})
        if editorial.get("publisher_id"):
            relations.append({"type": "published_by", "target_id": editorial["publisher_id"], "evidence_url": ev["url"]})
        if editorial.get("component_of"):
            relations.append({"type": "component_of", "target_id": canonical(editorial["component_of"])[0], "evidence_url": ev["url"]})
        if editorial.get("family_url"):
            relations.append({"type": "variant_of", "target_id": canonical(editorial["family_url"])[0], "evidence_url": ev["url"]})
        primary = {"role": "primary", "method": "editorial_primary_review", "supports": ["name", "kind", "summary", "environments", "topics", "scope", "relations"],
            "url": ev["url"], "retrieved_at": ev["retrieved_at"], "sha256": ev["sha256"]}
        if editorial.get("details"):
            primary["supports"].append("details")
        row = {"id": rid, "name": editorial["name"], "kind": editorial["kind"], "url": editorial["url"],
            "aliases": editorial.get("aliases", []), "environments": editorial["environments"], "topics": editorial["topics"],
            "scope": editorial.get("scope", "core"), "summary": editorial["summary"], "review_status": "curated",
            "published_at": base.get("published_at"), "updated_at": base.get("updated_at"), "authors": base.get("authors", []),
            "identifiers": base.get("identifiers", {}), "links": [{"rel": "primary", "url": editorial["url"]}],
            "relations": relations, "licenses": licenses, "evidence": base.get("evidence", []) + [primary] + extra.get("evidence", []),
            "last_verified_at": ev["retrieved_at"], "notes": editorial.get("notes", ""), "details": details}
        records[rid] = row
    return sorted(records.values(), key=lambda r: r["id"]), pending


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


def coverage(rows, pending):
    ids = {r["id"] for r in rows}
    by_id = {r["id"]: r for r in rows}
    candidates = read_jsonl(DATA / "candidates.jsonl")
    runs = {r["id"]: r for r in read_json(DATA / "discovery-runs.json", [])}
    sources = read_json(DATA / "sources.json", [])
    source_rows = []
    for source in sources:
        population = {r["id"] for r in candidates if any(o["source_id"] == source["id"] for o in r["discovered_in"])}
        present = population & ids
        source_rows.append({"id": source["id"], "name": source["name"], "url": source["homepage"],
            "snapshot": runs.get(source["id"]), "discovered": len(population), "indexed": len(present),
            "curated": sum(by_id[i]["review_status"] == "curated" for i in present), "unindexed": len(population - ids)})
    latest = max((e["retrieved_at"] for r in rows for e in r["evidence"]), default="")
    return {"as_of_utc": latest, "total_records": len(rows), "curated_records": sum(r["review_status"] == "curated" for r in rows),
        "bibliographic_records": sum(r["id"].startswith("arxiv:") for r in rows),
        "metadata_only_records": sum(r["review_status"] == "metadata_verified" for r in rows),
        "discovery_identifiers": len(candidates), "unindexed_candidates": len({r["id"] for r in candidates} - ids),
        "pending_editorial": pending, "by_kind": dict(sorted(collections.Counter(r["kind"] for r in rows).items())),
        "curated_by_environment": dict(sorted(collections.Counter(e for r in rows if r["review_status"] == "curated" for e in r["environments"]).items())),
        "license_declarations_by_scope": {slot: sum(r["licenses"][slot] is not None for r in rows) for slot in ("code", "data", "weights", "document")},
        "sources": source_rows, "primary_search": read_json(DATA / "arxiv-search.json", {}),
        "limits": ["Counts are resources, not distinct projects, companies, or independent discoveries.",
            "Metadata verification does not establish relevance, quality, reproducibility, availability, or endorsement.",
            "Source indexing measures only fetched source snapshots; incidental/out-of-scope links remain in discovery.",
            "Global completeness has no observed denominator and is not claimed.",
            "Environment facets overlap. Unknown license, size, price, or performance fields are not inferred."]}


def md(value):
    return str(value).replace("|", "\\|").replace("\n", " ").replace("[", "\\[").replace("]", "\\]")


def documents(rows, report):
    files = {}
    grouped = collections.defaultdict(list)
    for r in rows:
        if r["review_status"] == "curated":
            grouped[r["kind"]].append(r)
    for kind, group in sorted(grouped.items()):
        lines = [f"# {kind.title()} catalog", "", "[Home](../README.md) · [Methodology](methodology.md) · [Machine-readable catalog](../data/catalog.jsonl)", "",
            "Curated metadata, not a performance ranking. Each entry links its first-party evidence. Empty facts remain unknown.", "",
            "| Resource | Environments | Description | Evidence |", "| --- | --- | --- | --- |"]
        for r in sorted(group, key=lambda r: r["name"].casefold()):
            primary = next(e for e in r["evidence"] if e["method"] == "editorial_primary_review")
            lines.append(f"| [{md(r['name'])}]({r['url']}) | {', '.join(r['environments'])} | {md(r['summary'])} | [Source]({primary['url']}) · {primary['retrieved_at'][:10]} |")
        lines += ["", "Detailed notes and separate code/data/weights license declarations are in `data/catalog.jsonl`.", ""]
        filename = "companies" if kind == "company" else kind + "s"
        files[f"docs/{filename}.md"] = "\n".join(lines)
    paper_lines = ["# Research bibliography", "", "[Home](../README.md) · [Curated surveys](surveys.md) · [Query examples](query-guide.md)", "",
        "Official arXiv bibliographic metadata. Most entries have **not** undergone a relevance or methodological review. Discovery includes historical references and adjacent work; this is not a count of confirmed CUA papers.", ""]
    years = collections.defaultdict(list)
    for r in rows:
        if r["id"].startswith("arxiv:"):
            years[(r["published_at"] or "unknown")[:4]].append(r)
    for year in sorted(years, reverse=True):
        paper_lines += [f"## {year}", "", "| Date | Paper | Review |", "| --- | --- | --- |"]
        for r in sorted(years[year], key=lambda r: (r["published_at"], r["name"]), reverse=True):
            paper_lines.append(f"| {r['published_at']} | [{md(r['name'])}]({r['url']}) | {r['review_status']} |")
        paper_lines.append("")
    files["docs/papers.md"] = "\n".join(paper_lines)
    lines = ["# Coverage and quality ledger", "", f"Evidence snapshot through **{report['as_of_utc']}**. Generated from committed source receipts.", "",
        f"- {report['total_records']:,} resource records: {report['curated_records']:,} curated; {report['metadata_only_records']:,} bibliographic metadata only.",
        f"- {report['bibliographic_records']:,} arXiv records, including curated surveys. This count overlaps the status counts above.",
        f"- {report['discovery_identifiers']:,} discovery identifiers; {report['unindexed_candidates']:,} have no published catalog record.",
        f"- {len(report['pending_editorial'])} editorial proposals await verification or review.", "",
        "These are distinct resource identifiers, not distinct research projects. Papers, repositories, datasets, products, and publisher entities have different grains.", "",
        "## Source snapshot coverage", "", "The denominator is the normalized identifiers extracted from each fetched document, including incidental links. Sources overlap. These figures do not measure global completeness or editorial recall.", "",
        "| Source | Discovered | Indexed | Curated | Unindexed | Fetch |", "| --- | ---: | ---: | ---: | ---: | --- |"]
    for s in report["sources"]:
        status = s["snapshot"] or {}
        lines.append(f"| [{md(s['name'])}]({s['url']}) | {s['discovered']} | {s['indexed']} | {s['curated']} | {s['unindexed']} | {'OK' if status.get('ok') else 'FAILED'} · {status.get('retrieved_at', '')[:10]} |")
    search = report["primary_search"]
    lines += ["", "## Primary arXiv discovery", "", f"The recorded title query returned {search.get('unique_returned', 0):,} unique records out of {search.get('reported_total', 0):,} reported matches. Pagination complete: **{search.get('complete', False)}**. This query population overlaps the lists and is not the whole field.", "", "```text", search.get("query", ""), "```", "",
        "## License evidence", "", "| Scope | Recorded declarations |", "| --- | ---: |"]
    lines += [f"| {slot} | {n} |" for slot, n in report["license_declarations_by_scope"].items()]
    lines += ["", "A code license never fills a data or weights field. Hub declarations are publisher metadata, not independently audited legal conclusions. Missing values remain null.", "",
        "## Pending editorial proposals", "", "| Resource | Reason |", "| --- | --- |"]
    for p in report["pending_editorial"]:
        lines.append(f"| [{md(p['name'])}]({p['url']}) | {md(p['reason'])} |")
    lines += ["", "## Known gaps", "",
        "- Most bibliography records still require relevance review and detailed taxonomy.",
        "- Closed/private datasets, unpublished systems, regional products, and work absent from arXiv/lists are not exhaustively represented.",
        "- Asset sizes, model weights licenses, runtime requirements, and benchmark protocols need additional field-level curation.",
        "- Publisher entries cover selected brands; corporate ownership, funding, usage, revenue, and product pricing are not researched here.",
        "- Download links and available code do not establish that an asset is reproducible or still works.",
        "- Name changes, repository transfers, and related resource families need continuing entity resolution.", "",
        "See [methodology](methodology.md) for the inclusion boundary and [the review queue](../data/review-queue.jsonl) for actionable gaps.", ""]
    files["docs/coverage.md"] = "\n".join(lines)
    return files


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
    rows, pending = source_records()
    errors = validate_records(rows)
    if errors:
        raise ValueError("\n".join(errors[:30]))
    report = coverage(rows, pending)
    files = documents(rows, report)
    stats = (f"\n\n**{report['total_records']:,} resource records** · **{report['curated_records']:,} curated** · "
        f"**{report['bibliographic_records']:,} arXiv records** · **{len(report['sources'])} discovery documents**\n\n"
        f"Evidence through `{report['as_of_utc']}`. {report['metadata_only_records']:,} records have bibliographic verification only; "
        f"{report['unindexed_candidates']:,} discovered identifiers remain unindexed. Counts overlap as explained below.\n\n")
    for filename in ("README.md", "README.zh-CN.md"):
        path = ROOT / filename
        if path.exists():
            content = path.read_text()
            files[filename] = re.sub(r"(?<=<!-- STATS:START -->).*?(?=<!-- STATS:END -->)", stats, content, flags=re.S)
    files["data/catalog.jsonl"] = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
    files["data/coverage.json"] = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    ids = {r["id"] for r in rows}
    candidates = read_jsonl(DATA / "candidates.jsonl")
    queue = [{**r, "review_status": "candidate", "reason": "discovered identifier; primary evidence and relevance need review"} for r in candidates if r["id"] not in ids]
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
