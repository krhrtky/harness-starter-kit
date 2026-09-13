"""Technology discovery is advisory; only enabled registry commands execute."""
from __future__ import annotations

import os
import signal
import subprocess
import time
import uuid
from pathlib import Path
from typing import Protocol

from .gates import change_checks, receipt_for, required_caps, task_checks
from .storage import HarnessError, contained, digest, files, now, read, validate, write


class Adapter(Protocol):
    def run(self, root: Path, capability: dict, run_dir: Path) -> dict: ...


class ProcessAdapter:
    def run(self, root, capability, run_dir):
        started = time.monotonic()
        prior_artifacts = {p: contained(root,p).stat().st_mtime_ns if contained(root,p).is_file() else None for p in capability['artifacts']}
        log = run_dir / (capability['id']+'.log')
        status, code = 'error', None
        environment = {k:v for k,v in os.environ.items() if k in {'PATH','HOME','TMPDIR','SYSTEMROOT','LANG','LC_ALL','VIRTUAL_ENV'}}
        environment.update(capability['env'])
        with log.open('wb') as stream:
            try:
                process = subprocess.Popen(capability['argv'], cwd=contained(root,capability['cwd']), env=environment, stdout=stream, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
                try:
                    code = process.wait(timeout=capability['timeout_seconds'])
                    status = 'passed' if code==0 else 'failed'
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL)
                    process.wait()
                    status = 'timeout'
            except OSError as exc:
                stream.write(str(exc).encode())
        artifacts = []
        for relative in capability['artifacts']:
            path = contained(root,relative)
            if not path.is_file():
                status = 'failed'
                continue
            if path.stat().st_mtime_ns == prior_artifacts[relative]:
                status = 'failed'
            artifacts.append(dict(path=relative,digest=digest(path.read_bytes())))
        return dict(capability=capability['id'],argv=capability['argv'],status=status,exit_code=code,duration_seconds=round(time.monotonic()-started,6),log=log.relative_to(root).as_posix(),log_digest=digest(log.read_bytes()),artifacts=artifacts)


ADAPTERS: dict[str, Adapter] = {'process':ProcessAdapter()}


def suggestions(root):
    candidates = []
    if (root/'package.json').is_file():
        for name in read(root/'package.json').get('scripts',{}):
            if name in {'build','lint','test','typecheck'}:
                candidates.append(dict(id='test.unit' if name=='test' else name,argv=['npm','run',name],reason='package.json scripts'))
    if (root/'pyproject.toml').is_file():
        candidates.append(dict(id='test.unit',argv=['python','-m','unittest','discover','-s','tests'],reason='Python project; confirm test runner before enabling'))
    if (root/'go.mod').is_file():
        candidates.append(dict(id='test.unit',argv=['go','test','./...'],reason='go.mod'))
    return [dict(c,adapter='process',cwd='.',timeout_seconds=300,enabled=False,env={},artifacts=[]) for c in candidates]


def verify(root,data,task):
    receipt = receipt_for(root,task)
    blockers = task_checks(root,data,task,'verify') + change_checks(root,data,task,receipt)
    if blockers:
        return None,blockers
    selected = required_caps(data,task)
    caps = {c['id']:c for c in data['capabilities']['capabilities']}
    before = digest(files(root))
    run_id = 'EV-'+uuid.uuid4().hex
    run_dir = contained(root,f'.harness/runs/{task["id"]}/{run_id}')
    run_dir.mkdir(parents=True)
    records = [ADAPTERS[caps[name]['adapter']].run(root,caps[name],run_dir) for name in selected]
    try:
        revision = subprocess.run(['git','rev-parse','HEAD'],cwd=root,capture_output=True,text=True,check=False)
        revision_id = revision.stdout.strip() if revision.returncode==0 else None
    except FileNotFoundError:
        revision_id = None
    bundle = dict(schema_version=1,id=run_id,task=task['id'],task_digest=digest(task),receipt_digest=digest(receipt),source_digest=before,source_revision=revision_id,generated_at=now(),records=records,stable_source=before==digest(files(root)))
    validate('evidence',bundle)
    path = run_dir/'evidence.json'
    write(path,bundle)
    return path,[]
