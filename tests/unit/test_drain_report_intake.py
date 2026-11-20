"""Drain admits reports after ticket intake on each loop."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Drain admits reports after ticket intake on each loop.
# relates: [clutch/drain.py, clutch/triage.py]
# owner: engine
# verified: 0a308920
# hash: 3e2acad1187ced1d99252a7ba6874359b804806074d32edb3107f0f4159bd036

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import drain, triage


@pytest.mark.asyncio
async def test_loop_intakes_reports_after_tickets(monkeypatch):
    calls = []
    checkout = SimpleNamespace(
        repo=object(),
        git=object(),
        fs=object(),
        journal=SimpleNamespace(read=lambda: []),
        control=SimpleNamespace(inbox=SimpleNamespace(settle_triage=AsyncMock()), projection=SimpleNamespace(stop_requested=False)),
    )

    async def intake(repo, git, journal, fs, *, stems):
        calls.append(("tickets", repo, git, journal, fs, stems))

    monkeypatch.setattr(drain, "intake", intake)
    monkeypatch.setattr(triage, "report_intake", lambda c: calls.append(("reports", c)))
    monkeypatch.setattr(drain, "calibrate_when_due", lambda checkout: None)
    run = drain._Drain.__new__(drain._Drain)
    run.c, run.dispatch, run.before_dispatch = checkout, object(), None
    run.report, run.retro, run.provider_deadlines, run.storm_waiting = object(), None, [], False
    run._stopping = lambda: False
    run._offer_material = lambda: None

    async def scan():
        return SimpleNamespace(tickets={})

    run._scan = scan
    run._select = lambda *args: (None, False)
    run._settle = lambda *args: None
    assert await run.run() is run.report
    assert calls == [("tickets", checkout.repo, checkout.git, checkout.journal, checkout.fs, None), ("reports", checkout)]
