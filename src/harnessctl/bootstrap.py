"""Non-destructive seed installation and manifest-based upgrades."""
from __future__ import annotations

import shutil
from pathlib import Path

from .storage import HarnessError, RESOURCES, SCHEMAS, contained, digest, now, read, validate, write


def payload():
    seed = RESOURCES/'seed'
    result = {}
    for source in sorted(seed.rglob('*')):
        if not source.is_file():
            continue
        parts = source.relative_to(seed).parts
        target = '/'.join(('.harness' if parts[0]=='harness' else parts[0],*parts[1:]))
        result[target] = source.read_bytes()
    for source in sorted(SCHEMAS.glob('*.json')):
        result[f'.harness/schemas/{source.name}'] = source.read_bytes()
    for source in sorted((RESOURCES/'skills').glob('*/SKILL.md')):
        result[f'.agents/skills/{source.parent.name}/SKILL.md'] = source.read_bytes()
    return result


def init(root,mode,name,owner):
    if (root/'.harness/project.json').exists():
        validate('project',read(root/'.harness/project.json'))
        return dict(created=[],preserved=['.harness/project.json'],initialized=False)
    distribution = payload()
    for target in distribution:
        path = contained(root,target)
        if target.startswith('.harness/') and path.exists():
            raise HarnessError(f'Partial control plane exists; resolve before init: {target}')
    created,preserved = [],[]
    for relative,content in distribution.items():
        path = contained(root,relative)
        if path.exists():
            preserved.append(relative)
            continue
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(content)
        created.append(relative)
    project = dict(schema_version=1,name=name,mode=mode,maturity=0,owner=owner,team_bundle=None,team_digest=None)
    write(contained(root,'.harness/project.json'),project)
    interfaces = read(root/'.harness/interfaces.json')
    interfaces['interfaces'] = [dict(i,owner=owner) for i in interfaces['interfaces']]
    write(root/'.harness/interfaces.json',interfaces)
    knowledge = read(root/'.harness/knowledge.json')
    knowledge['documents'] = [dict(d,owner=owner,reviewed_at=now(),content_digest=digest(contained(root,d['path']).read_bytes())) for d in knowledge['documents']]
    write(root/'.harness/knowledge.json',knowledge)
    policy = read(root/'.harness/policy.json')
    policy['promotion_reviewers'] = [owner]
    write(root/'.harness/policy.json',policy)
    write(root/'.harness/seed-manifest.json',dict(version=1,files={p:digest(content) for p,content in distribution.items() if p in created}))
    return dict(created=created,preserved=preserved,initialized=True)


def migrate(root,apply=False):
    project_path = contained(root,'.harness/project.json')
    original = read(project_path)
    version = original.get('schema_version')
    if version not in [0,1]:
        raise HarnessError(f'Unsupported schema version: {version}')
    updated = dict(original)
    if version==0:
        updated['schema_version'] = 1
        updated['mode'] = updated.pop('baseline_mode')
    validate('project',updated)
    manifest_path = contained(root,'.harness/seed-manifest.json')
    manifest = read(manifest_path) if manifest_path.exists() else dict(version=0,files={})
    candidates,conflicts = {},[]
    for relative,content in payload().items():
        if relative in {'.harness/project.json','.harness/seed-manifest.json'}:
            continue
        target = contained(root,relative)
        if not target.exists():
            candidates[relative] = content
            continue
        current_hash = digest(target.read_bytes())
        if current_hash==digest(content):
            continue
        if current_hash==manifest['files'].get(relative):
            candidates[relative] = content
        elif relative.startswith(('.harness/schemas/','.agents/skills/')):
            conflicts.append(relative)
    report = dict(from_version=version,to_version=1,updates=sorted(candidates),conflicts=conflicts,applied=False)
    if not apply:
        return report
    if conflicts:
        raise HarnessError(f'Migration conflicts; merge locally first: {conflicts}')
    if not candidates and original==updated:
        return report
    backup = contained(root,'.harness/backups/'+now().replace(':','-'))
    backup.mkdir(parents=True)
    paths = set(candidates) | {'.harness/project.json','.harness/seed-manifest.json'}
    for relative in paths:
        target = contained(root,relative)
        if target.exists():
            copy = backup/relative
            copy.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(target,copy)
    for relative,content in candidates.items():
        target = contained(root,relative)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(content)
    write(project_path,updated)
    write(manifest_path,dict(version=1,files={**manifest['files'],**{p:digest(c) for p,c in candidates.items()}}))
    return dict(report,applied=True,backup=backup.relative_to(root).as_posix())
