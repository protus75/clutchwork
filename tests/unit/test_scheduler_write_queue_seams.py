# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test scheduler write queue seams
# relates: [clutch/scheduler.py, tests/dispatch_settle.py]
# owner: engine
# verified: 9a610809
# hash: 36ba039d435153e6d0727dda8b9db168bdd159297eab448ce67f1151f22fc6d0
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from clutch.scheduler import Scheduler
from tests.dispatch_settle import dispatch_settled


@pytest.mark.asyncio
async def test_queue_uses_injected_seams():
    writes = []
    fs = SimpleNamespace(write=lambda path, data: writes.append((path, data)))
    journal = SimpleNamespace(read=lambda: [])

    def clock():
        return datetime(2026, 3, 4, 5, 6, tzinfo=UTC)

    async def dispatch(ticket):
        pass

    async def sha(stem):
        return ""

    scheduler = Scheduler(
        journal, dispatch, state_dir=Path("/state"), fs=fs, clock=clock, caps=lambda: None, ticket_sha=sha, quarantined=set, drought_parked=set, completed_unmerged=lambda: 0, max_unmerged=1
    )
    ticket = SimpleNamespace(stem="chosen", frontmatter=SimpleNamespace(state="confirmed", priority="P2"), depends=(), runs_before=())
    scheduler.update(ticket)
    await dispatch_settled(scheduler)
    assert len(writes) == 1
    assert writes[0][0] == Path("/state/queue.json")
    value = json.loads(writes[0][1])
    assert value["at"] == "2026-03-04T05:06:00+00:00"
    assert value["order"] == ["chosen"]
