import pytest

from clutch import roadmap
from clutch.journal import EventType
from tests.unit.test_roadmap_author import put, r, run, setup


async def pending(ids):
    pass


@pytest.mark.parametrize("depends", ["`dependency-row`", "row 99"])
def test_rejected_row_waits_without_rewrite(setup, depends):
    checkout, box = setup
    put(checkout, r(1, "rejected-row", depends=depends))
    checkout.journal.append(EventType.STATE_TRANSITION, {"to": "rejected"}, ticket="rejected-row")
    path = checkout.repo / roadmap.ROADMAP
    original = path.read_bytes()

    lines = run(checkout, 1, pending)

    assert path.read_bytes() == original
    assert not [message for message in box.messages() if message.message_class == "roadmap_row"]
    assert any("row 1 rejected-row waits:" in line and ("dependency-row" if depends.startswith("`") else "unknown row 99") in line for line in lines)


def test_rejected_row_refiles_after_external_dependency_settles(setup):
    checkout, box = setup
    put(checkout, r(1, "rejected-row", depends="`dependency-row`"))
    checkout.journal.append(EventType.STATE_TRANSITION, {"to": "rejected"}, ticket="rejected-row")
    checkout.journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="dependency-row")

    lines = run(checkout, 1, pending)

    assert roadmap.parse((checkout.repo / roadmap.ROADMAP).read_text())[0].stem == "rejected-row-r1"
    assert [message.origin for message in box.messages()] == ["roadmap/rejected-row-r1"]
    assert not any("waits:" in line for line in lines)


@pytest.mark.parametrize("dependency", ["~~`dependency-row`~~", "`dependency-row`"])
def test_table_dependency_done_by_strike(setup, dependency):
    checkout, box = setup
    put(checkout, r(1, "rejected-row", depends="row 2"), r(2, "dependency-row").replace("`dependency-row`", dependency))
    checkout.journal.append(EventType.STATE_TRANSITION, {"to": "rejected"}, ticket="rejected-row")
    if not dependency.startswith("~~"):
        checkout.journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="dependency-row")

    run(checkout, 1, pending)

    assert [message.origin for message in box.messages()] == ["roadmap/rejected-row-r1"]
