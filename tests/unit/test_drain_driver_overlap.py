# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test drain driver overlap
# relates: [clutch/drain.py, clutch/roadmap.py, clutch/triage.py, tests/fakes.py, tests/unit/test_phase_events.py]
# owner: engine
# verified: 0a308920
# hash: 3654f89f1bfb10bfbea6dadcd74412198491f9584393412b5c606b19c2e662c9
import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import drain, roadmap, triage
from tests.fakes import FakeJournal
from tests.unit.test_phase_events import install_log


@pytest.fixture
def rig(tmp_path, monkeypatch):
    install_log(monkeypatch, drain)
    (tmp_path / "docs").mkdir()
    (tmp_path / roadmap.ROADMAP).touch()
    state = SimpleNamespace(count=0, tickets=[], dispatched=[])
    c = SimpleNamespace(
        repo=tmp_path,
        journal=FakeJournal(),
        config=SimpleNamespace(state_dir=tmp_path, providers=[], release=SimpleNamespace(pypi_token="")),
        env={},
        clock=datetime.now,
        sleep=asyncio.sleep,
        git=SimpleNamespace(main_write=lambda: state.lock),
        fs=None,
        control=SimpleNamespace(inbox=SimpleNamespace(settle_triage=AsyncMock()), projection=SimpleNamespace(stop_requested=False)),
    )
    state.lock = asyncio.Lock()
    d = drain._Drain.__new__(drain._Drain)
    d.c, d.dispatch, d.before_dispatch = c, object(), None
    d.report, d.retro, d.provider_deadlines, d.storm_waiting = object(), None, [], False
    d.deadline, d.upgrade = datetime.now() + timedelta(days=1), None
    d._stopping = lambda: False
    d._between_tickets = AsyncMock(return_value=True)
    d._offer_material = lambda: None

    async def scan():
        await asyncio.sleep(0)
        return SimpleNamespace(tickets={s: SimpleNamespace(stem=s) for s in state.tickets})

    d._scan = scan
    d._sha = AsyncMock(return_value="sha")
    d._select = lambda scan, *args: (next(iter(scan.tickets.values()), None), False)
    d._settle = lambda *args: None

    async def controlled(task, abort, sleep):
        return await task

    d._await_controlled = controlled

    async def dispatch(pick, reoffer, sha):
        state.dispatched.append(pick.stem)
        state.tickets.remove(pick.stem)

    d._run_one = dispatch
    monkeypatch.setattr(drain, "intake", AsyncMock())
    monkeypatch.setattr(triage, "report_intake", lambda c: None)
    monkeypatch.setattr(drain, "supervise_idle", AsyncMock())
    monkeypatch.setattr(drain, "calibrate_when_due", lambda c: None)
    monkeypatch.setattr(roadmap, "settles", lambda events: state.count)
    return d, state


@pytest.mark.asyncio
async def test_dispatch_starts_while_pass_runs(rig):
    d, state = rig
    entered, release = asyncio.Event(), asyncio.Event()
    state.tickets.append("next")

    async def driver(c, log):
        entered.set()
        await release.wait()

    d.driver = driver

    async def dispatch(pick, reoffer, sha):
        await entered.wait()
        assert not release.is_set() and not d.driver_task.done()
        state.dispatched.append(pick.stem)
        state.tickets.remove(pick.stem)
        release.set()

    d._run_one = dispatch
    await d.run()
    assert state.dispatched == ["next"]


@pytest.mark.asyncio
async def test_main_write_orders_pass_and_admission(rig):
    d, state = rig
    entered, release = asyncio.Event(), asyncio.Event()
    order = []
    state.tickets.append("next")

    async def driver(c, log):
        async with c.git.main_write():
            order.append("driver entered")
            entered.set()
            await release.wait()
            order.append("driver released")

    async def dispatch(pick, reoffer, sha):
        await entered.wait()

        async def admission():
            async with d.c.git.main_write():
                order.append("admission entered")

        task = asyncio.create_task(admission())
        await asyncio.sleep(0)
        assert order == ["driver entered"]
        release.set()
        await task
        state.tickets.remove(pick.stem)

    d.driver, d._run_one = driver, dispatch
    await d.run()
    assert order == ["driver entered", "driver released", "admission entered"]


@pytest.mark.asyncio
async def test_one_pass_at_a_time(rig):
    d, state = rig
    entered, release = asyncio.Event(), asyncio.Event()
    calls = []
    state.tickets.extend(["one", "two"])

    async def driver(c, log):
        calls.append(state.count)
        entered.set()
        if len(calls) == 1:
            await release.wait()

    async def dispatch(pick, reoffer, sha):
        await entered.wait()
        state.tickets.remove(pick.stem)
        state.count += 1
        assert calls == [0]
        if state.count == 2:
            release.set()

    d.driver, d._run_one = driver, dispatch
    await d.run()
    assert calls == [0, 2]


@pytest.mark.asyncio
async def test_run_waits_for_pass_and_surfaces_error(rig):
    d, state = rig
    entered, release = asyncio.Event(), asyncio.Event()

    async def driver(c, log):
        entered.set()
        await release.wait()

    d.driver = driver
    task = asyncio.create_task(d.run())
    await entered.wait()
    await asyncio.sleep(0)
    assert not task.done()
    release.set()
    assert await task is d.report

    async def broken(c, log):
        raise RuntimeError("driver failed")

    d.driver, d.driven = broken, None
    with pytest.raises(RuntimeError, match="driver failed"):
        await d.run()


@pytest.mark.asyncio
async def test_idle_exit_waits_for_pass(rig):
    d, state = rig
    entered, release = asyncio.Event(), asyncio.Event()
    calls = []

    async def driver(c, log):
        calls.append(state.count)
        if len(calls) == 1:
            entered.set()
            await release.wait()
            state.tickets.append("authored")
            state.count = 1

    d.driver = driver
    task = asyncio.create_task(d.run())
    await entered.wait()
    await asyncio.sleep(0)
    assert not task.done()
    release.set()
    await task
    assert state.dispatched == ["authored"]
    assert calls == [0, 1]
