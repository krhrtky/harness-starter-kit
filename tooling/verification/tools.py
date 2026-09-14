"""Pinned, repository-local verification profiles; no implicit installation on run."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import uuid
import venv

ROOT = Path(__file__).resolve().parents[2]
PROFILE = Path(__file__).resolve().parent
RUNTIME = ROOT/'.venv'
PYTHON = RUNTIME/'bin/python'
QUINT = PROFILE/'node_modules/.bin/quint'
QUINT_HOME = RUNTIME/'verification-tools/quint-home'
APALACHE_VERSION = '0.56.1'
APALACHE_URL = 'https://github.com/apalache-mc/apalache/releases/download/v0.56.1/apalache-0.56.1.tgz'
APALACHE_SHA256 = 'a61c07569d7195ddc589f01037fa10fafef4fb0796af2f1c9cb45226375dfbfc'
VERSIONS = {'quint': '0.32.0', 'apalache': APALACHE_VERSION, 'hypothesis': '6.168.0'}
RUNS = ROOT/'.harness/runs/verification-tools'


class ToolFailure(Exception):
    pass


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    temporary.replace(path)


def execute(argv, work, label, cwd=None, timeout=180):
    environment = dict(os.environ, QUINT_HOME=str(QUINT_HOME), PYTHONDONTWRITEBYTECODE='1',
                       HYPOTHESIS_STORAGE_DIRECTORY=str(work/'hypothesis'))
    managed = environment.get('HARNESS_MANAGED_PROCESS_GROUP') == '1'
    if managed and os.getpgrp() != os.getpid():
        raise ToolFailure('Managed mode requires the Harness process adapter group leader')
    log = work/f'{label}.log'
    with log.open('wb') as stream:
        try:
            process = subprocess.Popen(list(map(str, argv)), cwd=cwd or ROOT, env=environment,
                                       stdout=stream, stderr=subprocess.STDOUT, start_new_session=not managed)
        except OSError as exc:
            raise ToolFailure(f'{label}: {exc}; run setup first') from exc
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            stream.write(f'\n{label}: timed out after {timeout}s\n'.encode())
            stream.flush()
            group = os.getpgrp() if managed else process.pid
            os.killpg(group, signal.SIGKILL)
            process.wait()
            raise ToolFailure(f'{label}: timed out after {timeout}s')
    return dict(argv=list(map(str, argv)), exit_code=code,
                log=log.relative_to(ROOT).as_posix(), log_sha256=sha(log))


def require_pass(record):
    if record['exit_code'] != 0:
        raise ToolFailure(f"Command failed ({record['exit_code']}): {record['log']}")
    return record


def output(record):
    return (ROOT/record['log']).read_text(errors='replace').strip()


def prerequisites():
    if os.name != 'posix':
        raise ToolFailure('This profile supports macOS/Linux; use WSL on Windows')
    missing = [name for name in ['node', 'npm', 'java'] if not shutil.which(name)]
    if missing:
        raise ToolFailure(f'Missing prerequisites: {missing}. Install Node.js 20+ and Java 17+; see usage verification-tools')


def setup(work, archive_path=None):
    prerequisites()
    if not PYTHON.is_file():
        venv.EnvBuilder(with_pip=True).create(RUNTIME)
    records = [require_pass(execute([PYTHON, '-m', 'pip', 'install', '-e', ROOT, '-r', PROFILE/'requirements.txt'], work, 'pip-install', timeout=300)),
               require_pass(execute(['npm', 'ci', '--ignore-scripts', '--no-audit', '--no-fund'], work, 'npm-ci', cwd=PROFILE, timeout=300))]
    cache = RUNTIME/'verification-tools'
    cache.mkdir(parents=True, exist_ok=True)
    archive = archive_path or cache/'apalache-0.56.1.tgz'
    if archive_path is None and not archive.is_file():
        with urllib.request.urlopen(APALACHE_URL, timeout=60) as response:
            content = response.read()
        archive.write_bytes(content)
    if sha(archive) != APALACHE_SHA256:
        raise ToolFailure('Apalache archive checksum mismatch; no extraction performed')
    cached_archive = cache/'apalache-0.56.1.tgz'
    if archive.resolve() != cached_archive.resolve():
        shutil.copy2(archive, cached_archive)
    target = QUINT_HOME/f'apalache-dist-{APALACHE_VERSION}'/'apalache'
    with tempfile.TemporaryDirectory(dir=cache) as directory:
        extraction = Path(directory)
        with tarfile.open(archive, 'r:gz') as package:
            members = package.getmembers()
            if any(Path(m.name).is_absolute() or '..' in Path(m.name).parts or not (m.isfile() or m.isdir()) for m in members):
                raise ToolFailure('Unsafe archive member')
            package.extractall(extraction, members=members)
        source = extraction/f'apalache-{APALACHE_VERSION}'
        if not (source/'bin/apalache-mc').is_file():
            raise ToolFailure('Apalache executable is absent from archive')
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(source), target)
    return dict(records=records, archive_sha256=sha(archive), **status(work))


def status(work):
    prerequisites()
    expected = QUINT_HOME/f'apalache-dist-{APALACHE_VERSION}/apalache/bin/apalache-mc'
    if not expected.is_file():
        raise ToolFailure('Apalache is not installed; run setup')
    records = [require_pass(execute(['node', '--version'], work, 'node-version')),
               require_pass(execute(['java', '-version'], work, 'java-version')),
               require_pass(execute([QUINT, '--version'], work, 'quint-version')),
               require_pass(execute([PYTHON, '-c', 'import hypothesis; print(hypothesis.__version__)'], work, 'hypothesis-version')),
               require_pass(execute([expected, 'version'], work, 'apalache-version'))]
    if output(records[2]) != VERSIONS['quint'] or output(records[3]) != VERSIONS['hypothesis']:
        raise ToolFailure('Installed tool version differs from the pinned profile; rerun setup')
    if APALACHE_VERSION not in output(records[4]):
        raise ToolFailure('Apalache version differs from the pinned profile')
    return dict(versions={**VERSIONS, 'node': output(records[0]), 'java': output(records[1])},
                version_checks=records, npm_lock_sha256=sha(PROFILE/'package-lock.json'))


def formal(work, model=None, main='EvidenceLifecycle', invariant='acceptedIsCurrent', bound=8, mutation=False):
    installed = status(work)
    model = (model or ROOT/'verification/evidence.qnt').resolve()
    if not model.is_relative_to(ROOT) or not model.is_file():
        raise ToolFailure('Model must be an existing repository file')
    source = model.read_text()
    if mutation:
        original = "accepted' = passed and intact and verifiedRevision == revision,"
        if source.count(original) != 1:
            raise ToolFailure('Freshness mutation no longer matches the reviewed model')
        source = source.replace(original, "accepted' = passed and intact,", 1)
    copied = work/'model.qnt'
    copied.write_text(source)
    records = [require_pass(execute([QUINT, phase, copied], work, phase, cwd=work)) for phase in ['parse', 'typecheck']]
    if not mutation and model == ROOT/'verification/evidence.qnt':
        records.append(require_pass(execute([QUINT, 'test', copied, '--main='+main, '--backend=typescript'], work, 'reachability', cwd=work)))
    trace = work/'counterexample.itf.json'
    record = execute([QUINT, 'verify', copied, '--main='+main, '--init=init', '--step=step',
                      '--invariant='+invariant, '--backend=apalache', '--apalache-version='+APALACHE_VERSION,
                      '--max-steps='+str(bound), '--random-transitions=false', '--verbosity=0', '--out-itf='+str(trace)], work, 'verify', cwd=work)
    return dict(**installed, records=records+[record], model=model.relative_to(ROOT).as_posix(),
                model_sha256=sha(model), executed_model_sha256=sha(copied), max_steps=bound,
                mutation=mutation, counterexample=trace.relative_to(ROOT).as_posix() if trace.is_file() else None,
                tool_exit=record['exit_code'])


def properties(work, mutation=False):
    installed = status(work)
    command = [PYTHON, PROFILE/'properties.py'] + (['--mutate-freshness'] if mutation else [])
    record = execute(command, work, 'properties', timeout=240)
    return dict(**installed, records=[record], mutation=mutation, max_examples=25,
                stateful_step_count=12, derandomize=True, tool_exit=record['exit_code'])


def selftest(work):
    formal_dir, property_dir = work/'formal-mutant', work/'property-mutant'
    formal_dir.mkdir(); property_dir.mkdir()
    counterexample = formal(formal_dir, mutation=True)
    if counterexample['tool_exit'] != 1 or not counterexample['counterexample']:
        raise ToolFailure('Quint did not produce the expected invariant counterexample')
    states = json.loads((ROOT/counterexample['counterexample']).read_text())['states']
    if not any(s.get('accepted') is True and s.get('revision') != s.get('verifiedRevision') for s in states):
        raise ToolFailure('Quint trace does not demonstrate stale evidence acceptance')
    property_result = properties(property_dir, mutation=True)
    if property_result['tool_exit'] != 1 or 'evidence acceptance differs from independent state' not in output(property_result['records'][0]):
        raise ToolFailure('Hypothesis did not detect the omitted freshness gate')
    return dict(formal_mutation=counterexample, property_mutation=property_result,
                interpretation='PASS means expected defects were detected, not that the defective subjects passed')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['setup', 'status', 'formal', 'properties', 'selftest'])
    parser.add_argument('--apalache-archive', type=Path, help='Use a local archive with the pinned SHA-256')
    parser.add_argument('--model', type=Path, help='Repository-relative Quint file; default verification/evidence.qnt')
    parser.add_argument('--main', default='EvidenceLifecycle')
    parser.add_argument('--invariant', default='acceptedIsCurrent')
    parser.add_argument('--max-steps', type=int, default=8)
    args = parser.parse_args(argv)
    if args.max_steps < 1 or args.max_steps > 100:
        parser.error('--max-steps must be between 1 and 100')
    work = RUNS/uuid.uuid4().hex
    work.mkdir(parents=True)
    try:
        if args.action == 'setup':
            detail = setup(work, args.apalache_archive.resolve() if args.apalache_archive else None)
        elif args.action == 'formal':
            detail = formal(work, ROOT/args.model if args.model else None, args.main, args.invariant, args.max_steps)
        else:
            detail = {'status': status, 'properties': properties, 'selftest': selftest}[args.action](work)
        code = detail.get('tool_exit', 0)
        result = dict(schema_version=1, profile=args.action, decision='PASS' if code == 0 else 'FAIL', **detail)
    except (ToolFailure, OSError, ValueError, KeyError, tarfile.TarError) as exc:
        code, result = 2, dict(schema_version=1, profile=args.action, decision='ERROR', error=str(exc))
    result['run'] = work.relative_to(ROOT).as_posix()
    write(work/'result.json', result)
    write(RUNS/f'{args.action}.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if code == 0 else 1 if code == 1 else 2


if __name__ == '__main__':
    raise SystemExit(main())
