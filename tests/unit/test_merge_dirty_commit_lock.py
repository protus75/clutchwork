# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify dirty status waits for staged lifts to commit.
# relates: [clutch/merge.py]
# owner: clutch/merge.py
# verified: 407dfd0f
# hash: 7e5c9ffa80b0ae74d8f79dc2a0e9067811383c1853391c9130981fa9c2359a2a
import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch.merge import dirty_overlap


@pytest.mark.asyncio
async def test_status_waits_for_commit_lock():
    reached_main = asyncio.Event()
    commit_lock = asyncio.Lock()

    @asynccontextmanager
    async def main_write():
        reached_main.set()
        yield

    git = SimpleNamespace(main_write=main_write, _commit_lock=commit_lock, status_porcelain=AsyncMock(return_value="M  lifted.md\0"), diff_names=AsyncMock(return_value=[]))
    async with commit_lock:
        task = asyncio.create_task(dirty_overlap(SimpleNamespace(git=git, repo="repo"), "work"))
        await reached_main.wait()
        # Without the commit lock, status sees this staged lift and refuses it.
        assert git.status_porcelain.await_count == 0
        git.status_porcelain.return_value = ""
    assert await task == []
    assert git.status_porcelain.await_args.args == ("repo", "-z")
