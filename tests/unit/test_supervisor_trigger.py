"""Supervisor effects precede the terminal; only successful keeps follow it."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Supervisor effects precede the terminal; only successful keeps follow it.
# relates: [clutch/artifacts.py, clutch/caps.py, clutch/config.py, clutch/daemon.py, clutch/journal.py, clutch/rework.py, clutch/runner.py, clutch/status.py]
# owner: engine
# verified: 9a610809
# hash: 66169352bd5853f7ad37c669c745940021d83fcc3a90438df17c61f6b3bd2e99

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from clutch import daemon, runner
from clutch.artifacts import Cost, Finding, StageResult
from clutch.caps import spent, supervise_draws
from clutch.config import Caps
from clutch.journal import Event, EventType
from clutch.rework import ReworkOrder, ReworkReply, Supervise, TicketProposal
from clutch.status import reject_queue
from tests.unit.test_premise_overruled import MemoryJournal


def event(kind, body, stem="work"):
    return Event(1, kind, "time", stem, None, body)


def order(action="update"):
    return ReworkOrder(
        action=action, tickets=[TicketProposal(stem="work", ticket="proposed ticket\n")] if action == "update" else [], stem="work", attempt=0, produced_by_spec_version=1, produced_at_sha="old-sha"
    )


def rig(monkeypatch, result=None, *, exists=True, history=None, caps=None):
    journal = MemoryJournal(
        history
        if history is not None
        else [
            event(EventType.STATE_TRANSITION, {"to": "running"}),
            event(EventType.SIGNAL, {"signal": "diagnosis", "lessons": ["Fence tests/x.py"]}),
            event(EventType.CAP_CONSUMED, {"cap": "premise_bounce", "ticket_sha": "old-sha"}),
        ]
    )
    workspace = Mock()
    workspace.exists.return_value = exists
    workspace.__truediv__ = lambda self, part: Path("/fake/work") / part
    ctx = SimpleNamespace(
        repo=Path("/fake/repo"),
        config=SimpleNamespace(caps=caps or Caps()),
        worktree=lambda _: workspace,
        git=SimpleNamespace(rev_parse=AsyncMock(return_value="new-sha"), worktree_remove=AsyncMock()),
        fs=SimpleNamespace(write=Mock()),
        driver=SimpleNamespace(journal=journal, redactor=SimpleNamespace(scrub=Mock(side_effect=lambda text: text.replace("SECRET", "[redacted]")))),
    )
    ticket = SimpleNamespace(stem="work", frontmatter=SimpleNamespace(agent_tier="medium", agent_effort="medium"))

    async def apply(*args, **kwargs):
        # Wrong: an effect starts after the run has closed, leaving an orphan intent.
        assert not any(e.type == EventType.STATE_TRANSITION and e.body.get("to") != "running" for e in journal.events[len(journal.events) - 1 :])
        return result or StageResult(outcome="ok", artifact=order(), findings=[], cost=Cost())

    rework = AsyncMock(side_effect=apply)
    lift = AsyncMock()
    monkeypatch.setattr(daemon, "apply_rework", rework)
    monkeypatch.setattr(runner, "lift_outbox", lift)
    return ctx, ticket, rework, lift


async def finish(ctx, ticket, **kwargs):
    args = dict(outcome="premise_failed", stage="implement", findings=[], attempt=0, verdict="abandon-human", supervised=True)
    args.update(kwargs)
    return await runner.failure_terminal(ctx, ticket, **args)


@pytest.mark.asyncio
async def test_keep_follows_the_terminal(monkeypatch):
    ctx, ticket, rework, lift = rig(monkeypatch)
    assert await finish(ctx, ticket) == "premise_failed"  # Wrong: replace producing outcome with Rework's ok.
    assert rework.call_args.kwargs == {"attempt": 0, "supervise": Supervise("premise_bounce cap spent", ("Fence tests/x.py",))}  # Wrong: lose lessons or use the outcome as the trigger.
    events = ctx.driver.journal.read()
    terminal, draw, keep = events[-3:]
    assert terminal.type == EventType.STATE_TRANSITION and terminal.body["to"] == "premise_failed" and terminal.body["routed"] == "reject_queue"
    assert draw.type == EventType.CAP_CONSUMED and draw.body == {"cap": "supervise", "ticket_sha": "new-sha"}  # Wrong: keep without drawing, or use the old blob.
    assert keep.type == EventType.SIGNAL and keep.body == {"signal": "reject_verdict", "verdict": "keep", "actor": "supervisor", "ticket_sha": "new-sha"}
    assert "work" not in reject_queue(events) and spent(Caps(), events, "work") is None  # Wrong: keep before terminal or machine keep fails to reset lineage.
    ctx.git.rev_parse.assert_awaited_once_with(ctx.repo, "HEAD:tickets/work/ticket.md")
    lift.assert_not_called()  # Wrong: lift an approved edit as a refusal.


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["update", "escalate", "none"])
async def test_refusal_lifts_rework_md_before_the_terminal(monkeypatch, action):
    proposal = TicketProposal(stem="work", ticket="proposed SECRET goal\n")
    finding = Finding(code="supervise_edit", message="changed SECRET goal", paved_road="restore original goal")
    result = StageResult(
        outcome="gate_failed" if action != "escalate" else "ok",
        artifact=ReworkReply(action="update", tickets=[proposal]) if action == "update" else order("escalate") if action == "escalate" else None,
        findings=[finding] if action == "update" else [],
        cost=Cost(),
    )
    ctx, ticket, rework, lift = rig(monkeypatch, result)

    async def lifted(*args, **kwargs):
        # Wrong: proposal lift is after the terminal, risking a second terminal on recovery.
        assert not any(e.type == EventType.STATE_TRANSITION and e.body.get("to") != "running" for e in ctx.driver.journal.events)
        ctx.fs.write.assert_called_once()

    lift.side_effect = lifted
    await finish(ctx, ticket)
    path, content = ctx.fs.write.call_args.args
    assert path == Path("/fake/work/tickets/work/rework.md")  # Wrong: write to the canonical checkout instead of the outbox.
    text = content.decode()
    assert f"- trigger: premise_bounce cap spent\n- outcome: {result.outcome}\n- action: {action}" in text
    if action == "update":
        assert "- `supervise_edit`: changed [redacted] goal -- restore original goal" in text
        assert "````markdown\nproposed [redacted] goal\n````" in text  # Wrong: omit refused proposal or leak its secret.
    else:
        assert "## Findings\n\n- none" in text and "## Proposed ticket" not in text
    ctx.driver.redactor.scrub.assert_called_once()
    lift.assert_awaited_once_with(ctx, "work", "rework-proposal", attempt=0, only="rework.md")
    events = ctx.driver.journal.read()
    assert supervise_draws(events, "work") == 0 and not any(e.body.get("signal") == "reject_verdict" for e in events)  # Wrong: keep a refused or escalated edit.
    assert "work" in reject_queue(events)


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["disabled", "changed", "rework", "infra", "uncapped", "missing", "spent", "timeout", "invalid_artifact", "incomplete", "abandoned", "drought"])
async def test_supervisor_skips(monkeypatch, case):
    ctx, ticket, rework, lift = rig(monkeypatch, exists=case != "missing")
    kwargs = {}
    if case == "disabled":
        kwargs["supervised"] = False
    elif case == "changed":
        kwargs["findings"] = [Finding(code="ticket_changed", message="edited", paved_road="confirm")]
    elif case == "rework":
        kwargs["rework_requested"] = True
    elif case in {"infra", "timeout", "invalid_artifact", "incomplete", "abandoned"}:
        kwargs["outcome"] = "infra_error" if case == "infra" else case
        for _ in range(ctx.config.caps.infra):
            ctx.driver.journal.append(EventType.CAP_CONSUMED, {"cap": "infra", "ticket_sha": "old-sha"}, ticket="work")
    elif case == "uncapped":
        ctx.driver.journal.events = [event(EventType.STATE_TRANSITION, {"to": "running"})]
        kwargs.update(outcome="gate_failed", verdict="reject")
    elif case == "spent":
        for _ in range(2):
            ctx.driver.journal.append(EventType.CAP_CONSUMED, {"cap": "supervise", "ticket_sha": "old-sha"}, ticket="work")
    elif case == "drought":
        kwargs["provider_drought"] = {"provider": "offline"}
    await finish(ctx, ticket, **kwargs)
    rework.assert_not_called()  # Wrong: supervise the excluded route; each other guard still permits it.
    lift.assert_not_called()
    ctx.fs.write.assert_not_called()
    assert not any(e.body.get("actor") == "supervisor" for e in ctx.driver.journal.events)


@pytest.mark.asyncio
async def test_pending_attempt_cap_triggers(monkeypatch):
    history = [event(EventType.STATE_TRANSITION, {"to": "gate_failed"}) for _ in range(4)]
    history.append(event(EventType.STATE_TRANSITION, {"to": "running"}))
    ctx, ticket, rework, _ = rig(monkeypatch, history=history)
    await finish(ctx, ticket, outcome="gate_failed")
    assert rework.await_count == 1 and rework.call_args.kwargs["supervise"] == Supervise("attempts cap spent", ())  # Wrong: omit the pending fifth failure from spent().


@pytest.mark.asyncio
async def test_lessons_are_unique_and_lineage_scoped(monkeypatch):
    history = [
        event(EventType.SIGNAL, {"signal": "diagnosis", "lessons": ["stale"]}),
        event(EventType.SIGNAL, {"signal": "reject_verdict", "verdict": "keep", "actor": "supervisor"}),
        event(EventType.STATE_TRANSITION, {"to": "running"}),
        event(EventType.SIGNAL, {"signal": "diagnosis", "lessons": ["wrong stem"]}, "other"),
        event(EventType.SIGNAL, {"signal": "diagnosis", "lessons": ["zeta", "alpha", "zeta"]}),
        event(EventType.SIGNAL, {"signal": "diagnosis", "lessons": ["alpha", "middle"]}),
    ]
    ctx, ticket, rework, _ = rig(monkeypatch, history=history)
    await finish(ctx, ticket)
    assert rework.call_args.kwargs["supervise"] == Supervise("premise_failed", ("zeta", "alpha", "middle"))  # Wrong: include prior lineage/other stems, repeat or sort lessons.
