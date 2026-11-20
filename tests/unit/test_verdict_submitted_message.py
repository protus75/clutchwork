# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test verdict submitted message
# relates: [clutch/__main__.py, clutch/control.py, clutch/lockfile.py, clutch/runner.py]
# owner: engine
# verified: 9a610809
# hash: 96b2d3ee7772b3e0207883e7e653113e026beb57b4b90ed19637ea63df7823fa
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
