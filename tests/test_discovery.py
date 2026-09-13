import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from harnessctl.cli import command_catalog, parser
from harnessctl.discovery import schema, usage
from harnessctl.storage import HarnessError


class DiscoveryContracts(unittest.TestCase):
    def test_all_topics_and_schemas_resolve_without_repository(self):
        index=usage('index',command_catalog())
        self.assertTrue(index['offline'])
        self.assertEqual(10,len([t for t in index['topics'] if t['id'].startswith('harness-')]))
        for topic in index['topics']:
            self.assertTrue(usage(topic['id'],command_catalog())['ok'])
        for name in schema(None)['schemas']:
            self.assertIn('$schema',schema(name)['schema'])

    def test_commands_are_discoverable_as_machine_readable_arguments(self):
        catalog={c['name']:c for c in command_catalog()}
        self.assertTrue({'usage','schema','init','preflight','verify','check'}<=catalog.keys())
        task=next(a for a in catalog['preflight']['arguments'] if a['name']=='task')
        self.assertTrue(task['required'])
        self.assertEqual(['--task'],task['flags'])

    def test_unknown_names_cannot_read_arbitrary_files(self):
        for name in ['../../pyproject.toml','/etc/passwd','missing']:
            with self.assertRaises(HarnessError):usage(name,command_catalog())
            with self.assertRaises(HarnessError):schema(name)

    def test_cli_discovery_ignores_nonexistent_project_root(self):
        with tempfile.TemporaryDirectory() as temp:
            for command in [('usage','agent'),('schema','task')]:
                run=subprocess.run([sys.executable,'-m','harnessctl','--root',str(Path(temp)/'absent'),*command],capture_output=True,text=True)
                self.assertEqual(0,run.returncode,run.stderr)
                self.assertTrue(json.loads(run.stdout)['ok'])

    def test_help_points_to_offline_usage(self):
        self.assertIn('harnessctl usage',parser().format_help())
