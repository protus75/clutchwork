import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from clutch import __main__ as entry
from clutch import control, runner
from clutch.lockfile import LockHeld


def test_verdict_submitted_names_the_clutch_verb(tmp_path, monkeypatch, capsys):
    request_id = "d8cdcd906b374c46bc7b46cc9f9978a3"
    checkout = SimpleNamespace(repo=tmp_path, journal=SimpleNamespace(read=lambda: []), config=SimpleNamespace(state_dir=tmp_path / "state"), git=None, fs=None)
    monkeypatch.setattr(runner, "verdict", AsyncMock(side_effect=LockHeld(tmp_path / "clutch.lock", {"verb": "drain"})))
    monkeypatch.setattr(runner, "ticket_pending", AsyncMock(return_value=False))
    monkeypatch.setattr(control, "read_active", lambda *args: ("life-1", None))
    monkeypatch.setattr(control, "publish_request", lambda *args: None)
    monkeypatch.setattr(entry, "uuid4", lambda: SimpleNamespace(hex=request_id))

    asyncio.run(entry._verdict(checkout, "sample", "confirm", Mock(), True, False))
    assert capsys.readouterr().out.splitlines()[-1] == f"confirm submitted: {request_id} -- `clutch view status` shows the outcome"
