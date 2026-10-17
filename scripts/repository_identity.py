"""Source-reviewed former GitHub names, resolved without network or fuzzy matching."""
from __future__ import annotations

import copy
from datetime import datetime
import re
from urllib.parse import urlsplit

NAME = r'[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+'
IDENTITY = re.compile(r'github:(' + NAME + r')')
FIELDS = {'alias_id', 'target_id', 'repository_id', 'basis', 'reviewed_at', 'observations'}
OBSERVATION_FIELDS = {'url', 'resolved_url', 'repository_id', 'full_name', 'html_url', 'retrieved_at', 'sha256'}


def github_name(url, *, api=False):
    """Accept an exact public repository URL, not a component or arbitrary redirect."""
    if not isinstance(url, str):
        raise ValueError('Repository identity needs a URL string')
    if any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in url):
        raise ValueError('Repository identity URL cannot contain whitespace or control characters')
    parts = urlsplit(url)
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
        alias, target = declaration['alias_id'], declaration['target_id']
        for identity in (alias, target):
            if not isinstance(identity, str) or not IDENTITY.fullmatch(identity) or identity != identity.casefold():
                raise ValueError('Repository aliases require canonical lowercase GitHub IDs')
        if alias == target or alias in aliases:
            raise ValueError('Repository alias is self-referential or duplicated: ' + alias)
        if declaration['basis'] != 'official_github_repository_id':
            raise ValueError('Repository aliases require official GitHub identity evidence')
        rid = declaration['repository_id']
        if type(rid) is not int or rid <= 0:
            raise ValueError('Repository identity needs a positive numeric GitHub ID')
        if repository_owners.get(rid, target) != target or target_repositories.get(target, rid) != rid:
            raise ValueError('Repository identity has conflicting canonical owners')
        reviewed = timestamp(declaration['reviewed_at'])
        observations = declaration['observations']
        if not isinstance(observations, list) or len(observations) != 2:
            raise ValueError('Repository alias needs both former-name and canonical-name observations')
        requested = set()
        for observation in observations:
            if not isinstance(observation, dict) or set(observation) != OBSERVATION_FIELDS:
                raise ValueError('Malformed GitHub repository identity observation')
            observed_id = observation['repository_id']
            if type(observed_id) is not int or observed_id != rid:
                raise ValueError('Former and canonical names must have the same numeric repository ID')
            name = observation['full_name']
            if not isinstance(name, str) or not re.fullmatch(NAME, name) or 'github:' + name.casefold() != target:
                raise ValueError('Observed GitHub full_name differs from the canonical target')
            if 'github:' + github_name(observation['html_url']).casefold() != target:
                raise ValueError('Observed GitHub HTML URL differs from the canonical target')
            requested.add('github:' + github_name(observation['url'], api=True).casefold())
            resolved = observation['resolved_url']
            if resolved != 'https://api.github.com/repositories/' + str(rid):
                if 'github:' + github_name(resolved, api=True).casefold() != target:
                    raise ValueError('GitHub response resolved to a different repository')
            if not isinstance(observation['sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', observation['sha256']):
                raise ValueError('Repository identity observation needs its response SHA-256')
            if timestamp(observation['retrieved_at']) > reviewed:
                raise ValueError('Repository identity cannot be reviewed before its source observation')
        if requested != {alias, target}:
            raise ValueError('Repository alias observations do not cover both declared names')
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
            if 'github:' + github_name(record['url']).casefold() != target:
                raise ValueError('Repository alias target has a different primary repository URL')
    return aliases


def attach_repository_aliases(records, declarations):
    """Preserve records, adding former names and receipts only to their proven owner."""
    repository_aliases(declarations, records)
    result = copy.deepcopy(records)
    by_id = {record['id']: record for record in result}
    for declaration in declarations:
        record = by_id[declaration['target_id']]
        old = next(item for item in declaration['observations']
                   if 'github:' + github_name(item['url'], api=True).casefold() == declaration['alias_id'])
        old_name = github_name(old['url'], api=True)
        for value in (declaration['alias_id'], old_name, 'https://github.com/' + old_name):
            if value not in record['aliases']:
                record['aliases'].append(value)
        for observation in declaration['observations']:
            receipt = {key: observation[key] for key in ('url', 'sha256', 'retrieved_at')}
            receipt.update(role='primary', method='github_repository_identity', supports=['aliases'])
            if receipt not in record['evidence']:
                record['evidence'].append(receipt)
    return result
