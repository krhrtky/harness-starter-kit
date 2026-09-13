"""Create a native archive, usage entrypoint, licenses and checksum."""
import argparse
import hashlib
from importlib.metadata import distribution
from pathlib import Path
import platform
import shutil
import sysconfig
import tarfile
import tempfile

from harnessctl import __version__

START = '''# Harness Starter Kit — Start here

Pythonのインストールは不要です。展開したharnessctlを実行してください。
このarchiveはファイル名に示すOS/CPU専用です。

```sh
./harnessctl --version
./harnessctl --help
./harnessctl usage
./harnessctl usage agent
./harnessctl usage commands
./harnessctl schema task
./harnessctl usage harness-bootstrap
```

usage/schemaはネットワーク・ソースコード・repository初期化なしで取得できます。
JSONのcontentに手順全文が返ります。Agentにはまず「harnessctl usage agentを読んで進めて」と伝えてください。

```sh
./harnessctl --root /path/to/repo init --owner team-name --mode brownfield
./harnessctl --root /path/to/repo doctor
```

新規projectはgreenfield。init直後のUNKNOWNはproject固有の未設定項目です。
initで展開されるAGENTS.md、docs、Skillsからも手順を辿れます。既存AGENTSは上書きせずpreservedになります。
日常利用ではharnessctlをPATHに置くか、絶対pathを指定します。
対象projectのbuild/test runtimeは別途必要です。HarnessのPython runtimeとは独立しています。
macOS版はad-hoc署名で、Developer ID署名・notarizationは未実施です。
サードパーティのlicenseはlicenses/を参照してください。
'''


def package(binary, output):
    system={'Darwin':'macos','Linux':'linux'}.get(platform.system())
    arch={'aarch64':'arm64','arm64':'arm64','x86_64':'x86_64'}.get(platform.machine())
    if system is None or arch is None:
        raise ValueError('Unsupported release platform')
    name=f'harnessctl-v{__version__}-{system}-{arch}'
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)/name;root.mkdir()
        shutil.copy2(binary,root/'harnessctl')
        (root/'START-HERE.md').write_text(START)
        licenses=root/'licenses';licenses.mkdir()
        python_license=Path(sysconfig.get_path('stdlib'))/'LICENSE.txt'
        shutil.copy2(python_license,licenses/'Python-LICENSE.txt')
        for dependency in ['jsonschema','jsonschema-specifications','referencing','rpds-py','attrs','typing_extensions','pyinstaller']:
            dist=distribution(dependency)
            matches=[f for f in dist.files or [] if '/licenses/' in str(f)]
            if not matches:
                raise ValueError(f'Missing license files: {dependency}')
            for i,relative in enumerate(matches):
                shutil.copy2(dist.locate_file(relative),licenses/f'{dependency}-{i}-{Path(relative).name}')
        archive=output/f'{name}.tar.gz'
        with tarfile.open(archive,'w:gz') as target:
            target.add(root,arcname=name)
    checksum=hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_name(archive.name+'.sha256').write_text(f'{checksum}  {archive.name}\n')
    print(archive)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('binary',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    package(args.binary.resolve(),args.output.resolve())
