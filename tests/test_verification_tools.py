import importlib.util
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1]/'tooling/verification/tools.py'
spec = importlib.util.spec_from_file_location('verification_profile_tools', SCRIPT)
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)


class VerificationToolContracts(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.work = self.root/'run'
        self.work.mkdir()
        patcher = patch.object(tools, 'ROOT', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_tool_exit_and_raw_log_are_preserved(self):
        record = tools.execute([sys.executable, '-c', "print('known failure'); raise SystemExit(7)"], self.work, 'failure')
        self.assertEqual(7, record['exit_code'])
        self.assertIn('known failure', tools.output(record))
        with self.assertRaises(tools.ToolFailure):
            tools.require_pass(record)

    def test_missing_executable_and_timeout_never_pass(self):
        with self.assertRaises(tools.ToolFailure):
            tools.execute(['harness-tool-that-does-not-exist'], self.work, 'missing')
        with self.assertRaises(tools.ToolFailure):
            tools.execute([sys.executable, '-c', 'import time; time.sleep(60)'], self.work, 'timeout', timeout=1)
        self.assertTrue((self.work/'timeout.log').is_file())

    def test_missing_backend_fails_without_implicit_installation(self):
        with patch.object(tools, 'prerequisites'), patch.object(tools, 'QUINT_HOME', self.root/'missing'), patch.object(tools, 'setup') as install:
            with self.assertRaises(tools.ToolFailure):
                tools.status(self.work)
            install.assert_not_called()

    def test_managed_timeout_stops_the_wrapper_and_its_process_group(self):
        script = '''
import importlib.util, pathlib, sys
spec = importlib.util.spec_from_file_location('tools', sys.argv[1])
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)
tools.ROOT = pathlib.Path(sys.argv[2])
tools.execute([sys.executable, '-c', 'import os,time; print(os.getpgrp(), flush=True); time.sleep(60)'], tools.ROOT, 'managed', timeout=1)
'''
        command = [sys.executable, '-c', script, str(SCRIPT), str(self.work)]
        process = subprocess.Popen(command, env=dict(os.environ, HARNESS_MANAGED_PROCESS_GROUP='1'), start_new_session=True)
        self.assertEqual(-9, process.wait(timeout=10))
        log = (self.work/'managed.log').read_text()
        self.assertEqual(process.pid, int(log.splitlines()[0]))
        self.assertIn('timed out', log)

    def test_failed_invocation_replaces_previous_pass_summary(self):
        runs = self.root/'.harness/runs/verification-tools'
        tools.write(runs/'formal.json', {'decision': 'PASS'})
        with patch.object(tools, 'RUNS', runs), patch.object(tools, 'formal', side_effect=tools.ToolFailure('missing runtime')):
            with patch('builtins.print'):
                self.assertEqual(2, tools.main(['formal']))
        result = json.loads((runs/'formal.json').read_text())
        self.assertEqual('ERROR', result['decision'])
        self.assertEqual('missing runtime', result['error'])
        self.assertEqual(result, json.loads((self.root/result['run']/'result.json').read_text()))

    def test_model_checker_error_is_not_an_expected_counterexample(self):
        with patch.object(tools, 'formal', return_value={'tool_exit': 2, 'counterexample': None}), patch.object(tools, 'properties') as property_run:
            with self.assertRaises(tools.ToolFailure):
                tools.selftest(self.work)
            property_run.assert_not_called()

    def test_non_violating_trace_is_not_a_successful_mutation_probe(self):
        trace = self.root/'trace.json'
        trace.write_text(json.dumps({'states': [{'accepted': True, 'revision': 1, 'verifiedRevision': 1}]}))
        with patch.object(tools, 'formal', return_value={'tool_exit': 1, 'counterexample': 'trace.json'}):
            with self.assertRaises(tools.ToolFailure):
                tools.selftest(self.work)
