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


def discover(args):
    sources = read_json(DATA / "sources.json", [])
    existing = {r["id"]: r for r in read_jsonl(DATA / "candidates.jsonl")}
    manifests = {r["id"]: r for r in read_json(DATA / "discovery-runs.json", [])}
    for source in sources:
        info, body = fetch(source["url"], args.refresh)
        manifest = {"id": source["id"], **info, "unique_resources": 0}
        if not info["ok"]:
            manifests[source["id"]] = manifest
            print(f"FAILED {source['id']}: {info['error']}", flush=True)
            continue
        # Replace this source's old occurrences so deleted links remain historical candidates,
        # but cannot inflate current source coverage.
        for row in existing.values():
            row["discovered_in"] = [o for o in row["discovered_in"] if o["source_id"] != source["id"]]
        seen = set()
        heading = ""
        for line_no, line in enumerate(body.decode("utf-8", errors="replace").splitlines(), 1):
            if line.startswith("#"):
                heading = re.sub(r"[#*_]", "", line).strip()[:140]
            for url in re.findall(r"https?://[^\s<>\]\[\)\"']+", line):
                parsed = canonical(url)
                if not parsed:
                    continue
                rid, clean, provider = parsed
                if rid in seen or clean.lower() == source["homepage"].rstrip("/").lower():
                    continue
                seen.add(rid)
                row = existing.setdefault(rid, {"id": rid, "url": clean, "provider": provider,
                    "first_discovered_at": info["retrieved_at"], "discovered_in": []})
                row["discovered_in"].append({"source_id": source["id"], "line": line_no,
                    "section": heading, "snapshot_sha256": info["sha256"]})
        manifest["unique_resources"] = len(seen)
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
        "links": [{"rel": "paper", "url": url}], "relations": [],
        "licenses": {"code": None, "data": None, "weights": None, "document": None},
        "evidence": [{"role": "primary", "method": "arxiv_api", "supports": ["name", "authors", "published_at", "updated_at", "identifiers.arxiv"], **evidence}],
        "last_verified_at": evidence["retrieved_at"],
        "notes": "Bibliographic metadata checked against arXiv. Relevance and taxonomy await editorial review; presence is not an endorsement."}


def harvest(args):
    candidates = read_jsonl(DATA / "candidates.jsonl")
    records = {r["id"]: r for r in read_jsonl(DATA / "papers.jsonl")}
    ids = sorted({r["id"].split(":", 1)[1] for r in candidates if r["provider"] == "arxiv" and (args.refresh or r["id"] not in records)})
    if args.limit:
        ids = ids[:args.limit]
    failures = []
    for start in range(0, len(ids), 50):
        batch = ids[start:start + 50]
        url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"id_list": ",".join(batch), "max_results": len(batch)})
        info, body = fetch(url, args.refresh)
        got = set()
        if info["ok"]:
            try:
                root = ET.fromstring(body)
                for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
                    row = arxiv_entry(entry, {k: info[k] for k in ("url", "retrieved_at", "sha256")})
                    if row and row["id"].split(":", 1)[1] in batch:
                        records[row["id"]] = row
                        got.add(row["id"].split(":", 1)[1])
            except ET.ParseError as error:
                info["error"] = str(error)
        for aid in sorted(set(batch) - got):
            failures.append({"id": f"arxiv:{aid}", "checked_at": info["retrieved_at"], "error": info.get("error", "identifier absent from API response")})
        print(f"arXiv {start + 1}-{start + len(batch)}/{len(ids)}: {len(got)} metadata records", flush=True)
        write_jsonl(DATA / "papers.jsonl", records.values())
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
    candidates = {r["id"]: r for r in read_jsonl(DATA / "candidates.jsonl")}
    pages, seen = [], set()
    start, total = 0, None
    ceiling = args.limit or 5000
    while start < ceiling and (total is None or start < total):
        url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": query, "start": start, "max_results": min(100, ceiling - start), "sortBy": "submittedDate", "sortOrder": "descending"})
        info, body = fetch(url, args.refresh)
        if not info["ok"]:
            pages.append(info)
            break
        try:
            root = ET.fromstring(body)
        except ET.ParseError as error:
            pages.append({**info, "ok": False, "error": str(error)})
            break
        total = int(root.findtext("{http://a9.com/-/spec/opensearch/1.1/}totalResults", "0"))
        entries = root.findall("{http://www.w3.org/2005/Atom}entry")
        pages.append({**info, "start": start, "returned": len(entries)})
        for entry in entries:
            row = arxiv_entry(entry, {k: info[k] for k in ("url", "retrieved_at", "sha256")})
            if not row:
                continue
            rid = row["id"]
            records[rid] = row
            seen.add(rid)
            candidate = candidates.setdefault(rid, {"id": rid, "url": row["url"], "provider": "arxiv", "first_discovered_at": info["retrieved_at"], "discovered_in": []})
            candidate["discovered_in"] = [o for o in candidate["discovered_in"] if o["source_id"] != "arxiv-title-search"]
            candidate["discovered_in"].append({"source_id": "arxiv-title-search", "line": None, "section": "Title query; relevance not reviewed", "snapshot_sha256": info["sha256"]})
        print(f"arXiv search {start + len(entries)}/{total}", flush=True)
        write_jsonl(DATA / "papers.jsonl", records.values())
        write_jsonl(DATA / "candidates.jsonl", candidates.values())
        if not entries:
            break
        start += len(entries)
        if start < min(total, ceiling):
            time.sleep(3.1)
    write_json(DATA / "arxiv-search.json", {"id": "arxiv-title-search", "query": query, "cutoff_utc": cutoff,
        "reported_total": total, "unique_returned": len(seen), "complete": total is not None and len(seen) == total,
        "pages": pages, "warning": "A title query is a discovery population, not the whole field. Search results are metadata-verified, not editorially curated."})


def verify_editorial(args):
    """Retrieve first-party evidence for editorial entries; never promote on HTTP status alone."""
    rows = read_json(DATA / "editorial.json", [])
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
        # A raw Hub card may be the reviewed primary source rather than the API.
        # Read only an explicit scalar declaration in its metadata header; do not
        # inherit a dataset/model license from a linked repository or prose.
        if urllib.parse.urlsplit(ev["url"]).hostname == "huggingface.co" and "/raw/" in ev["url"]:
            header = re.match(r"\A---\r?\n(.*?)\r?\n---", raw, re.S)
            declaration = re.search(r"^license:[ \t]*([a-zA-Z0-9][a-zA-Z0-9_.-]*)[ \t]*$", header[1], re.M) if header else None
            slot = "data" if row["kind"] == "dataset" else "weights" if row["kind"] == "model" else None
            if declaration and slot:
                result["licenses"][slot] = {"declared": declaration[1], "url": ev["url"], "retrieved_at": ev["retrieved_at"], "basis": "publisher model/dataset card metadata; third-party assets retain their own terms"}
                result["evidence"].append({"role": "primary", "method": "huggingface_card", "supports": [f"licenses.{slot}"], **{k: ev[k] for k in ("url", "sha256", "retrieved_at")}})
        if "/api/datasets/" in ev["url"] or "/api/models/" in ev["url"]:
            payload = json.loads(raw)
            card = payload.get("cardData") or {}
            slot = "data" if "/api/datasets/" in ev["url"] else "weights"
            license_name = card.get("license")
            if license_name:
                result["licenses"][slot] = {"declared": license_name, "url": row["url"], "retrieved_at": ev["retrieved_at"], "basis": "publisher model/dataset card"}
            result["details"] = {"hub_id": payload.get("id"), "gated": payload.get("gated"), "disabled": payload.get("disabled"),
                "languages": card.get("language", []), "modalities": [t.split(":", 1)[1] for t in payload.get("tags", []) if t.startswith("modality:")],
                "size_category_reported": card.get("size_categories"), "download_url": row["url"] + "/tree/main"}
            # Dataset size tags may count archive files, not samples; never convert them into sample counts.
            result["evidence"].append({"role": "primary", "method": "huggingface_api", "url": ev["url"], "sha256": ev["sha256"], "retrieved_at": ev["retrieved_at"], "supports": ["details", f"licenses.{slot}"]})
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
    command = sub.add_parser("search", help="search names, descriptions, aliases, authors and curated topics")
    command.add_argument("query", nargs="?", default="")
    command.add_argument("--kind", choices=sorted(KINDS))
    command.add_argument("--status", choices=sorted(STATUSES))
    command.add_argument("--environment", choices=sorted(ENVIRONMENTS))
    command.add_argument("--topic")
    command.add_argument("--limit", type=int, default=20, help="0 returns every match")
    command.add_argument("--json", action="store_true")
    command.set_defaults(function=search)
    args = parser.parse_args()
    args.function(args)


if __name__ == "__main__":
    main()
