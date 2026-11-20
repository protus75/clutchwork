"""Calibration cadence and idle boundaries."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Calibration cadence and idle boundaries.
# relates: [clutch/calibration.py, clutch/config.py, clutch/drain.py, clutch/journal.py, clutch/serve.py, tests/fakes.py]
# owner: engine
# verified: 0a308920
# hash: c0a7d61e6323027acef9e952083a7277c88a7cc2a0dd0792bb12044b14b95312

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import drain, serve
from clutch.calibration import calibrate_when_due, due
from clutch.config import Caps
from clutch.journal import EventType
from tests.fakes import FakeClock, FakeFileSystem, FakeJournal
from tests.unit.test_supervise_idle_hooks import Checkout, EndPoll, drain_rig, serve_rig
from tests.unit.test_supervise_idle_point import Journal, arrival


def call(journal, clock, stem, surface="implement"):
    key = f"llm/{stem}/1/{surface}/1/1"
    journal.append(EventType.EFFECT_INTENT, {}, key=key)
    clock.advance(60)
    journal.append(EventType.EFFECT_COMPLETION, {"cost": {"provider": "p", "model": "m"}}, key=key)


def test_due_counts_implement_completions_since_the_latest_calibration():
    clock = FakeClock()
    journal = FakeJournal(clock)
    call(journal, clock, "a")
    call(journal, clock, "b")
    journal.append(EventType.SIGNAL, {"signal": "estimate_calibration"})
    call(journal, clock, "c")
    call(journal, clock, "d", "review")
    # Wrong: count old completions or review completions.
    assert not due(journal.read(), 2)
    call(journal, clock, "e")
    # Wrong: fail to count a completion after the signal.
    assert due(journal.read(), 2)


def test_calibrate_when_due_journals_only_when_due():
    clock = FakeClock()
    journal = FakeJournal(clock)
    checkout = SimpleNamespace(config=SimpleNamespace(calibration=SimpleNamespace(every=2)), journal=journal, fs=FakeFileSystem(), repo=Path("/repo"))
    call(journal, clock, "a")
    calibrate_when_due(checkout)
    # Wrong: calibrate before the threshold.
    assert [e for e in journal.read() if e.type == EventType.SIGNAL] == []
    call(journal, clock, "b")
    calibrate_when_due(checkout)
    calibrate_when_due(checkout)
    # Wrong: skip calibration or repeat it on the next poll.
    assert [e.body["signal"] for e in journal.read() if e.type == EventType.SIGNAL] == ["estimate_calibration"]


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["idle", "busy", "paused"])
async def test_serve_calibrates_at_its_idle_point(tmp_path, monkeypatch, mode):
    c = Checkout(tmp_path, Journal(), SimpleNamespace(caps=Caps()))
    s = serve_rig(tmp_path, monkeypatch, c, None)
    s.upgrade_idle = lambda: mode != "busy"
    s.control.projection.pause_id = "pause" if mode == "paused" else None
    calls = []

    async def supervise(checkout, make_ctx):
        calls.append(("supervise", s.locked, checkout))

    async def dispatch():
        calls.append(("dispatch", s.locked, None))

    monkeypatch.setattr(serve, "supervise_idle", supervise)
    monkeypatch.setattr(serve, "calibrate_when_due", lambda checkout: calls.append(("calibrate", s.locked, checkout)))
    s.core.scheduler.dispatch_next.side_effect = dispatch
    with pytest.raises(EndPoll):
        await s.dispatch()
    # Wrong: calibrate while busy or paused, outside the lock, or after dispatch.
    assert calls == ([("supervise", True, s.checkout), ("calibrate", True, s.checkout), ("dispatch", False, None)] if mode == "idle" else [("dispatch", False, None)] if mode == "busy" else [])


@pytest.mark.asyncio
@pytest.mark.parametrize("between", [False, True])
async def test_drain_calibrates_between_tickets(tmp_path, monkeypatch, between):
    history = arrival() if between else [arrival(to="gate_failed")[0]]
    c = Checkout(
        tmp_path,
        Journal(history),
        SimpleNamespace(caps=Caps()),
        SimpleNamespace(inbox=SimpleNamespace(settle_triage=AsyncMock()), projection=SimpleNamespace(stop_requested=False, retro_id=None), storm_holds=lambda: {}),
    )
    d = drain_rig(tmp_path, monkeypatch, c, object())
    calls = []

    async def supervise(checkout, make_ctx):
        calls.append(("supervise", checkout))

    monkeypatch.setattr(drain, "supervise_idle", supervise)
    monkeypatch.setattr(drain, "calibrate_when_due", lambda checkout: calls.append(("calibrate", checkout)))
    await d.run()
    # Wrong: calibrate during a retry or before supervision.
    assert calls == ([("supervise", c), ("calibrate", c)] if between else [])
