"""Scan and publication synchronize without excluding running implementations."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify scan and watch locks beside running implementations.
# relates: [clutch/serve.py, tests/unit/test_serve_idle_poll.py]
# owner: engine
# verified: 4296219b
# hash: 8ae56879b9309e545af882a2f49e698454be13a1608bbd9622e49911bf26983f

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import serve
from tests.unit.test_serve_idle_poll import owner  # noqa: F401


@pytest.mark.asyncio
async def test_scan_lock_and_stop(owner, monkeypatch):
    lock = asyncio.Lock()
    owner.checkout.git.main_write = lambda: lock
    reads = []
    owner.stems = lambda: ["changed"]
    owner.read = lambda stem: reads.append(lock.locked()) or "changed text"
    intake = AsyncMock()
    monkeypatch.setattr(serve, "intake", intake)
    # The fixture holds one admission slot; a gate would wait for that run.
    async with asyncio.timeout(1):
        result = await owner.scan()
    assert result == {"changed": "changed text"}
    assert owner.entries == []
    assert reads[-2:] == [True, True]
    owner.stopping = True
    owner.scan_snapshot = None
    intake.reset_mock()
    assert await owner.scan() == {}
    intake.assert_not_awaited()


@pytest.mark.asyncio
async def test_publication_serializes_selection(owner):
    slot = owner.core.scheduler._slot
    selected, release, published = (asyncio.Event() for _ in range(3))
    order = []

    async def selection():
        async with slot:
            selected.set()
            await release.wait()
            order.append("selection")

    class Watcher:
        _waits = {}

        async def run(self, changes):
            try:
                stem = await anext(changes)
                assert slot.locked()
                order.append(stem)
                published.set()
            finally:
                await changes.aclose()

    owner.scan = AsyncMock(return_value={"changed": "new"})
    owner.core.watcher = Watcher()
    task = asyncio.create_task(selection())
    await selected.wait()
    watch = asyncio.create_task(owner.watch())
    await asyncio.sleep(0)
    assert not published.is_set()
    release.set()
    await task
    await watch
    assert order == ["selection", "changed"]
    assert owner.entries == []
