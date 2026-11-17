import asyncio

import pytest

from clutch.serve import Responsiveness


def test_round_trip():
    r = Responsiveness()
    assert not r.responsive()
    r.ask()
    assert not r.responsive()
    r.reply()
    assert r.responsive()


@pytest.mark.asyncio
async def test_wait_answers_and_returns_or_raises():
    r = Responsiveness()
    started, release, answered = asyncio.Event(), asyncio.Event(), asyncio.Event()
    reply = r.reply

    def observe_reply():
        reply()
        answered.set()

    r.reply = observe_reply

    async def work():
        started.set()
        await release.wait()
        return "finished"

    task = asyncio.create_task(r.wait(work()))
    await started.wait()
    r.ask()
    await answered.wait()
    assert r.responsive() and not task.done()
    release.set()
    assert await task == "finished"
    error = ValueError("work failed")

    async def fail():
        raise error

    with pytest.raises(ValueError) as caught:
        await r.wait(fail())
    assert caught.value is error


@pytest.mark.asyncio
async def test_wait_cancels_owned_work():
    r = Responsiveness()
    started, cancelled = asyncio.Event(), asyncio.Event()

    async def work():
        started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.set()
            raise

    task = asyncio.create_task(r.wait(work()))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert cancelled.is_set()
