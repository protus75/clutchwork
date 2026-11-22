# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the production daemon core writes queue.json through the checkout filesystem seam into the configured state directory
# relates: [tests/dispatch_settle.py, tests/integration/test_daemon_composition.py]
# owner: engine
# verified: 92889fdb
# hash: 612c3e6385cdc47bcbbace5dbda902b16c953721def4c9e6e243a8121b3a0a6b
import json

import pytest

from tests.daemon_helpers import CoreRig
from tests.dispatch_settle import dispatch_settled

pytestmark = pytest.mark.disk_io_skip


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
