# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test requisition review whole value closure
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 96e46658
# hash: af321548e290dcd50af283b440cff2cee2722b96cb9b93bfbe1cab7121c08df1
from pathlib import Path

from clutch.specs import load_spec


def test_whole_value_closure_and_dependent_citation():
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/requisition_review.md").read_text()
    body = load_spec(text).body
    # Each phrase rules out omitting render changes, equality comparisons, or the limit.
    for phrase in (
        "changes text a render function emits",
        "whole-value comparisons",
        "only whole-value equality is a hit",
    ):
        assert phrase in body
    dependents = next(line for line in body.splitlines() if line.startswith("- Account for every listed dependent"))
    # Both citation requirements must apply to dependents, not another rule.
    assert "must cite the asserting" in dependents
    assert "file:line" in dependents
