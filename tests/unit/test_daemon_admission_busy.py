"""Admission detects both a held slot and a queued handoff."""

import asyncio

import pytest

from clutch.daemon import DaemonAdmission


@pytest.mark.asyncio
async def test_busy_including_handoff():
    admission = DaemonAdmission(None)
    # Wrong: treating an idle lock as occupied.
    assert admission.busy() is False
    first = admission.exclusive()
    await first.__aenter__()
    # Wrong: checking only waiters and ignoring the holder.
    assert admission.busy() is True
    second = admission.exclusive()
    waiter = asyncio.create_task(second.__aenter__())
    await asyncio.sleep(0)
    await first.__aexit__(None, None, None)
    try:
        # Wrong: locked() alone misses the handoff before the waiter runs.
        assert admission.busy() is True
    finally:
        await waiter
        await second.__aexit__(None, None, None)
