import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from harnessctl.adapters import verify
from harnessctl.bootstrap import init
from harnessctl.gates import delivery, preflight
from harnessctl.model import model
from harnessctl.results import DIALECT, validate_result
from harnessctl.storage import HarnessError, read, write
from support import FIXTURES, configured, findings


class ResultContracts(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.schema = read(FIXTURES/'delegated-result/accepted.schema.json')
        self.value = dict(schema_version=1, subject='fixture-v1', decision='PASS')
        write(self.root/'accepted.json', self.schema)
        write(self.root/'result.json', self.value)

    def cli(self):
        command = [sys.executable, '-m', 'harnessctl', '--root', str(self.root),
                   'result', 'validate', '--schema', 'accepted.json', '--input', 'result.json']
        process = subprocess.run(command, capture_output=True, text=True)
        return process.returncode, json.loads(process.stdout)

    def test_acceptance_schema_works_without_harness_initialization(self):
        code, result = self.cli()
        self.assertEqual(0, code)
        self.assertTrue(result['ok'])
        self.assertEqual(0, result['error_count'])
        self.assertEqual(64, len(result['input_digest']))
        self.assertFalse((self.root/'.harness').exists())

    def test_logical_fail_unknown_subject_version_and_extra_fields_reject(self):
        mutations = [dict(decision='FAIL'), dict(decision='UNKNOWN'), dict(subject='other'),
                     dict(schema_version=2), dict(extra=True), dict(schema_version=True)]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                write(self.root/'result.json', {**self.value, **mutation})
                code, result = self.cli()
                self.assertEqual(1, code)
                self.assertFalse(result['ok'])
                self.assertEqual('result.mismatch', result['findings'][0]['code'])

    def test_invalid_json_is_invalid_input_and_not_a_completed_check(self):
        for text in ['{broken', '{"decision":"FAIL","decision":"PASS"}', '{"value":NaN}', '{"value":Infinity}']:
            with self.subTest(text=text):
                (self.root/'result.json').write_text(text)
                code, result = self.cli()
                self.assertEqual(2, code)
                self.assertFalse(result['ok'])
                self.assertIn('error', result)

    def test_missing_input_and_invalid_schema_fail_closed(self):
        (self.root/'result.json').unlink()
        self.assertEqual(2, self.cli()[0])
        write(self.root/'result.json', self.value)
        for schema in [True, {}, {**self.schema, '$schema': 'http://json-schema.org/draft-07/schema#'},
                       {**self.schema, 'type': 'not-a-json-type'}]:
            with self.subTest(schema=schema):
                write(self.root/'accepted.json', schema)
                self.assertEqual(2, self.cli()[0])

    def test_internal_references_use_the_existing_schema_engine(self):
        write(self.root/'accepted.json', dict(**{'$schema': DIALECT, '$defs': {'result': self.schema}, '$ref': '#/$defs/result'}))
        self.assertEqual(0, self.cli()[0])
        write(self.root/'result.json', {**self.value, 'decision': 'FAIL'})
        self.assertEqual(1, self.cli()[0])

    def test_unresolved_references_never_fetch_network_or_sibling_files(self):
        for reference in ['https://example.invalid/remote.json', 'file:///etc/passwd', 'result.json', '#/$defs/missing']:
            with self.subTest(reference=reference):
                write(self.root/'accepted.json', {'$schema': DIALECT, '$ref': reference})
                with patch('urllib.request.urlopen', side_effect=AssertionError('Network must not run')):
                    with self.assertRaises(HarnessError):
                        validate_result(self.root, 'accepted.json', 'result.json')
                self.assertEqual(2, self.cli()[0])

    def test_schema_cannot_come_from_ignored_runtime_directory(self):
        for relative in ['.harness/runs/schema.json', 'build/schema.json', '.venv/schema.json']:
            with self.subTest(relative=relative):
                write(self.root/relative, self.schema)
                with self.assertRaises(HarnessError):
                    validate_result(self.root, relative, 'result.json')

    def test_paths_cannot_escape_repository(self):
        with tempfile.TemporaryDirectory() as outside:
            (self.root/'escape').symlink_to(Path(outside).resolve(), target_is_directory=True)
            for schema, instance in [('../accepted.json', 'result.json'), ('accepted.json', '../result.json'),
                                     ('escape/accepted.json', 'result.json'), ('accepted.json', 'escape/result.json')]:
                with self.subTest(schema=schema, instance=instance):
                    with self.assertRaises(HarnessError):
                        validate_result(self.root, schema, instance)


class DelegatedResultGateContracts(unittest.TestCase):
    def test_wrapper_to_delivery_preserves_producer_and_semantic_failures(self):
        cases = ['normal', 'logical-fail', 'unknown', 'wrong-subject', 'unknown-version',
                 'invalid-json', 'missing', 'producer-failed']
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                task = configured(root)
                shutil.copytree(FIXTURES/'delegated-result', root/'app/delegated')
                registry = read(root/'.harness/capabilities.json')
                registry['capabilities'].append(dict(id='verify.result', adapter='process',
                    argv=[sys.executable, 'app/delegated/check.py', case], cwd='.', timeout_seconds=10,
                    enabled=True, env={}, artifacts=['.harness/runs/delegated-result.json']))
                write(root/'.harness/capabilities.json', registry)
                task['required_capabilities'].append('verify.result')
                write(root/'.harness/tasks/task.json', task)
                self.assertEqual([], preflight(root, model(root), task))
                write(root/'.harness/runs/delegated-result.json', dict(schema_version=1, subject='fixture-v1', decision='PASS'))
                path, blockers = verify(root, model(root), task)
                self.assertEqual([], blockers)
                bundle = read(path)
                record = next(r for r in bundle['records'] if r['capability'] == 'verify.result')
                verdict = delivery(root, model(root), task, bundle, findings(root, task))
                self.assertEqual(case == 'normal', not verdict)
                self.assertEqual('passed' if case == 'normal' else 'failed', record['status'])
                if case == 'producer-failed':
                    self.assertEqual(7, record['exit_code'])
                if case != 'normal':
                    self.assertIn('evidence.failed', {f['code'] for f in verdict})
                if case == 'normal':
                    contract = root/'app/delegated/accepted.schema.json'
                    contract.write_text(contract.read_text()+'\n')
                    stale = delivery(root, model(root), task, bundle, findings(root, task))
                    self.assertIn('evidence.stale', {f['code'] for f in stale})

    def test_init_distributes_the_guide_and_adaptation_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            init(root, 'greenfield', 'delegation', 'owner')
            self.assertIn('result validate', (root/'docs/harness/verification.md').read_text())
            self.assertIn('独自実装', (root/'.agents/skills/harness-adapt/SKILL.md').read_text())
