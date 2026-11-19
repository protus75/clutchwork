import pytest

from clutch import runner
from clutch.artifacts import Cost, Finding, StageResult
from clutch.journal import EventType
from tests.integration.test_daemon_composition import production_writer
from tests.integration.test_mergequeue import ctx as admission_context
from tests.integration.test_mergequeue import ready
from tests.unit.test_supervisor_trigger import order


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
