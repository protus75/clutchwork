# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test serve driver
# relates: [clutch/roadmap.py, tests/integration/serve_rig.py, tests/integration/test_cli.py, tests/integration/test_scheduler.py]
# owner: engine
# verified: 96e46658
# hash: 008213d5e6849b881a3fa00c7f705227563ec04c06d65febc25891382cecd795
import asyncio

import pytest

from clutch import roadmap
from tests.integration.serve_rig import finish, graph, script, terminals, until, write
from tests.integration.test_cli import root  # noqa: F401
from tests.integration.test_scheduler import text


@pytest.mark.asyncio
@pytest.mark.parametrize("present", [True, False])
async def test_serve_runs_driver_beside_admission(root, monkeypatch, present):
    second_implement = asyncio.Event()

    async def before(ctx, ticket, stage, attempt):
        if ticket.stem == "two" and stage == "implement":
            second_implement.set()

    calls, _, _ = script(monkeypatch, before=before)
    rig = await graph(root, monkeypatch)
    if present:
        (root / "docs").mkdir(exist_ok=True)
        (root / roadmap.ROADMAP).write_text("roadmap\n")
    write(root, "one", text())
    if not present:
        write(root, "two", text())
    driven = []

    async def driver(c, log):
        count = roadmap.settles(c.journal.read())
        if count == 1:
            write(root, "two", text())
            await second_implement.wait()
        driven.append((count, list(calls)))

    rig.owner.driver = driver
    run = asyncio.create_task(rig.owner.run())
    try:
        await until(rig, lambda: len(terminals(rig)) >= 2 and (not present or len(driven) >= 3))
        if present:
            assert [count for count, _ in driven] == [0, 1, 2]
            # Holding admission for the pass cannot record two's implement here.
            assert [call[0] for call in driven[1][1] if call[1] == "implement"] == ["one", "two"]
        else:
            assert driven == []
        assert len([call for call in calls if call[1] == "implement"]) == 2
    finally:
        await finish(rig, run)
