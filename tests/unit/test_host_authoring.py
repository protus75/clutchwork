"""Keep critical ticket-writing guidance in the host authoring guide."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Keep critical ticket-writing guidance in the host authoring guide.
# relates: []
# owner: engine
# verified: 0a308920
# hash: f89665f72e7080ee76e1719bbb4fab7f429fb4154a13092132a315086158c25c

from pathlib import Path


def test_critical_authoring_guidance_is_present():
    doc = (Path(__file__).resolve().parents[2] / "clutch/docs/host-authoring.md").read_text()
    for phrase in (
        "has a criterion whose test fails when the invariant is dropped",
        "depends on the ticket that creates it",
        "names every edit the change forces there",
        "reads its fence and criteria",
        "names the one expectation that may change",
        "marked hand-built",
        "before any change that destroys it",
    ):
        assert phrase in doc
