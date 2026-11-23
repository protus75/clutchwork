# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that failure_terminal marks the fence_gap flag only when every Implement premise_failed finding is a fence_gap on a real path outside the scope fence, and that ImplementReply accepts fence_gap but rejects other finding codes.
# relates: [clutch/artifacts.py, clutch/journal.py, clutch/runner.py, clutch/stages.py, tests/unit/test_supervisor_trigger.py]
# owner: engine
# verified: 800fa1a3
# hash: cc8018e0d3a8a7573d7bf840c3b1c2de5ea7b4b5ba65644c1fd9e2c06cefdd52
import pytest
from pydantic import ValidationError

from clutch import runner
from clutch.artifacts import Finding
from clutch.journal import EventType
from clutch.stages import ImplementReply
from tests.unit.test_supervisor_trigger import rig


def finding(code="fence_gap", path="tests/missing.py"):
    return Finding(code=code, path=path, message="forced edit", paved_road="widen fence")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("outcome", "stage", "findings", "expected"),
    [
        ("premise_failed", "implement", [finding(), finding(path="docs/missing.md")], True),
        ("premise_failed", "implement", [finding(), finding(code="premise")], False),
        ("premise_failed", "implement", [finding(path="src/inside.py")], False),
        ("premise_failed", "implement", [finding(path="tickets/other/ticket.md")], False),
        ("premise_failed", "implement", [finding(path=None)], False),
        ("premise_failed", "implement", [finding(path=" ")], False),
        ("gate_failed", "implement", [finding()], False),
        ("premise_failed", "review", [finding()], False),
        ("premise_failed", "implement", [], False),
    ],
)
async def test_marker_requires_only_outside_fence_findings(monkeypatch, outcome, stage, findings, expected):
    ctx, ticket, _, _ = rig(monkeypatch, exists=False)
    ticket.scope_fence = ("src",)
    await runner.failure_terminal(ctx, ticket, outcome=outcome, stage=stage, findings=findings, attempt=0)
    terminal = [e.body for e in ctx.driver.journal.read() if e.type == EventType.STATE_TRANSITION][-1]
    # Wrong: mark every premise failure, or never preserve a valid fence gap.
    assert terminal.get("fence_gap") is True if expected else "fence_gap" not in terminal


def test_reply_accepts_fence_gap_without_accepting_arbitrary_codes():
    reply = dict(outcome="premise_failed", summary="gap", surprises="none", dead_ends="none", predicted_vs_actual="none", findings=[finding()])
    # Wrong: the reply validator rejects the marker before the runner sees it.
    assert ImplementReply.model_validate(reply).findings[0].code == "fence_gap"
    # Wrong: allow unrelated finding codes on Implement premise replies.
    with pytest.raises(ValidationError):
        ImplementReply.model_validate({**reply, "findings": [finding(code="other")]})
