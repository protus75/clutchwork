# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify merge sections admit runs, exclude mutations and release on cancellation.
# relates: [clutch/daemon.py]
# owner: clutch/daemon.py
# verified: 407dfd0f
# hash: 158bb8a05025de5d498a9e9ec4f285e9652dab29f8ca1d70364d55ca5ab55b81
import asyncio
from types import SimpleNamespace

import pytest

from clutch.daemon import DaemonAdmission


@pytest.mark.asyncio
async def test_merging_admits_runs():
    started = {stem: asyncio.Event() for stem in ("first", "second")}
    release = asyncio.Event()

    async def dispatch(ticket):
        started[ticket.stem].set()
        await release.wait()

    admission = DaemonAdmission(dispatch, max_runs=2)
    first = asyncio.create_task(admission.dispatch(SimpleNamespace(stem="first")))
    await started["first"].wait()
    try:
        async with asyncio.timeout(1):
            async with admission.merging():
                # Exclusive-based merging would wait for first or advertise a waiter.
                assert (admission.exclusive_pending(), admission._exclusive_waiters) == (False, 0)
                assert (admission.busy(), admission.idle(), admission.mutating) == (True, False, asyncio.current_task())
                second = asyncio.create_task(admission.dispatch(SimpleNamespace(stem="second")))
                await started["second"].wait()
    finally:
        release.set()
        await first
        if "second" in locals():
            await second


@pytest.mark.asyncio
@pytest.mark.parametrize("first,second", [("merging", "exclusive"), ("exclusive", "merging"), ("merging", "merging")])
async def test_sections_exclude_each_other(first, second):
    admission = DaemonAdmission(None, max_runs=2)
    attempted, entered = asyncio.Event(), asyncio.Event()

    async def enter():
        attempted.set()
        async with getattr(admission, second)():
            entered.set()

    async with getattr(admission, first)():
        task = asyncio.create_task(enter())
        await attempted.wait()
        # Omitting either state bit from the predicate overlaps these bodies.
        assert not entered.is_set()
    async with asyncio.timeout(1):
        await task
    assert entered.is_set()


@pytest.mark.asyncio
@pytest.mark.parametrize("contended", [False, True])
async def test_cancelled_merge_releases_state(contended):
    admission = DaemonAdmission(None)
    entered, releasing = asyncio.Event(), asyncio.Event()
    original = admission._release_exclusive

    async def release():
        releasing.set()
        await original()

    admission._release_exclusive = release

    async def merge():
        async with admission.merging():
            entered.set()
            await asyncio.Event().wait()

    task = asyncio.create_task(merge())
    await entered.wait()
    # With no runs, busy/idle must still observe the held merge section.
    assert (admission.busy(), admission.idle(), admission.mutating) == (True, False, task)
    if contended:
        await admission._condition.acquire()
    task.cancel()
    if contended:
        await releasing.wait()
        task.cancel()
        admission._condition.release()
    with pytest.raises(asyncio.CancelledError):
        await task
    # A leaked flag prevents the next exclusive body from entering.
    assert (admission.mutating, admission.busy(), admission.idle()) == (None, False, True)
    async with asyncio.timeout(1):
        async with admission.exclusive():
            pass
