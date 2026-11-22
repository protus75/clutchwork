"""Maintenance no longer emits a liveness file."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Asserts serve maintenance writes no heartbeat liveness file and that the clutch.heartbeat module and HeartbeatCycle are gone
# relates: [clutch/daemon.py, clutch/seams.py, clutch/serve.py]
# owner: clutch/serve.py
# verified: 5214eb3e
# hash: 42ab394e3a74c737b3ce2f2e30b4a5887450cd9f1f88327aaf97a1022f65ef0a

import importlib.util
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from clutch import daemon
from clutch.seams import LocalFileSystem
from clutch.serve import Serve


@pytest.mark.asyncio
async def test_maintenance_does_not_write_heartbeat(tmp_path):
    owner = Serve.__new__(Serve)
    owner.checkout = SimpleNamespace(fs=LocalFileSystem(), config=SimpleNamespace(state_dir=tmp_path))
    owner.control = SimpleNamespace(poll=Mock(), projection=SimpleNamespace(kill_requested=False))
    owner.stopping = False
    owner.core = SimpleNamespace(restart=SimpleNamespace(timers=SimpleNamespace(fire_due=Mock())), admission=SimpleNamespace(busy=lambda: True))
    owner.notifications = SimpleNamespace(poll=Mock())
    await owner.maintenance()
    assert not (tmp_path / "heartbeat").exists()
    assert owner.notifications.poll.called


def test_heartbeat_owners_removed():
    assert importlib.util.find_spec("clutch.heartbeat") is None
    assert not hasattr(daemon, "HeartbeatCycle")
