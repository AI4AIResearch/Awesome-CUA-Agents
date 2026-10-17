"""Source-reviewed former GitHub and Hugging Face names, resolved without network or fuzzy matching."""
from __future__ import annotations

import copy
from datetime import datetime
import hashlib
import re
from urllib.parse import urlsplit

NAME = r'[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+'
IDENTITY = re.compile(r'github:(' + NAME + r')')
HUB_NAME = r'[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9_.-]+'
HUB_IDENTITY = re.compile(r'url:[0-9a-f]{20}')
HUB_SECTIONS = {'api', 'datasets', 'spaces', 'models', 'collections', 'papers', 'docs', 'organizations'}
HUB = 'official_huggingface_repository_id'
# Each basis names the receipt method its observations become on the owner record.
BASES = {'official_github_repository_id': 'github_repository_identity', HUB: 'huggingface_repository_identity'}
FIELDS = {'alias_id', 'target_id', 'repository_id', 'basis', 'reviewed_at', 'observations'}
OBSERVATION_FIELDS = {'url', 'resolved_url', 'repository_id', 'full_name', 'html_url', 'retrieved_at', 'sha256'}


def exact_url(url):
    if not isinstance(url, str):
        raise ValueError('Repository identity needs a URL string')
    if any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in url):
        raise ValueError('Repository identity URL cannot contain whitespace or control characters')
    return urlsplit(url)


def hub_path(url, *, api=False):
    """Accept an exact Hub model or dataset URL and return its page path, such as datasets/<owner>/<name>."""
    parts = exact_url(url)
    prefix = '/api/' if api else '/'
    if (parts.scheme != 'https' or parts.netloc != 'huggingface.co' or parts.query or parts.fragment
            or not parts.path.startswith(prefix)):
        raise ValueError('Repository identity needs an exact HTTPS Hugging Face URL')
    path = parts.path[len(prefix):]
    section, _, name = path.partition('/') if api or path.startswith('datasets/') else ('models', '', path)
    if (section not in {'models', 'datasets'} or not re.fullmatch(HUB_NAME, name) or name.split('/')[0] in HUB_SECTIONS
            or name.rsplit('/', 1)[-1] in {'.', '..'}):
        raise ValueError('Repository identity URL must name one Hugging Face model or dataset')
    return ('datasets/' if section == 'datasets' else '') + name


def hub_identity(path):
    """The catalog ID of a Hub page path; canonical() keeps the path's case, so each spelling hashes to its own ID."""
    return 'url:' + hashlib.sha256(('https://huggingface.co/' + path).encode()).hexdigest()[:20]


def requested_identity(url, basis):
    return hub_identity(hub_path(url, api=True)) if basis == HUB else 'github:' + github_name(url, api=True).casefold()


def github_name(url, *, api=False):
    """Accept an exact public repository URL, not a component or arbitrary redirect."""
    parts = exact_url(url)
    host = 'api.github.com' if api else 'github.com'
    prefix = '/repos/' if api else '/'
    if (parts.scheme != 'https' or parts.netloc != host or parts.query or parts.fragment
            or not parts.path.startswith(prefix)):
        raise ValueError('Repository identity needs an exact HTTPS GitHub URL')
    name = parts.path[len(prefix):]
    if not re.fullmatch(NAME, name) or name.rsplit('/', 1)[-1] in {'.', '..'} or name.endswith('.git'):
        raise ValueError('Repository identity URL must name one repository')
    return name


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('Repository identity timestamp must be a string')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Repository identity timestamp needs a timezone')
    return parsed


def repository_aliases(declarations, records=None):
    """Validate paired official observations and return direct former-ID mappings.

    A recorded repository identity is not an assertion of release completeness,
    licensing, or current scope. Only existing curated targets may own aliases.
    """
    if not isinstance(declarations, list):
        raise ValueError('Repository aliases must be a list')
    aliases, repository_owners, target_repositories = {}, {}, {}
    for declaration in declarations:
        if not isinstance(declaration, dict) or set(declaration) != FIELDS:
            raise ValueError('Repository alias has missing or unsupported fields')
        alias, target, basis = declaration['alias_id'], declaration['target_id'], declaration['basis']
        if not isinstance(basis, str) or basis not in BASES:
            raise ValueError('Repository aliases require official GitHub or Hugging Face identity evidence')
        for identity in (alias, target):
            if not isinstance(identity, str) or not (HUB_IDENTITY if basis == HUB else IDENTITY).fullmatch(identity) or identity != identity.casefold():
                raise ValueError('Repository aliases require canonical lowercase GitHub IDs or Hugging Face URL IDs')
        if alias == target or alias in aliases:
            raise ValueError('Repository alias is self-referential or duplicated: ' + alias)
        rid = declaration['repository_id']
        if not ((isinstance(rid, str) and re.fullmatch(r'[0-9a-f]{24}', rid)) if basis == HUB else (type(rid) is int and rid > 0)):
            raise ValueError('Repository identity needs a positive numeric GitHub ID or a Hugging Face object ID')
        if repository_owners.get(rid, target) != target or target_repositories.get(target, rid) != rid:
            raise ValueError('Repository identity has conflicting canonical owners')
        reviewed = timestamp(declaration['reviewed_at'])
        observations = declaration['observations']
        if not isinstance(observations, list) or len(observations) != 2:
            raise ValueError('Repository alias needs both former-name and canonical-name observations')
        requested, hub_names = set(), set()
        for observation in observations:
            if not isinstance(observation, dict) or set(observation) != OBSERVATION_FIELDS:
                raise ValueError('Malformed repository identity observation')
            observed_id = observation['repository_id']
            if type(observed_id) is not type(rid) or observed_id != rid:
                raise ValueError('Former and canonical names must have the same repository ID')
            if not isinstance(observation['sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', observation['sha256']):
                raise ValueError('Repository identity observation needs its response SHA-256')
            if timestamp(observation['retrieved_at']) > reviewed:
                raise ValueError('Repository identity cannot be reviewed before its source observation')
            name = observation['full_name']
            requested.add(requested_identity(observation['url'], basis))
            if basis == HUB:
                # The Hub API answers every spelling with the repository's current id; the catalog may own any of them.
                if not isinstance(name, str) or not re.fullmatch(HUB_NAME, name):
                    raise ValueError('Observed Hugging Face id is not one repository name')
                current = ('datasets/' if hub_path(observation['url'], api=True).startswith('datasets/') else '') + name
                if hub_path(observation['html_url']) != current or hub_path(observation['resolved_url'], api=True) != current:
                    raise ValueError('Hugging Face response resolved to a different repository')
                hub_names.add(current)
                continue
            if not isinstance(name, str) or not re.fullmatch(NAME, name) or 'github:' + name.casefold() != target:
                raise ValueError('Observed GitHub full_name differs from the canonical target')
            if 'github:' + github_name(observation['html_url']).casefold() != target:
                raise ValueError('Observed GitHub HTML URL differs from the canonical target')
            resolved = observation['resolved_url']
            if resolved != 'https://api.github.com/repositories/' + str(rid):
                if 'github:' + github_name(resolved, api=True).casefold() != target:
                    raise ValueError('GitHub response resolved to a different repository')
        if requested != {alias, target} or len(hub_names) > 1:
            raise ValueError('Repository alias observations do not cover both declared names of one repository')
        aliases[alias] = target
        repository_owners[rid] = target
        target_repositories[target] = rid
    if set(aliases) & set(aliases.values()):
        raise ValueError('Repository aliases must resolve directly; chains and cycles are not allowed')
    if records is not None:
        by_id = {record['id']: record for record in records}
        if len(by_id) != len(records):
            raise ValueError('Duplicate catalog IDs while resolving repository aliases')
        for alias, target in aliases.items():
            if alias in by_id:
                raise ValueError('A former repository ID is also an active resource: ' + alias)
            record = by_id.get(target)
            if not record or record['review_status'] != 'curated' or record['scope'] not in {'core', 'adjacent'}:
                raise ValueError('Repository alias target must be an active reviewed resource: ' + target)
            if (hub_identity(hub_path(record['url'])) if HUB_IDENTITY.fullmatch(target) else 'github:' + github_name(record['url']).casefold()) != target:
                raise ValueError('Repository alias target has a different primary repository URL')
    return aliases


def attach_repository_aliases(records, declarations):
    """Preserve records, adding former names and receipts only to their proven owner."""
    repository_aliases(declarations, records)
    result = copy.deepcopy(records)
    by_id = {record['id']: record for record in result}
    for declaration in declarations:
        record = by_id[declaration['target_id']]
        basis = declaration['basis']
        old = next(item for item in declaration['observations'] if requested_identity(item['url'], basis) == declaration['alias_id'])
        if basis == HUB:
            path = hub_path(old['url'], api=True)
            values = (declaration['alias_id'], path.removeprefix('datasets/'), 'https://huggingface.co/' + path)
        else:
            old_name = github_name(old['url'], api=True)
            values = (declaration['alias_id'], old_name, 'https://github.com/' + old_name)
        for value in values:
            if value not in record['aliases']:
                record['aliases'].append(value)
        for observation in declaration['observations']:
            receipt = {key: observation[key] for key in ('url', 'sha256', 'retrieved_at')}
            receipt.update(role='primary', method=BASES[basis], supports=['aliases'])
            if receipt not in record['evidence']:
                record['evidence'].append(receipt)
    return result


def unrecorded_hub_renames(records, aliases):
    """Curated Hub records whose API id differs from their URL path without a recorded alias for that id."""
    result = []
    for record in records:
        name = record.get('details', {}).get('hub_id')
        if record.get('review_status') != 'curated' or not isinstance(name, str):
            continue
        path = hub_path(record['url'])
        current = ('datasets/' if path.startswith('datasets/') else '') + name
        if current != path and aliases.get(hub_identity(current)) != record['id']:
            result.append((record['id'], path, current))
    return result
