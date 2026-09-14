import json
from pathlib import Path
import sys

case = sys.argv[1]
output = Path('.harness/runs/delegated-result.json')
value = dict(schema_version=1, subject='fixture-v1', decision='PASS')
if case == 'logical-fail':
    value['decision'] = 'FAIL'
elif case == 'unknown':
    value['decision'] = 'UNKNOWN'
elif case == 'wrong-subject':
    value['subject'] = 'another-fixture'
elif case == 'unknown-version':
    value['schema_version'] = 99
if case == 'missing':
    raise SystemExit(0)
output.write_text('{broken' if case == 'invalid-json' else json.dumps(value))
raise SystemExit(7 if case == 'producer-failed' else 0)
