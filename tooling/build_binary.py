"""Build the host-native standalone binary with all discovery resources."""
import argparse
from pathlib import Path
import platform
import subprocess
import sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    args=parser.parse_args()
    if platform.system() not in {'Darwin','Linux'}:
        parser.error('This release supports macOS and Linux only')
    root=Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True,exist_ok=True)
    args.work.mkdir(parents=True,exist_ok=True)
    command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--name','harnessctl','--distpath',str(args.output.resolve()),'--workpath',str(args.work.resolve()/'build'),'--specpath',str(args.work.resolve()),'--paths',str(root/'src'),'--collect-data','harnessctl','--collect-data','jsonschema_specifications',str(root/'tooling/binary_entry.py')]
    return subprocess.run(command,cwd=root,check=False).returncode


if __name__=='__main__':raise SystemExit(main())
