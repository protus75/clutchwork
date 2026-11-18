"""The orphan sweep skips a slot handed to a queued operation."""

import asyncio

import pytest

from clutch.daemon import DaemonAdmission, DaemonCore


@pytest.mark.asyncio
async def test_sweep_skips_queued_handoff():
    admission = DaemonAdmission(None)
    core = DaemonCore(admission, None, None)
    await admission._slot.acquire()
    waiter = asyncio.create_task(admission._slot.acquire())
    await asyncio.sleep(0)
    admission._slot.release()
    try:
        # Wrong: acquiring behind the waiter blocks instead of skipping the sweep.
        assert await asyncio.wait_for(core.sweep_orphans(), timeout=1) == []
    finally:
        await waiter
        admission._slot.release()
