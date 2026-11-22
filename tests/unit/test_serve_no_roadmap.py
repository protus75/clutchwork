# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks serve's dispatch loop never reads docs/roadmap.md or calls the roadmap module, while still dispatching and running the idle supervisor step
# relates: [clutch/roadmap.py, clutch/serve.py]
# owner: engine
# verified: 18f3cf87
# hash: d6a2b67717f7a2409831e17c07547d28d69e958c8078a7ac4a77ab9e464098a0
import inspect
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, MagicMock

import pytest

from clutch import roadmap, serve


@pytest.mark.asyncio
async def test_dispatch_idle_never_reads_roadmap(monkeypatch, tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("roadmap accessed")

    for name, value in vars(roadmap).copy().items():
        if not name.startswith("_") and inspect.isfunction(value) and value.__module__ == roadmap.__name__:
            monkeypatch.setattr(roadmap, name, forbidden)
    original_read = Path.read_text

    def read(path, *args, **kwargs):
        if path == tmp_path / "docs/roadmap.md":
            forbidden()
        return original_read(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)
    assert not hasattr(serve.Serve, "driver_pending")
    assert "roadmap" not in vars(serve)
    owner = serve.Serve.__new__(serve.Serve)
    owner.responses = [NS(wait=lambda work: work)]
    owner.stopping = False
    owner.control = NS(poll=lambda: None, projection=NS(kill_requested=False, pause_id=None, stop_requested=False), inbox=NS(settle_triage=AsyncMock()), load_config=lambda: None)
    owner.core = NS(scheduler=NS(raise_failure=lambda: None, dispatch_next=AsyncMock()), admission=NS(busy=lambda: False, exclusive_pending=lambda: False))
    owner.check_upgrade = AsyncMock()
    owner.upgrade_idle = lambda: True
    owner.mutations = MagicMock()
    owner.mutations.return_value.__aenter__ = AsyncMock()
    owner.mutations.return_value.__aexit__ = AsyncMock()
    monkeypatch.setattr(serve, "supervise_idle", AsyncMock())
    monkeypatch.setattr(serve, "calibrate_when_due", lambda _: None)

    async def end(_):
        raise StopAsyncIteration

    owner.checkout = NS(repo=tmp_path, sleep=end)
    with pytest.raises(StopAsyncIteration):
        await owner.dispatch()
    owner.core.scheduler.dispatch_next.assert_awaited_once()
    serve.supervise_idle.assert_awaited_once()
