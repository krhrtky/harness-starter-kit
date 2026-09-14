"""Exercise only the copied executable with no Python or Git on child PATH."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from support import configured, findings
from harnessctl.storage import read, write


def smoke(binary):
    with tempfile.TemporaryDirectory() as temp:
        base=Path(temp).resolve()
        executable=base/'harnessctl'
        shutil.copy2(binary,executable)
        root=base/'project';root.mkdir()
        empty=base/'empty-path';empty.mkdir()
        environment={**os.environ,'PATH':str(empty),'PYTHONPATH':str(empty),'PYTHONHOME':str(empty)}
        def run(*args,expected=0):
            process=subprocess.run([str(executable),'--root',str(root),*args],cwd=base,env=environment,capture_output=True,text=True,timeout=60)
            if process.returncode!=expected:
                raise RuntimeError(f'{args}: exit {process.returncode}\n{process.stdout}\n{process.stderr}')
            return json.loads(process.stdout)
        index=run('usage')
        skill_topics={topic['id'] for topic in index['topics'] if topic['id'].startswith('harness-')}
        if 'harness-document' not in skill_topics:
            raise RuntimeError('Document Skill is not discoverable')
        for topic in index['topics']:run('usage',topic['id'])
        for name in run('schema')['schemas']:run('schema',name)
        write(root/'accepted.schema.json',{'$schema':'https://json-schema.org/draft/2020-12/schema','type':'object','properties':{'status':{'const':'PASS'}},'required':['status']})
        write(root/'result.json',{'status':'PASS'})
        run('result','validate','--schema','accepted.schema.json','--input','result.json')
        write(root/'result.json',{'status':'FAIL'})
        run('result','validate','--schema','accepted.schema.json','--input','result.json',expected=1)
        (root/'result.json').write_text('{invalid')
        run('result','validate','--schema','accepted.schema.json','--input','result.json',expected=2)
        run('init','--owner','fixture-owner')
        run('doctor',expected=1)
        installed_skills={path.parent.name for path in (root/'.agents/skills').glob('*/SKILL.md')}
        if installed_skills != skill_topics:
            raise RuntimeError('Discovered and installed Skills differ')
        for name in skill_topics:
            if (root/'.agents/skills'/name/'SKILL.md').read_text()!=run('usage',name)['content']:
                raise RuntimeError(f'Installed Skill differs from embedded usage: {name}')
        task=configured(root)
        capabilities=read(root/'.harness/capabilities.json')
        capabilities['capabilities'][0]['argv']=['/bin/sh','-c','test -f app/orders.py']
        write(root/'.harness/capabilities.json',capabilities)
        run('doctor')
        run('preflight','--task','.harness/tasks/task.json')
        result=run('verify','--task','.harness/tasks/task.json')
        review='.harness/runs/TASK-1/review.json'
        write(root/review,findings(root,task))
        run('check','--phase','delivery','--task','.harness/tasks/task.json','--bundle',result['bundle'],'--findings',review)
        print(json.dumps(dict(ok=True,topics=len(index['topics']),schemas=len(run('schema')['schemas']),skills=len(installed_skills),external_python=False,external_git=False,delivery='passed')))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('binary',type=Path)
    smoke(parser.parse_args().binary.resolve())
