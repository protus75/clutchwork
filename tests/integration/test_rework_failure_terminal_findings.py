# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that a failure terminal journals rework_findings, each with its paved road, only when a requested non-mechanical Rework fails and the ticket goes to the reject queue
# relates: [clutch/artifacts.py, clutch/journal.py, clutch/runner.py, tests/integration/test_daemon_composition.py, tests/integration/test_mergequeue.py]
# owner: clutch/runner.py
# verified: 92889fdb
# hash: 0e1dfd633cd5e9d87931a4ec539370c39224565a958e733f75ac7b0e4a30df24
import pytest

from clutch import runner
from clutch.artifacts import Cost, Finding, StageResult
from clutch.journal import EventType
from tests.daemon_helpers import ctx as admission_context
from tests.daemon_helpers import production_writer, ready
from tests.unit.test_supervisor_trigger import order

pytestmark = pytest.mark.disk_io_skip


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["failed", "ok", "not_requested", "mechanical"])
async def test_journaled_rework_findings(admission_context, case):
    _, writer = production_writer(admission_context, [])
    ctx = writer.ctx
    ticket = await ready(ctx)
    if case == "ok":
        for _ in range(4):
            ctx.driver.journal.append(EventType.STATE_TRANSITION, {"to": "gate_failed"}, ticket=ticket.stem)
    findings = [Finding(code="gap", message="fence gap", paved_road="add path"), Finding(code="seam", message="missing seam", paved_road="add seam")]
    result = StageResult(outcome="ok" if case == "ok" else "gate_failed", artifact=order() if case == "ok" else None, findings=findings, cost=Cost())
    await runner.failure_terminal(
        ctx,
        ticket,
        outcome="gate_failed",
        stage="review",
        findings=[Finding(code="render_over_bound", message="too large", paved_road="shrink")] if case == "mechanical" else [],
        attempt=0,
        reworked=result,
        rework_requested=case != "not_requested",
        mechanical=case == "mechanical",
        verdict="reject",
    )
    terminal = [e.body for e in ctx.driver.journal.read() if e.type == EventType.STATE_TRANSITION][-1]
    if case == "failed":
        # Wrong: journal only the original failure or omit a paved road.
        assert terminal["rework_findings"] == ["fence gap; add path", "missing seam; add seam"]
        assert terminal["routed"] == "reject_queue"  # Wrong: attach the messages to an unrouted terminal.
    else:
        # Wrong: add the field for successful, unrequested, or mechanical rework.
        assert "rework_findings" not in terminal
