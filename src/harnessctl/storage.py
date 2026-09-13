"""Versioned JSON contracts and repository-contained storage."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

RESOURCES = Path(__file__).parent / 'resources'
SCHEMAS = RESOURCES / 'schemas'
IGNORED_DIRS = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'build', 'dist'}
RUNTIME_DIRS = {'.harness/runs', '.harness/backups'}


class HarnessError(Exception):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    data = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()


def read(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        raise HarnessError(f'{path}: {exc}') from exc


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, indent=2, ensure_ascii=False) + '\n'
    fd, temporary = tempfile.mkstemp(prefix='.harness-write-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def contained(root, relative):
    value = Path(relative)
    if value.is_absolute() or '..' in value.parts:
        raise HarnessError(f'Path must be repository relative: {relative}')
    result = (root / value).resolve()
    if not result.is_relative_to(root.resolve()):
        raise HarnessError(f'Path escapes repository: {relative}')
    return result


def validate(kind, data):
    schemas = [read(p) for p in sorted(SCHEMAS.glob('*.json'))]
    registry = Registry().with_resources((s['$id'], Resource.from_contents(s)) for s in schemas)
    schema = next(s for s in schemas if s['$id'].endswith(f'/{kind}.schema.json'))
    errors = sorted(Draft202012Validator(schema, registry=registry, format_checker=FormatChecker()).iter_errors(data), key=lambda e: str(e.path))
    if errors:
        raise HarnessError('; '.join(f'{kind}/{"/".join(map(str,e.path))}: {e.message}' for e in errors[:8]))
    return data


def load(root, name, kind=None):
    return validate(kind or name, read(contained(root, f'.harness/{name}.json')))


def files(root):
    result = {}
    for current, dirs, names in os.walk(root, followlinks=False):
        base = Path(current)
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS and not d.endswith('.egg-info') and (base / d).relative_to(root).as_posix() not in RUNTIME_DIRS)
        for name in sorted(names):
            p = base / name
            if name.endswith(('.pyc', '.pyo')) or name == '.DS_Store':
                continue
            rel = p.relative_to(root).as_posix()
            if p.is_symlink():
                result[rel] = digest(('symlink:' + os.readlink(p)).encode())
            else:
                result[rel] = digest(p.read_bytes())
        for name in dirs:
            p = base / name
            if p.is_symlink():
                result[p.relative_to(root).as_posix()] = digest(('symlink:' + os.readlink(p)).encode())
    return result


def control_digest(root):
    return digest({k:v for k,v in files(root).items() if k.startswith('.harness/') and not k.startswith('.harness/lifecycle/') and k not in {'.harness/quality.json', '.harness/knowledge.json', '.harness/assets.json'} })


def age_hours(timestamp):
    value = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    if value.tzinfo is None:
        raise HarnessError('Timestamps require a timezone')
    return (datetime.now(timezone.utc) - value).total_seconds()/3600
