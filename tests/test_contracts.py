import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from harnessctl.adapters import ProcessAdapter, verify
from harnessctl.bootstrap import init, migrate, payload
from harnessctl.checks import structure_checks
from harnessctl.evolution import baseline, promote, record_feedback, transition
from harnessctl.gates import baseline_checks, delivery, evidence_checks, preflight, receipt_for, task_checks
from harnessctl.model import model
from harnessctl.storage import HarnessError, SCHEMAS, digest, files, now, read, validate, write
from support import configured, findings


class HarnessContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.task = configured(self.root)

    def cli(self,*args):
        r = subprocess.run([sys.executable,'-m','harnessctl','--root',str(self.root),*args],capture_output=True,text=True)
        return r.returncode,json.loads(r.stdout)

    def mutate(self,name,fn):
        path = self.root/f'.harness/{name}.json'
        obj = read(path)
        fn(obj)
        write(path,obj)

    def codes(self,items):
        return {i['code'] for i in items}

    def admit(self):
        self.assertEqual([],preflight(self.root,model(self.root),self.task))

    def verified(self):
        self.admit()
        path, blockers = verify(self.root,model(self.root),self.task)
        self.assertEqual([],blockers)
        return read(path)

    def test_full_delivery_cli(self):
        self.assertEqual(0,self.cli('preflight','--task','.harness/tasks/task.json')[0])
        code, output = self.cli('verify','--task','.harness/tasks/task.json')
        self.assertEqual(0,code,output)
        review = '.harness/runs/TASK-1/review.json'
        write(self.root/review,findings(self.root,self.task))
        code,output = self.cli('check','--phase','delivery','--task','.harness/tasks/task.json','--bundle',output['bundle'],'--findings',review,'--ci')
        self.assertEqual(0,code,output)

    def test_schema_rejects_empty_acceptance_and_extra_fields(self):
        for key,value in [('acceptance',[]),('invented',True),('risk',{'level':'unknown','reasons':[]})]:
            with self.subTest(key=key),self.assertRaises(HarnessError):
                validate('task',dict(self.task,**{key:value}))

    def test_schemas_are_valid_draft202012(self):
        from jsonschema import Draft202012Validator
        for path in SCHEMAS.glob('*.json'):
            Draft202012Validator.check_schema(read(path))

    def test_no_adapter_core_is_operable_but_required_task_blocks(self):
        self.mutate('capabilities',lambda d:d.update(capabilities=[]))
        self.assertEqual(0,self.cli('doctor')[0])
        self.assertIn('task.capability',self.codes(task_checks(self.root,model(self.root),self.task,'preflight')))

    def test_missing_router(self):
        (self.root/'ARCHITECTURE.md').unlink()
        self.assertIn('router.missing',self.codes(task_checks(self.root,model(self.root),self.task,'preflight')))

    def test_missing_domain_and_stale_knowledge(self):
        (self.root/'docs/domain/index.md').unlink()
        (self.root/'docs/security/index.md').write_text('Changed policy')
        codes = self.codes(structure_checks(self.root,model(self.root)))
        self.assertTrue({'knowledge.missing','knowledge.stale'}<=codes)

    def test_must_rule_cannot_lack_enforcement(self):
        self.mutate('policy',lambda d:d['rules'].append(dict(id='ARCH-1',interface='H02',owner='fixture-owner',severity='must',scope=['app/**'],source='ARCHITECTURE.md',enforcement=[],forbid_paths=[],require_paths=[])))
        self.assertIn('rule.unenforced',self.codes(structure_checks(self.root,model(self.root))))

    def test_asset_search_gate(self):
        self.task['asset_analysis']['duplicates_considered']=[]
        self.assertIn('asset.unconsidered',self.codes(task_checks(self.root,model(self.root),self.task,'preflight')))

    def test_known_duplicate_needs_distinction(self):
        self.task['asset_analysis']['new_assets']=[dict(id='orders.other',provides=['order.cancel'],path='app/other.py',reason='New helper')]
        self.assertIn('asset.duplicate',self.codes(task_checks(self.root,model(self.root),self.task,'preflight')))

    def test_transition_forbids_new_legacy_placement(self):
        self.mutate('evolution',lambda d:d['transition'].append(dict(id='MIG-1',owner='fixture-owner',status='active',source=['app/**'],target=['domain/**'],new_code='target-only',consumers=['orders-ui'],evidence=[])))
        self.assertIn('evolution.source',self.codes(task_checks(self.root,model(self.root),self.task,'preflight')))

    def test_cross_consumer_gate(self):
        a=self.task['asset_analysis']; a['reused']=[];a['extended']=['orders.cancel'];a['duplicates_considered'][0]['decision']='extend'
        self.task['cross_system_impact']['consumers']=[]
        self.assertIn('impact.missing',self.codes(task_checks(self.root,model(self.root),self.task,'preflight')))

    def test_out_of_scope_changes_block_before_execution(self):
        self.admit()
        (self.root/'unexpected.py').write_text('pass\n')
        path, blockers=verify(self.root,model(self.root),self.task)
        self.assertIsNone(path)
        self.assertIn('scope.exceeded',self.codes(blockers))

    def test_deleted_out_of_scope_file_blocks(self):
        self.admit()
        (self.root/'docs/decisions/index.md').unlink()
        _,blockers=verify(self.root,model(self.root),self.task)
        self.assertIn('scope.exceeded',self.codes(blockers))

    def test_failing_contract_is_not_passing_evidence(self):
        self.admit()
        (self.root/'app/orders.py').write_text("def cancel(state):\n    return 'cancelled'\n")
        path,blockers=verify(self.root,model(self.root),self.task)
        self.assertEqual([],blockers)
        self.assertEqual('failed',read(path)['records'][0]['status'])

    def test_stale_evidence_after_edit(self):
        bundle=self.verified()
        (self.root/'app/orders.py').write_text('# mutation\n'+(self.root/'app/orders.py').read_text())
        self.assertIn('evidence.stale',self.codes(evidence_checks(self.root,model(self.root),self.task,bundle,receipt_for(self.root,self.task))))

    def test_log_integrity(self):
        bundle=self.verified()
        (self.root/bundle['records'][0]['log']).write_text('fabricated')
        self.assertIn('evidence.integrity',self.codes(evidence_checks(self.root,model(self.root),self.task,bundle,receipt_for(self.root,self.task))))

    def test_future_and_expired_evidence(self):
        bundle=self.verified()
        for timestamp in ['2000-01-01T00:00:00Z','2999-01-01T00:00:00Z']:
            bundle['generated_at']=timestamp
            self.assertIn('evidence.age',self.codes(evidence_checks(self.root,model(self.root),self.task,bundle,receipt_for(self.root,self.task))))

    def test_missing_semantic_view_and_unknown_block(self):
        bundle=self.verified()
        review=findings(self.root,self.task)
        review['findings'].pop()
        review['findings'][0]['conclusion']='unknown'
        codes=self.codes(delivery(self.root,model(self.root),self.task,bundle,review))
        self.assertTrue({'review.missing','review.unresolved'}<=codes)

    def test_semantic_contradiction_is_consumed_not_invented(self):
        bundle=self.verified()
        review=findings(self.root,self.task)
        review['findings'][0]['contradictions']=['Domain contract contradicts observed implementation']
        self.assertIn('review.unresolved',self.codes(delivery(self.root,model(self.root),self.task,bundle,review)))

    def test_preflight_receipt_cannot_be_silently_rebased(self):
        self.admit()
        (self.root/'app/new.py').write_text('pass')
        with self.assertRaises(HarnessError): self.admit()

    def test_task_mutation_invalidates_receipt(self):
        self.admit()
        self.task['outcome']='Changed objective'
        with self.assertRaises(HarnessError):receipt_for(self.root,self.task)

    def test_policy_changes_cannot_weaken_current_delivery(self):
        self.admit()
        self.mutate('policy',lambda d:d.update(required_review_views=['entailment']))
        _,blockers=verify(self.root,model(self.root),self.task)
        self.assertIn('control.changed',self.codes(blockers))

    def test_quality_global_ratchet(self):
        self.admit()
        self.mutate('quality',lambda d:d['scores'][0].update(score=79))
        _,blockers=verify(self.root,model(self.root),self.task)
        self.assertIn('quality.regression',self.codes(blockers))

    def test_brownfield_touched_interface_cannot_hide_debt(self):
        self.mutate('project',lambda d:d.update(mode='brownfield'))
        self.mutate('knowledge',lambda d:d['documents'][1].update(status='unknown'))
        data=model(self.root)
        self.assertEqual([],baseline(self.root,data))
        self.assertEqual([],baseline_checks(self.root,data))
        self.assertIn('knowledge.unknown',self.codes(task_checks(self.root,data,self.task,'preflight')))

    def test_baseline_rejects_new_debt_and_quality_drop(self):
        self.assertEqual([],baseline(self.root,model(self.root)))
        self.mutate('quality',lambda d:d['scores'][0].update(score=0))
        (self.root/'ARCHITECTURE.md').unlink()
        blockers=baseline(self.root,model(self.root))
        self.assertTrue({'quality.regression','router.missing'}<=self.codes(blockers))

    def test_baseline_can_only_shrink(self):
        self.mutate('knowledge',lambda d:d['documents'][1].update(status='unknown'))
        baseline(self.root,model(self.root))
        self.mutate('knowledge',lambda d:d['documents'][1].update(status='documented'))
        self.assertEqual([],baseline(self.root,model(self.root)))
        self.assertEqual([],read(self.root/'.harness/baselines/current.json')['findings'])

    def test_team_invariant_is_additive_and_pinned(self):
        local=model(self.root)
        team=dict(schema_version=1,name='platform',assets=dict(schema_version=1,assets=[]),policy=copy.deepcopy(local['policy']),evolution=local['evolution'])
        team['policy']['rules']=[dict(id='TEAM-1',interface='H02',owner='platform',severity='must',scope=['app/**'],source='ARCHITECTURE.md',enforcement=[],forbid_paths=['app/**'],require_paths=[])]
        write(self.root/'.harness/team.json',team)
        self.mutate('project',lambda d:d.update(team_bundle='.harness/team.json',team_digest=digest(team)))
        self.assertIn('architecture.forbidden',self.codes(task_checks(self.root,model(self.root),self.task,'preflight')))
        team['name']='tampered';write(self.root/'.harness/team.json',team)
        with self.assertRaises(HarnessError):model(self.root)

    def test_schema_path_traversal_and_symlink_are_rejected(self):
        self.mutate('capabilities',lambda d:d['capabilities'][0].update(cwd='../outside'))
        with self.assertRaises(HarnessError):model(self.root)
        (self.root/'escape').symlink_to(self.root.parent,target_is_directory=True)
        from harnessctl.storage import contained
        with self.assertRaises(HarnessError):contained(self.root,'escape/something')

    def test_timeout_and_missing_executable_contract(self):
        run_dir=self.root/'.harness/runs/direct';run_dir.mkdir(parents=True)
        cap=model(self.root)['capabilities']['capabilities'][0]
        cap=dict(cap,argv=[sys.executable,'-c','import time; time.sleep(10)'],timeout_seconds=1)
        self.assertEqual('timeout',ProcessAdapter().run(self.root,cap,run_dir)['status'])
        cap['argv']=['harness-command-that-does-not-exist']
        self.assertEqual('error',ProcessAdapter().run(self.root,cap,run_dir)['status'])

    def test_argv_does_not_invoke_shell(self):
        run_dir=self.root/'.harness/runs/direct';run_dir.mkdir(parents=True)
        cap=model(self.root)['capabilities']['capabilities'][0]
        cap=dict(cap,argv=[sys.executable,'-c','import sys; print(sys.argv[1])','$(touch injected)'])
        self.assertEqual('passed',ProcessAdapter().run(self.root,cap,run_dir)['status'])
        self.assertFalse((self.root/'injected').exists())

    def test_lifecycle_requires_all_consumers_and_valid_next_state(self):
        request=dict(schema_version=1,asset='orders.cancel',from_status='standard',to_status='deprecated',reviewed_by='fixture-owner',decision='ARCHITECTURE.md',evidence=['app/check.py'],consumers_verified=[],replacement=None)
        with self.assertRaises(HarnessError):transition(self.root,model(self.root),request)
        request['consumers_verified']=['orders-ui']
        self.assertEqual('deprecated',transition(self.root,model(self.root),request)['status'])
        with self.assertRaises(HarnessError):transition(self.root,model(self.root),request)

    def test_feedback_promotes_existing_artifact_with_review(self):
        feedback=dict(schema_version=1,id='FB-1',task='TASK-1',category='regression',root_cause='Missing terminal state guard',recurrence=2,deterministic=True,existing_assets=['orders.cancel'],evidence=['app/check.py'],intervention='test',reason='Executable regression is the smallest intervention',status='recorded',promotion=None)
        record_feedback(self.root,model(self.root),feedback)
        with self.assertRaises(HarnessError):promote(self.root,model(self.root),'FB-1','app/check.py','unknown','ARCHITECTURE.md')
        self.assertEqual('promoted',promote(self.root,model(self.root),'FB-1','app/check.py','fixture-owner','ARCHITECTURE.md')['status'])

    def test_migration_is_dry_by_default_and_backs_up_v0(self):
        self.mutate('project',lambda d:d.update(schema_version=0,baseline_mode=d.pop('mode')))
        before=files(self.root)
        self.assertFalse(migrate(self.root)['applied'])
        self.assertEqual(before,files(self.root))
        report=migrate(self.root,True)
        self.assertTrue(report['applied'])
        self.assertEqual(1,read(self.root/'.harness/project.json')['schema_version'])
        self.assertTrue((self.root/report['backup']/'.harness/project.json').is_file())

    def test_modified_skill_causes_upgrade_conflict(self):
        skill=self.root/'.agents/skills/harness-intake/SKILL.md'
        skill.write_text('Locally modified')
        self.assertIn(skill.relative_to(self.root).as_posix(),migrate(self.root)['conflicts'])
        with self.assertRaises(HarnessError):migrate(self.root,True)

    def test_init_preserves_existing_files_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve()
            (root/'AGENTS.md').write_text('Existing instructions')
            report=init(root,'brownfield','legacy','owner')
            self.assertIn('AGENTS.md',report['preserved'])
            self.assertEqual('Existing instructions',(root/'AGENTS.md').read_text())
            before=files(root)
            init(root,'brownfield','legacy','owner')
            self.assertEqual(before,files(root))
            self.assertTrue(structure_checks(root,model(root)))

    def test_cli_invalid_input_and_required_delivery_fields(self):
        self.assertEqual(2,self.cli('check','--phase','delivery')[0])
        self.mutate('project',lambda d:d.update(schema_version=99))
        self.assertEqual(2,self.cli('doctor')[0])


    def test_unchanged_artifact_is_not_fresh_evidence(self):
        run_dir=self.root/'.harness/runs/direct';run_dir.mkdir(parents=True)
        artifact=run_dir/'old.txt';artifact.write_text('old result')
        cap=model(self.root)['capabilities']['capabilities'][0]
        cap=dict(cap,artifacts=[artifact.relative_to(self.root).as_posix()])
        self.assertEqual('failed',ProcessAdapter().run(self.root,cap,run_dir)['status'])

    def test_verifier_source_mutation_cannot_pass(self):
        self.mutate('capabilities',lambda d:d['capabilities'][0].update(argv=[sys.executable,'-c',"from pathlib import Path; Path('app/orders.py').write_text('changed')"]))
        self.admit()
        path,blockers=verify(self.root,model(self.root),self.task)
        self.assertEqual([],blockers)
        self.assertFalse(read(path)['stable_source'])

    def test_greenfield_unknown_outside_slice_is_reported_by_doctor_only(self):
        self.mutate('knowledge',lambda d:d['documents'][7].update(status='unknown'))
        self.mutate('interfaces',lambda d:d['interfaces'][7].update(readiness=1))
        self.assertIn('knowledge.unknown',self.codes(structure_checks(self.root,model(self.root))))
        self.assertEqual([],preflight(self.root,model(self.root),self.task))

    def test_schema_tampering_does_not_weaken_validator(self):
        (self.root/'.harness/schemas/task.schema.json').write_text('{}')
        self.assertIn('schema.mismatch',self.codes(structure_checks(self.root,model(self.root))))
        with self.assertRaises(HarnessError):validate('task',{})

    def test_new_asset_can_be_registered_and_delivered(self):
        self.task['scope'].append('.harness/assets.json')
        self.task['asset_analysis']['searched_capabilities'].append('order.validate')
        self.task['asset_analysis']['new_assets']=[dict(id='orders.validate',provides=['order.validate'],path='app/validate.py',reason='New distinct validation behavior')]
        self.admit()
        (self.root/'app/validate.py').write_text('def validate(value):\n    return bool(value)\n')
        template=model(self.root)['assets']['assets'][0]
        self.mutate('assets',lambda d:d['assets'].append(dict(template,id='orders.validate',location='app/validate.py',provides=['order.validate'])))
        path,blockers=verify(self.root,model(self.root),self.task)
        self.assertEqual([],blockers)
        self.assertEqual([],delivery(self.root,model(self.root),self.task,read(path),findings(self.root,self.task)))

    def test_asset_cannot_be_deleted_from_catalog_to_hide_reuse(self):
        self.admit()
        self.mutate('assets',lambda d:d.update(assets=[]))
        _,blockers=verify(self.root,model(self.root),self.task)
        self.assertIn('asset.deleted',self.codes(blockers))
