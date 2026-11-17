"""Both terminal producers share supervisor attempts and the operator-lineage bound."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import daemon, runner
from clutch.artifacts import Cost, Finding, StageResult
from clutch.config import Caps
from clutch.journal import EventType
from clutch.rework import ReworkReply
from clutch.stages import StagesRun
from tests.unit.test_supervisor_trigger import event, order, rig


async def produce(monkeypatch, ctx, ticket, route, outcome="gate_failed", findings=()):
    result = StageResult(outcome=outcome, artifact=None, findings=list(findings), cost=Cost())
    monkeypatch.setattr(runner, "harvest_failure", AsyncMock())
    if route == "merge":
        writer = daemon.TicketWriter(ctx, SimpleNamespace())
        await writer.consume_result(ticket, result, attempt=4)
    else:
        run = StagesRun(attempt=4, results={"implement": result}, ticket_sha="old-sha")
        ctx.boundary = SimpleNamespace(run=run, next_stage=None)
        monkeypatch.setattr(runner, "run_stages", AsyncMock(return_value=run))
        monkeypatch.setattr(runner, "ticket_change_findings", AsyncMock(return_value=[]))
        await runner.drive(ctx, ticket)


def spent_history():
    # Four prior failures plus this failure hit the attempts cap, without Diagnosis.
    return [event(EventType.STATE_TRANSITION, {"to": "gate_failed"}) for _ in range(4)] + [event(EventType.STATE_TRANSITION, {"to": "running"})]


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["drive", "merge"])
@pytest.mark.parametrize("reply", ["approve", "refuse", "escalate"])
@pytest.mark.parametrize("outcome", ["gate_failed", "premise_failed"])
async def test_attempt_signal_merge_route(monkeypatch, route, reply, outcome):
    proposal = order() if reply == "approve" else order("escalate") if reply == "escalate" else ReworkReply(action="update", tickets=order().tickets)
    result = StageResult(outcome="gate_failed" if reply == "refuse" else "ok", artifact=proposal, findings=[], cost=Cost())
    ctx, ticket, rework, _ = rig(monkeypatch, result, history=spent_history())

    async def apply(*args, **kwargs):
        # Wrong: append after Rework, omit the attempt, duplicate it, or name another stem.
        signals = [e for e in ctx.driver.journal.read() if e.body.get("signal") == "supervisor_attempt"]
        assert [(e.ticket, e.body) for e in signals] == [("work", {"signal": "supervisor_attempt", "stem": "work"})]
        return result

    rework.side_effect = apply
    await produce(monkeypatch, ctx, ticket, route, outcome)
    # Wrong: leave merge delivery unsupervised.
    rework.assert_awaited_once()
    events = ctx.driver.journal.read()
    # Wrong: emit another signal after the attempted call.
    assert [(e.ticket, e.body) for e in events if e.body.get("signal") == "supervisor_attempt"] == [("work", {"signal": "supervisor_attempt", "stem": "work"})]
    # Wrong: omit the approved keep, keep a refused proposal, or attribute it to the operator.
    assert [e.body for e in events if e.body.get("signal") == "reject_verdict"] == (
        [{"signal": "reject_verdict", "verdict": "keep", "actor": "supervisor", "ticket_sha": "new-sha"}] if reply == "approve" else []
    )


@pytest.mark.asyncio
async def test_cap_spent_merge_route(monkeypatch):
    history = []
    for n in range(2):
        history.extend(
            [
                event(EventType.CAP_CONSUMED, {"cap": "supervise", "ticket_sha": f"sha-{n}"}),
                event(EventType.SIGNAL, {"signal": "reject_verdict", "verdict": "keep", "actor": "supervisor", "ticket_sha": f"sha-{n}"}),
            ]
        )
    history.extend(spent_history())
    ctx, ticket, rework, _ = rig(monkeypatch, history=history, caps=Caps(supervise=2))
    await produce(monkeypatch, ctx, ticket, "merge")
    # Wrong: supervisor keeps reset their own bound, or equality permits a third attempt.
    rework.assert_not_awaited()
    assert [e.body for e in ctx.driver.journal.read() if e.body.get("signal") in {"supervisor_attempt", "reject_verdict"}] == [e.body for e in history if e.body.get("signal") == "reject_verdict"]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["ticket_changed", "abandoned"])
async def test_merge_route_exclusions(monkeypatch, case):
    history = [*spent_history(), event(EventType.CAP_CONSUMED, {"cap": "premise_bounce", "ticket_sha": "old-sha"})]
    ctx, ticket, rework, _ = rig(monkeypatch, history=history)
    findings = [Finding(code="ticket_changed", message="edited", paved_road="confirm")] if case == "ticket_changed" else []
    if case == "abandoned":
        await runner.failure_terminal(ctx, ticket, outcome="abandoned", stage="merge", findings=[], attempt=4, supervised=True)
    else:
        await produce(monkeypatch, ctx, ticket, "merge", findings=findings)
    # Wrong: enabling merge supervision bypasses the shared exclusions.
    rework.assert_not_awaited()
    assert not any(e.body.get("signal") == "supervisor_attempt" for e in ctx.driver.journal.read())
