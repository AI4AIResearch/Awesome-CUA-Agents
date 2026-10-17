#!/usr/bin/env python3
"""Export recorded paper/survey citations as UTF-8 BibTeX or CSL JSON, offline.

Names remain literals: the catalog does not record family/given name boundaries.
UTF-8 is preserved, so non-ASCII BibTeX requires a Unicode-capable bibliography
and TeX toolchain. Input text is escaped, never interpreted as LaTeX commands.
The classic BibTeX fields remain usable with standard styles; url, doi, eprint,
and archivePrefix are optional extensions that some older styles ignore.

Format audit (2026-10-17): CSL's official input schema permits literal names,
article, version, issued, and a custom object. Its specification recommends
article for repository preprints. Patashnik's original BibTeX manual defines
misc without required fields, suitable when no publication venue is recorded.
Primary source URLs and reviewed-byte hashes are in FORMAT_SOURCES below.
"""
import argparse
import copy
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAPER_KINDS = frozenset({'paper', 'survey'})
REVIEW_STATES = frozenset({'curated', 'metadata_verified'})
ARXIV_ID = re.compile(r'(?:\d{4}\.\d{4,5}|[a-z][a-z0-9.-]*/\d{7})', re.I)
FORMAT_SOURCES = (
    {
        'url': 'https://raw.githubusercontent.com/citation-style-language/schema/master/schemas/input/csl-data.json',
        'sha256': '23b2c062d7526060f4631bb04b4b3ba237e488484253e327bd00fa691861b811',
        'reviewed_at': '2026-10-17',
    },
    {
        'url': 'https://mirrors.ctan.org/biblio/bibtex/base/btxdoc.tex',
        'sha256': 'abad948b62e1b693d9dcdae0b9d175504e03ed002482ec0d84c8f14e7c2b89d4',
        'reviewed_at': '2026-10-17',
    },
    {
        'url': 'https://raw.githubusercontent.com/TeX-Live/texlive-source/trunk/texk/web2c/bibtex.web',
        'sha256': '04c15be36dce19be38361617f139b1b8a70aa21f97def5cdc478622941398fa0',
        'reviewed_at': '2026-10-17',
    },
)


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{field} must be a nonempty string')
    if any(unicodedata.category(char) in {'Cc', 'Cs'} and char not in '\t\r\n' for char in value):
        raise ValueError(f'{field} contains an unsupported control character')
    return value


def tex_escape(value):
    """Escape literal text, including unbalanced braces and TeX ^^ sequences."""
    replacements = {
        '\\': r'\textbackslash{}', '{': r'\textbraceleft{}', '}': r'\textbraceright{}',
        '$': r'\$', '&': r'\&', '#': r'\#', '%': r'\%', '_': r'\_',
        '^': r'\textasciicircum{}', '~': r'\textasciitilde{}',
        '\n': ' ', '\r': ' ', '\t': ' ',
    }
    return ''.join(replacements.get(char, char) for char in _text(value, 'BibTeX text'))


def citation_key(record):
    """Keys follow archive identity, not mutable titles, authors, or versions."""
    rid = _text(record.get('id'), 'id')
    if re.fullmatch(r'arxiv:\d{4}\.\d{4,5}', rid):
        return rid.replace(':', '_').replace('.', '_')
    return 'cua_' + hashlib.sha256(rid.encode('utf-8')).hexdigest()[:24]


def _date(value, field):
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError(f'{field} must be an ISO calendar date or null')
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f'Invalid {field}: {value}') from exc


def _url(value, field):
    value = _text(value, field)
    parts = urlsplit(value)
    if (parts.scheme not in {'http', 'https'} or not parts.hostname
            or parts.username is not None or parts.password is not None
            or any(char.isspace() or char == '\\' for char in value)):
        raise ValueError(f'Invalid {field}: expected a public HTTP(S) URL')
    return value


def _facts(record):
    rid = _text(record.get('id'), 'id')
    if record.get('kind') not in PAPER_KINDS:
        raise ValueError('Citations require a paper or survey: ' + rid)
    if record.get('review_status') not in REVIEW_STATES:
        raise ValueError('Unrecognized catalog review status: ' + rid)
    title = _text(record.get('name'), 'name')
    authors = record.get('authors', [])
    if not isinstance(authors, list):
        raise ValueError('authors must be a list: ' + rid)
    for author in authors:
        _text(author, 'author')
    identifiers = record.get('identifiers', {})
    if not isinstance(identifiers, dict):
        raise ValueError('identifiers must be an object: ' + rid)
    for key, value in identifiers.items():
        _text(key, 'identifier key')
        _text(value, 'identifier value')
    arxiv = identifiers.get('arxiv')
    if arxiv is not None and not ARXIV_ID.fullmatch(arxiv):
        raise ValueError('Invalid arXiv identifier: ' + rid)
    if rid.startswith('arxiv:') and rid != 'arxiv:' + (arxiv or ''):
        raise ValueError('arXiv identity does not match identifiers: ' + rid)
    preferred = identifiers.get('preferred_arxiv')
    if preferred is not None and not ARXIV_ID.fullmatch(preferred):
        raise ValueError('Invalid preferred arXiv identifier: ' + rid)
    published = _date(record.get('published_at'), 'published_at')
    _date(record.get('updated_at'), 'updated_at')
    canonical = _url(record.get('url'), 'url')
    details = record.get('details') or {}
    if not isinstance(details, dict):
        raise ValueError('details must be an object: ' + rid)
    snapshot = details.get('arxiv_snapshot')
    if snapshot is not None and not isinstance(snapshot, dict):
        raise ValueError('arxiv_snapshot must be an object or null: ' + rid)
    version = (snapshot or {}).get('version')
    if version is not None and (type(version) is not int or version < 1):
        raise ValueError('arXiv version must be a positive integer: ' + rid)
    versioned_url = (snapshot or {}).get('versioned_url')
    if versioned_url is not None:
        _url(versioned_url, 'versioned_url')
        if not arxiv or not version or versioned_url != f'https://arxiv.org/abs/{arxiv}v{version}':
            raise ValueError('arXiv version URL does not match recorded identity/version: ' + rid)
    return {
        'id': rid, 'title': title, 'authors': authors, 'identifiers': identifiers,
        'arxiv': arxiv, 'preferred': preferred, 'published': published,
        'canonical_url': canonical, 'source_url': versioned_url or canonical,
        'snapshot': snapshot, 'version': version,
    }


def _note(record, facts):
    notes = []
    if facts['published']:
        notes.append('First published: ' + record['published_at'])
    if facts['version']:
        notes.append('Recorded arXiv version: v' + str(facts['version']))
    updated = (facts['snapshot'] or {}).get('updated_at') or record.get('updated_at')
    if updated:
        notes.append('Recorded version updated: ' + _text(updated, 'version updated'))
    if facts['preferred']:
        notes.append(f"Preferred arXiv record recorded by catalog: arXiv:{facts['preferred']} "
                     f"(https://arxiv.org/abs/{facts['preferred']}); this citation retains {facts['id']}")
    return '; '.join(notes) + ('.' if notes else '')


def citation_csl(record):
    """Return one CSL-JSON item, without substituting another archive's metadata."""
    facts = _facts(record)
    custom = {
        'catalog_id': facts['id'], 'catalog_kind': record['kind'],
        'catalog_review_status': record['review_status'],
        'canonical_source_url': facts['canonical_url'],
        'identifiers': copy.deepcopy(facts['identifiers']),
        'first_published_at': record.get('published_at'),
        'record_updated_at': record.get('updated_at'),
    }
    if record.get('scope') is not None:
        custom['catalog_scope'] = record['scope']
    if facts['snapshot'] is not None:
        custom['arxiv_snapshot'] = copy.deepcopy(facts['snapshot'])
    if facts['preferred']:
        custom['preferred_record_id'] = 'arxiv:' + facts['preferred']
    item = {
        'id': facts['id'], 'citation-key': citation_key(record), 'type': 'article',
        'title': facts['title'], 'URL': facts['source_url'],
        'custom': custom,
    }
    note = _note(record, facts)
    if note:
        item['note'] = note
    if facts['authors']:
        item['author'] = [{'literal': author} for author in facts['authors']]
    if facts['published']:
        published = facts['published']
        item['issued'] = {'date-parts': [[published.year, published.month, published.day]]}
    if facts['arxiv']:
        item.update(archive='arXiv', archive_location=facts['arxiv'], genre='preprint')
    if facts['version']:
        item['version'] = str(facts['version'])
    if facts['identifiers'].get('doi'):
        item['DOI'] = facts['identifiers']['doi']
    return item


def citation_bibtex(record):
    """Return one braced BibTeX @misc entry with full, protected literal names."""
    facts = _facts(record)
    fields = [('title', '{' + tex_escape(facts['title']) + '}')]
    if facts['authors']:
        fields.append(('author', ' and '.join('{' + tex_escape(author) + '}' for author in facts['authors'])))
    if facts['published']:
        fields.append(('year', str(facts['published'].year)))
    if facts['arxiv']:
        eprint = facts['arxiv'] + (f"v{facts['version']}" if facts['version'] else '')
        fields.extend([('eprint', tex_escape(eprint)), ('archivePrefix', 'arXiv')])
    if facts['identifiers'].get('doi'):
        fields.append(('doi', tex_escape(facts['identifiers']['doi'])))
    fields.append(('url', tex_escape(facts['source_url'])))
    note = _note(record, facts)
    if note:
        fields.append(('note', tex_escape(note)))
    metadata = {
        'catalog_id': facts['id'], 'catalog_review_status': record['review_status'],
        'identifiers': facts['identifiers'],
    }
    if record.get('scope') is not None:
        metadata['catalog_scope'] = record['scope']
    if facts['preferred']:
        metadata['preferred_record_id'] = 'arxiv:' + facts['preferred']
    # JSON escapes CR/LF and Unicode separators. Classic BibTeX scans for @ even
    # on lines starting with %, so encode it as JSON \u0040 as well. Both forms
    # decode to the original metadata without exposing an extra entry token.
    metadata_json = json.dumps(metadata, ensure_ascii=True, sort_keys=True).replace('@', r'\u0040')
    comment = '% AwesomeCUA: ' + metadata_json + '\n'
    return comment + '@misc{' + citation_key(record) + ',\n' + ',\n'.join(
        '  ' + field + ' = {' + value + '}' for field, value in fields) + '\n}\n'


def citation_records(records, include_metadata=False, record_id=None):
    """Validate identities, then select papers; a requested ID must be eligible."""
    indexed = {}
    for record in records:
        rid = _text(record.get('id'), 'id')
        if rid in indexed:
            raise ValueError('Duplicate resource identifier: ' + rid)
        if record.get('review_status') not in REVIEW_STATES:
            raise ValueError('Unrecognized catalog review status: ' + rid)
        indexed[rid] = record
    if record_id is not None:
        if record_id not in indexed:
            raise ValueError('Unknown active resource identifier: ' + record_id)
        selected = [indexed[record_id]]
        if selected[0].get('kind') not in PAPER_KINDS:
            raise ValueError('Citations require a paper or survey: ' + record_id)
        if not include_metadata and selected[0]['review_status'] != 'curated':
            raise ValueError('Metadata-only citation requires --include-metadata: ' + record_id)
    else:
        selected = [r for r in indexed.values() if r.get('kind') in PAPER_KINDS
                    and (include_metadata or r['review_status'] == 'curated')]
    return sorted(selected, key=lambda record: record['id'])


def encode_citations(records, format='bibtex', include_metadata=False, record_id=None):
    selected = citation_records(records, include_metadata, record_id)
    if format == 'bibtex':
        return '\n'.join(citation_bibtex(record) for record in selected).encode('utf-8')
    if format == 'csl-json':
        return (json.dumps([citation_csl(record) for record in selected], ensure_ascii=False,
                           sort_keys=True, indent=2) + '\n').encode('utf-8')
    raise ValueError('Unsupported citation format: ' + format)


def build_citation_exports(records, destination, source_bytes):
    """Write both reviewed and metadata-inclusive exports plus their manifest.

    All bytes are prepared before writing, so malformed records cannot leave a
    partially generated export. Output ordering and hashes are deterministic.
    """
    records = list(records)
    payloads = []
    exports = []
    for include_metadata, stem in [(False, 'citations'), (True, 'citations-all')]:
        count = len(citation_records(records, include_metadata))
        for format, suffix in [('bibtex', '.bib'), ('csl-json', '.csl.json')]:
            filename = stem + suffix
            body = encode_citations(records, format, include_metadata)
            payloads.append((filename, body))
            exports.append({'file': filename, 'format': format, 'records': count,
                            'includes_metadata_only': include_metadata, 'bytes': len(body),
                            'sha256': hashlib.sha256(body).hexdigest()})
    manifest = {
        'schema_version': 1, 'catalog_sha256': hashlib.sha256(source_bytes).hexdigest(),
        'encoding': 'UTF-8', 'resource_kinds': sorted(PAPER_KINDS),
        'citation_policy': 'Recorded source versions and full literal author names; unknown venues and dates are omitted.',
        'date_policy': 'issued/year use first published_at only; version updates remain separate in note/custom.',
        'review_policy': 'curated is catalog editorial review, not academic peer review; metadata-only records remain explicitly marked.',
        'identity_policy': 'One citation per archive identity; preferred_arxiv is retained without substituting its bibliographic facts.',
        'bibtex_compatibility': 'UTF-8 literal names; non-ASCII rendering requires a Unicode-capable bibliography/TeX toolchain. Older styles may ignore url, doi, eprint, and archivePrefix.',
        'format_sources': list(FORMAT_SOURCES), 'exports': exports,
    }
    payloads.append(('citations-manifest.json', (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')))
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for filename, body in payloads:
        (destination / filename).write_bytes(body)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'data/catalog.jsonl')
    parser.add_argument('--output', type=Path, help='Output path; defaults to standard output.')
    parser.add_argument('--format', choices=['bibtex', 'csl-json'], default='bibtex')
    parser.add_argument('--include-metadata', action='store_true', help='Include paper metadata still awaiting relevance review.')
    parser.add_argument('--id', dest='record_id', help='Export one exact active catalog ID (for example arxiv:2404.07972).')
    args = parser.parse_args(argv)
    if args.output and args.output.resolve() == args.input.resolve():
        parser.error('Output must not overwrite the source catalog')
    try:
        records = [json.loads(line) for line in args.input.read_text(encoding='utf-8').splitlines() if line.strip()]
        body = encode_citations(records, args.format, args.include_metadata, args.record_id)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.error(str(exc))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(body)
    else:
        sys.stdout.buffer.write(body)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
