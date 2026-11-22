# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that retro due_trigger decides whether a retro is due before production evidence loads, covering not-due skips, forced runs, merge thresholds and override invoices that cannot trigger
# relates: [clutch/config.py, clutch/journal.py, clutch/retro.py]
# owner: clutch/retro.py
# verified: 2182d51e
# hash: 04647fc2a5025b9a0cd89494a9397d208611c74f76182e4e5555ec7c22892e26
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import retro
from clutch.config import Retro as RetroSettings
from clutch.journal import EventType


def merge(n):
    return SimpleNamespace(type=EventType.STATE_TRANSITION, body={"to": "merged", "commit": f"sha-{n}"}, ticket=f"ticket-{n}", ts="2026-01-01T00:00:00+00:00", key=None)


def hook_for(events):
    checkout = SimpleNamespace(journal=SimpleNamespace(read=lambda: events), config=SimpleNamespace(retro=RetroSettings()))
    return retro.Retro(checkout, SimpleNamespace())


@pytest.mark.asyncio
async def test_not_due_skips_production_evidence(monkeypatch):
    evidence = AsyncMock(side_effect=AssertionError("unexpected evidence"))
    monkeypatch.setattr(retro, "production_evidence", evidence)
    assert await hook_for([merge(1)])(forced=False) is None
    evidence.assert_not_awaited()


@pytest.mark.asyncio
async def test_forced_selects_before_loading_evidence(monkeypatch):
    evidence = AsyncMock(return_value={"marker": 1})
    monkeypatch.setattr(retro, "production_evidence", evidence)
    hook = hook_for([merge(1)])
    with pytest.raises(retro.RetroConstructionError):
        await hook(forced=True)
    evidence.assert_awaited_once()
    assert hook.due is True
    assert retro.due_trigger(retro.project_window([merge(1)]), RetroSettings(), forced=True) == "forced"


def test_merge_threshold():
    settings = RetroSettings(merges={"every": 3})
    assert retro.due_trigger(retro.project_window([merge(1), merge(2)]), settings, forced=False) is None
    assert retro.due_trigger(retro.project_window([merge(1), merge(2), merge(3)]), settings, forced=False) == "merges"


def test_override_invoices_do_not_trigger_or_load_evidence(monkeypatch):
    events = []
    for n in range(5):
        event = merge(n)
        events.extend(
            [
                SimpleNamespace(
                    type=EventType.EFFECT_COMPLETION,
                    body={"result": {"commit": f"sha-{n}"}, "bypassed": ["scope_fence"]},
                    ticket=event.ticket,
                    ts=event.ts,
                    key=f"ticket-plane/{event.ticket}/0/checks",
                ),
                event,
            ]
        )
    monkeypatch.setattr(retro, "production_evidence", AsyncMock(side_effect=AssertionError("git show")))
    window = retro.project_window(events)
    settings = RetroSettings(spikes={"kinds": ["override"]})
    assert retro.due_trigger(window, settings, forced=False) is None
    retro.production_evidence.assert_not_awaited()
    facts = retro.measurements(window)
    facts["spikes"]["override"] = 5
    assert retro.select_trigger(window, facts, settings, forced=False) is None
