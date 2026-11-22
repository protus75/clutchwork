# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for the phase_start and phase_end engine-log events and their outcomes in runner preflight and in the drain and serve retro checks
# relates: [clutch/drain.py, clutch/runner.py, clutch/serve.py]
# owner: engine
# verified: 2182d51e
# hash: 769596fcf8605721451b971ba80c7d542aa6cd850badbb2812a50843ee174448
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import drain, runner, serve
from clutch.journal import EventType


class RecordingLog:
    def __init__(self, *args):
        self.events = []

    def event(self, event, **fields):
        self.events.append((event, fields))


def install_log(monkeypatch, module):
    log = RecordingLog()
    monkeypatch.setattr(module, "engine_log", lambda *args: log)
    return log


def events(phase, outcome):
    return [("phase_start", {"phase": phase}), ("phase_end", {"phase": phase, "outcome": outcome})]


@pytest.mark.asyncio
@pytest.mark.parametrize("result,outcome", [([], "ok"), (["bad provider"], "failed"), (RuntimeError("probe"), "failed")])
async def test_preflight_events(monkeypatch, result, outcome):
    log = install_log(monkeypatch, runner)
    config = SimpleNamespace(state_dir=Path("/state"), providers=[], release=SimpleNamespace(pypi_token=""))
    checkout = SimpleNamespace(config=config, exec_=None, fs=None, env={}, repo=Path("/repo"), control=SimpleNamespace(providers=None), clock=None)
    provider = SimpleNamespace(preflight=AsyncMock(side_effect=result if isinstance(result, Exception) else None, return_value=result), preflight_notices=[])
    monkeypatch.setattr(runner, "ProviderLLM", lambda *args, **kwargs: provider)
    monkeypatch.setattr(runner, "call_timeout", lambda config: 1)
    bound = object()
    monkeypatch.setattr(runner, "bind", lambda checkout, llm: bound)
    if isinstance(result, Exception):
        with pytest.raises(RuntimeError, match="probe"):
            await runner.prepare_pipeline(checkout)
    elif result:
        with pytest.raises(runner.Refusal, match="bad provider"):
            await runner.prepare_pipeline(checkout)
    else:
        assert await runner.prepare_pipeline(checkout) is bound
    assert log.events == events("preflight", outcome)


@pytest.mark.asyncio
@pytest.mark.parametrize("due,result,outcome", [(False, None, "not_due"), (True, object(), "due"), (True, None, "due"), (False, RuntimeError("retro"), "failed")])
async def test_drain_retro_events(monkeypatch, due, result, outcome):
    log = install_log(monkeypatch, drain)
    d = object.__new__(drain._Drain)
    d.c = SimpleNamespace(
        config=SimpleNamespace(state_dir=Path("/state"), providers=[], release=SimpleNamespace(pypi_token="")), env={}, clock=None, sleep=None, control=None, journal=SimpleNamespace(read=lambda: [])
    )
    d.retro_terminal_count = None
    d.retro = AsyncMock(side_effect=result if isinstance(result, Exception) else None, return_value=result)
    d.retro.due = due
    d.retro.abort_current = AsyncMock()
    if isinstance(result, Exception):
        with pytest.raises(RuntimeError, match="retro"):
            await d._run_retro(forced=False)
    else:
        await d._run_retro(forced=False)
    assert log.events == events("retro_check", outcome)


@dataclass
class Checkout:
    config: object
    journal: object
    clock: object


@pytest.mark.asyncio
@pytest.mark.parametrize("trigger,outcome", [(None, "not_due"), (object(), "due")])
async def test_serve_retro_events(monkeypatch, trigger, outcome):
    s = object.__new__(serve.Serve)
    s.log = RecordingLog()
    s.retro_checked = None
    config = SimpleNamespace(retro=object())
    s.checkout = Checkout(config, SimpleNamespace(read=lambda: [SimpleNamespace(type=EventType.STATE_TRANSITION, body={"to": "merged"})]), lambda: "now")
    s.control = SimpleNamespace(load_config=lambda: config)
    s.retro_due = False
    monkeypatch.setattr(serve, "snapshot_config", lambda value: value)
    monkeypatch.setattr(serve, "project_window", lambda value: value)
    monkeypatch.setattr(serve, "suppressing_failure", lambda value: None)
    monkeypatch.setattr(serve, "due_trigger", lambda *args, **kwargs: trigger)
    await s.check_retro()
    assert s.retro_due is (trigger is not None)
    assert s.log.events == events("retro_check", outcome)


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["journal", "evidence"])
async def test_serve_retro_failure(monkeypatch, failure):
    s = object.__new__(serve.Serve)
    s.log = RecordingLog()
    s.retro_checked = None
    config = SimpleNamespace(retro=object())

    def read():
        if failure == "journal":
            raise RuntimeError("journal")
        return [SimpleNamespace(type=EventType.STATE_TRANSITION, body={"to": "merged"})]

    s.checkout = Checkout(config, SimpleNamespace(read=read), lambda: "now")
    s.control = SimpleNamespace(load_config=lambda: config)
    monkeypatch.setattr(serve, "snapshot_config", lambda value: value)
    monkeypatch.setattr(serve, "project_window", lambda value: value)
    monkeypatch.setattr(serve, "suppressing_failure", lambda value: None)

    def fail_measurements(*args, **kwargs):
        raise RuntimeError("evidence")

    monkeypatch.setattr(serve, "due_trigger", fail_measurements)
    with pytest.raises(RuntimeError, match=failure):
        await s.check_retro()
    assert s.log.events == ([] if failure == "journal" else events("retro_check", "failed"))
