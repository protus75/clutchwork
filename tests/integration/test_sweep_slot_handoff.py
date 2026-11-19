"""The orphan sweep skips a slot handed to a queued operation."""

import asyncio

import pytest

from clutch.daemon import DaemonAdmission, DaemonCore


@pytest.mark.asyncio
async def test_sweep_skips_queued_handoff():
    admission = DaemonAdmission(None)
    core = DaemonCore(admission, None, None)
    first = admission.exclusive()
    await first.__aenter__()
    second = admission.exclusive()
    waiter = asyncio.create_task(second.__aenter__())
    await asyncio.sleep(0)
    await first.__aexit__(None, None, None)
    try:
        # Wrong: acquiring behind the waiter blocks instead of skipping the sweep.
        assert await asyncio.wait_for(core.sweep_orphans(), timeout=1) == []
    finally:
        await waiter
        await second.__aexit__(None, None, None)
