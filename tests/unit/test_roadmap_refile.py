# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks a declined roadmap row is re-filed with its decision record's evidence up to the re-file cap, and re-filed with a distinct summary when the record is missing
# relates: [clutch/box.py, clutch/journal.py, clutch/roadmap.py, tests/unit/test_roadmap_author.py]
# owner: engine
# verified: 18f3cf87
# hash: a5259949aec9e42ff05a651ec76db605374c96d313e7766b790dce2d145da521
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
