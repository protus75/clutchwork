# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Dirty-overlap status check waits for the commit lock so a staged lift is not refused as dirty
# relates: [clutch/merge.py]
# owner: clutch/merge.py
# verified: 452057e3
# hash: 7d91259708b717bf97323b667e3b0f4910d354613acd6bc7aad0cd2f380c2b11
import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch.merge import dirty_overlap
from tests.git_fake import GitFake


@pytest.mark.asyncio
async def test_status_waits_for_commit_lock():
    reached_main = asyncio.Event()
    commit_lock = asyncio.Lock()

    @asynccontextmanager
    async def main_write():
        reached_main.set()
        yield

    git = GitFake(main_write=main_write, status_porcelain="M  lifted.md\0", diff_names=[])
    git._commit_lock = commit_lock
    async with commit_lock:
        task = asyncio.create_task(dirty_overlap(SimpleNamespace(git=git, repo="repo"), "work"))
        await reached_main.wait()
        # Without the commit lock, status sees this staged lift and refuses it.
        assert not [call for call in git.calls if call[0] == "status_porcelain"]
        git._overrides["status_porcelain"] = ""
    assert await task == []
    assert [call for call in git.calls if call[0] == "status_porcelain"] == [("status_porcelain", ("repo", "-z"), {})]
