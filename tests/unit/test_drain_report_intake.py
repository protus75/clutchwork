"""Drain admits reports after ticket intake on each loop."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit test that each drain loop runs host report intake after ticket intake
# relates: [clutch/drain.py, clutch/triage.py]
# owner: engine
# verified: 45e4e081
# hash: de95682fd4f9e650a14fc677853370dafd2cd3768c3dcbb2c0bb9fe03e3c140d

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
