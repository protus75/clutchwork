import asyncio

import pytest

from clutch import roadmap
from tests.integration.serve_rig import finish, graph, script, terminals, until, write
from tests.integration.test_cli import root  # noqa: F401
from tests.integration.test_scheduler import text


@pytest.mark.asyncio
@pytest.mark.parametrize("present", [True, False])
async def test_serve_holds_admission_for_the_driver(root, monkeypatch, present):
    calls, _, _ = script(monkeypatch)
    rig = await graph(root, monkeypatch)
    if present:
        (root / "docs").mkdir(exist_ok=True)
        (root / roadmap.ROADMAP).write_text("roadmap\n")
    write(root, "one", text())
    write(root, "two", text())
    driven = []

    async def driver(c, log):
        driven.append((roadmap.settles(c.journal.read()), list(calls)))

    rig.owner.driver = driver
    run = asyncio.create_task(rig.owner.run())
    try:
        await until(rig, lambda: len(terminals(rig)) >= 2 and (not present or len(driven) >= 3))
        if present:
            assert [count for count, _ in driven] == [0, 1, 2]
            assert len([call for call in driven[1][1] if call[1] == "implement"]) == 1
        else:
            assert driven == []
        assert len([call for call in calls if call[1] == "implement"]) == 2
    finally:
        await finish(rig, run)
