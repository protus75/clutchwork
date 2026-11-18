"""Admission detects both a held slot and a queued handoff."""

import asyncio

import pytest

from clutch.daemon import DaemonAdmission


@pytest.mark.asyncio
async def test_busy_including_handoff():
    admission = DaemonAdmission(None)
    # Wrong: treating an idle lock as occupied.
    assert admission.busy() is False
    await admission._slot.acquire()
    # Wrong: checking only waiters and ignoring the holder.
    assert admission.busy() is True
    waiter = asyncio.create_task(admission._slot.acquire())
    await asyncio.sleep(0)
    admission._slot.release()
    try:
        # Wrong: locked() alone misses the handoff before the waiter runs.
        assert admission._slot.locked() is False
        assert admission.busy() is True
    finally:
        await waiter
        admission._slot.release()
