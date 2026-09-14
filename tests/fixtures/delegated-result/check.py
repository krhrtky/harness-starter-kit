from pathlib import Path
import subprocess
import sys

output = Path('.harness/runs/delegated-result.json')
output.parent.mkdir(parents=True, exist_ok=True)
output.unlink(missing_ok=True)
produced = subprocess.run([sys.executable, 'app/delegated/producer.py', sys.argv[1]], check=False)
if produced.returncode != 0:
    raise SystemExit(produced.returncode)
checked = subprocess.run([sys.executable, '-m', 'harnessctl', 'result', 'validate',
                          '--schema', 'app/delegated/accepted.schema.json',
                          '--input', output.as_posix()], check=False)
raise SystemExit(checked.returncode)
