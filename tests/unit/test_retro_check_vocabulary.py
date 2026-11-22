# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that the retro check outcome vocabulary is exactly due, not_due and failed, and that Retro records its due flag and failure reports correctly
# relates: [clutch/retro.py]
# owner: clutch/retro.py
# verified: 2182d51e
# hash: bf43feeadecdaaab371177e5e85f8e7e59526daeaea239c3c542de47973a82aa
from types import SimpleNamespace
from typing import get_args
from unittest.mock import AsyncMock

import pytest

from clutch import retro


def test_one_vocabulary():
    assert get_args(retro.RetroCheckOutcome) == ("due", "not_due", "failed")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "trigger,failure,initial_due,expected_due",
    [(None, None, True, False), ("merges", SimpleNamespace(key="failure"), True, False), ("merges", None, False, True)],
)
async def test_retro_records_due(monkeypatch, trigger, failure, initial_due, expected_due):
    window = object()
    checkout = SimpleNamespace(journal=SimpleNamespace(read=lambda: []), clock=lambda: "now", config=SimpleNamespace(retro=object()))
    hook = retro.Retro(checkout, SimpleNamespace())
    hook.due = initial_due
    reports = []
    monkeypatch.setattr(retro, "project_window", lambda events: window)
    monkeypatch.setattr(retro, "production_evidence", AsyncMock(return_value="evidence"))
    monkeypatch.setattr(retro, "due_trigger", lambda *args, **kwargs: trigger)
    monkeypatch.setattr(retro, "suppressing_failure", lambda value: failure)
    monkeypatch.setattr(hook, "failure_report", reports.append)
    if expected_due:
        with pytest.raises(retro.RetroConstructionError):
            await hook()
    else:
        assert await hook() is None
    assert hook.due is expected_due
    assert reports == (["failure"] if failure else [])
