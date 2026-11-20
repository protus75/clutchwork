# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test roadmap stuck rows
# relates: [clutch/box.py, clutch/journal.py, clutch/roadmap.py, tests/unit/test_roadmap_status.py]
# owner: engine
# verified: 9a610809
# hash: 7c568a11e153594976bb408c96914312e888474770a643b944aa329e385a387a
import asyncio

from clutch import roadmap
from clutch.box import Box, Resolution, RoadmapRow
from clutch.journal import Event, EventType
from tests.unit.test_roadmap_status import HEADER, fixture, row


def test_rejected_linked_row_waits():
    rows = roadmap.parse("### 1.0.0\n" + HEADER + row(1, "rejected-row", "`tickets/rejected-row/`"))
    choice = roadmap.choose(rows, states={"rejected-row": "rejected"}, files=set())
    assert choice.open == 0
    assert len(choice.waits) == 1 and "rejected" in choice.waits[0].reason and "new stem" in choice.waits[0].road


def test_draft_linked_row_waits():
    rows = roadmap.parse("### 1.0.0\n" + HEADER + row(1, "d", "`tickets/d/`"))
    choice = roadmap.choose(rows, states={}, files=set(), drafts=frozenset({"d"}))
    assert choice.open == 0 and "still a draft" in choice.waits[0].reason
    assert not roadmap.choose(rows, states={}, files=set()).waits


def test_status_rejected_row_single_wait(tmp_path):
    checkout, _, _, events = fixture(tmp_path)
    (tmp_path / roadmap.ROADMAP).write_text("### 1.0.0\n" + HEADER + row(2, "r-row", "`tickets/r-row/`"))
    events.append(Event(1, EventType.STATE_TRANSITION, "ts", "r-row", None, {"to": "rejected"}))
    box = Box(checkout.config.state_dir / "box", checkout.fs)
    payload = RoadmapRow(number=2, release="1.0.0", stem="r-row", owner="roadmap", kind="feature", priority="P1", content="Work.", plan=roadmap.ROADMAP)
    for n in (1, 2):
        id_, _ = box.enqueue(message_class="roadmap_row", origin=f"roadmap/r-row-r{n}", summary=f"Work [re-file {n}]", roadmap_row=payload)
        box.resolve(id_, Resolution(kind="declined", link="missing"))
    lines = asyncio.run(roadmap.status(checkout))
    waits = [line for line in lines if line.startswith("waits: row 2 r-row:")]
    assert len(waits) == 1 and "rejected" in waits[0]


def test_merged_reports_draft(tmp_path):
    checkout, _, _, _ = fixture(tmp_path)
    (tmp_path / roadmap.ROADMAP).write_text("### 1.0.0\n" + HEADER + row(2, "d-row", "`tickets/d-row/`") + row(3, "missing-row"))
    path = tmp_path / "tickets/d-row/ticket.md"
    path.parent.mkdir(parents=True)
    path.write_text("---\nstate: draft\n---\n")
    result, lines = asyncio.run(roadmap.merged(checkout, ["d-row", "missing-row"]))
    assert not result
    assert lines == ["roadmap merged: row 2 d-row is a draft", "roadmap merged: row 3 missing-row is not in the journal"]


def test_skipped_rows_have_visible_blocker(tmp_path):
    checkout, _, _, events = fixture(tmp_path)
    text = (
        "### 1.0.0\n"
        + HEADER
        + row(1, "reject", "`tickets/reject/`")
        + row(2, "declined")
        + row(3, "draft", "`tickets/draft/`")
        + row(4, "after-reject", depends="`reject`")
        + row(5, "after-declined", depends="`declined`")
        + row(6, "after-draft", depends="`draft`")
    )
    (tmp_path / roadmap.ROADMAP).write_text(text)
    path = tmp_path / "tickets/draft/ticket.md"
    path.parent.mkdir(parents=True)
    path.write_text("---\nstate: draft\n---\n")
    events.append(Event(1, EventType.STATE_TRANSITION, "ts", "reject", None, {"to": "rejected"}))
    box = Box(checkout.config.state_dir / "box", checkout.fs)
    payload = RoadmapRow(number=2, release="1.0.0", stem="declined", owner="roadmap", kind="feature", priority="P1", content="Work.", plan=roadmap.ROADMAP)
    id_, _ = box.enqueue(message_class="roadmap_row", origin="roadmap/declined", summary="Declined", roadmap_row=payload)
    box.resolve(id_, Resolution(kind="declined", link="missing"))
    rows = roadmap.parse(text)
    states = roadmap.last_states(events)
    choice = roadmap.choose(rows, states=states, files=set(), drafts=roadmap.draft_stems(tmp_path, rows))
    visible = {r.stem for r in choice.strike + choice.link + choice.ready} | {w.row.stem for w in choice.waits}
    skipped = [r for r in rows if not r.struck and r.stem not in visible]
    assert {r.stem for r in skipped} == {"after-reject", "after-declined", "after-draft"}
    assert all(any(dep in visible or (dep in states and states[dep] not in roadmap.SETTLED) for dep in roadmap.depends_on(r, rows)) for r in skipped)
    lines = asyncio.run(roadmap.status(checkout))
    assert all(any(f" {stem}:" in line for line in lines if line.startswith("waits:")) for stem in ("reject", "declined", "draft"))
