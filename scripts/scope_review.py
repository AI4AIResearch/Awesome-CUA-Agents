"""Explicit, reversible scope decisions over retained bibliographic snapshots."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import urllib.parse


def metadata_fingerprint(record):
    fields = {key: record.get(key) for key in ('id', 'name', 'authors', 'published_at', 'updated_at')}
    return hashlib.sha256(json.dumps(fields, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def resolve_exclusions(records, decisions, observed_changes=()):
    """Resolve only authored decisions; titles and keywords never create exclusions."""
    observed_changes = set(observed_changes)
    if not isinstance(decisions,list):
        raise ValueError('Scope decisions must be a list')
    results, seen = [], set()
    for decision in decisions:
        if not isinstance(decision,dict):
            raise ValueError('Each scope decision must be an object')
        rid = decision.get('id')
        if not isinstance(rid,str) or not re.fullmatch(r'arxiv:\d{4}\.\d{4,5}',rid) or rid in seen:
            raise ValueError('Invalid or duplicate scope-decision identity')
        seen.add(rid)
        if rid not in records:
            raise ValueError(f'{rid}: scope decision has no retained bibliographic record')
        record = records[rid]
        if decision.get('decision') != 'out_of_scope' or decision.get('basis') != 'primary_abstract_review':
            raise ValueError(f'{rid}: scope decision requires an explicit abstract review')
        if not isinstance(decision.get('reason'),str) or not decision['reason'].strip() or not decision.get('name'):
            raise ValueError(f'{rid}: missing scope rationale or reviewed title')
        if decision.get('url') != 'https://arxiv.org/abs/' + rid.split(':',1)[1]:
            raise ValueError(f'{rid}: invalid original publication URL')
        fingerprint = decision.get('metadata_fingerprint')
        if not isinstance(fingerprint,str) or not re.fullmatch(r'[0-9a-f]{64}',fingerprint):
            raise ValueError(f'{rid}: invalid reviewed metadata fingerprint')
        evidence = decision.get('evidence',{})
        if not isinstance(evidence,dict) or not isinstance(evidence.get('url'),str) or not isinstance(evidence.get('sha256'),str):
            raise ValueError(f'{rid}: invalid primary evidence receipt')
        url = urllib.parse.urlsplit(evidence.get('url',''))
        if url.scheme != 'https' or not url.netloc or not re.fullmatch(r'[0-9a-f]{64}',evidence.get('sha256','')):
            raise ValueError(f'{rid}: scope decision lacks a primary evidence receipt')
        try:
            reviewed = dt.datetime.fromisoformat(decision['reviewed_at'].replace('Z','+00:00'))
            retrieved = dt.datetime.fromisoformat(evidence['retrieved_at'].replace('Z','+00:00'))
            if reviewed.tzinfo is None or retrieved.tzinfo is None or reviewed < retrieved:
                raise ValueError('invalid review order')
        except (KeyError,TypeError,ValueError,AttributeError) as error:
            raise ValueError(f'{rid}: invalid scope-review timestamps') from error
        if record.get('review_status') == 'curated':
            raise ValueError(f'{rid}: curated inclusion conflicts with scope exclusion; reconcile the editorial decisions')
        matching_receipt = any(source.get('url') == evidence['url'] and source.get('sha256') == evidence['sha256'] for source in record.get('evidence',[]))
        current = matching_receipt and metadata_fingerprint(record) == decision['metadata_fingerprint'] and rid not in observed_changes
        results.append({**decision, 'status':'excluded' if current else 'revalidation_pending',
            'status_reason':'Reviewed snapshot matches retained metadata.' if current else 'Metadata, primary evidence, or an observed upstream change requires another scope review.'})
    excluded = {result['id'] for result in results if result['status']=='excluded'}
    for rid,record in records.items():
        if rid in excluded:
            continue
        targets = {relation['target_id'] for relation in record.get('relations',[])}
        preferred = record.get('identifiers',{}).get('preferred_arxiv')
        if preferred:
            targets.add('arxiv:' + preferred)
        if targets & excluded:
            raise ValueError(f'{rid}: published relationships depend on excluded records {sorted(targets & excluded)}')
    return sorted(results,key=lambda result:result['id'])


def scope_report(results):
    return {'schema_version':1,
        'excluded_records':sum(result['status']=='excluded' for result in results),
        'revalidation_pending':sum(result['status']=='revalidation_pending' for result in results),
        'policy':'Explicit primary-abstract scope review; not a judgment of research quality. Raw metadata remains in the archive. Changed or unresolved decisions do not suppress records.',
        'decisions':results}
