# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify conditional main HEAD and preserved intake snapshot inputs.
# relates: [clutch/journal.py, clutch/serve.py, tests/unit/test_serve_idle_poll.py]
# owner: engine
# verified: fc08bb14
# hash: 00988465d680adeb8a11737333141f859cbc11377c435627f1e275a34fb86263
import pytest

from clutch.journal import EventType
from tests.unit.test_serve_idle_poll import owner


@pytest.mark.asyncio
@pytest.mark.parametrize("pending", [False, True])
async def test_main_moves_only_invalidate_pending_intake(owner, pending):
    owner.checkout.git.status_porcelain.return_value = " M tickets/refused/ticket.md\n" if pending else ""
    owner.checkout.git.rev_parse.return_value = "a"
    before = await owner.intake_snapshot()
    owner.checkout.git.rev_parse.return_value = "b"
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
        owner.checkout.git.status_porcelain.return_value = " M tickets/existing/ticket.md\n"
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
        owner.checkout.git.status_porcelain.return_value = " M tickets/existing/run.md\n"
    else:
        owner.checkout.journal.append(EventType.STATE_TRANSITION, {"to": "rejected"}, ticket="existing")
    # Dropping the selected input caches stale intake despite all other inputs staying fixed.
    assert await owner.intake_snapshot() != before
