"""Provider-independent JSON CLI. Exit 0 passes, 1 blocks, 2 is invalid input."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .adapters import suggestions, verify
from .bootstrap import init, migrate
from .discovery import schema, usage
from .checks import duplicate_candidates, knowledge_checks, quality_regressions, structure_checks
from .evolution import baseline, eval_report, promote, propose, record_feedback, transition
from .gates import baseline_checks, delivery, evidence_checks, preflight, receipt_for, task_at
from .model import model, search_assets
from .results import validate_result
from .storage import HarnessError, contained, digest, files, read, validate, write


def parser():
    p = argparse.ArgumentParser(prog='harnessctl',description='Start here: harnessctl usage. Offline guides, Skills and schemas are embedded.')
    p.add_argument('--version',action='version',version=__version__)
    p.add_argument('--root',default='.',help='Repository root; place before the subcommand')
    subs = p.add_subparsers(dest='command',required=True)
    i = subs.add_parser('usage',help='Read offline guides, Skills and the command catalog')
    i.add_argument('topic',nargs='?',default='index',help='documentation for placement rules; agent for the entrypoint; omit to list all guides and Skills')
    i = subs.add_parser('schema',help='Read embedded JSON Schema contracts without a repository')
    i.add_argument('name',nargs='?',help='Schema name; omit to list all names')
    i = subs.add_parser('result',help='Validate tool JSON against a repository-owned result schema')
    i.add_argument('action',choices=['validate'])
    i.add_argument('--schema',required=True,help='Repository-relative Draft 2020-12 acceptance schema')
    i.add_argument('--input',required=True,help='Repository-relative JSON result')
    i = subs.add_parser('init')
    i.add_argument('--mode',choices=['greenfield','brownfield'],default='greenfield')
    i.add_argument('--name',default='project')
    i.add_argument('--owner',required=True)
    for name in ['inspect','doctor']:
        subs.add_parser(name)
    i = subs.add_parser('inventory')
    i.add_argument('action',choices=['list','search','duplicates','transition'],nargs='?',default='list')
    i.add_argument('--capability',action='append',default=[])
    i.add_argument('--file')
    i = subs.add_parser('preflight')
    i.add_argument('--task',required=True)
    i = subs.add_parser('check')
    i.add_argument('--ci',action='store_true')
    i.add_argument('--phase',choices=['structure','delivery'],default='structure')
    i.add_argument('--task')
    i.add_argument('--bundle')
    i.add_argument('--findings')
    i = subs.add_parser('verify')
    i.add_argument('--task',required=True)
    i.add_argument('--ci',action='store_true')
    i = subs.add_parser('evidence')
    i.add_argument('action',choices=['validate'])
    i.add_argument('--task',required=True)
    i.add_argument('--bundle',required=True)
    i = subs.add_parser('knowledge')
    i.add_argument('action',choices=['check','index'],nargs='?',default='check')
    i = subs.add_parser('quality')
    i.add_argument('--against',help='Quality or baseline JSON path')
    i = subs.add_parser('feedback')
    i.add_argument('action',choices=['add','list','propose'])
    i.add_argument('--file')
    i.add_argument('--id')
    i = subs.add_parser('promote')
    i.add_argument('--id',required=True)
    i.add_argument('--target',required=True)
    i.add_argument('--reviewed-by',required=True)
    i.add_argument('--decision',required=True)
    subs.add_parser('baseline')
    i = subs.add_parser('migrate')
    i.add_argument('--apply',action='store_true')
    i = subs.add_parser('eval')
    i.add_argument('action',choices=['add','report'],nargs='?',default='report')
    i.add_argument('--file')
    return p


def needed(args,*names):
    for name in names:
        if not getattr(args,name,None):
            raise HarnessError(f'--{name.replace("_","-")} is required')


def result(findings=None, **data):
    findings = findings or []
    return dict(ok=not findings,findings=findings,**data),int(bool(findings))


def command_catalog():
    commands = next(a for a in parser()._actions if isinstance(a,argparse._SubParsersAction))
    return [dict(name=name,usage=p.format_usage().strip(),arguments=[dict(name=a.dest,flags=a.option_strings,required=a.required,choices=list(a.choices) if a.choices is not None else None,default=a.default,help=a.help) for a in p._actions if a.dest!='help']) for name,p in commands.choices.items()]


def dispatch(a):
    if a.command=='usage':
        return usage(a.topic,command_catalog()),0
    if a.command=='schema':
        return schema(a.name),0
    root = Path(a.root).resolve()
    if not root.is_dir():
        raise HarnessError(f'Repository directory does not exist: {root}')
    if a.command=='result':
        return validate_result(root,a.schema,a.input)
    if a.command=='init':
        return result(**init(root,a.mode,a.name,a.owner))
    if a.command=='migrate':
        report = migrate(root,a.apply)
        return dict(ok=not report['conflicts'],**report),int(bool(report['conflicts']))
    if a.command=='inspect':
        return result(initialized=(root/'.harness/project.json').exists(),candidates=suggestions(root),source_digest=digest(files(root)),instruction_files=sorted(p for p in files(root) if p.endswith(('AGENTS.md','AGENTS.override.md'))))
    data = model(root)
    if a.command=='doctor':
        return result(structure_checks(root,data),version=__version__,interfaces=27,adapters=['process'])
    if a.command=='inventory':
        if a.action=='transition':
            needed(a,'file')
            return result(asset=transition(root,data,read(contained(root,a.file))))
        if a.action=='duplicates':
            return result(candidates=duplicate_candidates(data),semantic_equivalence='unverified')
        return result(assets=search_assets(data,a.capability) if a.action=='search' else data['all_assets'])
    if a.command=='preflight':
        return result(preflight(root,data,task_at(root,a.task)))
    if a.command=='check':
        if a.phase=='structure':
            return result(baseline_checks(root,data))
        needed(a,'task','bundle','findings')
        return result(delivery(root,data,task_at(root,a.task),read(contained(root,a.bundle)),read(contained(root,a.findings))))
    if a.command=='verify':
        task = task_at(root,a.task)
        path, blockers = verify(root,data,task)
        if blockers:
            return result(blockers)
        bundle = read(path)
        return result(evidence_checks(root,data,task,bundle,receipt_for(root,task)),bundle=path.relative_to(root).as_posix())
    if a.command=='evidence':
        task = task_at(root,a.task)
        return result(evidence_checks(root,data,task,read(contained(root,a.bundle)),receipt_for(root,task)))
    if a.command=='knowledge':
        return result(knowledge_checks(root,data)) if a.action=='check' else result(documents=data['knowledge']['documents'])
    if a.command=='quality':
        path = a.against or '.harness/baselines/current.json'
        if not contained(root,path).is_file():
            return result(quality=data['quality'],comparison='no baseline')
        prior = read(contained(root,path))
        prior = validate('baseline',prior)['quality'] if 'quality' in prior else validate('quality',prior)
        return result(quality_regressions(prior,data['quality']),quality=data['quality'])
    if a.command=='baseline':
        return result(baseline(root,data))
    if a.command=='feedback':
        if a.action=='add':
            needed(a,'file')
            return result(path=record_feedback(root,data,read(contained(root,a.file))).relative_to(root).as_posix())
        if a.action=='propose':
            needed(a,'id')
            feedback = validate('feedback',read(contained(root,f'.harness/feedback/{a.id}.json')))
            return result(suggested_intervention=propose(feedback),recorded_intervention=feedback['intervention'])
        return result(feedback=[validate('feedback',read(p)) for p in sorted(contained(root,'.harness/feedback').glob('*.json'))])
    if a.command=='promote':
        return result(feedback=promote(root,data,a.id,a.target,a.reviewed_by,a.decision))
    if a.command=='eval':
        if a.action=='report':
            return result(**eval_report(root))
        needed(a,'file')
        event = validate('eval',read(contained(root,a.file)))
        target = contained(root,f'.harness/evals/{event["id"]}.json')
        if target.exists() and read(target)!=event:
            raise HarnessError('Eval ID already exists')
        write(target,event)
        return result(event=event['id'])
    raise HarnessError('Unsupported command')


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        output,code = dispatch(args)
    except (HarnessError,OSError,ValueError,KeyError) as exc:
        output,code = dict(ok=False,error=str(exc)),2
    print(json.dumps(output,ensure_ascii=False,sort_keys=True,indent=2))
    return code
