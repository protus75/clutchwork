# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify that a main HEAD move changes the serve intake snapshot only when intake is pending, and that content, directory, removal, status and journal-state changes still change it.
# relates: [clutch/journal.py, clutch/serve.py, tests/unit/test_serve_idle_poll.py]
# owner: engine
# verified: 53cd7139
# hash: 421100974b47de46f8f631a7be35400e244b2f1f85fefc18f422ebba82605555
import pytest

from clutch.journal import EventType
from tests.unit.test_serve_idle_poll import owner


@pytest.mark.asyncio
@pytest.mark.parametrize("pending", [False, True])
async def test_main_moves_only_invalidate_pending_intake(owner, pending):
    owner.checkout.git._overrides["status_porcelain"] = " M tickets/refused/ticket.md\n" if pending else ""
    owner.checkout.git._overrides["rev_parse"] = "a"
    before = await owner.intake_snapshot()
    owner.checkout.git._overrides["rev_parse"] = "b"
    after = await owner.intake_snapshot()
    # Unconditional HEAD invalidates idle scans; omitting HEAD strands refusals.
    assert (before != after, before[3], after[3]) == ((True, "a", "b") if pending else (False, None, None))


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["content", "directory", "removed", "status", "state"])
async def test_other_intake_inputs_still_invalidate(owner, change):
    path = owner.checkout.repo / "tickets/existing/ticket.md"
    owner.checkout.fs.write(path, b"before")
    owner.stems = lambda: ["existing"]
    owner.read = lambda stem: owner.checkout.fs.read_bytes(owner.checkout.repo / f"tickets/{stem}/ticket.md").decode()
    if change == "state":
        owner.checkout.git._overrides["status_porcelain"] = " M tickets/existing/ticket.md\n"
    before = await owner.intake_snapshot()
    if change == "content":
        owner.checkout.fs.write(path, b"after")
    elif change == "directory":
        (owner.checkout.repo / "tickets/new").mkdir()
    elif change == "removed":
        path.unlink()
        path.parent.rmdir()
        owner.stems = lambda: []
    elif change == "status":
        owner.checkout.git._overrides["status_porcelain"] = " M tickets/existing/run.md\n"
    else:
        owner.checkout.journal.append(EventType.STATE_TRANSITION, {"to": "rejected"}, ticket="existing")
    # Dropping the selected input caches stale intake despite all other inputs staying fixed.
    assert await owner.intake_snapshot() != before
