"""Idle supervision selects operator lineages without producing another terminal."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Idle supervision selects operator lineages without producing another terminal.
# relates: [clutch/artifacts.py, clutch/config.py, clutch/daemon.py, clutch/journal.py, clutch/rework.py, clutch/runner.py, clutch/supervise_idle.py]
# owner: engine
# verified: 11213934
# hash: 670ed0ba803e05e65dcfb9ab2953d3407741938736dc2f74f8b1b8f1ad02907b

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, call

import pytest

from clutch import daemon, runner
from clutch import supervise_idle as idle
from clutch.artifacts import Cost, StageResult
from clutch.config import Caps
from clutch.journal import Event, EventType
from clutch.rework import ReworkOrder, ReworkReply, Supervise


class Journal:
    def __init__(self, events=()):
        self.events = list(events)

    def read(self):
        return list(self.events)

    def append(self, kind, body, *, ticket, key=None):
        self.events.append(Event(len(self.events), kind, "time", ticket, key, body))


def event(kind, body, stem="work"):
    return Event(1, kind, "time", stem, None, body)


def arrival(**changes):
    return [event(EventType.STATE_TRANSITION, {"to": "premise_failed", "reason": "bad_path", **changes}), event(EventType.SIGNAL, {"signal": "reject_arrival"})]


def rig(tmp_path, monkeypatch, *, history=None, reply="approve"):
    journal = Journal(arrival() if history is None else history)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    git = Mock()
    git.worktree_add_detached = AsyncMock()
    git.worktree_remove = AsyncMock()
    git.worktree_prune = AsyncMock()
    git.rev_parse = AsyncMock(return_value="new-blob")
    ctx = SimpleNamespace(
        repo=tmp_path,
        config=SimpleNamespace(caps=Caps()),
        git=git,
        worktree=lambda _: workspace,
        fs=SimpleNamespace(read_bytes=Mock(return_value=b"ticket"), write=Mock()),
        driver=SimpleNamespace(journal=journal, redactor=SimpleNamespace(scrub=lambda text: text)),
    )
    ticket = SimpleNamespace(stem="work", frontmatter=SimpleNamespace(agent_tier="medium", agent_effort="medium"))
    checkout = SimpleNamespace(repo=tmp_path, config=ctx.config, journal=journal)
    monkeypatch.setattr(idle, "parse_ticket", Mock(return_value=ticket))
    proposal = ReworkOrder(
        action="update" if reply == "approve" else "escalate",
        tickets=[{"stem": "work", "ticket": "new"}] if reply == "approve" else [],
        stem="work",
        attempt=0,
        produced_by_spec_version=1,
        produced_at_sha="old",
    )
    result = StageResult(outcome="gate_failed" if reply == "refuse" else "ok", artifact=ReworkReply(action="escalate", tickets=[]) if reply == "refuse" else proposal, cost=Cost(), findings=[])
    apply = AsyncMock(return_value=result)
    monkeypatch.setattr(daemon, "apply_rework", apply)
    monkeypatch.setattr(runner, "lift_outbox", AsyncMock())
    return checkout, ctx, ticket, apply


@pytest.mark.asyncio
@pytest.mark.parametrize("reply", ["approve", "refuse", "escalate"])
async def test_once_without_terminal_and_cleanup(tmp_path, monkeypatch, reply):
    c, ctx, ticket, apply = rig(tmp_path, monkeypatch, reply=reply)
    make = AsyncMock(return_value=ctx)
    before = [e for e in c.journal.read() if e.type == EventType.STATE_TRANSITION]
    await idle.supervise_idle(c, make)
    await idle.supervise_idle(c, make)
    # Wrong: require routed, repeat a refused attempt, or prepare on empty polls.
    assert apply.await_count == make.await_count == 1
    # Wrong: manufacture a new terminal for any supervisor result.
    assert [e for e in c.journal.read() if e.type == EventType.STATE_TRANSITION] == before
    # Wrong: detach from ticket HEAD, skip cleanup, reorder it, or delete outside git.
    assert ctx.git.mock_calls == [
        call.worktree_add_detached(ctx.repo, ctx.worktree("work"), "main"),
        *([call.rev_parse(ctx.repo, "HEAD:tickets/work/ticket.md")] if reply == "approve" else []),
        call.worktree_remove(ctx.repo, ctx.worktree("work")),
        call.worktree_prune(ctx.repo),
    ]
    # Wrong: delete the worktree directly in addition to calling the fake git cleanup.
    assert ctx.worktree("work").is_dir()
    # Wrong: omit the scope, reason finding, attempt number, or trigger.
    assert apply.call_args.args == (ctx, ticket, [idle.Finding(code="bad_path", message="bad_path", paved_road="review the supervisor proposal and keep or reject the ticket")])
    assert apply.call_args.kwargs == {"attempt": 0, "supervise": Supervise("premise_failed", ()), "key_scope": "sup"}
    tail = c.journal.read()[len(before) + 1 :]
    # Wrong: keep before attempting, omit cap consumption, or keep a refusal.
    assert [(e.type, e.body) for e in tail] == [
        (EventType.SIGNAL, {"signal": "supervisor_attempt", "stem": "work"}),
        *(
            [
                (EventType.CAP_CONSUMED, {"cap": "supervise", "ticket_sha": "new-blob"}),
                (EventType.SIGNAL, {"signal": "reject_verdict", "verdict": "keep", "actor": "supervisor", "ticket_sha": "new-blob"}),
            ]
            if reply == "approve"
            else []
        ),
    ]
    if reply != "approve":
        # Wrong: lift under the earlier unscoped Rework key.
        runner.lift_outbox.assert_awaited_once_with(ctx, "work", "rework-proposal", attempt=0, only="rework.md", key_scope="sup")


@pytest.mark.asyncio
@pytest.mark.parametrize("after", [False, True])
async def test_operator_lineage(tmp_path, monkeypatch, after):
    attempt = event(EventType.SIGNAL, {"signal": "supervisor_attempt"})
    keep = event(EventType.SIGNAL, {"signal": "reject_verdict", "verdict": "keep", "actor": "operator"})
    c, ctx, _, apply = rig(tmp_path, monkeypatch, history=[attempt, keep, event(EventType.SIGNAL, {"signal": "supervisor_attempt"}, "other"), *([attempt] if after else []), *arrival()])
    await idle.supervise_idle(c, AsyncMock(return_value=ctx))
    # Wrong: count attempts across operator keeps, or ignore attempts after one.
    assert apply.await_count == (0 if after else 1)
    if not after:
        # Wrong: number attempts only within the current lineage.
        assert apply.call_args.kwargs["attempt"] == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["changed", "abandoned", "spent", "uncapped", "runtime", "not_queued", "supervisor_keep"])
async def test_exclusions_are_not_attempts(tmp_path, monkeypatch, case):
    history = arrival()
    if case == "changed":
        history = arrival(reason="bad_path,ticket_changed")
    elif case == "abandoned":
        history = arrival(to="abandoned")
    elif case == "spent":
        history = [event(EventType.CAP_CONSUMED, {"cap": "supervise"})] * 2 + history
    elif case == "uncapped":
        history = arrival(to="gate_failed")
    elif case == "runtime":
        history = arrival(to="timeout")
    elif case == "not_queued":
        history = history[:1]
    elif case == "supervisor_keep":
        history = [event(EventType.SIGNAL, {"signal": "supervisor_attempt"}), event(EventType.SIGNAL, {"signal": "reject_verdict", "verdict": "keep", "actor": "supervisor"}), *history]
    c, ctx, _, apply = rig(tmp_path, monkeypatch, history=history)
    make = AsyncMock(return_value=ctx)
    await idle.supervise_idle(c, make)
    # Wrong: prepare, create a worktree, or emit a refused attempt for an exclusion.
    assert c.journal.read() == history
    make.assert_not_awaited()
    assert ctx.git.mock_calls == []
    apply.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["conflict", "rework", "spent_gate"])
async def test_other_arrival_routes(tmp_path, monkeypatch, route):
    history = arrival(stage="merge" if route == "conflict" else "implement", rework_requested=route == "rework", to="gate_failed" if route == "spent_gate" else "premise_failed")
    history = [event(EventType.CAP_CONSUMED, {"cap": "diagnosis"})] * Caps().diagnosis + history
    history = [
        event(EventType.SIGNAL, {"signal": "diagnosis", "lessons": ["stale"]}),
        event(EventType.SIGNAL, {"signal": "reject_verdict", "verdict": "keep", "actor": "operator"}),
        event(EventType.SIGNAL, {"signal": "diagnosis", "lessons": ["other stem"]}, "other"),
        event(EventType.SIGNAL, {"signal": "diagnosis", "lessons": ["fence", "fence", "path"]}),
        *history,
    ]
    c, ctx, _, apply = rig(tmp_path, monkeypatch, history=history)
    await idle.supervise_idle(c, AsyncMock(return_value=ctx))
    # Wrong: exclude handoffs/Rework or gate failures even with a spent cap.
    assert apply.await_count == 1
    # Wrong: lose diagnosis lessons or use the reason instead of the spent cap.
    assert apply.call_args.kwargs["supervise"] == Supervise("diagnosis cap spent", ("fence", "path"))


@pytest.mark.asyncio
async def test_no_context_skips_git_and_attempt(tmp_path, monkeypatch):
    c, ctx, _, _ = rig(tmp_path, monkeypatch)
    before = c.journal.read()
    make = AsyncMock(return_value=None)
    await idle.supervise_idle(c, make)
    make.assert_awaited_once_with()  # Wrong: never request context for eligible work.
    assert c.journal.read() == before  # Wrong: journal the attempt before context exists.
    assert ctx.git.mock_calls == []  # Wrong: create a worktree without a provider context.


@pytest.mark.asyncio
async def test_failure_terminal_still_owns_one_terminal(tmp_path, monkeypatch):
    c, ctx, ticket, _ = rig(tmp_path, monkeypatch, history=[])
    await runner.failure_terminal(ctx, ticket, outcome="premise_failed", stage="implement", findings=[], attempt=3, verdict="abandon-human", supervised=True)
    # Wrong: move terminal ownership into the helper or reorder the keep.
    assert [e.type for e in c.journal.read()] == [EventType.SIGNAL, EventType.STATE_TRANSITION, EventType.CAP_CONSUMED, EventType.SIGNAL]


@pytest.mark.asyncio
async def test_real_publication_effect_is_scoped(tmp_path, monkeypatch):
    real_apply = daemon.apply_rework
    c, ctx, ticket, apply = rig(tmp_path, monkeypatch)
    result = apply.return_value
    ticket.stuck_minutes = 1
    keys = []

    async def effect(action, *, key, ticket):
        keys.append(key)
        return await action()

    ctx.driver.effects = SimpleNamespace(run=effect)
    ctx.git._run = AsyncMock(side_effect=["old", "new"])

    async def commit_edit(*args, edit, **kwargs):
        await edit()
        return "commit"

    ctx.git.commit_edit = AsyncMock(side_effect=commit_edit)
    monkeypatch.setattr(daemon, "apply_rework", real_apply)
    monkeypatch.setattr(idle, "parse_ticket", lambda *args: ticket)
    monkeypatch.setattr(daemon, "parse_ticket", lambda *args: ticket)
    monkeypatch.setattr(daemon, "rework", AsyncMock(return_value=result))
    monkeypatch.setattr(daemon, "record_supersedes", AsyncMock(return_value=[]))
    await idle.supervise_idle(c, AsyncMock(return_value=ctx))
    # Wrong: publish under the old attempt's unscoped effect and replay its result.
    assert keys == ["ticket-plane/work/sup-0/rework"]
