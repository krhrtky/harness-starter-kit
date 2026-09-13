"""Load the local control plane and a pinned team snapshot."""
from __future__ import annotations

from fnmatch import fnmatchcase

from .storage import HarnessError, contained, digest, load, read, validate

NAMES = ('project','interfaces','capabilities','policy','assets','quality','evolution','knowledge')


def matches(path, patterns):
    return any(pattern == '.' or fnmatchcase(path, pattern) or (pattern.endswith('/**') and path == pattern[:-3]) for pattern in patterns)


def unique(items, field, kind):
    values = [i[field] for i in items]
    if len(values) != len(set(values)):
        raise HarnessError(f'Duplicate {kind} {field}')


def model(root):
    data = {name:load(root,name) for name in NAMES}
    project = data['project']
    if project['team_bundle'] is not None:
        team = validate('team', read(contained(root, project['team_bundle'])))
        if digest(team) != project['team_digest']:
            raise HarnessError('Team bundle digest mismatch; review and pin the new snapshot')
        data['team'] = team
    elif project['team_digest'] is not None:
        raise HarnessError('team_digest without team_bundle')
    team = data.get('team', {})
    data['all_assets'] = team.get('assets', {}).get('assets', []) + data['assets']['assets']
    data['all_rules'] = team.get('policy', {}).get('rules', []) + data['policy']['rules']
    data['all_transitions'] = team.get('evolution', {}).get('transition', []) + data['evolution']['transition']
    for items, label in [(data['all_assets'],'asset'),(data['all_rules'],'rule'),(data['all_transitions'],'transition'),(data['interfaces']['interfaces'],'interface'),(data['capabilities']['capabilities'],'capability'),(data['knowledge']['documents'],'knowledge')]:
        unique(items,'id',label)
    actual = {i['id'] for i in data['interfaces']['interfaces']}
    if actual != {f'H{i:02}' for i in range(27)}:
        raise HarnessError('Interface registry must contain exactly H00-H26')
    for i in data['interfaces']['interfaces']:
        if i['family'] != ('delivery' if int(i['id'][1:]) <= 16 else 'evolution'):
            raise HarnessError(f'Wrong interface family: {i["id"]}')
    keys = [(s['scope'],s['dimension']) for s in data['quality']['scores']]
    if len(keys) != len(set(keys)):
        raise HarnessError('Duplicate quality scope/dimension')
    return data


def policies(data):
    return [data['policy']] + ([data['team']['policy']] if 'team' in data else [])


def minimum(data, phase, risk):
    return max(p['readiness'][phase][risk] for p in policies(data))


def search_assets(data, capabilities):
    return [a for a in data['all_assets'] if set(a['provides']) & set(capabilities) and a['status'] != 'removed']
