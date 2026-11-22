# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that serve journals serve_upgrade_pending once on an engine tree change, and before serve_handoff after a merge that changes clutch/
# relates: [clutch/serve.py, tests/cli_helpers.py, tests/integration/serve_rig.py]
# owner: engine
# verified: a6482110
# hash: 40c461e468a2752612fc279263e3d05c5060c59e534ad071fbff9b0aac5388c5
import asyncio
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock

import pytest

from clutch.serve import Serve
from tests.cli_helpers import root
from tests.integration.serve_rig import admission_graph, admission_ticket, enable_upgrade, finish, until


@pytest.mark.disk_io_skip
@pytest.mark.asyncio
async def test_merge_journals_upgrade_before_handoff(root, monkeypatch):
    rig = await admission_graph(root, monkeypatch, {"work": {"clutch/thing.py": "changed\n"}})
    await enable_upgrade(rig, root)
    admission_ticket(root, "work", paths=("clutch/thing.py",))
    run = asyncio.create_task(rig.owner.run())
    try:
        await until(rig, run.done)
        assert await run == 7
        records = rig.journal.read()
        pending = [e for e in records if e.body.get("signal") == "serve_upgrade_pending"]
        handoff = [e for e in records if e.body.get("signal") == "serve_handoff"]
        assert len(pending) == len(handoff) == 1
        assert pending[0].body == {"signal": "serve_upgrade_pending", "clutch": await rig.checkout.git.rev_parse(root, "HEAD:clutch")}
        assert records.index(pending[0]) < records.index(handoff[0])
    finally:
        if not run.done():
            await finish(rig, run)


@pytest.mark.asyncio
async def test_detection_records_once():
    append = Mock()
    owner = NS(trees=("old",), upgrade=None, engine_trees=AsyncMock(return_value=("new",)), checkout=NS(journal=NS(append=append)))
    await Serve.check_upgrade(owner)
    await Serve.check_upgrade(owner)
    assert append.call_count == 1
    assert append.call_args.args[1] == {"signal": "serve_upgrade_pending", "clutch": "new"}
