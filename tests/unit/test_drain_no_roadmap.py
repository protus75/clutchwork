# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks drain dispatches, settles and exits without touching the roadmap module or any driver hook, while still running the idle supervisor step
# relates: [clutch/drain.py, clutch/journal.py, clutch/roadmap.py, clutch/triage.py, tests/fakes.py]
# owner: engine
# verified: 18f3cf87
# hash: 636213855d4b765c5096ee3bfd4c59e2a41e1a7e6a7f6f3a1b2fdd034976aae4
import inspect
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

import pytest

from clutch import drain, roadmap, triage
from clutch.journal import EventType
from tests.fakes import FakeJournal


@pytest.mark.asyncio
async def test_drain_settle_and_exit_without_roadmap(monkeypatch, tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("roadmap accessed")

    for name, value in vars(roadmap).copy().items():
        if not name.startswith("_") and inspect.isfunction(value) and value.__module__ == roadmap.__name__:
            monkeypatch.setattr(roadmap, name, forbidden)
    assert not any(hasattr(drain._Drain, name) for name in ("driver", "driver_task", "_run_driver"))
    assert "roadmap" not in vars(drain)
    d = drain._Drain.__new__(drain._Drain)
    journal = FakeJournal()
    d.c = NS(repo=tmp_path, git=None, fs=None, journal=journal, control=NS(projection=NS(stop_requested=False, retro_id=None), inbox=NS(settle_triage=AsyncMock())))
    d.dispatch, d.before_dispatch, d.retro = object(), None, None
    d.last_dispatched, d.report = None, object()
    d.provider_deadlines, d.storm_waiting = [], False
    d._stopping = lambda: False
    d._offer_material = lambda: None
    d._scan = AsyncMock(return_value=NS(tickets={}))
    ticket = NS(stem="work")
    picks = iter([(ticket, False), (None, False)])
    d._select = lambda *args: next(picks)
    d._scan = AsyncMock(return_value=NS(tickets={"work": ticket}))
    d._sha = AsyncMock(return_value="sha")

    async def settle(*args):
        d.last_dispatched = "work"
        journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="work")

    d._run_one = AsyncMock(side_effect=settle)
    d.upgrade = None
    d.deadline = __import__("datetime").datetime.max
    d.c.clock = lambda: __import__("datetime").datetime.min
    d._settle = lambda *args: None
    monkeypatch.setattr(drain, "intake", AsyncMock())
    monkeypatch.setattr(triage, "report_intake", lambda *a: None)
    monkeypatch.setattr(drain, "supervise_idle", AsyncMock())
    monkeypatch.setattr(drain, "calibrate_when_due", lambda *a: None)
    assert await d.run() is d.report
    d._run_one.assert_awaited_once_with(ticket, False, "sha")
    assert drain.supervise_idle.await_count == 2
