# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test author slice follow up
# relates: [clutch/author.py]
# owner: clutch/author.py
# verified: 0a308920
# hash: 901d639002e2a566767c1339ce3def7705d406b2eb3f71bfb41d2fda853ff592
from types import SimpleNamespace

import pytest

from clutch import author


@pytest.mark.parametrize("goal", ["Roadmap row 128, first slice: surfaces.", "First SLICE: surfaces."])
def test_slice_requires_roadmap_fence(goal):
    findings = author.slice_follow_up(object(), goal, ("clutch/author.py",))
    assert len(findings) == 1
    assert "docs/roadmap.md" in findings[0].paved_road
    assert author.slice_follow_up(object(), goal, ("clutch/author.py", "docs/roadmap.md")) == []


@pytest.mark.parametrize("goal", ["Roadmap row 128: one owner for surfaces.", "part of the row", "slices of work"])
def test_non_slice_goal_needs_no_fence(goal):
    assert author.slice_follow_up(object(), goal, ("clutch/author.py",)) == []


def test_non_roadmap_request_needs_no_fence():
    assert author.slice_follow_up(None, "first slice", ("clutch/author.py",)) == []


def test_gate_checks_parsed_goal_and_fence(tmp_path, monkeypatch):
    row = SimpleNamespace(stem="sample-row", kind="feature", priority="P1")
    gate = author.AuthorGate(SimpleNamespace(repo=tmp_path, journal=SimpleNamespace(read=lambda: [])))
    gate.message = SimpleNamespace(roadmap_row=row, report=None)
    parsed = SimpleNamespace(frontmatter=SimpleNamespace(kind="feature", priority="P1"), sections={"Goal / Why": "first slice"}, scope_fence=("clutch/author.py",))
    monkeypatch.setattr(author, "validate_ticket", lambda *args: parsed)
    reply = author.AuthorReply(stem="sample-row", ticket="## Goal / Why\nfirst slice")
    report = gate.check(reply, tmp_path)
    assert report.verdict == "fail"
    assert len(report.findings) == 1
    parsed.scope_fence = ("docs/roadmap.md",)
    assert gate.check(reply, tmp_path).verdict == "pass"
