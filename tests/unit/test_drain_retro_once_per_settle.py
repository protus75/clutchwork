# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that drain runs the retro check once per terminal settle, always runs forced checks, and does not record the count after a failed check
# relates: [clutch/drain.py, clutch/journal.py]
# owner: engine
# verified: 331196ce
# hash: cf05a1c08838531ee90502d965b12ea5a51f1ef02534e0ec1b35ac814dd5ac21
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import drain
from clutch.journal import EventType


@pytest.fixture
def setup(monkeypatch):
    events = [SimpleNamespace(type=EventType.STATE_TRANSITION, body={"to": "merged"})]
    log_events = []
    log = SimpleNamespace(event=lambda name, **fields: log_events.append((name, fields)))
    monkeypatch.setattr(drain, "engine_log", lambda *args: log)
    config = SimpleNamespace(state_dir=Path("/state"), providers=[], release=SimpleNamespace(pypi_token=""), drain=SimpleNamespace(max_runtime_hours=1))
    checkout = SimpleNamespace(config=config, env={}, clock=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc), sleep=None, control=None, journal=SimpleNamespace(read=lambda: events))
    d = drain._Drain(checkout, None, frozenset())
    d.retro = AsyncMock()
    d.retro.due = False
    d.retro.abort_current = AsyncMock()
    return d, events, log_events


@pytest.mark.asyncio
async def test_unchanged_count_skips_hook_and_events(setup):
    d, _, log = setup
    await d._run_retro(forced=False)
    await d._run_retro(forced=False)
    assert d.retro.await_count == 1
    assert log == [("phase_start", {"phase": "retro_check"}), ("phase_end", {"phase": "retro_check", "outcome": "not_due"})]


@pytest.mark.asyncio
@pytest.mark.parametrize("state,expected", [("gate_failed", 2), ("running", 1)])
async def test_only_terminal_transition_triggers_check(setup, state, expected):
    d, events, _ = setup
    await d._run_retro(forced=False)
    events.append(SimpleNamespace(type=EventType.STATE_TRANSITION, body={"to": state}))
    await d._run_retro(forced=False)
    assert d.retro.await_count == expected


@pytest.mark.asyncio
async def test_forced_check_runs_and_records_count(setup):
    d, events, _ = setup
    await d._run_retro(forced=False)
    events.append(SimpleNamespace(type=EventType.STATE_TRANSITION, body={"to": "merged"}))
    await d._run_retro(forced=True)
    await d._run_retro(forced=True)
    await d._run_retro(forced=False)
    assert d.retro.await_count == 3
    assert [call.kwargs for call in d.retro.await_args_list] == [{"forced": False}, {"forced": True}, {"forced": True}]


@pytest.mark.asyncio
async def test_failed_check_does_not_record_count(setup):
    d, _, log = setup
    d.retro.side_effect = [RuntimeError("retro"), None]
    with pytest.raises(RuntimeError, match="retro"):
        await d._run_retro(forced=False)
    await d._run_retro(forced=False)
    assert d.retro.await_count == 2
    assert log == [
        ("phase_start", {"phase": "retro_check"}),
        ("phase_end", {"phase": "retro_check", "outcome": "failed"}),
        ("phase_start", {"phase": "retro_check"}),
        ("phase_end", {"phase": "retro_check", "outcome": "not_due"}),
    ]
