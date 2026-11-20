import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from clutch.config import Caps, Parallel
from clutch.journal import EventType
from tests.fakes import turn
from tests.unit.test_scheduler_parallel_fill import rig, ticket
from tests.unit.test_supervise_idle_point import event


async def returned(scheduler):
    selection = asyncio.create_task(scheduler.dispatch_next())
    try:
        await turn()
        # Wrong: selection awaits the blocked run instead of returning its ticket.
        assert selection.done()
        return await selection
    finally:
        if not selection.done():
            selection.cancel()
            await asyncio.gather(selection, return_exceptions=True)


@pytest.mark.asyncio
@pytest.mark.parametrize("parallel", [False, True])
async def test_slot_cap_precedes_selection(parallel):
    items = [ticket(stem) for stem in ("a", "b", "c")]
    obj, _, _, _ = rig(items, Parallel(enabled=parallel, max_runs=2))
    release = asyncio.Event()
    calls = []

    async def dispatch(item):
        calls.append(item.stem)
        await release.wait()

    obj.dispatch = dispatch
    obj.caps = Caps
    obj.select = Mock(return_value=True)
    obj.ticket_sha = AsyncMock(return_value="changed")
    # The waiting candidate passes all filters and requires a blob read if eligibility runs.
    obj.journal.read = lambda: [event(EventType.STATE_TRANSITION, stem="c", body={"to": "running", "ticket_sha": "old"}), event(EventType.STATE_TRANSITION, stem="c", body={"to": "premise_failed"})]
    capacity = 2 if parallel else 1
    try:
        for item in items[:capacity]:
            assert await returned(obj) is item  # Wrong: selecting another eligible stem.
        obj.select.reset_mock()
        obj.ticket_sha.reset_mock()
        assert await returned(obj) is None  # Wrong: exceeding the slot cap.
        assert set(obj.flying) == set(calls) == {t.stem for t in items[:capacity]}  # Wrong: clearing ownership on return or starting an extra run.
        obj.select.assert_not_called()  # Wrong: checking capacity after eligibility side effects.
        obj.ticket_sha.assert_not_awaited()  # Wrong: fetching parked blobs while full.
        release.set()
        while obj.flying:
            await turn()
        assert await returned(obj) is items[capacity]  # Wrong: never releasing capacity on completion.
    finally:
        await obj.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("consumer", ["dispatch_next", "raise_failure", "close"])
async def test_failure_is_owned_until_raised_once(consumer):
    item = ticket("broken")
    obj, _, _, _ = rig([item])
    error = ValueError("run failed")

    async def fail(_):
        raise error

    obj.dispatch = fail
    assert await returned(obj) is item  # Wrong: propagating the run error from its starting call.
    while obj.flying:
        await turn()
    assert obj.occupied()  # Wrong: ignoring pending failures in idle checks.
    with pytest.raises(ValueError) as caught:
        result = getattr(obj, consumer)()
        if consumer != "raise_failure":
            await result
    assert caught.value is error  # Wrong: replacing the original exception.
    assert not obj.occupied()  # Wrong: retaining an already delivered failure.
    assert await obj.dispatch_next() is None  # Wrong: delivering a failure twice.
    await obj.close()  # Wrong: close re-delivers the same failure.


@pytest.mark.asyncio
async def test_close_cancels_and_awaits_every_run():
    obj, _, _, _ = rig([ticket("a"), ticket("b")], Parallel(enabled=True, max_runs=2))
    entered = {stem: asyncio.Event() for stem in "ab"}
    cleaned = set()

    async def block(item):
        entered[item.stem].set()
        try:
            await asyncio.Event().wait()
        finally:
            await turn()
            cleaned.add(item.stem)

    obj.dispatch = block
    for _ in "ab":
        await returned(obj)
    for signal in entered.values():
        await signal.wait()
    await obj.close()
    assert cleaned == {"a", "b"}  # Wrong: cancelling only one run, or not awaiting cleanup.
    assert obj.flying == {} and not obj.occupied()  # Wrong: leaving cancelled run ownership behind.
    assert obj.failures == []  # Wrong: recording cancellation as a run failure.
