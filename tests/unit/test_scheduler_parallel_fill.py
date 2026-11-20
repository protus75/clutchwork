import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from clutch.config import Config, Parallel
from clutch.daemon import daemon_core
from clutch.drain import SKIP_LIMIT
from clutch.scheduler import Scheduler
from clutch.tickets import Frontmatter, Ticket


def ticket(stem, priority="P2", depends=(), path=None):
    return Ticket(
        stem=stem,
        frontmatter=Frontmatter(state="confirmed", source="human", priority=priority, kind="feature"),
        sections={},
        depends=depends,
        context=(),
        on_demand=(),
        scope_fence=(path or stem,),
        verification=(),
        expected_minutes=20,
        stuck_minutes=40,
        runs_before=(),
    )


def rig(items, parallel=Parallel()):
    writes, calls, logs = [], [], []

    async def dispatch(t):
        calls.append(t)

    async def sha(stem):
        return "sha"

    obj = Scheduler(
        NS(read=lambda: []),
        dispatch,
        state_dir=Path("/state"),
        fs=NS(write=lambda p, data: writes.append(json.loads(data))),
        clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
        caps=lambda: None,
        ticket_sha=sha,
        quarantined=set,
        drought_parked=set,
        completed_unmerged=lambda: 0,
        max_unmerged=1,
    )
    obj.parallel = lambda: parallel
    obj.log = lambda *args, **kwargs: logs.append((args, kwargs))
    for item in items:
        obj.update(item)
    return obj, writes, calls, logs


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled,expected,order", [(False, "short", ["short", "long"]), (True, "long", ["long", "short"])])
async def test_order(enabled, expected, order):
    long, short = ticket("long"), ticket("short", "P1")
    children = [ticket("child1", depends=("long",)), ticket("child2", depends=("long",))]
    obj, writes, calls, logs = rig([long, short, *children], Parallel(enabled=enabled))
    assert (await obj.dispatch_next()).stem == expected
    assert [t.stem for t in calls] == [expected]
    assert writes[0]["order"] == order
    assert logs == []
    assert obj.flying == {}


@pytest.mark.asyncio
async def test_p0_precedes_chain():
    long, short, urgent = ticket("long"), ticket("short", "P1"), ticket("urgent", "P0")
    obj, writes, _, _ = rig([long, short, urgent, ticket("child1", depends=("long",)), ticket("child2", depends=("long",))], Parallel(enabled=True))
    assert await obj.dispatch_next() is urgent
    assert writes[0]["order"] == ["urgent", "long", "short"]


@pytest.mark.asyncio
async def test_overlap_skip_and_queue():
    blocked, later, busy = ticket("blocked", "P1", path="src/file"), ticket("later", path="docs"), ticket("busy", path="src")
    obj, writes, calls, logs = rig([blocked, later], Parallel(enabled=True, max_runs=3))
    obj.flying[busy.stem] = busy
    assert await obj.dispatch_next() is later
    assert calls == [later]
    assert obj.skips == {"blocked": 1}
    assert logs == [(("dispatch_skip",), {"stem": "blocked", "count": 1})]
    assert writes[0]["order"] == ["later", "blocked"]
    assert obj.flying == {"busy": busy}


@pytest.mark.asyncio
async def test_barrier_and_capacity():
    blocked, later, busy = ticket("blocked", "P1", path="src/file"), ticket("later", path="docs"), ticket("busy", path="src")
    obj, writes, calls, logs = rig([blocked, later], Parallel(enabled=True, max_runs=2))
    obj.flying[busy.stem] = busy
    obj.skips = {"blocked": SKIP_LIMIT}
    assert await obj.dispatch_next() is None
    assert calls == [] and writes == []
    assert obj.skips == {"blocked": SKIP_LIMIT + 1}
    assert logs == [(("dispatch_skip",), {"stem": "blocked", "count": SKIP_LIMIT + 1})]
    obj.flying["other"] = ticket("other")
    assert await obj.dispatch_next() is None
    assert obj.skips == {"blocked": SKIP_LIMIT + 1} and len(logs) == 1 and calls == []


@pytest.mark.asyncio
async def test_shared_path_and_dispatch_failure_cleanup():
    candidate, busy = ticket("candidate", path="src/file"), ticket("busy", path="src")
    obj, _, calls, logs = rig([candidate], Parallel(enabled=True, max_runs=2, shared_paths=["src"]))
    obj.flying["busy"] = busy

    async def fail(t):
        calls.append(t)
        assert obj.flying == {"busy": busy, "candidate": candidate}
        raise ValueError("dispatch")

    obj.dispatch = fail
    with pytest.raises(ValueError, match="dispatch"):
        await obj.dispatch_next()
    assert calls == [candidate] and obj.skips == {} and logs == []
    assert obj.flying == {"busy": busy}


@pytest.mark.asyncio
async def test_failed_config_keeps_pending():
    item = ticket("item")
    obj, _, calls, _ = rig([item])

    def fail():
        raise ValueError("load")

    obj.parallel = fail
    with pytest.raises(ValueError, match="load"):
        await obj.dispatch_next()
    assert obj.pending == {"item": item} and calls == []
    obj.parallel = Parallel
    assert await obj.dispatch_next() is item
    assert calls == [item]


def test_daemon_wires_live_parallel_and_log():
    parallel = Parallel(enabled=True, max_runs=3)
    config = Config.model_construct(scheduler=NS(parallel=parallel))

    def log(*args, **kwargs):
        return None

    core = daemon_core(
        Path("/repo"),
        journal=NS(read=lambda: []),
        state_dir=Path("/state"),
        fs=NS(),
        load=lambda: config,
        bind=lambda _: None,
        read=lambda _: None,
        clock=lambda: None,
        sleep=lambda _: None,
        debounce=0,
        ticket_sha=lambda _: None,
        quarantined=set,
        drought_parked=set,
        completed_unmerged=lambda: 0,
        max_unmerged=1,
        log=log,
    )
    assert core.scheduler.parallel() == parallel
    assert core.scheduler.log is log
