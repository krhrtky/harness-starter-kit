"""Task admission, bounded change detection and evidence-based delivery."""
from __future__ import annotations

from .checks import issue, quality_regressions, readiness_regressions, structure_checks
from .model import matches, minimum, policies, search_assets, unique
from .storage import HarnessError, age_hours, contained, control_digest, digest, files, load, now, read, validate, write


def task_at(root, path):
    task = validate('task',read(contained(root,path)))
    unique(task['acceptance'],'id','acceptance')
    unique(task['asset_analysis']['new_assets'],'id','new asset')
    unique(task['asset_analysis']['duplicates_considered'],'asset','duplicate decision')
    return task


def required_caps(data, task):
    requested = set(task['required_capabilities']) | {c for ac in task['acceptance'] for c in ac['capabilities']}
    requested |= {c for i in data['interfaces']['interfaces'] if i['id'] in task['affected_interfaces'] for c in i['capabilities']}
    requested |= {c for r in data['all_rules'] for c in r['enforcement'] if r['severity']=='must'}
    return sorted(requested)


def baseline_checks(root, data, touched=()):
    current = structure_checks(root,data)
    path = contained(root,'.harness/baselines/current.json')
    if data['project']['mode'] != 'brownfield':
        return [f for f in current if not touched or f['code'] not in {'knowledge.unknown','interface.owner'} or f['interface'] in touched]
    if not path.exists():
        return current + [issue('baseline.missing','.harness/baselines/current.json','Brownfield requires a baseline')]
    baseline = validate('baseline',read(path))
    known = {f['fingerprint'] for f in baseline['findings']}
    blockers = [f for f in current if f['fingerprint'] not in known or f['interface'] in touched or f['code'] in {'schema.mismatch','rule.unenforced'}]
    return blockers + quality_regressions(baseline['quality'],data['quality']) + readiness_regressions(baseline,data)


def task_checks(root, data, task, phase):
    result = baseline_checks(root,data,task['affected_interfaces'])
    if task['unknowns']:
        result.append(issue('task.unknown','.harness/tasks',f'Unresolved unknowns: {task["unknowns"]}','H14'))
    required = minimum(data,'preflight' if phase=='verify' else phase,task['risk']['level'])
    for entry in data['interfaces']['interfaces']:
        if entry['id'] in task['affected_interfaces'] and entry['readiness'] < required:
            result.append(issue('task.readiness','.harness/interfaces.json',f'{entry["id"]} needs R{required}, has R{entry["readiness"]}',entry['id']))
    caps = {c['id']:c for c in data['capabilities']['capabilities']}
    for name in required_caps(data,task):
        if name not in caps or not caps[name]['enabled']:
            result.append(issue('task.capability','.harness/capabilities.json',f'Required capability unavailable: {name}','H09'))
    analysis = task['asset_analysis']
    new_ids = {a['id'] for a in analysis['new_assets']}
    matches_found = [a for a in search_assets(data,analysis['searched_capabilities']) if phase=='preflight' or a['id'] not in new_ids]
    decisions = {d['asset']:d for d in analysis['duplicates_considered']}
    assets = {a['id']:a for a in data['all_assets']}
    for asset in matches_found:
        if asset['id'] not in decisions:
            result.append(issue('asset.unconsidered','.harness/assets.json',f'Consider existing asset {asset["id"]}','H18'))
    for name in set(analysis['reused']+analysis['extended']+list(decisions)):
        if name not in assets:
            result.append(issue('asset.unknown','.harness/assets.json',f'Unknown asset {name}','H17'))
            continue
        if name in analysis['reused']+analysis['extended'] and assets[name]['status'] in ['deprecated','removed']:
            result.append(issue('asset.retired','.harness/assets.json',f'Cannot reuse or extend {assets[name]["status"]} asset {name}','H19'))
        decision = decisions.get(name,{}).get('decision')
        if name in analysis['reused'] and decision != 'reuse' or name in analysis['extended'] and decision != 'extend':
            result.append(issue('asset.decision','.harness/assets.json',f'Inconsistent reuse decision for {name}','H18'))
    for new in analysis['new_assets']:
        if phase=='preflight' and new['id'] in assets:
            result.append(issue('asset.exists',new['path'],f'{new["id"]} already exists; declare reuse/extension','H18'))
        if phase!='preflight' and new['id'] in assets:
            registered = assets[new['id']]
            if registered['location']!=new['path'] or set(registered['provides'])!=set(new['provides']):
                result.append(issue('asset.registration',new['path'],'Catalog registration differs from planned asset','H17'))
        for asset in data['all_assets']:
            if asset['id'] == new['id'] and phase != 'preflight':
                continue
            if asset['status']!='removed' and set(new['provides'])&set(asset['provides']):
                decision = decisions.get(asset['id'])
                if not decision or decision['decision']!='distinct':
                    result.append(issue('asset.duplicate',new['path'],f'New asset overlaps {asset["id"]}; reuse or explain semantic distinction','H18'))
        if not set(new['provides']) <= set(analysis['searched_capabilities']):
            result.append(issue('asset.search',new['path'],'Search all capabilities before creating an asset','H17'))
        if phase != 'preflight' and new['id'] not in assets:
            result.append(issue('asset.uncatalogued',new['path'],f'Register new asset {new["id"]}','H17'))
    consumers = {c for a in data['all_assets'] if a['id'] in analysis['extended'] for c in a['consumers']}
    for path in [p['path'] for p in task['placement']]:
        contained(root,path)
        if not matches(path,task['scope']):
            result.append(issue('task.placement',path,'Placement is outside the task scope','H18'))
        for transition in data['all_transitions']:
            if transition['status'] in ['planned','active'] and matches(path,transition['source']):
                consumers.update(transition['consumers'])
                if transition['new_code']=='target-only':
                    result.append(issue('evolution.source',path,f'{transition["id"]}: place new functionality in {transition["target"]}','H26'))
    if not consumers <= set(task['cross_system_impact']['consumers']):
        result.append(issue('impact.missing','.harness/tasks',f'Missing consumers: {sorted(consumers-set(task["cross_system_impact"]["consumers"]))}','H22'))
    if data['evolution']['target']=='UNKNOWN':
        result.append(issue('evolution.unknown','.harness/evolution.json','Target architecture is UNKNOWN','H26'))
    for rule in data['all_rules']:
        for p in task['placement']:
            if rule['severity']=='must' and matches(p['path'],rule['scope']) and matches(p['path'],rule['forbid_paths']):
                result.append(issue('architecture.forbidden',p['path'],f'{rule["id"]} forbids this placement',rule['interface']))
    if not data['quality']['scores']:
        result.append(issue('quality.missing','.harness/quality.json','At least one global quality score is required','H20'))
    return result


def receipt_path(task):
    return f'.harness/runs/{task["id"]}/preflight.json'


def preflight(root, data, task):
    findings = task_checks(root,data,task,'preflight')
    if findings:
        return findings
    snapshot = files(root)
    receipt = dict(schema_version=1,task=task['id'],task_digest=digest(task),created_at=now(),source_digest=digest(snapshot),files=snapshot,quality=data['quality'],assets=dict(schema_version=1,assets=data['all_assets']),control_digest=control_digest(root))
    path = contained(root,receipt_path(task))
    if path.exists():
        existing = validate('receipt',read(path))
        if existing['task_digest']==digest(task) and existing['source_digest']==digest(snapshot):
            return []
        raise HarnessError('Preflight receipt already exists; use a new task ID for a revised contract or scope')
    write(path,validate('receipt',receipt))
    return []


def receipt_for(root, task):
    receipt = validate('receipt',read(contained(root,receipt_path(task))))
    if receipt['task']!=task['id'] or receipt['task_digest']!=digest(task):
        raise HarnessError('Task changed after preflight; use a new task ID and perform preflight again')
    return receipt


def change_checks(root, data, task, receipt):
    result = []
    current = files(root)
    old_assets = {a['id']:a for a in receipt['assets']['assets']}
    current_assets = {a['id']:a for a in data['all_assets']}
    declared_new = {a['id'] for a in task['asset_analysis']['new_assets']}
    for identifier in current_assets.keys()-old_assets.keys()-declared_new:
        result.append(issue('asset.undeclared','.harness/assets.json',f'Unplanned asset registration: {identifier}','H17'))
    for identifier, previous in old_assets.items():
        if identifier not in current_assets:
            result.append(issue('asset.deleted','.harness/assets.json',f'Retain lifecycle record for removed asset: {identifier}','H19'))
    changed = sorted(p for p in current.keys() | receipt['files'].keys() if current.get(p)!=receipt['files'].get(p))
    for path in changed:
        if not matches(path,task['scope']):
            result.append(issue('scope.exceeded',path,'Changed file is outside the Task Contract','H14'))
        if path not in receipt['files'] and not matches(path,[p['path'] for p in task['placement']]):
            result.append(issue('placement.unplanned',path,'New file has no placement decision','H18'))
        if path not in receipt['files']:
            for transition in data['all_transitions']:
                if transition['status'] in ['planned','active'] and transition['new_code']=='target-only' and matches(path,transition['source']):
                    result.append(issue('evolution.source',path,f'{transition["id"]} forbids new code in migration source','H26'))
        for rule in data['all_rules']:
            if rule['severity']=='must' and matches(path,rule['scope']) and matches(path,rule['forbid_paths']):
                result.append(issue('architecture.forbidden',path,f'{rule["id"]} forbids changes here',rule['interface']))
    if receipt['control_digest']!=control_digest(root):
        result.append(issue('control.changed','.harness/project.json','Policy/contract control plane changed after preflight; separate governance change','H12'))
    return result + quality_regressions(receipt['quality'],data['quality'])


def evidence_checks(root, data, task, bundle, receipt):
    validate('evidence',bundle)
    result = []
    if bundle['task']!=task['id'] or bundle['task_digest']!=digest(task) or bundle['receipt_digest']!=digest(receipt):
        result.append(issue('evidence.task','.harness/runs','Evidence does not match task/preflight','H09'))
    if not bundle['stable_source'] or bundle['source_digest']!=digest(files(root)):
        result.append(issue('evidence.stale','.harness/runs','Source changed during or after verification','H09'))
    age = age_hours(bundle['generated_at'])
    if age < -0.05 or age > min(p['evidence_max_age_hours'] for p in policies(data)):
        result.append(issue('evidence.age','.harness/runs','Evidence is expired or future dated','H09'))
    unique(bundle['records'],'capability','evidence record')
    records = {r['capability']:r for r in bundle['records']}
    caps = {c['id']:c for c in data['capabilities']['capabilities']}
    for cap in required_caps(data,task):
        if cap not in records or records[cap]['status']!='passed' or records[cap]['exit_code']!=0:
            result.append(issue('evidence.failed','.harness/runs',f'Missing passing evidence: {cap}','H09'))
    for record in records.values():
        cap = caps.get(record['capability'])
        if not cap or record['argv']!=cap['argv']:
            result.append(issue('evidence.command','.harness/runs',f'Capability mismatch: {record["capability"]}','H09'))
        if cap and set(cap['artifacts'])!={a['path'] for a in record['artifacts']}:
            result.append(issue('evidence.artifacts','.harness/runs',f'Artifact set mismatch: {record["capability"]}','H09'))
        for path, expected in [(record['log'],record['log_digest'])]+[(a['path'],a['digest']) for a in record['artifacts']]:
            artifact = contained(root,path)
            if not artifact.is_file() or digest(artifact.read_bytes())!=expected:
                result.append(issue('evidence.integrity',path,'Evidence artifact is missing or changed','H09'))
    return result


def semantic_checks(root, data, task, findings):
    validate('findings',findings)
    unique(findings['findings'],'id','semantic finding')
    result = []
    current = digest(files(root))
    valid = []
    criteria = {a['id'] for a in task['acceptance']} | {'global-impact'}
    for f in findings['findings']:
        if f['task']!=task['id'] or f['criterion'] not in criteria or f['source_digest']!=current or f['reviewer']!=task['reviewer']:
            result.append(issue('review.binding','.harness/runs',f'{f["id"]}: stale or mismatched finding','H09'))
            continue
        if f['conclusion']!='pass' or f['contradictions'] or f['unsupported_assumptions']:
            result.append(issue('review.unresolved','.harness/runs',f'{f["id"]}: {f["conclusion"]}','H09'))
        for path in f['evidence']:
            if not contained(root,path).is_file():
                result.append(issue('review.evidence',path,f'{f["id"]}: missing evidence','H09'))
        valid.append(f)
    views = {v for p in policies(data) for v in p['required_review_views']}
    for criterion in criteria:
        for view in views:
            if not any(f['criterion']==criterion and f['view']==view for f in valid):
                result.append(issue('review.missing','.harness/runs',f'{criterion}: missing {view} review','H09'))
    return result


def delivery(root, data, task, bundle, findings):
    receipt = receipt_for(root,task)
    return (task_checks(root,data,task,'delivery') + change_checks(root,data,task,receipt)
            + evidence_checks(root,data,task,bundle,receipt) + semantic_checks(root,data,task,findings))
