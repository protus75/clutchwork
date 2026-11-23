# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the Implement and Diagnose specs state that Check or Review retries start from the rebased failed branch and other retries start from main
# relates: [clutch/specs/implement.md, clutch/specs/diagnose.md]
# owner: engine
# verified: 800fa1a3
# hash: 9b7e172bad6d7d93787135da3f6f3b87f94128030670093fff39cf8dc3089e9a
from pathlib import Path


def test_retry_starting_points():
    root = Path(__file__).resolve().parents[2] / "clutch/specs"
    implement = (root / "implement.md").read_text()
    diagnose = (root / "diagnose.md").read_text()
    assert "keep what the retry findings do not contradict and change only what they name, without redoing the change" in implement
    assert "After a Check or Review failure the next attempt starts from the failed branch rebased onto main" in diagnose
    assert "after any other Implement failure or a merge conflict it starts from main, so lessons restate the work" in diagnose
    assert "no earlier diff survives" not in diagnose
