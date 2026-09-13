"""Repository ratchets and reviewed team asset evolution."""
from __future__ import annotations

from .checks import quality_regressions, readiness_regressions, structure_checks
from .model import policies, search_assets
from .storage import HarnessError, contained, digest, now, read, validate, write


def baseline(root,data):
    path = contained(root,'.harness/baselines/current.json')
    findings = structure_checks(root,data)
    if path.exists():
        old = validate('baseline',read(path))
        known = {f['fingerprint'] for f in old['findings']}
        regressions = [f for f in findings if f['fingerprint'] not in known] + quality_regressions(old['quality'],data['quality']) + readiness_regressions(old,data)
        if regressions:
            return regressions
    new = dict(schema_version=1,created_at=now(),findings=findings,quality=data['quality'],readiness={i['id']:i['readiness'] for i in data['interfaces']['interfaces']})
    write(path,validate('baseline',new))
    return []


def require_reviewer(data, reviewer):
    if any(reviewer not in p['promotion_reviewers'] for p in policies(data)):
        raise HarnessError(f'{reviewer} is not listed in every applicable governance policy')


def require_files(root, paths):
    for path in paths:
        if not contained(root,path).is_file():
            raise HarnessError(f'Required evidence/decision missing: {path}')


def record_feedback(root,data,feedback):
    validate('feedback',feedback)
    if feedback['status']!='recorded' or feedback['promotion'] is not None:
        raise HarnessError('New feedback must be recorded and unpromoted')
    known = {a['id'] for a in data['all_assets']}
    if not set(feedback['existing_assets']) <= known:
        raise HarnessError('Feedback references unknown assets')
    require_files(root,feedback['evidence'])
    path = contained(root,f'.harness/feedback/{feedback["id"]}.json')
    if path.exists():
        if read(path)==feedback:
            return path
        raise HarnessError('Feedback ID already exists')
    write(path,feedback)
    return path


def propose(feedback):
    if feedback['intervention']=='none':
        return 'none'
    if feedback['deterministic']:
        return 'test' if feedback['category']=='regression' else 'rule'
    if feedback['recurrence']>=2 and feedback['category']=='procedure':
        return 'skill'
    return 'knowledge'


def promote(root,data,identifier,target,reviewer,decision):
    path = contained(root,f'.harness/feedback/{identifier}.json')
    feedback = validate('feedback',read(path))
    require_reviewer(data,reviewer)
    require_files(root,[target,decision])
    if feedback['status']=='promoted':
        raise HarnessError('Feedback is already promoted')
    if feedback['intervention']=='none':
        raise HarnessError('No-intervention feedback cannot be promoted')
    updated = dict(feedback,status='promoted',promotion=dict(target=target,reviewed_by=reviewer,decision=decision))
    write(path,validate('feedback',updated))
    return updated


def transition(root,data,request):
    validate('lifecycle',request)
    require_reviewer(data,request['reviewed_by'])
    require_files(root,[request['decision']]+request['evidence'])
    assets = data['assets']['assets']
    asset = next((a for a in assets if a['id']==request['asset']),None)
    if asset is None:
        raise HarnessError('Lifecycle changes apply to locally owned assets; update team source separately')
    next_status = {'experimental':'standard','standard':'deprecated','deprecated':'removed'}
    if asset['status']!=request['from_status'] or next_status.get(asset['status'])!=request['to_status']:
        raise HarnessError('Invalid lifecycle transition')
    if set(asset['consumers'])!=set(request['consumers_verified']):
        raise HarnessError('Verify every registered consumer before lifecycle transition')
    replacement = request['replacement']
    if replacement is not None:
        candidate = next((a for a in data['all_assets'] if a['id']==replacement),None)
        if not candidate or candidate['status']!='standard' or replacement==asset['id']:
            raise HarnessError('Replacement must be a different standard asset')
    updated = dict(asset,status=request['to_status'],deprecated_by=replacement,evidence=request['evidence'])
    log = contained(root,f'.harness/lifecycle/{asset["id"]}-{request["to_status"]}.json')
    if log.exists():
        raise HarnessError('Lifecycle event already exists')
    write(log,request)
    write(contained(root,'.harness/assets.json'),dict(schema_version=1,assets=[updated if a['id']==asset['id'] else a for a in assets]))
    return updated


def eval_report(root):
    events = [validate('eval',read(p)) for p in sorted(contained(root,'.harness/evals').glob('*.json'))]
    if not events:
        return dict(count=0,rates={},totals={})
    flags = ['first_pass','asset_miss','architecture_violation','escaped_defect','reviewer_disagreement']
    counts = ['human_interventions','rework','reused_assets','new_assets','time_to_evidence_seconds']
    return dict(count=len(events),rates={k:sum(e[k] for e in events)/len(events) for k in flags},totals={k:sum(e[k] for e in events) for k in counts})
