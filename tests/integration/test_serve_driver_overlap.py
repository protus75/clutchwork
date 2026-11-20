# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test serve driver overlap
# relates: [clutch/roadmap.py, clutch/serve.py, tests/integration/serve_rig.py, tests/integration/test_cli.py, tests/integration/test_scheduler.py]
# owner: engine
# verified: 96e46658
# hash: 9d3d4b00b26ade4393b2879c5b3fadf1ff6768eccaa77770239f5badab312fd4
import asyncio

import pytest

from clutch import roadmap, serve
from tests.integration.serve_rig import finish, graph, script, terminals, until, write
from tests.integration.test_cli import root  # noqa: F401
from tests.integration.test_scheduler import text
from tests.unit.test_phase_events import RecordingLog


@pytest.mark.asyncio
async def test_dispatch_starts_while_pass_runs(root, monkeypatch):
    first, release_ticket, entered, release_pass = (asyncio.Event() for _ in range(4))
    observations = []

    async def before(ctx, ticket, stage, attempt):
        if stage == "implement":
            if ticket.stem == "one":
                first.set()
                await release_ticket.wait()
            else:
                observations.append((entered.is_set(), release_pass.is_set()))

    script(monkeypatch, before=before)
    rig = await graph(root, monkeypatch)

    async def driver(c, log):
        entered.set()
        await release_pass.wait()

    rig.owner.driver = driver
    write(root, "one", text())
    run = asyncio.create_task(rig.owner.run())
    try:
        await until(rig, first.is_set)
        (root / "docs").mkdir(exist_ok=True)
        (root / roadmap.ROADMAP).write_text("roadmap\n")
        # An idle-only start gate cannot reach this boundary while one is implementing.
        await until(rig, entered.is_set)
        write(root, "two", text())
        release_ticket.set()
        await until(rig, lambda: bool(observations))
        # A select hold or mutations wrapper prevents two from implementing until release.
        assert observations == [(True, False)]
    finally:
        release_ticket.set()
        release_pass.set()
        await finish(rig, run)


@pytest.mark.asyncio
async def test_one_pass_at_a_time_and_shutdown_waits(root, monkeypatch):
    script(monkeypatch)
    rig = await graph(root, monkeypatch)
    (root / "docs").mkdir(exist_ok=True)
    (root / roadmap.ROADMAP).write_text("roadmap\n")
    release_first, release_second = asyncio.Event(), asyncio.Event()
    entries, active = [], []

    async def driver(c, log):
        # Starting another pass while the first is blocked violates single ownership.
        assert not active
        active.append(asyncio.current_task())
        entries.append(roadmap.settles(c.journal.read()))
        try:
            await (release_first if len(entries) == 1 else release_second).wait()
        finally:
            active.clear()

    rig.owner.driver = driver
    run = asyncio.create_task(rig.owner.run())
    try:
        await until(rig, lambda: len(entries) == 1)
        for stem in ("one", "two"):
            write(root, stem, text())
            await until(rig, lambda: bool(terminals(rig, stem)))
        cycles = rig.owner.responses[0].sent
        await until(rig, lambda: rig.owner.responses[0].sent > cycles + 1)
        # Clearing the task too soon would schedule a pass for each intervening settle.
        assert entries == [0]
        release_first.set()
        await until(rig, lambda: len(entries) == 2)
        # Updating driven at completion would lose these two intervening settles.
        assert entries == [0, 2]
        driver_task = rig.owner.driver_task
        rig.owner.stop()
        # Observe shutdown entering wait_driver, not merely one event-loop tick.
        await until(rig, lambda: rig.owner.driver_task is None or run.done())
        # Without the shutdown await, run returns or never clears the driver task.
        assert rig.owner.driver_task is None
        assert not run.done()
        # Aborting the pass instead of awaiting it would finish the captured task.
        assert not driver_task.done()
        release_second.set()
        await until(rig, run.done)
        assert await run == 0
        assert entries == [0, 2]
    finally:
        release_first.set()
        release_second.set()
        await finish(rig, run)


@pytest.mark.asyncio
@pytest.mark.parametrize("shutdown", [False, True])
async def test_pass_failure_stops_serve(root, monkeypatch, shutdown):
    script(monkeypatch)
    rig = await graph(root, monkeypatch)
    (root / "docs").mkdir(exist_ok=True)
    (root / roadmap.ROADMAP).write_text("roadmap\n")
    log = RecordingLog()
    rig.owner.log = log
    entered, release = asyncio.Event(), asyncio.Event()

    async def driver(c, log):
        entered.set()
        await release.wait()
        raise RuntimeError("pass exploded")

    rig.owner.driver = driver
    run = asyncio.create_task(rig.owner.run())
    try:
        await until(rig, entered.is_set)
        if shutdown:
            rig.owner.stop()
            await until(rig, lambda: rig.owner.driver_task is None or run.done())
        release.set()
        await until(rig, run.done)
        # Swallowing either the loop result or shutdown-wait error returns zero.
        assert await run == 1
        # Leaving the failed task attached handles it twice and logs twice.
        assert [(event, fields) for event, fields in log.events if event == "serve_failed"] == [("serve_failed", {"error": "pass exploded"})]
    finally:
        release.set()
        rig.owner.stop()
        await until(rig, run.done)
        await run
