"""Verdict settlement owns the idle recovery boundary, including on failure."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit test checking that Serve.verdicts marks restart recovery as owned while verdicts settle, and releases it on both success and failure
# relates: [clutch/__main__.py, clutch/runner.py, clutch/serve.py, tests/unit/test_serve_idle_poll.py]
# owner: engine
# verified: 10f08d74
# hash: 6cc56f140b40646536a40344ba8ff72e71b55d2453ebb6411d226f3714da5cc8

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from clutch import __main__ as cli
from clutch import serve
from clutch.runner import Checkout
from tests.git_fake import GitFake
from tests.unit.test_serve_idle_poll import PollFinished, Response, stop_poll


@pytest.mark.asyncio
@pytest.mark.parametrize("raises", [False, True])
async def test_verdict_ownership_clears(monkeypatch, tmp_path, raises):
    core = MagicMock()
    core.control._recover = [].clear
    core.admission.occupied.return_value = False
    core.control.projection.kill_requested = False
    monkeypatch.setattr(cli, "build_daemon_core", lambda *a, **k: core)
    monkeypatch.setattr(cli, "build_driver", MagicMock())
    monkeypatch.setattr(cli, "build_notifications", MagicMock())
    monkeypatch.setattr(serve, "engine_log", MagicMock())
    monkeypatch.setattr(serve.Redactor, "from_config", MagicMock())
    checkout = Checkout(repo=tmp_path, config=SimpleNamespace(state_dir=tmp_path), env={}, exec_=None, fs=MagicMock(), clock=MagicMock(), journal=MagicMock(), git=GitFake(), sleep=stop_poll)
    owner = serve.Serve(checkout, read=lambda _: None, stems=lambda: [])
    owner.responses = [Response() for _ in range(5)]
    entered, release = asyncio.Event(), asyncio.Event()

    async def settle(_):
        entered.set()
        await release.wait()
        if raises:
            raise ValueError("verdict failed")

    core.control.inbox.settle_admissions = settle
    core.control.poll = lambda: None
    task = asyncio.create_task(owner.verdicts())
    await entered.wait()
    assert core.restart.owned() is True  # Omitting verdict ownership exposes the live effect.
    release.set()
    with pytest.raises(ValueError if raises else PollFinished):
        await task
    assert core.restart.owned() is False  # A missing finally would strand recovery after failure.
