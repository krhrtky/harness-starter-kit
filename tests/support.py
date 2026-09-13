from pathlib import Path
import shutil
import sys

from harnessctl.bootstrap import init
from harnessctl.storage import digest, files, now, read, write

FIXTURES = Path(__file__).parent/'fixtures'


def configured(root,mode='greenfield'):
    init(root,mode,'fixture','fixture-owner')
    shutil.copytree(FIXTURES/'valid-small-app'/'app',root/'app')
    (root/'ARCHITECTURE.md').write_text('# Fixture architecture\n\nSingle orders module; application dependencies stay inside app/.\n')
    knowledge = read(root/'.harness/knowledge.json')
    for doc in knowledge['documents']:
        path = root/doc['path']
        path.write_text(f'# {doc["id"]}\n\nThis fixture tests Harness gates for an in-memory order state transition.\nOwner: fixture-owner. External production concerns are not applicable to this test fixture.\n')
    knowledge['documents'] = [dict(d,status='documented',content_digest=digest((root/d['path']).read_bytes()),reviewed_at=now()) for d in knowledge['documents']]
    write(root/'.harness/knowledge.json',knowledge)
    interfaces = read(root/'.harness/interfaces.json')
    interfaces['interfaces'] = [dict(i,readiness=3) for i in interfaces['interfaces']]
    write(root/'.harness/interfaces.json',interfaces)
    write(root/'.harness/evolution.json',dict(schema_version=1,current='Single module',target='Single module with explicit order invariants',transition=[]))
    write(root/'.harness/capabilities.json',dict(schema_version=1,capabilities=[dict(id='test.unit',adapter='process',argv=[sys.executable,'app/check.py'],cwd='.',timeout_seconds=5,enabled=True,env={},artifacts=[])]))
    write(root/'.harness/quality.json',dict(schema_version=1,scores=[dict(scope='app/**',dimension='correctness',score=80,basis='Three order state invariants are executable',evidence=['app/check.py'])]))
    write(root/'.harness/assets.json',dict(schema_version=1,assets=[dict(id='orders.cancel',type='code',purpose='Cancel orders with shipped-state protection',scope=['app/**'],status='standard',owner='fixture-owner',location='app/orders.py',provides=['order.cancel'],version='1',consumers=['orders-ui'],evidence=['app/check.py'],deprecated_by=None,constraints=[])]))
    task = dict(schema_version=1,id='TASK-1',outcome='Keep cancellation idempotent and reject shipped orders',non_goals=['Cross-domain redesign'],acceptance=[dict(id='AC-1',statement='Shipped orders cannot be cancelled',capabilities=['test.unit'])],risk=dict(level='low',reasons=['In-memory fixture only']),affected_interfaces=['H00','H01','H02','H09','H17','H18','H20','H26'],scope=['app/**'],constraints=['Do not remove shipped guard'],required_capabilities=['test.unit'],unknowns=[],asset_analysis=dict(searched_capabilities=['order.cancel'],reused=['orders.cancel'],extended=[],new_assets=[],duplicates_considered=[dict(asset='orders.cancel',decision='reuse',reason='Same order lifecycle semantics')],consolidation_opportunities=[]),placement=[dict(path='app/**',reason='Order domain code',target_alignment='Single order module')],cross_system_impact=dict(consumers=['orders-ui'],reason='Order UI consumes this function'),reviewer='fixture-reviewer')
    write(root/'.harness/tasks/task.json',task)
    return task


def findings(root,task):
    return dict(schema_version=1,findings=[dict(schema_version=1,id=f'{criterion}-{view}',task=task['id'],criterion=criterion,view=view,interface='H09',severity='info',claim='The fixture invariants are supported by executable tests',premises=['Shipped is terminal'],evidence=['app/check.py'],counterexamples_considered=['Repeated cancellation and shipped state'],conclusion='pass',confidence='high',contradictions=[],unsupported_assumptions=[],reviewer=task['reviewer'],source_digest=digest(files(root))) for criterion in ['AC-1','global-impact'] for view in ['entailment','contradiction','counterexample']])


def scenario(root,name):
    spec=read(FIXTURES/name/'fixture.json')
    if spec.get('empty'):
        init(root,'greenfield','empty','fixture-owner')
        return None,spec
    task=configured(root,spec.get('mode','greenfield'))
    for relative in spec.get('delete',[]):
        (root/relative).unlink()
    for relative,content in spec.get('write',{}).items():
        path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
    for patch in spec.get('patches',[]):
        path=root/f'.harness/{patch["file"]}.json'
        data=read(path);node=data
        for part in patch['path'][:-1]:node=node[part]
        node[patch['path'][-1]]=patch['value'];write(path,data)
    if spec.get('baseline'):
        from harnessctl.evolution import baseline
        from harnessctl.model import model
        baseline(root,model(root))
    return task,spec
