"""Evaluate repository-owned result contracts with the existing schema engine."""
from __future__ import annotations

import json

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry
from referencing.exceptions import Unresolvable

from .storage import HarnessError, contained, digest, files

DIALECT = 'https://json-schema.org/draft/2020-12/schema'


def unique_object(pairs):
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate JSON members')
    return dict(pairs)


def reject_constant(value):
    raise ValueError(f'Non-JSON numeric constant: {value}')


def read_json(path):
    try:
        content = path.read_bytes()
        value = json.loads(content, object_pairs_hook=unique_object, parse_constant=reject_constant)
        return value, digest(content)
    except (OSError, ValueError) as exc:
        raise HarnessError(f'{path}: {exc}') from exc


def validate_result(root, schema_path, input_path):
    contract_path = contained(root, schema_path)
    relative_schema = contract_path.relative_to(root).as_posix()
    if relative_schema not in files(root):
        raise HarnessError('Result schema must be in the source snapshot, outside runtime/cache directories')
    contract, contract_digest = read_json(contract_path)
    if not isinstance(contract, dict) or contract.get('$schema') != DIALECT:
        raise HarnessError(f'Result schema must explicitly declare {DIALECT}')
    instance, input_digest = read_json(contained(root, input_path))
    try:
        Draft202012Validator.check_schema(contract)
        validator = Draft202012Validator(contract, registry=Registry(), format_checker=FormatChecker())
        errors = list(validator.iter_errors(instance))
    except (SchemaError, Unresolvable, RecursionError) as exc:
        raise HarnessError(f'Invalid or unresolved result schema: {exc}') from exc
    findings = [dict(code='result.mismatch', path=list(error.absolute_path), message=error.message)
                for error in errors[:8]]
    return dict(ok=not errors, findings=findings, error_count=len(errors),
                schema=relative_schema, schema_digest=contract_digest,
                input=contained(root, input_path).relative_to(root).as_posix(), input_digest=input_digest), int(bool(errors))
