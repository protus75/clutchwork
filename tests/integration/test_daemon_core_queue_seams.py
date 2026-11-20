# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test daemon core queue seams
# relates: [tests/dispatch_settle.py, tests/integration/test_daemon_composition.py]
# owner: engine
# verified: 148a8874
# hash: e2559dca78154f1ff694b9747bc0757108bf44bb6c62578704ffe671ea091e33
import json

import pytest

from tests.dispatch_settle import dispatch_settled
from tests.integration.test_daemon_composition import CoreRig


@pytest.mark.asyncio
async def test_production_core_writes_queue_to_checkout_seams(tmp_path):
    async def prepare(checkout):
        async def dispatch(ticket):
            return "done"

        return dispatch

    rig = CoreRig(tmp_path, prepare=prepare)
    rig.journal.dir = tmp_path / "other-state" / "journal"
    writes = []
    original_write = rig.fs.write

    def record(path, data):
        writes.append((path, data))
        original_write(path, data)

    rig.fs.write = record
    await rig.add("selected")
    await dispatch_settled(rig.core.scheduler)
    queue_writes = [(path, data) for path, data in writes if path.name == "queue.json"]
    assert len(queue_writes) == 1
    assert queue_writes[0][0] == rig.checkout.config.state_dir / "queue.json"
    assert queue_writes[0][0] != rig.journal.dir.parent / "queue.json"
    assert json.loads(queue_writes[0][1])["order"] == ["selected"]
