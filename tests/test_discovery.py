import json
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from harnessctl.bootstrap import init, migrate
from harnessctl.cli import command_catalog, parser
from harnessctl.discovery import schema, usage
from harnessctl.storage import HarnessError, RESOURCES


class DiscoveryContracts(unittest.TestCase):
    def test_all_topics_and_schemas_resolve_without_repository(self):
        index=usage('index',command_catalog())
        self.assertTrue(index['offline'])
        self.assertEqual(11,len([t for t in index['topics'] if t['id'].startswith('harness-')]))
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
        result_arguments = {a['name']:a for a in catalog['result']['arguments']}
        self.assertTrue(result_arguments['schema']['required'])
        self.assertTrue(result_arguments['input']['required'])
        self.assertIn('result validate', usage('verification',command_catalog())['content'])

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

    def test_documentation_is_discoverable_before_init(self):
        with tempfile.TemporaryDirectory() as temp:
            command = [sys.executable, '-m', 'harnessctl', '--root', str(Path(temp)/'absent')]
            index = subprocess.run([*command, 'usage'], capture_output=True, text=True)
            self.assertEqual(0, index.returncode, index.stderr)
            topics = {topic['id']: topic for topic in json.loads(index.stdout)['topics']}
            self.assertIn('documentation', topics)
            guide = subprocess.run([*command, 'usage', 'documentation'], capture_output=True, text=True)
            self.assertEqual(0, guide.returncode, guide.stderr)
            result = json.loads(guide.stdout)
            self.assertTrue(result['ok'])
            self.assertEqual('markdown', result['format'])
            self.assertEqual((RESOURCES/'seed/docs/harness/documentation-policy.md').read_text(), result['content'])
            self.assertFalse((Path(temp)/'absent').exists())
            help_result = subprocess.run([*command, 'usage', '--help'], capture_output=True, text=True)
            self.assertEqual(0, help_result.returncode)
            self.assertIn('documentation', help_result.stdout)

    def test_documentation_routes_resolve_from_guides_and_skills(self):
        for topic in ['agent', 'getting-started', 'cli', 'harness-bootstrap', 'harness-intake',
                      'harness-plan', 'harness-learn', 'harness-garden', 'harness-review', 'harness-document']:
            with self.subTest(topic=topic):
                content = usage(topic, command_catalog())['content']
                destinations = re.findall(r'(?:harnessctl )?usage (documentation)\b', content)
                self.assertTrue(destinations, f'{topic} has no documentation route')
                for destination in destinations:
                    self.assertTrue(usage(destination, command_catalog())['ok'])

    def test_preserved_local_rules_do_not_hide_embedded_documentation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            local = root/'docs/harness/documentation-policy.md'
            local.parent.mkdir(parents=True)
            local.write_text('Local approved placement rules: keep specifications in existing design/.')
            agent = root/'AGENTS.md'
            agent.write_text('Use the existing project instructions and local documentation policy.')
            original = {path: path.read_bytes() for path in [local, agent]}
            command = [sys.executable, '-m', 'harnessctl', '--root', str(root)]
            initialized = subprocess.run([*command, 'init', '--owner', 'example-team'], capture_output=True, text=True)
            self.assertEqual(0, initialized.returncode, initialized.stderr)
            preserved = json.loads(initialized.stdout)['preserved']
            self.assertTrue({'AGENTS.md', 'docs/harness/documentation-policy.md'} <= set(preserved))
            for path, content in original.items():
                self.assertEqual(content, path.read_bytes())
            embedded = subprocess.run([*command, 'usage', 'documentation'], capture_output=True, text=True)
            self.assertEqual(0, embedded.returncode, embedded.stderr)
            self.assertEqual(usage('documentation', command_catalog())['content'], json.loads(embedded.stdout)['content'])
            self.assertNotEqual(local.read_text(), json.loads(embedded.stdout)['content'])
            entry = subprocess.run([*command, 'usage', 'agent'], capture_output=True, text=True)
            self.assertEqual(0, entry.returncode, entry.stderr)
            self.assertIn('harnessctl usage documentation', json.loads(entry.stdout)['content'])

    def test_document_skill_is_available_and_installed_without_editing_existing_skills(self):
        index = usage('index', command_catalog())
        self.assertIn('harness-document', {topic['id'] for topic in index['topics']})
        content = usage('harness-document', command_catalog())['content']
        self.assertEqual((RESOURCES/'skills/harness-document/SKILL.md').read_text(), content)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            existing = root/'.agents/skills/harness-document/SKILL.md'
            initialized = init(root, 'greenfield', 'fixture', 'fixture-owner')
            self.assertIn('.agents/skills/harness-document/SKILL.md', initialized['created'])
            self.assertEqual(content, existing.read_text())
            existing.write_text('Local document workflow')
            init(root, 'greenfield', 'fixture', 'fixture-owner')
            self.assertEqual('Local document workflow', existing.read_text())

    def test_document_skill_migration_adds_missing_skill_and_blocks_local_overwrite(self):
        relative = '.agents/skills/harness-document/SKILL.md'
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            init(root, 'greenfield', 'fixture', 'fixture-owner')
            path = root/relative
            path.unlink()
            manifest_path = root/'.harness/seed-manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['files'].pop(relative)
            manifest_path.write_text(json.dumps(manifest))
            preview = migrate(root)
            self.assertIn(relative, preview['updates'])
            self.assertFalse(path.exists())
            self.assertTrue(migrate(root, apply=True)['applied'])
            self.assertEqual(usage('harness-document', command_catalog())['content'], path.read_text())
            path.write_text('Local document workflow')
            self.assertIn(relative, migrate(root)['conflicts'])
            with self.assertRaises(HarnessError):
                migrate(root, apply=True)
            self.assertEqual('Local document workflow', path.read_text())

    def test_phase_skills_route_document_work_to_the_bundled_skill(self):
        for topic in ['agent', 'getting-started', 'cli', 'harness-bootstrap', 'harness-intake',
                      'harness-plan', 'harness-learn', 'harness-garden', 'harness-review']:
            with self.subTest(topic=topic):
                targets = re.findall(r'(?:harnessctl )?usage (harness-document)\b', usage(topic, command_catalog())['content'])
                self.assertTrue(targets)
                for target in targets:
                    self.assertTrue(usage(target, command_catalog())['ok'])
