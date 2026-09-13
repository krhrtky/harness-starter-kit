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
        for topic in index['topics']:run('usage',topic['id'])
        for name in run('schema')['schemas']:run('schema',name)
        run('init','--owner','fixture-owner')
        run('doctor',expected=1)
        if len(list((root/'.agents/skills').glob('*/SKILL.md')))!=10:
            raise RuntimeError('Bundled Skills missing')
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
        print(json.dumps(dict(ok=True,topics=len(index['topics']),schemas=len(run('schema')['schemas']),skills=10,external_python=False,external_git=False,delivery='passed')))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('binary',type=Path)
    smoke(parser.parse_args().binary.resolve())
