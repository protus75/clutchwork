# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the Implement and Diagnose prompt specs tell the agent to commit in-fence work on a fence gap, use the fence_gap code only for files that must change, and keep the retry from redoing that work.
# relates: [clutch/specs/implement.md, clutch/specs/diagnose.md]
# owner: engine
# verified: 800fa1a3
# hash: 7a362d9ea54e1f805c4db45f1ff6d4cf6e8005e25bceb958d6f383e4c6b404cf
from pathlib import Path


def test_fence_gap_prompts():
    specs = Path(__file__).resolve().parents[2] / "clutch/specs"
    implement = (specs / "implement.md").read_text()
    diagnose = (specs / "diagnose.md").read_text()
    # Wrong: discard the in-fence work or label unrelated findings as fence gaps.
    assert "If every finding is a fence gap, first commit the in-fence work in progress, then reply; otherwise commit nothing further." in implement
    assert "Use code `fence_gap` only for a finding naming a file that must change to satisfy the ticket" in implement
    # Wrong: Diagnose instructs the retry to redo work after a fence gap.
    assert "as it does after an Implement `premise_failed` with `fence_gap` true" in diagnose
