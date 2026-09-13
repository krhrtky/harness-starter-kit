"""Deterministic fitness checks. Semantic judgments enter as finding contracts."""
from __future__ import annotations

import re
from pathlib import Path

from .model import matches, policies
from .storage import SCHEMAS, age_hours, contained, digest


def issue(code, path, message, interface=None):
    return dict(code=code,path=path,message=message,interface=interface,fingerprint=digest([code,path,message,interface]))


def knowledge_checks(root, data):
    result = []
    max_days = min(p['knowledge_max_age_days'] for p in policies(data))
    for doc in data['knowledge']['documents']:
        path = contained(root, doc['path'])
        if not path.is_file():
            result.append(issue('knowledge.missing',doc['path'],'Knowledge file is missing',doc['interface']))
            continue
        if doc['status'] == 'unknown':
            result.append(issue('knowledge.unknown',doc['path'],'Knowledge is UNKNOWN',doc['interface']))
        age = age_hours(doc['reviewed_at'])
        if age < -0.05 or age > max_days*24 or digest(path.read_bytes()) != doc['content_digest']:
            result.append(issue('knowledge.stale',doc['path'],'Knowledge review is stale or content changed',doc['interface']))
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text()):
            if '://' in target or target.startswith(('#','mailto:')):
                continue
            relative = target.split('#')[0].split(' ')[0].strip('<>')
            resolved = (path.parent / relative).resolve()
            if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                result.append(issue('knowledge.link',doc['path'],f'Broken local link: {target}',doc['interface']))
    return result


def structure_checks(root, data):
    result = knowledge_checks(root,data)
    for schema in SCHEMAS.glob('*.json'):
        local = contained(root,f'.harness/schemas/{schema.name}')
        if not local.is_file() or local.read_bytes()!=schema.read_bytes():
            result.append(issue('schema.mismatch',f'.harness/schemas/{schema.name}','Installed schema differs from CLI distribution'))
    caps = {c['id']:c for c in data['capabilities']['capabilities']}
    for entry in data['interfaces']['interfaces']:
        if entry['owner'] == 'UNKNOWN':
            result.append(issue('interface.owner','.harness/interfaces.json',f'{entry["id"]} owner is UNKNOWN',entry['id']))
        for source in entry['sources']:
            if not contained(root,source).exists():
                result.append(issue('interface.source',source,'Interface source is missing',entry['id']))
        for capability in entry['capabilities']:
            if capability not in caps or not caps[capability]['enabled']:
                result.append(issue('interface.capability','.harness/capabilities.json',f'{entry["id"]}: unavailable capability {capability}',entry['id']))
        if entry['readiness'] >= 2:
            docs = [d for d in data['knowledge']['documents'] if d['interface']==entry['id']]
            if not docs or any(d['status']!='documented' for d in docs):
                result.append(issue('interface.readiness','.harness/interfaces.json',f'{entry["id"]} readiness exceeds documented knowledge',entry['id']))
        if entry['readiness'] >= 4 and not entry['capabilities']:
            result.append(issue('interface.enforcement','.harness/interfaces.json',f'{entry["id"]} R4+ needs enforcement',entry['id']))
    for path in ['AGENTS.md','ARCHITECTURE.md']:
        if not contained(root,path).is_file():
            result.append(issue('router.missing',path,'Routing document is missing','H13'))
    for rule in data['all_rules']:
        if not contained(root,rule['source']).is_file():
            result.append(issue('rule.source',rule['source'],f'{rule["id"]} source is missing',rule['interface']))
        if rule['severity']=='must' and not (rule['enforcement'] or rule['forbid_paths'] or rule['require_paths']):
            result.append(issue('rule.unenforced',rule['source'],f'{rule["id"]} MUST has no enforcement',rule['interface']))
        for cap in rule['enforcement']:
            if cap not in caps or not caps[cap]['enabled']:
                result.append(issue('rule.capability',rule['source'],f'{rule["id"]} unavailable enforcement {cap}',rule['interface']))
        for path in rule['require_paths']:
            if not contained(root,path).exists():
                result.append(issue('rule.required',path,f'{rule["id"]} required path is missing',rule['interface']))
    for cap in caps.values():
        if not contained(root,cap['cwd']).is_dir():
            result.append(issue('capability.cwd',cap['cwd'],f'{cap["id"]} working directory is missing','H10'))
        for path in cap['artifacts']:
            contained(root,path)
    asset_ids = {a['id'] for a in data['all_assets']}
    for asset in data['all_assets']:
        if asset['status']=='removed':
            continue
        if '://' not in asset['location'] and not contained(root,asset['location']).exists():
            result.append(issue('asset.missing',asset['location'],f'{asset["id"]} location is missing','H17'))
        if asset['deprecated_by'] is not None and asset['deprecated_by'] not in asset_ids:
            result.append(issue('asset.replacement','.harness/assets.json',f'{asset["id"]} replacement is unknown','H19'))
        for path in asset['evidence']:
            if not contained(root,path).is_file():
                result.append(issue('asset.evidence',path,f'{asset["id"]} evidence is missing','H17'))
    for score in data['quality']['scores']:
        for path in score['evidence']:
            if not contained(root,path).is_file():
                result.append(issue('quality.evidence',path,'Quality score evidence is missing','H20'))
    return result


def duplicate_candidates(data):
    active = [a for a in data['all_assets'] if a['status'] not in ['removed','deprecated']]
    return [dict(left=a['id'],right=b['id'],capabilities=sorted(set(a['provides'])&set(b['provides']))) for i,a in enumerate(active) for b in active[i+1:] if set(a['provides'])&set(b['provides'])]


def quality_regressions(before, after):
    current = {(s['scope'],s['dimension']):s['score'] for s in after['scores']}
    return [issue('quality.regression','.harness/quality.json',f'{s["scope"]}/{s["dimension"]}: {s["score"]} -> {current.get((s["scope"],s["dimension"]),"missing")}','H20') for s in before['scores'] if current.get((s['scope'],s['dimension']),-1)<s['score']]


def readiness_regressions(baseline, data):
    current = {i['id']:i['readiness'] for i in data['interfaces']['interfaces']}
    return [issue('readiness.regression','.harness/interfaces.json',f'{i}: {r} -> {current.get(i,0)}',i) for i,r in baseline['readiness'].items() if current.get(i,0)<r]
