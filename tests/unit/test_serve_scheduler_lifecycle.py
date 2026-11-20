# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test serve scheduler lifecycle
# relates: [clutch/daemon.py, clutch/serve.py, tests/fakes.py, tests/unit/test_supervise_idle_hooks.py]
# owner: engine
# verified: 9a610809
# hash: 55aea33441d745691f1a20c1aee69608a00a1fb4c51572f12cd7126f4706a5a7
import asyncio
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock

import pytest

from clutch import serve
from clutch.daemon import DaemonAdmission
from tests.fakes import turn
from tests.unit.test_supervise_idle_hooks import Checkout, EndPoll, serve_rig


@pytest.mark.asyncio
@pytest.mark.parametrize("stopping", [False, True])
async def test_failure_surfaces_before_pause_or_stop(tmp_path, monkeypatch, stopping):
    obj = serve_rig(tmp_path, monkeypatch, Checkout(tmp_path, None, None), None)
    obj.control.projection.pause_id = "paused"
    obj.stopping = stopping
    error = ValueError("run failed")
    obj.core.scheduler.raise_failure = Mock(side_effect=error)
    with pytest.raises(ValueError) as caught:
        await obj.dispatch()
    assert caught.value is error  # Wrong: failing to surface the original run error while paused/stopping.
    obj.core.scheduler.dispatch_next.assert_not_awaited()  # Wrong: selecting before draining pending failures.


@pytest.mark.asyncio
@pytest.mark.parametrize("exclusive", [False, True])
async def test_busy_runs_refill_without_idle_work(tmp_path, monkeypatch, exclusive):
    obj = serve_rig(tmp_path, monkeypatch, Checkout(tmp_path, None, None), None)
    obj.core.admission.busy = Mock(return_value=True)
    obj.core.admission.exclusive_pending = Mock(return_value=exclusive)
    supervise = AsyncMock()
    monkeypatch.setattr(serve, "supervise_idle", supervise)
    with pytest.raises(EndPoll):
        await obj.dispatch()
    assert obj.core.scheduler.dispatch_next.await_count == int(not exclusive)  # Wrong: busy blocks all refill, or exclusive work permits selection.
    supervise.assert_not_awaited()  # Wrong: supervising during running work.
    obj.check_upgrade.assert_not_awaited()  # Wrong: moving upgrade checks out of the idle guard.
    obj.core.admission.busy.assert_called_once_with()  # Wrong: resampling admission after supervision.
    obj.core.admission.exclusive_pending.assert_called_once_with()


@pytest.mark.asyncio
async def test_exclusive_pending_distinguishes_runs_waiters_and_holder():
    started, release, entered, finish = (asyncio.Event() for _ in range(4))

    async def run(_):
        started.set()
        await release.wait()

    admission = DaemonAdmission(run)

    async def exclusive():
        async with admission.exclusive():
            entered.set()
            await finish.wait()

    running = asyncio.create_task(admission.dispatch(NS(stem="run")))
    waiting = None
    try:
        await started.wait()
        assert admission.busy() and not admission.exclusive_pending()  # Wrong: reporting run slots as exclusive.
        waiting = asyncio.create_task(exclusive())
        await turn()
        assert admission.exclusive_pending() and not entered.is_set()  # Wrong: forgetting exclusive waiters.
        release.set()
        await entered.wait()
        assert admission.exclusive_pending()  # Wrong: reporting only waiters, not the holder.
        finish.set()
        await waiting
        await running
        assert not admission.exclusive_pending()  # Wrong: retaining the exclusive flag after release.
    finally:
        release.set()
        finish.set()
        await asyncio.gather(running, *([waiting] if waiting else []))


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [False, True])
async def test_cleanup_closes_scheduler_after_workers_and_finishes_on_error(monkeypatch, failure):
    obj = object.__new__(serve.Serve)
    calls = []
    error = ValueError("close failed")
    obj.ready = asyncio.Event()
    obj.ready.set()
    obj.control = NS(projection=object())
    monkeypatch.setattr(serve, "replace", lambda value, **kwargs: value)

    async def stop(_):
        calls.append("abort")

    async def workers(_):
        calls.append("workers")

    async def close():
        calls.append("scheduler")
        if failure:
            raise error

    async def notify():
        calls.append("notifications")

    async def background():
        calls.append("background")

    monkeypatch.setattr(serve, "_stop_workers", lambda tasks: asyncio.create_task(workers(tasks)))
    obj.stopper = NS(stop=stop)
    obj.workers = []
    obj.core = NS(scheduler=NS(close=close))
    obj.notifications = NS(close=notify)
    obj.background = background()
    obj.observation = background()
    obj.writers = {"work": NS(continuations={"work": object()})}
    if failure:
        with pytest.raises(ValueError) as caught:
            await obj.cleanup()
        assert caught.value is error  # Wrong: swallowing or replacing the scheduler close error.
    else:
        await obj.cleanup()
    assert [call for call in calls if call != "background"] == ["abort", "workers", "scheduler", "notifications"]  # Wrong: closing before stopping workers or skipping notifications after failure.
    assert calls.count("background") == 2  # Wrong: omitting background cleanup.
    assert obj.writers["work"].continuations == {}  # Wrong: close failure bypasses writer clearing.
