from pathlib import Path
import tempfile
import unittest

from harnessctl.adapters import verify
from harnessctl.checks import structure_checks
from harnessctl.gates import delivery, evidence_checks, preflight, receipt_for
from harnessctl.model import model
from harnessctl.storage import HarnessError, read
from support import FIXTURES, findings, scenario


class FixtureMatrix(unittest.TestCase):
    def test_named_repository_scenarios(self):
        for fixture in sorted(FIXTURES.glob('*/fixture.json')):
            with self.subTest(fixture=fixture.parent.name), tempfile.TemporaryDirectory() as directory:
                root=Path(directory).resolve()
                task,spec=scenario(root,fixture.parent.name)
                if spec['expected']=='invalid':
                    with self.assertRaises(HarnessError):model(root)
                    continue
                data=model(root)
                if task is None:
                    blockers=structure_checks(root,data)
                else:
                    blockers=preflight(root,data,task)
                    if not blockers:
                        if 'outside_change' in spec:(root/spec['outside_change']).write_text('changed')
                        path,blockers=verify(root,data,task)
                        if path:
                            bundle=read(path)
                            blockers=evidence_checks(root,data,task,bundle,receipt_for(root,task))
                            if not blockers:
                                review=findings(root,task)
                                if 'semantic_contradiction' in spec:review['findings'][0]['contradictions']=[spec['semantic_contradiction']]
                                blockers=delivery(root,data,task,bundle,review)
                if spec['expected']=='pass':self.assertEqual([],blockers)
                else:self.assertIn(spec['expected'],{b['code'] for b in blockers})
