# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that Serve.check_retro logs one retro_check phase pair per terminal-transition count across sequential and concurrent calls, rechecks only after a new terminal transition, retries after a failure, and never calls production_evidence
# relates: [clutch/journal.py, clutch/retro.py, clutch/serve.py]
# owner: clutch/serve.py
# verified: 2182d51e
# hash: 0c68ad1932ce07c7f0478cdeb8463a6af879688e11807f170e020feeb6abd418
import asyncio
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from clutch import retro, serve
from clutch.journal import EventType


@dataclass
class Checkout:
    config: object
    journal: object
    clock: object


def pair(outcome):
    return [("phase_start", {"phase": "retro_check"}), ("phase_end", {"phase": "retro_check", "outcome": outcome})]


@pytest.fixture
def setup(monkeypatch):
    journal = [SimpleNamespace(type=EventType.STATE_TRANSITION, body={"to": "merged"})]
    log = []
    config = SimpleNamespace(retro=object())
    s = object.__new__(serve.Serve)
    s.retro_checked = None
    s.retro_due = False
    s.log = SimpleNamespace(event=lambda name, **fields: log.append((name, fields)))
    s.checkout = Checkout(config, SimpleNamespace(read=lambda: list(journal)), lambda: "now")
    s.control = SimpleNamespace(load_config=lambda: config)
    monkeypatch.setattr(serve, "snapshot_config", lambda value: value)
    monkeypatch.setattr(serve, "project_window", lambda value: value)
    monkeypatch.setattr(serve, "suppressing_failure", lambda value: None)
    monkeypatch.setattr(serve, "due_trigger", lambda *args, **kwargs: None)
    return s, journal, log


@pytest.mark.asyncio
async def test_sequential_calls_log_one_pair(setup):
    s, _, log = setup
    await s.check_retro()
    await s.check_retro()
    assert log == pair("not_due")


@pytest.mark.asyncio
async def test_concurrent_calls_log_one_pair(setup):
    s, _, log = setup
    await asyncio.gather(s.check_retro(), s.check_retro())
    assert log == pair("not_due")


@pytest.mark.asyncio
@pytest.mark.parametrize("state,expected", [("gate_failed", 2), ("running", 1)])
async def test_only_terminal_transition_runs_again(setup, state, expected):
    s, journal, log = setup
    await s.check_retro()
    journal.append(SimpleNamespace(type=EventType.STATE_TRANSITION, body={"to": state}))
    await s.check_retro()
    assert log == pair("not_due") * expected


@pytest.mark.asyncio
async def test_failure_retries_same_count(setup, monkeypatch):
    s, _, log = setup

    def fail(*args, **kwargs):
        raise RuntimeError("measurements")

    monkeypatch.setattr(serve, "due_trigger", fail)
    with pytest.raises(RuntimeError, match="measurements"):
        await s.check_retro()
    assert s.retro_checked is None
    monkeypatch.setattr(serve, "due_trigger", lambda *args, **kwargs: None)
    await s.check_retro()
    assert log == pair("failed") + pair("not_due")


@pytest.mark.asyncio
async def test_does_not_call_production_evidence(setup, monkeypatch):
    s, _, log = setup

    async def fail(*args):
        raise AssertionError("production evidence called")

    monkeypatch.setattr(retro, "production_evidence", fail)
    await s.check_retro()
    assert log == pair("not_due")
