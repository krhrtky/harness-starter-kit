"""Generate action sequences against the real Harness Evidence gate."""
from pathlib import Path
import sys
import tempfile

from hypothesis import settings, strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, precondition, rule, run_state_machine_as_test

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tests'))
from support import configured
from harnessctl.adapters import verify
from harnessctl.gates import evidence_checks, preflight, receipt_for
from harnessctl.model import model
from harnessctl.storage import read


class EvidenceMachine(RuleBasedStateMachine):
    def __init__(self, omit_freshness=False):
        super().__init__()
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.task = configured(self.root)
        assert not preflight(self.root, model(self.root), self.task)
        self.good_source = (self.root/'app/orders.py').read_text()
        self.bundle = None
        self.expected_fresh = False
        self.expected_intact = False
        self.expected_pass = False
        self.edits = 0
        self.omit_freshness = omit_freshness

    @rule(success=st.booleans())
    def run_verification(self, success):
        source = self.good_source if success else "def cancel(state):\n    return 'cancelled'\n"
        (self.root/'app/orders.py').write_text(source)
        path, blockers = verify(self.root, model(self.root), self.task)
        assert not blockers, blockers
        self.bundle = read(path)
        self.expected_pass = success
        self.expected_fresh = True
        self.expected_intact = True

    @rule()
    def edit_source(self):
        self.edits += 1
        path = self.root/'app/orders.py'
        path.write_text(path.read_text()+f'\n# generated edit {self.edits}\n')
        self.expected_fresh = False

    @precondition(lambda self: self.bundle is not None)
    @rule()
    def tamper_log(self):
        path = self.root/self.bundle['records'][0]['log']
        path.write_text(path.read_text()+'\ntampered\n')
        self.expected_intact = False

    @invariant()
    def accepted_exactly_when_current_successful_and_intact(self):
        if self.bundle is None:
            return
        findings = evidence_checks(self.root, model(self.root), self.task, self.bundle, receipt_for(self.root, self.task))
        if self.omit_freshness:
            findings = [finding for finding in findings if finding['code'] != 'evidence.stale']
        expected = self.expected_fresh and self.expected_pass and self.expected_intact
        assert (not findings) == expected, 'evidence acceptance differs from independent state'

    def teardown(self):
        self.temporary.cleanup()


if __name__ == '__main__':
    mutation = '--mutate-freshness' in sys.argv[1:]
    run_state_machine_as_test(lambda: EvidenceMachine(mutation),
        settings=settings(max_examples=25, stateful_step_count=12, deadline=None,
                          derandomize=True, database=None))
    print('Hypothesis stateful Evidence gate checks passed (25 examples, at most 12 steps each).')
