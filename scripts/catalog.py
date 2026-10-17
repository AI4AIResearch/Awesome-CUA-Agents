#!/usr/bin/env python3
"""Reproducible CUA metadata catalog. Standard library only; no remote code execution."""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from arxiv_metadata import entry_snapshot, consider_paper, parse_search_feed

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "http"
DATA = ROOT / "data"
UA = "Awesome-CUA/0.1 (+https://github.com/reacher-z/Awesome-CUA)"
ARXIV_RE = re.compile(r"(?:arxiv\.org/(?:abs|pdf|html)/|huggingface\.co/papers/)(\d{4}\.\d{4,5})(?:v\d+)?", re.I)
KINDS = {"paper", "survey", "model", "dataset", "benchmark", "agent", "framework", "infrastructure", "product", "company", "tool", "learning"}
ENVIRONMENTS = {"web", "desktop", "android", "ios", "harmonyos", "windows", "macos", "linux", "cross-platform", "unspecified"}
STATUSES = {"curated", "metadata_verified"}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_json(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in sorted(rows, key=lambda r: r["id"])))


def fetch(url, refresh=False):
    """Cache successful GETs; persist failures as evidence, never as successful content."""
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(url.encode()).hexdigest()
    info_path, body_path = CACHE / f"{key}.json", CACHE / f"{key}.body"
    old = read_json(info_path, {})
    if not refresh and old.get("ok") and body_path.exists():
        return old, body_path.read_bytes()
    info = {"url": url, "retrieved_at": now(), "ok": False}
    try:
        request = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, application/atom+xml, text/html, text/plain, */*"})
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read(10_000_001)
            if len(body) > 10_000_000:
                raise ValueError("response exceeds 10 MB metadata budget")
            info.update(ok=True, status=response.status, final_url=response.url,
                        content_type=response.headers.get("Content-Type", ""),
                        sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))
        body_path.write_bytes(body)
        write_json(info_path, info)
        return info, body
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as error:
        info.update(error=str(error), status=getattr(error, "code", None))
        headers = getattr(error, "headers", None)
        if headers and headers.get('Retry-After'):
            info['retry_after'] = headers.get('Retry-After')
        # Keep the previous successful cache intact when a refresh fails.
        write_json(CACHE / f"{key}.error.json", info)
        return info, b""


def canonical(url):
    """Resource identity: arXiv version folding, GitHub repo folding, URL cleanup."""
    url = html.unescape(url).strip().rstrip(".,;:)").replace("http://", "https://", 1)
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError:
        return None
    if parts.scheme != "https" or not parts.netloc:
        return None
    host = parts.hostname.lower() if parts.hostname else ""
    if host in {"arxiv.org", "www.arxiv.org", "export.arxiv.org", "huggingface.co"}:
        match = ARXIV_RE.search(url)
        if match:
            aid = match.group(1)
            return f"arxiv:{aid}", f"https://arxiv.org/abs/{aid}", "arxiv"
    if host in {"github.com", "www.github.com"}:
        segments = parts.path.strip("/").split("/")
        if len(segments) < 2 or segments[0].lower() in {"topics", "orgs", "users", "settings", "sponsors", "features", "collections", "marketplace", "user-attachments"}:
            return None
        owner, repo = segments[:2]
        repo = re.sub(r"\.git$", "", repo, flags=re.I)
        if not re.fullmatch(r"[\w.-]+", owner) or not re.fullmatch(r"[\w.-]+", repo):
            return None
        if len(segments) > 2 and segments[2] not in {"tree", "blob"}:
            return None
        return f"github:{owner.lower()}/{repo.lower()}", f"https://github.com/{owner}/{repo}", "github"
    if host.endswith(("shields.io", "githubusercontent.com")) or host in {"doi.org", "img.shields.io", "badge.fury.io", "twitter.com", "x.com", "discord.gg", "linkedin.com", "www.linkedin.com", "youtube.com", "www.youtube.com"}:
        return None
    if re.search(r"\.(png|svg|jpg|jpeg|gif|webp)$", parts.path, re.I):
        return None
    query = urllib.parse.urlencode([(k, v) for k, v in urllib.parse.parse_qsl(parts.query) if not k.startswith("utm_")])
    clean = urllib.parse.urlunsplit(("https", host, parts.path.rstrip("/"), query, ""))
    return "url:" + hashlib.sha256(clean.encode()).hexdigest()[:20], clean, "url"


def source_links(source, body):
    """Parse only declared source formats; provider metadata remains a candidate."""
    parser = source.get('parser', 'links')
    if parser == 'huggingface_models':
        url = urllib.parse.urlsplit(source['url'])
        params = urllib.parse.parse_qs(url.query)
        if url.scheme != 'https' or url.hostname != 'huggingface.co' or url.path != '/api/models':
            raise ValueError('Model-index source must be the official Hugging Face models API')
        author = params.get('author', [''])[0]
        limit = params.get('limit', [''])[0]
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', author) or not limit.isdigit() or not 1 <= int(limit) <= 100:
            raise ValueError('Model-index source requires one publisher and a limit of 1..100')
        payload = json.loads(body)
        if not isinstance(payload, list) or len(payload) > int(limit):
            raise ValueError('Model-index response exceeds its declared window or is not a list')
        result = []
        for item in payload:
            identity = item.get('id') if isinstance(item, dict) else None
            if not isinstance(identity, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', identity):
                raise ValueError('Model-index entry has an invalid repository identifier')
            if identity.split('/')[0].casefold() != author.casefold():
                raise ValueError('Model-index entry is outside the declared publisher')
            result.append((None, 'Publisher model index; relevance and variant identity await review', 'https://huggingface.co/' + identity))
        return result
    if parser != 'links':
        raise ValueError('Unknown discovery source parser: ' + str(parser))
    result, heading = [], ''
    for line_no, line in enumerate(body.decode('utf-8', errors='replace').splitlines(), 1):
        if line.startswith('#'):
            heading = re.sub(r'[#*_]', '', line).strip()[:140]
        result.extend((line_no, heading, url) for url in re.findall(r"https?://[^\s<>\]\[\)\"']+", line))
    return result


def discovery_occurrence(source_id, info, line=None, section=''):
    """Keep source facts with the occurrence, even after its latest run fails."""
    evidence = {key: info[key] for key in ('url', 'sha256', 'retrieved_at')}
    identity = json.dumps([source_id, evidence['url'], evidence['sha256']], separators=(',', ':'))
    return {'source_id': source_id, 'line': line, 'section': section,
            'snapshot_sha256': evidence['sha256'],
            'receipt_id': 'discovery:' + hashlib.sha256(identity.encode()).hexdigest(),
            'evidence': evidence}


def retain_discovery_evidence(rows, previous_runs):
    """Backfill only matching old receipts; never relabel old content as current."""
    for row in rows:
        for occurrence in row.get('discovered_in', []):
            if occurrence.get('evidence'):
                continue
            previous = previous_runs.get(occurrence['source_id'], {})
            info = previous.get('evidence', previous)
            if (info.get('ok') and not previous.get('parse_error')
                    and info.get('sha256') == occurrence.get('snapshot_sha256')
                    and all(info.get(key) for key in ('url', 'sha256', 'retrieved_at'))):
                receipt = discovery_occurrence(occurrence['source_id'], info)
                occurrence.update({key: receipt[key] for key in ('receipt_id', 'evidence')})


def discover(args):
    sources = read_json(DATA / "sources.json", [])
    existing = {r["id"]: r for r in read_jsonl(DATA / "candidates.jsonl")}
    previous = {r["id"]: r for r in read_json(DATA / "discovery-runs.json", [])}
    retain_discovery_evidence(existing.values(), previous)
    manifests, rate_limited_hosts = {}, set()
    started = now()
    for source in sources:
        host = urllib.parse.urlsplit(source['url']).hostname
        deferred = host in rate_limited_hosts
        if deferred:
            info, body = {'url': source['url'], 'retrieved_at': now(), 'ok': False,
                'error': 'Deferred after an HTTP 429 from this host; no request made.'}, b''
        else:
            info, body = fetch(source["url"], args.refresh)
        manifest = {"id": source["id"], **info, "unique_resources": 0,
            'run_started_at': started, 'provider_host': host,
            'request_attempted': not deferred, 'state': 'deferred' if deferred else 'failed'}
        if info.get('status') == 429:
            rate_limited_hosts.add(host)
        if not info["ok"]:
            manifests[source["id"]] = manifest
            print(f"FAILED {source['id']}: {info['error']}", flush=True)
            continue
        try:
            links = source_links(source, body)
        except (ValueError, TypeError) as error:
            manifests[source['id']] = {**manifest, 'ok': False, 'parse_error': str(error)}
            print(f"FAILED {source['id']}: {error}", flush=True)
            continue
        # Replace this source's old occurrences so deleted links remain historical candidates,
        # but cannot inflate current source coverage.
        for row in existing.values():
            row["discovered_in"] = [o for o in row["discovered_in"] if o["source_id"] != source["id"]]
        seen = set()
        for line_no, heading, url in links:
            parsed = canonical(url)
            if not parsed:
                continue
            rid, clean, provider = parsed
            if rid in seen or clean.lower() == source["homepage"].rstrip("/").lower():
                continue
            seen.add(rid)
            row = existing.setdefault(rid, {"id": rid, "url": clean, "provider": provider,
                "first_discovered_at": info["retrieved_at"], "discovered_in": []})
            row["discovered_in"].append(discovery_occurrence(source['id'],
                {**info, 'url': source['url']}, line_no, heading))
        manifest["unique_resources"] = len(seen)
        manifest['state'] = 'success'
        manifests[source["id"]] = manifest
        print(f"{source['id']}: {len(seen)} unique identifiers", flush=True)
    for row in existing.values():
        row["discovered_in"].sort(key=lambda x: (x["source_id"], x["line"]))
    write_jsonl(DATA / "candidates.jsonl", existing.values())
    write_json(DATA / "discovery-runs.json", sorted(manifests.values(), key=lambda r: r["id"]))
    from collections import Counter
    print(json.dumps(Counter(r["provider"] for r in existing.values())))


def arxiv_entry(entry, evidence):
    ns = {"a": "http://www.w3.org/2005/Atom", "ar": "http://arxiv.org/schemas/atom"}
    get = lambda key: " ".join((entry.findtext("a:" + key, default="", namespaces=ns)).split())
    parsed = canonical(get("id"))
    if not parsed or parsed[2] != "arxiv":
        return None
    rid, url, _ = parsed
    title = get("title")
    if not title:
        return None
    return {"id": rid, "name": title, "kind": "paper", "url": url,
        "aliases": [], "environments": ["unspecified"], "topics": [],
        "summary": None, "review_status": "metadata_verified",
        "published_at": get("published")[:10] or None, "updated_at": get("updated")[:10] or None,
        "authors": [" ".join((a.findtext("a:name", default="", namespaces=ns)).split()) for a in entry.findall("a:author", ns)],
        "identifiers": {"arxiv": rid.split(":", 1)[1]},
        "details": {"arxiv_snapshot": entry_snapshot(entry, rid.split(":", 1)[1])},
        "links": [{"rel": "paper", "url": url}], "relations": [],
        "licenses": {"code": None, "data": None, "weights": None, "document": None},
        "evidence": [{"role": "primary", "method": "arxiv_api", "supports": ["name", "authors", "published_at", "updated_at", "identifiers.arxiv", "details.arxiv_snapshot"], **evidence}],
        "last_verified_at": evidence["retrieved_at"],
        "notes": "Bibliographic metadata checked against arXiv. Relevance and taxonomy await editorial review; presence is not an endorsement."}


def harvest(args):
    candidates = read_jsonl(DATA / "candidates.jsonl")
    records = {r["id"]: r for r in read_jsonl(DATA / "papers.jsonl")}
    proposals = {r['id']: r for r in read_jsonl(DATA / 'metadata-updates.jsonl')}
    ids = sorted({r["id"].split(":", 1)[1] for r in candidates if r["provider"] == "arxiv" and (args.refresh or r["id"] not in records)})
    if args.limit:
        ids = ids[:args.limit]
    failures = []
    for start in range(0, len(ids), 50):
        batch = ids[start:start + 50]
        url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"id_list": ",".join(batch), "max_results": len(batch)})
        info, body = fetch(url, args.refresh)
        got, invalid = set(), {}
        if info["ok"]:
            try:
                root = ET.fromstring(body)
                if root.tag != '{http://www.w3.org/2005/Atom}feed':
                    raise ValueError('arXiv response is not an Atom feed')
                for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
                    try:
                        row = arxiv_entry(entry, {k: info[k] for k in ("url", "retrieved_at", "sha256")})
                    except ValueError as error:
                        parsed = canonical(entry.findtext("{http://www.w3.org/2005/Atom}id", ""))
                        if parsed and parsed[2] == "arxiv":
                            invalid[parsed[0].split(":", 1)[1]] = f"invalid Atom entry: {error}"
                        continue
                    if row and row["id"].split(":", 1)[1] in batch:
                        consider_paper(row, records, proposals, info['retrieved_at'])
                        got.add(row["id"].split(":", 1)[1])
            except (ET.ParseError, ValueError) as error:
                info["error"] = str(error)
        for aid in sorted(set(batch) - got):
            failures.append({"id": f"arxiv:{aid}", "checked_at": info["retrieved_at"], "error": invalid.get(aid) or info.get("error", "identifier absent from API response")})
        print(f"arXiv {start + 1}-{start + len(batch)}/{len(ids)}: {len(got)} metadata records", flush=True)
        write_jsonl(DATA / "papers.jsonl", records.values())
        write_jsonl(DATA / "metadata-updates.jsonl", proposals.values())
        if info.get('status') == 429:
            for aid in ids[start + len(batch):]:
                failures.append({'id': 'arxiv:' + aid, 'checked_at': info['retrieved_at'],
                    'deferred': True, 'request_attempted': False,
                    'error': 'Deferred after an arXiv HTTP 429; no additional request made in this harvest.'})
            break
        if start + 50 < len(ids):
            time.sleep(3.1)
    write_jsonl(DATA / "harvest-failures.jsonl", failures)
    print(f"Stored {len(records)} papers; {len(failures)} unresolved in this run.")


def search_arxiv(args):
    """Primary-source discovery with persisted queries and explicit pagination limits."""
    query = 'ti:"computer use" OR ti:"computer-use" OR ti:"GUI agent" OR ti:"GUI agents" OR ti:"GUI grounding" OR ti:"web agents" OR ti:"browser agent"'
    cutoff = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M")
    query = f'({query}) AND submittedDate:[200001010000 TO {cutoff}]'
    records = {r["id"]: r for r in read_jsonl(DATA / "papers.jsonl")}
    proposals = {r['id']: r for r in read_jsonl(DATA / 'metadata-updates.jsonl')}
    candidates = {r["id"]: r for r in read_jsonl(DATA / "candidates.jsonl")}
    pages, seen = [], set()
    start, total = 0, None
    ceiling = args.limit or 5000
    while start < ceiling and (total is None or start < total):
        batch_size = min(100, ceiling-start)
        url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": query, "start": start, "max_results": batch_size, "sortBy": "submittedDate", "sortOrder": "descending"})
        info, body = fetch(url, args.refresh)
        if not info["ok"]:
            pages.append(info)
            break
        try:
            entries,total = parse_search_feed(body,total,batch_size)
        except (ET.ParseError,ValueError) as error:
            pages.append({**info, "ok": False, "error": str(error)})
            break
        page = {**info, "start": start, "returned": len(entries)}
        pages.append(page)
        for entry in entries:
            try:
                row = arxiv_entry(entry, {k: info[k] for k in ("url", "retrieved_at", "sha256")})
            except ValueError as error:
                page.setdefault("entry_errors", []).append({"id": " ".join(entry.findtext("{http://www.w3.org/2005/Atom}id", "").split()), "error": str(error)})
                continue
            if not row:
                continue
            rid = row["id"]
            consider_paper(row,records,proposals,info['retrieved_at'])
            seen.add(rid)
            candidate = candidates.setdefault(rid, {"id": rid, "url": row["url"], "provider": "arxiv", "first_discovered_at": info["retrieved_at"], "discovered_in": []})
            candidate["discovered_in"] = [o for o in candidate["discovered_in"] if o["source_id"] != "arxiv-title-search"]
            candidate["discovered_in"].append({"source_id": "arxiv-title-search", "line": None, "section": "Title query; relevance not reviewed", "snapshot_sha256": info["sha256"]})
        print(f"arXiv search {start + len(entries)}/{total}", flush=True)
        write_jsonl(DATA / "papers.jsonl", records.values())
        write_jsonl(DATA / "metadata-updates.jsonl", proposals.values())
        write_jsonl(DATA / "candidates.jsonl", candidates.values())
        if not entries:
            break
        start += len(entries)
        if start < min(total, ceiling):
            time.sleep(3.1)
    write_json(DATA / "arxiv-search.json", {"id": "arxiv-title-search", "query": query, "cutoff_utc": cutoff,
        "reported_total": total, "unique_returned": len(seen), "complete": total is not None and len(seen) == total and bool(pages) and all(page.get('ok') and not page.get('entry_errors') for page in pages),
        "pages": pages, "warning": "A title query is a discovery population, not the whole field. Search results are metadata-verified, not editorially curated."})


def require_editorial_identities(rows):
    """Stop before any network work if an editorial URL has no resource identity."""
    invalid = [f"INVALID {row.get('name', '')}: {row['url']} has no canonical identity" for row in rows if not canonical(row["url"])]
    if invalid:
        raise SystemExit("\n".join(invalid))


def verify_editorial(args):
    """Retrieve first-party evidence for editorial entries; never promote on HTTP status alone."""
    rows = read_json(DATA / "editorial.json", [])
    require_editorial_identities(rows)
    previous = {r["id"]: r for r in read_jsonl(DATA / "primary-evidence.jsonl")}

    def one(row):
        rid, url, provider = canonical(row["url"])
        rid = row.get("id", rid)
        url = row["url"]
        urls = row.get("evidence_urls", [])
        if not urls:
            if provider == "github":
                repo = url.split("github.com/", 1)[1]
                urls = [f"https://raw.githubusercontent.com/{repo}/HEAD/README.md", f"https://raw.githubusercontent.com/{repo}/HEAD/README.MD", f"https://raw.githubusercontent.com/{repo}/HEAD/readme.md", url]
            elif url.startswith("https://huggingface.co/datasets/"):
                urls = [url.replace("huggingface.co/datasets/", "huggingface.co/api/datasets/")]
            elif url.startswith("https://huggingface.co/") and "/collections/" not in url:
                urls = [url.replace("huggingface.co/", "huggingface.co/api/models/")]
            else:
                urls = [url]
        attempts = []
        for evidence_url in urls:
            info, body = fetch(evidence_url, args.refresh)
            attempts.append(info)
            if info["ok"]:
                text = body.decode("utf-8", errors="replace")
                terms = row.get("verify_terms", [row["name"]])
                matched = [term for term in terms if " ".join(term.casefold().split()) in " ".join(text.casefold().split())]
                # A soft-200 challenge/landing page must not be treated as primary evidence.
                blocked = any(s in text[:15000].lower() for s in ("just a moment...", "checking your browser", "verify you are human"))
                ok = bool(matched) and not blocked
                result = {"id": rid, "source_url": url, **info, "content_matched": ok, "matched_terms": matched, "attempts": len(attempts)}
                if ok:
                    for supporting in row.get("additional_evidence", []):
                        supporting_info, _ = fetch(supporting["url"], args.refresh)
                        if not supporting_info["ok"] or supporting_info.get("sha256") != supporting["sha256"]:
                            result.update(content_matched=False, error="supporting source unavailable or changed; editorial review required: " + supporting["url"])
                            break
                    return result
        return {"id": rid, "source_url": url, **attempts[-1], "content_matched": False, "attempts": len(attempts)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(one, rows):
            previous[result["id"]] = result
            print(f"{'MATCH' if result['content_matched'] else 'REVIEW'} {result['id']} {result.get('status')}", flush=True)
    write_jsonl(DATA / "primary-evidence.jsonl", previous.values())


def cached_body(url):
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest() + ".body")
    return path.read_bytes() if path.exists() else b""


def enrich(args):
    """Extract declared licenses and outbound references without inferring semantic relationships."""
    rows = read_json(DATA / "editorial.json", [])
    require_editorial_identities(rows)
    evidence = {r["id"]: r for r in read_jsonl(DATA / "primary-evidence.jsonl")}
    previous = {r["id"]: r for r in read_jsonl(DATA / "enrichment.jsonl")}

    def one(row):
        rid, url, provider = canonical(row["url"])
        rid = row.get("id", rid)
        ev = evidence.get(rid)
        if not ev or not ev.get("content_matched"):
            return None
        raw = cached_body(ev["url"]).decode("utf-8", errors="replace")
        if provider == "github" and "<html" in raw.lower():
            # Restrict reference extraction to the rendered README, excluding site navigation.
            article = re.search(r"<article\b[^>]*>(.*?)</article>", raw, re.S)
            raw = article.group(1) if article else ""
        result = {"id": rid, "evidence_sha256": ev["sha256"], "licenses": {}, "details": {}, "references": [], "evidence": []}
        source = urllib.parse.urlsplit(ev["url"])
        hub_source = source.hostname == "huggingface.co"
        # A raw Hub card may be the reviewed primary source rather than the API.
        # Read only an explicit scalar declaration in its metadata header; do not
        # inherit a dataset/model license from a linked repository or prose.
        if hub_source and "/raw/" in source.path:
            header = re.match(r"\A---\r?\n(.*?)\r?\n---", raw, re.S)
            declaration = re.search(r"^license:[ \t]*([a-zA-Z0-9][a-zA-Z0-9_.-]*)[ \t]*$", header[1], re.M) if header else None
            slot = "data" if row["kind"] == "dataset" else "weights" if row["kind"] == "model" else None
            if declaration and slot:
                result["licenses"][slot] = {"declared": declaration[1], "url": ev["url"], "retrieved_at": ev["retrieved_at"], "basis": "publisher model/dataset card metadata; third-party assets retain their own terms"}
                result["evidence"].append({"role": "primary", "method": "huggingface_card", "supports": [f"licenses.{slot}"], **{k: ev[k] for k in ("url", "sha256", "retrieved_at")}})
        if hub_source and source.path.startswith(("/api/datasets/", "/api/models/")):
            payload = json.loads(raw)
            card = payload.get("cardData") or {}
            slot = "data" if source.path.startswith("/api/datasets/") else "weights"
            license_name = card.get("license")
            if license_name:
                result["licenses"][slot] = {"declared": license_name, "url": row["url"], "retrieved_at": ev["retrieved_at"], "basis": "publisher model/dataset card"}
            result["details"] = {"hub_id": payload.get("id"), "gated": payload.get("gated"), "disabled": payload.get("disabled"),
                "languages": card.get("language", []), "modalities": [t.split(":", 1)[1] for t in payload.get("tags", []) if t.startswith("modality:")],
                "size_category_reported": card.get("size_categories"), "download_url": row["url"] + "/tree/main"}
            # Dataset size tags may count archive files, not samples; never convert them into sample counts.
            result["evidence"].append({"role": "primary", "method": "huggingface_api", "url": ev["url"], "sha256": ev["sha256"], "retrieved_at": ev["retrieved_at"], "supports": ["details", f"licenses.{slot}"]})
        elif row["kind"] == "dataset" and source.hostname == "dataverse.harvard.edu" and source.path.startswith("/api/datasets/"):
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = None
            dataset = payload.get("data") if isinstance(payload, dict) and payload.get("status") == "OK" else None
            version = dataset.get("latestVersion") if isinstance(dataset, dict) else None
            if (isinstance(version, dict) and dataset.get("datasetType") == "dataset"
                    and version.get("datasetType") == "dataset" and isinstance(version.get("metadataBlocks"), dict)):
                license_metadata = version.get("license")
                if not isinstance(license_metadata, dict):
                    license_metadata = None
                result["details"]["dataverse"] = {
                    "publisher": dataset.get("publisher"), "persistent_url": dataset.get("persistentUrl"),
                    "publication_date": dataset.get("publicationDate"), "version_number": version.get("versionNumber"),
                    "version_minor_number": version.get("versionMinorNumber"), "version_state": version.get("versionState"),
                    "released_at": version.get("releaseTime"), "license": license_metadata,
                    "file_count": len(version["files"]) if isinstance(version.get("files"), list) else None,
                }
                # Keep the publisher's license text/URI verbatim, including its scheme.
                # The HTTPS API receipt is the license source; files are not samples,
                # and neither fileAccessRequest nor a DOI establishes a download URL.
                supports = ["details.dataverse"]
                license_name = license_metadata.get("name") if license_metadata else None
                if isinstance(license_name, str) and license_name.strip():
                    result["licenses"]["data"] = {"declared": license_name, "url": ev["url"], "retrieved_at": ev["retrieved_at"],
                        "basis": "publisher Dataverse dataset-version license metadata; original declaration and URI retained in details.dataverse.license"}
                    supports.append("licenses.data")
                result["evidence"].append({"role": "primary", "method": "dataverse_api", "supports": supports,
                    **{k: ev[k] for k in ("url", "sha256", "retrieved_at")}})
        if provider == "github":
            repo = url.split("github.com/", 1)[1]
            for filename in ("LICENSE", "LICENSE.md", "LICENSE.txt"):
                license_url = f"https://raw.githubusercontent.com/{repo}/HEAD/{filename}"
                info, body = fetch(license_url, args.refresh)
                if not info["ok"]:
                    continue
                license_text = body.decode("utf-8", errors="replace")
                declared = None
                if re.search(r"^\s*(?:The )?MIT License", license_text, re.I):
                    declared = "MIT"
                elif "Apache License" in license_text[:250] and "Version 2.0" in license_text[:300]:
                    declared = "Apache-2.0"
                elif "BSD 3-Clause" in license_text[:100]:
                    declared = "BSD-3-Clause"
                elif "BSD 2-Clause" in license_text[:100]:
                    declared = "BSD-2-Clause"
                # Ambiguous/custom/composite declarations stay unknown rather than being guessed.
                if declared:
                    result["licenses"]["code"] = {"declared": declared, "url": license_url, "retrieved_at": info["retrieved_at"], "basis": "repository LICENSE header; not a weights/data license"}
                    result["evidence"].append({"role": "primary", "method": "license_header", "supports": ["licenses.code"], **{k: info[k] for k in ("url", "sha256", "retrieved_at")}})
                break
        seen = set()
        if provider == "arxiv":
            # A batched API response is not a paper's reference list.
            return result
        for link in re.findall(r"https?://[^\s<>\]\[\)\"']+", raw):
            parsed = canonical(link)
            if not parsed:
                continue
            target, clean, target_provider = parsed
            if target == rid or target in seen or not (target_provider in {"arxiv", "github"} or clean.startswith("https://huggingface.co/")):
                continue
            seen.add(target)
            result["references"].append({"target_id": target, "target_url": clean, "relation": "mentions", "source_url": ev["url"], "source_sha256": ev["sha256"], "retrieved_at": ev["retrieved_at"]})
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(one, rows):
            if result:
                previous[result["id"]] = result
    write_jsonl(DATA / "enrichment.jsonl", previous.values())
    print(f"Enrichment receipts: {len(previous)}")


def nonnegative(value):
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError(f"must be 0 or greater: {value}")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, function in [("discover", discover), ("harvest", harvest), ("search-arxiv", search_arxiv), ("verify", verify_editorial), ("enrich", enrich)]:
        command = sub.add_parser(name)
        command.add_argument("--refresh", action="store_true", help="fetch new snapshots instead of reusing local cache")
        command.add_argument("--limit", type=int, default=0)
        command.set_defaults(function=function)
    from build import build, validate, search
    command = sub.add_parser("build", help="generate catalog, category docs, coverage, JSON and SQLite exports offline")
    command.add_argument("--check", action="store_true", help="fail if generated committed views differ")
    command.set_defaults(function=build)
    command = sub.add_parser("validate", help="validate catalog against JSON Schema and quality invariants")
    command.set_defaults(function=validate)
    command = sub.add_parser("search", help="search names, descriptions, aliases, authors, curated topics, ids and URLs")
    command.add_argument("query", nargs="?", default="")
    command.add_argument("--kind", choices=sorted(KINDS))
    command.add_argument("--status", choices=sorted(STATUSES))
    command.add_argument("--environment", choices=sorted(ENVIRONMENTS))
    command.add_argument("--topic")
    command.add_argument("--limit", type=nonnegative, default=20, help="0 returns every match")
    command.add_argument("--json", action="store_true")
    command.set_defaults(function=search)
    args = parser.parse_args()
    args.function(args)


if __name__ == "__main__":
    main()
