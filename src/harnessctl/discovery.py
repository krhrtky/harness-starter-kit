"""Offline usage and contract discovery from the installed distribution."""
from __future__ import annotations

from . import __version__
from .storage import HarnessError, RESOURCES, SCHEMAS, read

GUIDES = {
    'verification-tools': ('Quint・Apalache・Hypothesisのsetupと実行', 'verification-tools.md'),
    'verification': ('検証の3分類・tool接続と結果契約', 'verification.md'),
    'getting-started': ('ユーザーとAgentの利用開始', 'getting-started.md'),
    'operating-model': ('3ループと責務', 'operating-model.md'),
    'cli': ('CLI操作と実行例', 'cli.md'),
    'agent': ('バイナリからのAgent利用', 'agent-usage.md'),
    'releases': ('GitHubからの取得と配布条件', 'releases.md'),
}


def usage(topic, commands):
    skills = {p.parent.name:p for p in sorted((RESOURCES/'skills').glob('*/SKILL.md'))}
    if topic=='index':
        return dict(ok=True,version=__version__,next_command='harnessctl usage agent',topics=[dict(id=name,description=description) for name,(description,_) in GUIDES.items()]+[dict(id='commands',description='実際のCLI引数をJSONで取得')]+[dict(id=name,description='同梱Skillの全文') for name in skills],exit_codes={'0':'pass','1':'gate blocker','2':'invalid input'},schema_command='harnessctl schema',offline=True)
    if topic=='commands':
        return dict(ok=True,version=__version__,commands=commands)
    if topic in GUIDES:
        path = RESOURCES/'seed/docs/harness'/GUIDES[topic][1]
    elif topic in skills:
        path = skills[topic]
    else:
        raise HarnessError(f'Unknown usage topic: {topic}. Run harnessctl usage for available topics.')
    return dict(ok=True,version=__version__,topic=topic,content=path.read_text(),format='markdown')


def schema(name):
    available = {p.name.removesuffix('.schema.json'):p for p in sorted(SCHEMAS.glob('*.schema.json'))}
    if name is None:
        return dict(ok=True,version=__version__,schemas=sorted(available),next_command='harnessctl schema task')
    if name not in available:
        raise HarnessError(f'Unknown schema: {name}. Run harnessctl schema for available schemas.')
    return dict(ok=True,version=__version__,name=name,schema=read(available[name]))
