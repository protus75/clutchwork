# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test runner rework findings terminal
# relates: [clutch/artifacts.py, clutch/journal.py, clutch/runner.py, tests/unit/test_supervisor_trigger.py]
# owner: engine
# verified: 9a610809
# hash: 44fcaa48d53b3018449f6c30834b9558161b367d4d36a45b489df441701183e1
from unittest.mock import AsyncMock

import pytest

from clutch import runner
from clutch.artifacts import Cost, Finding, StageResult
from clutch.journal import EventType
from tests.unit.test_supervisor_trigger import order, rig


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["failed", "ok", "not_requested"])
async def test_rework_findings_on_routed_terminal(monkeypatch, case):
    ctx, ticket, _, _ = rig(monkeypatch)
    monkeypatch.setattr(runner, "harvest", AsyncMock())
    if case == "ok":
        for _ in range(4):
            ctx.driver.journal.append(EventType.STATE_TRANSITION, {"to": "gate_failed"}, ticket=ticket.stem)
    findings = [Finding(code="gap", message="fence gap", paved_road="add path"), Finding(code="seam", message="missing seam", paved_road="add seam")]
    result = StageResult(outcome="ok" if case == "ok" else "gate_failed", artifact=order() if case == "ok" else None, findings=findings, cost=Cost())
    await runner.failure_terminal(ctx, ticket, outcome="gate_failed", stage="review", findings=[], attempt=0, reworked=result, rework_requested=case != "not_requested", verdict="reject")
    terminal = [e.body for e in ctx.driver.journal.read() if e.type == EventType.STATE_TRANSITION][-1]
    if case == "failed":
        # Wrong: discard either message or its paved road.
        assert terminal["rework_findings"] == ["fence gap; add path", "missing seam; add seam"]
    else:
        # Wrong: attach findings from a successful or unrequested rework.
        assert "rework_findings" not in terminal
