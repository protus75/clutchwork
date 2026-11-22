# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for the phase_start and phase_end engine-log events and their outcomes in runner preflight and in the drain retro check
# relates: [clutch/drain.py, clutch/runner.py, clutch/serve.py]
# owner: engine
# verified: 45e4e081
# hash: 9a8635351baac05bd050b1b710436edb7c24f51129abc37d306176c45f5f812f
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import drain, runner


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
    d.retro = AsyncMock(side_effect=result if isinstance(result, Exception) else None, return_value=result)
    d.retro.due = due
    d.retro.abort_current = AsyncMock()
    if isinstance(result, Exception):
        with pytest.raises(RuntimeError, match="retro"):
            await d._run_retro()
    else:
        await d._run_retro()
    # Wrong: keep an unforced path for an operator request.
    d.retro.assert_awaited_once_with(forced=True)
    assert log.events == events("retro_check", outcome)
