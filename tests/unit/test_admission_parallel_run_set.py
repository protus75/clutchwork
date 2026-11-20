# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test admission parallel run set
# relates: [clutch/__main__.py, clutch/daemon.py, clutch/scheduler.py, clutch/serve.py, tests/dispatch_settle.py]
# owner: engine
# verified: 0a308920
# hash: 6fe70842fe5f5e7311bc2c2747ad9a9abbdb32d265c9bac97b3681c65023710a
import asyncio
from types import SimpleNamespace

import pytest

from clutch.daemon import DaemonAdmission


@pytest.mark.asyncio
async def test_slots_and_waiting_merge():
    started = {stem: asyncio.Event() for stem in "abc"}
    release = {stem: asyncio.Event() for stem in "abc"}
    merging = asyncio.Event()
    resume = asyncio.Event()

    async def dispatch(ticket):
        started[ticket.stem].set()
        if ticket.stem == "a":
            await merging.wait()
            async with admission.waiting_for_merge():
                await resume.wait()
        await release[ticket.stem].wait()
        return ticket.stem

    admission = DaemonAdmission(dispatch, max_runs=2)
    tasks = [asyncio.create_task(admission.dispatch(SimpleNamespace(stem=s))) for s in "abc"]
    await started["a"].wait()
    await started["b"].wait()
    await asyncio.sleep(0)
    assert not started["c"].is_set()
    merging.set()
    await started["c"].wait()
    assert admission.occupied() and set(admission.runs) == {"a", "b", "c"}
    release["b"].set()
    release["c"].set()
    resume.set()
    release["a"].set()
    assert await asyncio.gather(*tasks) == list("abc")
    assert not admission.occupied()


@pytest.mark.asyncio
async def test_merge_wait_allows_mutation():
    entered, finish = asyncio.Event(), asyncio.Event()

    async def dispatch(ticket):
        async with admission.waiting_for_merge():
            entered.set()
            await finish.wait()
        return ticket.stem

    admission = DaemonAdmission(dispatch)
    task = asyncio.create_task(admission.dispatch(SimpleNamespace(stem="a")))
    await entered.wait()
    async with asyncio.timeout(1):
        async with admission.mutations():
            assert admission.occupied() and "a" in admission.runs
    finish.set()
    assert await task == "a"


def test_parallel_configuration():
    from clutch.__main__ import _admission_max_runs

    assert _admission_max_runs(SimpleNamespace(enabled=False, max_runs=4)) == 1
    assert _admission_max_runs(SimpleNamespace(enabled=True, max_runs=4)) == 4


@pytest.mark.asyncio
async def test_exclusive_waits_and_blocks_dispatch():
    entered, release, gate_entered, gate_release = (asyncio.Event() for _ in range(4))
    starts = []

    async def dispatch(ticket):
        starts.append(ticket.stem)
        entered.set()
        await release.wait()
        return ticket.stem

    admission = DaemonAdmission(dispatch, max_runs=2)
    first = asyncio.create_task(admission.dispatch(SimpleNamespace(stem="first")))
    await entered.wait()

    async def mutate():
        async with admission.mutations():
            gate_entered.set()
            await gate_release.wait()

    gate = asyncio.create_task(mutate())
    await asyncio.sleep(0)
    assert not gate_entered.is_set()
    release.set()
    await first
    await gate_entered.wait()
    attempted = asyncio.Event()
    acquire = admission._acquire_run

    async def tracked_acquire():
        attempted.set()
        await acquire()

    admission._acquire_run = tracked_acquire
    second = asyncio.create_task(admission.dispatch(SimpleNamespace(stem="second")))
    await attempted.wait()
    await asyncio.sleep(0)
    assert starts == ["first"]
    gate_release.set()
    await gate
    assert await second == "second"


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["startup", "sweep"])
async def test_core_exclusive_blocks_admission(operation):
    from clutch.daemon import DaemonCore

    entered, release, started = (asyncio.Event() for _ in range(3))

    class Restart:
        async def startup(self):
            entered.set()
            await release.wait()

        async def sweep_orphans(self):
            entered.set()
            await release.wait()
            return ["orphan"]

    async def dispatch(ticket):
        started.set()
        return ticket.stem

    admission = DaemonAdmission(dispatch)
    admission.restart = Restart()
    core = DaemonCore(admission, None, None)
    work = asyncio.create_task(core.startup() if operation == "startup" else core.sweep_orphans())
    await entered.wait()
    attempted = asyncio.Event()
    acquire = admission._acquire_run

    async def tracked_acquire():
        attempted.set()
        await acquire()

    admission._acquire_run = tracked_acquire
    run = asyncio.create_task(admission.dispatch(SimpleNamespace(stem="blocked")))
    await attempted.wait()
    await asyncio.sleep(0)
    assert not started.is_set()
    release.set()
    result = await work
    assert result == (None if operation == "startup" else ["orphan"])
    assert await run == "blocked"


@pytest.mark.asyncio
async def test_scheduler_occupied_during_dispatch(monkeypatch, tmp_path):
    from clutch import scheduler as scheduler_module
    from clutch.scheduler import Scheduler

    entered, release = asyncio.Event(), asyncio.Event()

    async def dispatch(ticket):
        entered.set()
        await release.wait()

    async def sha(stem):
        return "sha"

    monkeypatch.setattr(scheduler_module, "write_queue", lambda *args: None)
    scheduler = Scheduler(
        SimpleNamespace(read=lambda: []),
        dispatch,
        state_dir=tmp_path,
        fs=None,
        clock=None,
        caps=lambda: None,
        ticket_sha=sha,
        quarantined=set,
        drought_parked=set,
        completed_unmerged=lambda: 0,
        max_unmerged=1,
    )
    ticket = SimpleNamespace(stem="a", frontmatter=SimpleNamespace(state="confirmed", priority="P2"), depends=(), runs_before=())
    scheduler.update(ticket)
    from tests.dispatch_settle import dispatch_settled

    task = asyncio.create_task(dispatch_settled(scheduler))
    await entered.wait()
    assert scheduler.occupied()
    release.set()
    assert await task is ticket
    assert not scheduler.occupied()


@pytest.mark.asyncio
async def test_watch_publication_excludes_runs():
    from clutch.serve import Serve

    publishing, release, started = (asyncio.Event() for _ in range(3))

    async def dispatch(ticket):
        started.set()
        return ticket.stem

    class Response:
        async def wait(self, work):
            return await work

    class Watcher:
        _waits = {}

        async def run(self, changes):
            async for stem in changes:
                assert stem == "changed"
                publishing.set()
                await release.wait()
                break

    async def scan():
        return {"changed": "text"}

    admission = DaemonAdmission(dispatch)
    owner = SimpleNamespace(responses=[None, None, None, Response()], scan=scan, core=SimpleNamespace(admission=admission, watcher=Watcher()))
    watch = asyncio.create_task(Serve.watch(owner))
    await publishing.wait()
    attempted = asyncio.Event()
    acquire = admission._acquire_run

    async def tracked_acquire():
        attempted.set()
        await acquire()

    admission._acquire_run = tracked_acquire
    run = asyncio.create_task(admission.dispatch(SimpleNamespace(stem="later")))
    await attempted.wait()
    await asyncio.sleep(0)
    assert not started.is_set()
    release.set()
    await watch
    assert await run == "later"


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["run", "gate"])
async def test_repeated_cancellation_during_contended_release(kind):
    entered = asyncio.Event()

    async def dispatch(ticket):
        entered.set()
        await asyncio.Event().wait()

    admission = DaemonAdmission(dispatch)

    async def hold_gate():
        async with admission.exclusive():
            entered.set()
            await asyncio.Event().wait()

    releasing = asyncio.Event()
    release = admission._release_run if kind == "run" else admission._release_exclusive

    async def tracked_release():
        releasing.set()
        await release()

    if kind == "run":
        admission._release_run = tracked_release
    else:
        admission._release_exclusive = tracked_release
    task = asyncio.create_task(admission.dispatch(SimpleNamespace(stem="first")) if kind == "run" else hold_gate())
    await entered.wait()
    await admission._condition.acquire()
    task.cancel()
    await releasing.wait()
    task.cancel()
    admission._condition.release()
    with pytest.raises(asyncio.CancelledError):
        await task

    async def complete(ticket):
        return ticket.stem

    admission._dispatch = complete
    async with asyncio.timeout(1):
        assert await admission.dispatch(SimpleNamespace(stem="next")) == "next"
        async with admission.exclusive():
            assert not admission.occupied()
