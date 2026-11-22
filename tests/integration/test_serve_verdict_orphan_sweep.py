"""An idle sweep cannot reap an in-flight draft confirmation."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Integration test checking that an idle maintenance sweep does not abandon or orphan-alert a draft confirmation that is still in progress, and that the confirmation still completes
# relates: [clutch/__main__.py, clutch/control.py, clutch/daemon.py, clutch/journal.py, clutch/restart.py, clutch/runner.py, clutch/serve.py, tests/fakes.py]
# owner: engine
# verified: 10f08d74
# hash: 45b4439db1caef54a708e91b6ab81d79d8fd10052babd583cf0b3ff37e6052fe

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from clutch import __main__ as cli
from clutch import serve
from clutch.control import ControlInbox
from clutch.daemon import DaemonAdmission, DaemonCore
from clutch.journal import EventType
from clutch.restart import Restart
from clutch.runner import Checkout
from tests.fakes import FakeJournal
from tests.git_fake import GitFake
from tests.unit.test_serve_idle_poll import PollFinished, Response, stop_poll


@pytest.mark.asyncio
async def test_confirmation_survives_idle_sweep(tmp_path, monkeypatch):
    journal = FakeJournal()
    checkout = Checkout(
        repo=tmp_path,
        config=SimpleNamespace(state_dir=tmp_path, worktree_root=tmp_path),
        env={},
        exec_=None,
        fs=MagicMock(),
        clock=MagicMock(),
        journal=journal,
        git=GitFake(),
        sleep=stop_poll,
    )
    timers = SimpleNamespace(fire_due=lambda: None)
    restart = Restart(checkout, timers=timers, owned=lambda: False)
    admission = DaemonAdmission(None)
    admission.restart = restart
    scheduler = MagicMock()
    scheduler.occupied.return_value = False
    control = MagicMock()
    control._recover = [].clear
    control.projection.kill_requested = False
    core = DaemonCore(admission, scheduler, MagicMock(), control)
    monkeypatch.setattr(cli, "build_daemon_core", lambda *a, **k: core)
    monkeypatch.setattr(cli, "build_driver", MagicMock())
    monkeypatch.setattr(cli, "build_notifications", MagicMock())
    monkeypatch.setattr(serve, "engine_log", MagicMock())
    monkeypatch.setattr(serve.Redactor, "from_config", MagicMock())
    owner = serve.Serve(checkout, read=lambda _: None, stems=lambda: [])
    owner.responses = [Response() for _ in range(5)]
    owner.box = SimpleNamespace(recover=lambda: None)
    owner.checkpoint = SimpleNamespace(poll=AsyncMock())
    owner.heartbeat = SimpleNamespace(cycle=lambda: None)
    owner.notifications = SimpleNamespace(poll=lambda: None)
    control.poll = lambda: None
    control.inbox = ControlInbox(journal=journal, lifecycle_id="life", holds=lambda: set(), apply=lambda _: None, files=lambda: [], read=lambda _: b"", known=lambda _: True)
    journal.append(
        EventType.SIGNAL,
        {
            "kind": "control_decision",
            "request_id": "confirm-draft",
            "lifecycle_id": "life",
            "verb": "confirm",
            "hold_id": None,
            "decision": "accepted",
            "reason": "accepted",
            "stem": "draft",
            "actor": "operator",
        },
    )
    entered, release = asyncio.Event(), asyncio.Event()
    state = {"draft": "draft"}

    async def verdict(stem, verb, key, actor):
        entered.set()
        await release.wait()
        state[stem] = "confirmed"
        return {"refusal": None}

    owner.apply_verdict = verdict
    task = asyncio.create_task(owner.verdicts())
    try:
        await entered.wait()
        key = "ticket-plane/draft/confirm/confirm-draft"
        assert [e.type for e in journal.read() if e.key == key] == [EventType.EFFECT_INTENT]
        await owner.maintenance()
        release.set()
        with pytest.raises(PollFinished):
            await task
        events = [e for e in journal.read() if e.ticket == "draft"]
        assert state["draft"] == "confirmed"
        assert not any(e.type == EventType.STATE_TRANSITION and e.body.get("to") == "abandoned" for e in events)
        assert not any(e.body.get("reason") == "orphaned run" for e in events)
        assert any(e.type == EventType.EFFECT_COMPLETION and e.key == key and e.body["result"]["refusal"] is None for e in events)
    finally:
        release.set()
        if not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
