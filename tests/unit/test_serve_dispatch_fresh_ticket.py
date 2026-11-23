"""Dispatch binds selection and run identity to the same committed ticket."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that Serve dispatch reads and journals the resolved committed ticket blob, re-offers a ticket whose committed content changed before the overlap check, and never runs a ticket whose committed blob fails to parse
# relates: [clutch/config.py, clutch/tickets.py, tests/dispatch_settle.py, tests/unit/test_scheduler_parallel_fill.py]
# owner: engine
# verified: 333d8906
# hash: e5f676dc8e95b7542c1a94b350b2ef6e0d108b3843e1f685d1cf4439ad68f436

from unittest.mock import AsyncMock

import pytest

from clutch.config import Parallel
from clutch.tickets import parse_ticket
from tests.dispatch_settle import dispatch_settled
from tests.unit.test_scheduler_parallel_fill import rig as scheduler_rig
from tests.unit.test_scheduler_parallel_fill import ticket
from tests.unit.test_serve_dispatch_containment import bodies, rig  # noqa: F401


@pytest.mark.asyncio
async def test_changed_selection_is_reoffered_before_overlap_check(rig):
    old = parse_ticket("aa", rig.text, rig.repo)
    fresh_text = rig.text.replace("- fix.py", "- fix.py\n- shared")
    fresh = parse_ticket("aa", fresh_text, rig.repo)
    busy = ticket("busy", path="shared/file")
    scheduler, _, _, _ = scheduler_rig([old], Parallel(enabled=True, max_runs=2))
    scheduler.journal = rig.journal
    scheduler.dispatch = rig.dispatch
    scheduler.flying["busy"] = busy
    rig.owner.core.scheduler = scheduler
    rig.owner.publish(fresh, fresh_text)
    scheduler.update(old)
    rig.owner.checkout.git._overrides["_run"] = fresh_text

    # Wrong: trust the last publication rather than the selected object's content.
    assert await dispatch_settled(scheduler) == old
    assert scheduler.pending == {"aa": fresh}
    assert scheduler.flying == {"busy": busy}
    assert bodies(rig, "aa") == []
    rig.callback.assert_not_called()
    # Wrong: start the widened fence alongside an overlapping flight.
    assert await scheduler.dispatch_next() is None
    assert scheduler.pending == {"aa": fresh}


@pytest.mark.asyncio
async def test_resolved_blob_is_read_and_journaled(rig):
    selected = parse_ticket("aa", rig.text, rig.repo)
    later = rig.text.replace("- fix.py", "- later.py")
    reads = []

    def show(repo, verb, ref):
        reads.append((verb, ref))
        return rig.text if ref == "sha" else later

    rig.owner.checkout.git._overrides["_run"] = show
    rig.callback.side_effect = AsyncMock(return_value="done")
    assert await rig.dispatch(selected) == "done"
    # Wrong: resolve one blob and read a later mutable main revision.
    assert reads == [("show", "sha")]
    assert rig.callback.call_args.args[0] == selected
    assert rig.callback.call_args.args[0] is not selected
    assert bodies(rig, "aa") == [{"to": "running", "ticket_sha": "sha"}]


@pytest.mark.asyncio
async def test_invalid_committed_blob_never_runs(rig):
    selected = parse_ticket("aa", rig.text, rig.repo)
    rig.owner.checkout.git._overrides["_run"] = "invalid"
    assert await rig.dispatch(selected) == "running"
    # Wrong: fall back to the selected ticket after the committed parse fails.
    rig.callback.assert_not_called()
    assert bodies(rig, "aa") == []
