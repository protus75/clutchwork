from contextlib import asynccontextmanager
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import drain, roadmap, serve, triage
from clutch.journal import EventType
from tests.fakes import FakeJournal
from tests.unit.test_phase_events import install_log


@dataclass(frozen=True)
class Checkout:
    repo: object
    journal: object
    config: object


@pytest.mark.asyncio
async def test_serve_driver_pending_and_run(tmp_path, monkeypatch):
    s = object.__new__(serve.Serve)
    journal = FakeJournal()
    journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="a")
    s.checkout = Checkout(tmp_path, journal, "old")
    s.control = SimpleNamespace(load_config=lambda: "new", poll=lambda: None, projection=SimpleNamespace(stop_requested=False, kill_requested=False))
    s.log, s.driven, s.stopping = object(), None, False
    s.driver = AsyncMock()
    monkeypatch.setattr(serve, "snapshot_config", lambda c: c)

    @asynccontextmanager
    async def mutations():
        yield

    s.mutations = mutations
    assert not s.driver_pending()
    (tmp_path / "docs").mkdir()
    (tmp_path / roadmap.ROADMAP).touch()
    assert s.driver_pending()
    await s.run_driver()
    s.driver.assert_awaited_once_with(Checkout(tmp_path, journal, "new"), s.log)
    assert s.driven == 1 and not s.driver_pending()
    s.stopping = True
    await s.run_driver()
    assert s.driver.await_count == 1


@pytest.mark.asyncio
async def test_drain_runs_driver_between_tickets(tmp_path, monkeypatch):
    log = install_log(monkeypatch, drain)
    (tmp_path / "docs").mkdir()
    path = tmp_path / roadmap.ROADMAP
    path.touch()
    journal = FakeJournal()
    journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="a")
    c = SimpleNamespace(
        repo=tmp_path,
        journal=journal,
        config=SimpleNamespace(state_dir=tmp_path),
        env={},
        clock=None,
        sleep=None,
        git=None,
        fs=None,
        control=SimpleNamespace(inbox=SimpleNamespace(settle_triage=AsyncMock()), projection=SimpleNamespace(stop_requested=False)),
    )
    d = drain._Drain.__new__(drain._Drain)
    d.c, d.dispatch, d.before_dispatch = c, object(), None
    d.report, d.retro, d.provider_deadlines, d.storm_waiting = object(), None, [], False
    d.driver = AsyncMock()
    d._stopping = lambda: False
    d._between_tickets = AsyncMock(return_value=True)
    d._offer_material = lambda: None
    d._scan = AsyncMock(return_value=SimpleNamespace(tickets={}))
    d._select = lambda *args: (None, False)
    d._settle = lambda *args: None
    d._await_controlled = AsyncMock(side_effect=lambda task, abort, sleep: task)

    async def controlled(task, abort, sleep):
        await task

    d._await_controlled = controlled
    monkeypatch.setattr(drain, "intake", AsyncMock())
    monkeypatch.setattr(triage, "report_intake", lambda c: None)
    monkeypatch.setattr(drain, "calibrate_when_due", lambda checkout: None)
    await d.run()
    d.driver.assert_awaited_once_with(c, log)
    assert d.driven == 1
    await d.run()
    assert d.driver.await_count == 1
    d.driven = None
    d._between_tickets.return_value = False
    await d.run()
    path.unlink()
    d._between_tickets.return_value = True
    await d.run()
    path.touch()
    d.driver = None
    await d.run()
    assert d.driven is None


def test_serve_select_holds_only_new_admission(tmp_path):
    s = object.__new__(serve.Serve)
    journal = FakeJournal()
    (tmp_path / "docs").mkdir()
    (tmp_path / roadmap.ROADMAP).touch()
    s.checkout = Checkout(tmp_path, journal, None)
    s.driven, s.stopping, s.upgrade = None, False, None
    s.writers = {}
    s.control = SimpleNamespace(
        poll=lambda: None,
        projection=SimpleNamespace(kill_requested=False, stop_requested=False, pause_id=None, released_hold_ids=set()),
        providers=SimpleNamespace(active=False),
        admission=None,
    )
    s.storm = SimpleNamespace(held_stages=lambda: {})
    s.retro_pending = lambda: False
    ticket = SimpleNamespace(stem="one")
    assert not s.select(ticket, "implement")
    s.writers["one"] = object()
    assert s.select(ticket, "check")
    del s.writers["one"]
    s.driven = 0
    assert s.select(ticket, "implement")
