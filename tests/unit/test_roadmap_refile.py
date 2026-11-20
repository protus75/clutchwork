# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test roadmap refile
# relates: [clutch/box.py, clutch/journal.py, clutch/roadmap.py, tests/unit/test_roadmap_author.py]
# owner: engine
# verified: 9a610809
# hash: 0becbdfc907b7364970f2cdd0a853532c5b553fe03eaebfa24caec93986ec38b
import asyncio

from clutch import roadmap
from clutch.box import DecisionRecord, Resolution, record_path, render_record
from clutch.journal import EventType
from tests.unit.test_roadmap_author import put, r, run, setup


def test_declines_refile_with_evidence_and_cap(setup):
    checkout, box = setup
    put(checkout, r(1, "held-row"))

    async def decline(ids):
        box.resolve(ids[0], Resolution(kind="declined", link="declined-one"))

    run(checkout, 1, decline)
    assert len(box.messages()) == 1
    path = checkout.repo / record_path("declined-one")
    path.parent.mkdir(parents=True)
    path.write_text(render_record(DecisionRecord(id="declined-one", kind="declined", link="held-row", reopen_after_days=1), "Evidence: use the documented seam\n"))
    run(checkout, 1, decline)
    messages = box.messages()
    assert len(messages) == 2
    assert "use the documented seam [re-file 1]" in messages[-1].summary
    assert not any("re-files spent" in line for line in asyncio.run(roadmap.status(checkout)))
    run(checkout, 1, decline)
    assert len(box.messages()) == 3
    lines = run(checkout, 1, decline)
    assert len(box.messages()) == 3
    assert any("held-row" in line and "use the documented seam" in line for line in lines)
    assert any("held-row" in line and "use the documented seam" in line for line in asyncio.run(roadmap.status(checkout)))


def test_missing_record_refiles(setup):
    checkout, box = setup
    put(checkout, r(1, "missing-row"))

    async def decline(ids):
        box.resolve(ids[0], Resolution(kind="declined", link="missing"))

    run(checkout, 1, decline)
    run(checkout, 1, decline)
    first, second = box.messages()
    assert first.summary != second.summary
    assert second.summary.endswith(" [re-file 1]")


def test_rejected_linked_row_is_rewritten(setup):
    checkout, box = setup
    put(checkout, r(1, "old-row"))

    async def pending(ids):
        pass

    run(checkout, 1, pending)
    put(checkout, r(1, "old-row", content="**Authored** (`tickets/old-row/`). Build it."))
    checkout.journal.append(EventType.STATE_TRANSITION, {"to": "premise_failed", "reason": "bad premise", "routed": "reject_queue"}, ticket="old-row")
    checkout.journal.append(EventType.SIGNAL, {"signal": "diagnosis", "lessons": ["fix the path"]}, ticket="old-row")
    checkout.journal.append(EventType.STATE_TRANSITION, {"to": "rejected"}, ticket="old-row")
    run(checkout, 1, pending)
    row = roadmap.parse((checkout.repo / roadmap.ROADMAP).read_text())[0]
    assert row.stem == "old-row-r1" and row.content == "Build it." and not row.linked
    assert box.messages()[-1].origin == "roadmap/old-row-r1"
    assert "bad premise" in box.messages()[-1].summary
    assert "fix the path" in box.messages()[-1].summary
    assert "[re-file 1]" in box.messages()[-1].summary
    assert checkout.git.commits[-1][0] == "clutch(roadmap): refile old-row as old-row-r1"


def test_rejected_without_messages_refiles_twice(setup):
    checkout, box = setup
    put(checkout, r(1, "empty-row"))
    checkout.journal.append(EventType.STATE_TRANSITION, {"to": "rejected"}, ticket="empty-row")

    async def pending(ids):
        pass

    lines = run(checkout, 1, pending)
    assert not any("give the row a new stem" in line for line in lines)
    checkout.journal.append(EventType.STATE_TRANSITION, {"to": "rejected"}, ticket="empty-row-r1")
    run(checkout, 1, pending)
    checkout.journal.append(EventType.STATE_TRANSITION, {"to": "rejected"}, ticket="empty-row-r2")
    run(checkout, 1, pending)
    assert [m.origin for m in box.messages()] == ["roadmap/empty-row-r1", "roadmap/empty-row-r2"]
    assert roadmap.parse((checkout.repo / roadmap.ROADMAP).read_text())[0].stem == "empty-row-r2"
