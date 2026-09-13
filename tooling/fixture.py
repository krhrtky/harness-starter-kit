"""Materialize a checked-in fixture in a new directory for manual inspection."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from support import scenario
from harnessctl.storage import HarnessError


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('name')
    parser.add_argument('destination',type=Path)
    args=parser.parse_args()
    if args.destination.exists():
        parser.error('destination must not exist')
    args.destination.mkdir(parents=True)
    task,spec=scenario(args.destination.resolve(),args.name)
    print(f'Fixture: {args.name}; expected: {spec["expected"]}')
    if task:print('Task: .harness/tasks/task.json')


if __name__=='__main__':main()
