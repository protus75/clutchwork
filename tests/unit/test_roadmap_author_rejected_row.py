# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks roadmap authoring leaves a rejected row's ticket unchanged and reports its rejection reason as a wait in author and status output
# relates: [clutch/journal.py, clutch/roadmap.py, tests/unit/test_roadmap_author.py]
# owner: engine
# verified: 18f3cf87
# hash: 770796cf29b4c8b2e4ff3f4eef61a7eed4b84d6356b1cf7fd9ebda875732bf05
import asyncio

from clutch import roadmap
from clutch.journal import EventType
from tests.unit.test_roadmap_author import put, r, run, setup


def test_rejected_row_is_left_and_reports_reason(setup):
    assert not any(hasattr(roadmap, name) for name in ("drive", "ship", "ship_when_queue_low"))
    checkout, box = setup
    put(checkout, r(1, "broken-row", content="**Authored** (`tickets/broken-row/`). Work."))
    path = checkout.repo / roadmap.ROADMAP
    original = path.read_bytes()
    checkout.journal.append(EventType.STATE_TRANSITION, {"to": "premise_failed", "routed": "reject_queue", "reason": "bad contract"}, ticket="broken-row")
    checkout.journal.append(EventType.STATE_TRANSITION, {"to": "rejected"}, ticket="broken-row")

    async def author(ids):
        raise AssertionError(ids)

    lines = run(checkout, 2, author)
    assert any("waits:" in line and "bad contract" in line for line in lines)
    assert path.read_bytes() == original
    assert not checkout.git.commits
    assert not box.messages()
    assert any("waits:" in line and "broken-row" in line and "bad contract" in line for line in asyncio.run(roadmap.status(checkout)))
