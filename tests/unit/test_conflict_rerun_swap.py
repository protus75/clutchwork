"""Discarded conflicts use their own accounting and operator release."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Discarded conflicts use their own accounting and operator release.
# relates: [clutch/artifacts.py, clutch/caps.py, clutch/config.py, clutch/daemon.py, clutch/drain.py, clutch/git.py, clutch/journal.py, clutch/merge.py]
# owner: engine
# verified: 0a308920
# hash: 7b83743db29b573080f9f5a07c93cc8f62e3c01a2835fd8ab979ab093d0d29de

import asyncio
import json
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import caps, daemon, drain, merge, runner
from clutch.artifacts import Cost, Finding, refused
from clutch.config import Caps
from clutch.daemon import TicketWriter
from clutch.git import GitError
from clutch.journal import Event, EventType, _parse_line
from clutch.status import last_states, reject_queue
from tests.unit.test_merge_admission_params import rig


class MemoryJournal:
    def __init__(self):
        self.events = []

    def read(self):
        return list(self.events)

    def append(self, kind, body, *, ticket=None, **kwargs):
        event = Event(1, kind, "2026-01-01T00:00:00+00:00", ticket, None, body)
        self.events.append(event)
        return event


def test_queue_refusal_aborts_and_records_rerun(monkeypatch):
    queue, ticket, events, _ = rig(monkeypatch)
    queue.ctx.git.rebase_stop_at_conflict = AsyncMock(side_effect=GitError(["git"], 1, "", "conflict"))
    queue.ctx.git.conflicted_paths = AsyncMock(return_value=["src/conflict"])
    queue.ctx.git._call = AsyncMock()
    queue.ctx.git._run = AsyncMock(return_value="text")
    queue.ctx.git.merge_base = AsyncMock(return_value="base")
    queue.ctx.fs = SimpleNamespace(read_bytes=lambda _: b"text")
    queue._resolve = AsyncMock(return_value=[Finding(code="mechanical", message="refused", paved_road="rerun")])
    queue._model_resolve = AsyncMock(return_value=[Finding(code="model", message="declined", paved_road="rerun")])
    result = asyncio.run(queue._admit(ticket, 7))
    # A successful result, missing conflict path, skipped abort, or old rung differs.
    assert (result.outcome, result.findings[0].code, result.findings[0].path) == ("gate_failed", "merge_conflict_rerun", "src/conflict")
    assert queue.ctx.git._call.await_args.args == (queue.ctx.worktree(ticket.stem), "rebase", "--abort")
    assert events == [{"kind": "merge_conflict_facts", "conflicted_paths": ["src/conflict"], "resolving_rung": "rerun", "strategy_paths": [], "integration_red_paths": []}]


def writer_rig(monkeypatch):
    journal = MemoryJournal()
    ctx = SimpleNamespace(repo=Path("/virtual"), driver=SimpleNamespace(journal=journal), git=SimpleNamespace(diff=AsyncMock(return_value="discarded diff")))
    queue = SimpleNamespace(active=None, _slot=asyncio.Lock())
    writer = TicketWriter.__new__(TicketWriter)
    writer.ctx, writer.queue = ctx, queue
    writer.admission = SimpleNamespace(deliver=lambda *args: False)
    lift, retire = AsyncMock(), AsyncMock()
    monkeypatch.setattr(daemon, "lift_prior_diff", lift)
    monkeypatch.setattr(merge, "retire", retire)
    monkeypatch.setattr(runner, "harvest_failure", AsyncMock())
    result = refused([Finding(code="merge_conflict_rerun", path="src/conflict", message="conflict", paved_road="rerun")], Cost())
    return writer, SimpleNamespace(stem="work"), result, journal, lift, retire


def test_signal_lift_retirement_and_free_reoffer(monkeypatch):
    writer, ticket, result, journal, lift, retire = writer_rig(monkeypatch)
    journal.append(EventType.STATE_TRANSITION, {"to": "gate_failed"}, ticket="work")
    before = caps.failed_attempts(journal.read(), "work")
    asyncio.run(writer.consume_result(ticket, result, attempt=7))
    # Wrong attempt, stem, diff or conflict exclusions cannot pass the lift assertion.
    assert lift.await_args.args == (writer.ctx, "work")
    assert lift.await_args.kwargs == {"attempt": 7, "diff": "discarded diff", "conflicted": ["src/conflict"]}
    assert retire.await_args.args == (writer.ctx, "work")
    assert [e.body for e in journal.read() if e.type == EventType.SIGNAL] == [{"signal": "merge_conflict_rerun", "attempt": 7}]
    assert journal.read()[-1].body == {"to": "gate_failed", "stage": "merge", "reason": "merge_conflict_rerun", "conflict_rerun": True}
    drain.record_reoffer(journal, journal.read(), "work", "ticket-sha")
    # Counting all gate failures or drawing ordinary retry would change these values.
    assert caps.failed_attempts(journal.read(), "work") == before == 1
    assert [e for e in journal.read() if e.type == EventType.CAP_CONSUMED] == []
    assert drain.reofferable(journal.read(), "work", Caps())


def test_limit_parks_and_operator_keep_releases(monkeypatch):
    writer, ticket, result, journal, lift, retire = writer_rig(monkeypatch)
    for _ in range(4):
        journal.append(EventType.STATE_TRANSITION, {"to": "gate_failed"}, ticket="work")
    for n in range(3):
        asyncio.run(writer.consume_result(ticket, result, attempt=n))
    # An off-by-one limit gives three signals, lifts or no park.
    assert [e.body for e in journal.read() if e.type == EventType.SIGNAL] == [{"signal": "merge_conflict_rerun", "attempt": 0}, {"signal": "merge_conflict_rerun", "attempt": 1}]
    assert lift.await_count == 2 and retire.await_count == 3
    assert caps.failed_attempts(journal.read(), "work") == 4
    terminal = reject_queue(journal.read())["work"]
    assert (terminal["reason"], terminal["dispatch"], terminal["routed"]) == ("merge_conflict_rerun_spent", "reject_queue", "reject_queue")
    assert [(f["code"], f["paved_road"]) for f in terminal["findings"]] == [("merge_conflict_rerun_spent", caps.CONFLICT_RERUN_ROAD)]
    assert drain.awaiting_operator(journal.read(), "work", Caps()) and not drain.reofferable(journal.read(), "work", Caps())
    journal.append(EventType.SIGNAL, {"signal": "reject_verdict", "verdict": "keep", "actor": "operator"}, ticket="work")
    asyncio.run(writer.consume_result(ticket, result, attempt=3))
    assert journal.read()[-2].body == {"signal": "merge_conflict_rerun", "attempt": 3}
    assert not drain.awaiting_operator(journal.read(), "work", Caps()) and drain.reofferable(journal.read(), "work", Caps())


def test_historical_rework_fact_still_folds():
    journal = MemoryJournal()
    journal.append(EventType.STATE_TRANSITION, {"to": "running"}, ticket="work")
    journal.append(EventType.SIGNAL, {"kind": "merge_conflict_facts", "resolving_rung": "rework", "conflicted_paths": ["old"]}, ticket="work")
    journal.append(EventType.STATE_TRANSITION, {"to": "gate_failed", "conflict_rerun": True}, ticket="work")
    # Ignoring the later terminal, or interpreting facts as a state, leaves running.
    assert last_states([_parse_line(Path("/virtual/journal"), n, json.dumps(asdict(e)).encode()) for n, e in enumerate(journal.read(), 1)]) == {"work": "gate_failed"}


def test_live_delivery_follows_terminal(monkeypatch):
    writer, ticket, result, journal, _, _ = writer_rig(monkeypatch)
    delivered = []
    writer.admission.deliver = lambda *args: delivered.append(journal.read()[-1].body) or True
    asyncio.run(writer.consume_result(ticket, result, attempt=4))
    # Delivering first lets drive finish before rerun custody is complete.
    assert delivered == [{"to": "gate_failed", "stage": "merge", "reason": "merge_conflict_rerun", "conflict_rerun": True}]


def test_consumer_refuses_active_admission(monkeypatch):
    writer, ticket, result, journal, _, _ = writer_rig(monkeypatch)
    writer.queue.active = "other"
    with pytest.raises(ValueError, match="await MergeQueue.process"):
        asyncio.run(writer.consume_conflict_rerun(ticket, result, attempt=0))
