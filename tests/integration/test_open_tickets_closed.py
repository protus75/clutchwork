import asyncio

from clutch.author import list_open_tickets
from clutch.box import parse_record, record_path
from clutch.journal import EventType
from clutch.llm import FakeLLM
from tests.integration.test_drain import commit_ticket, pause_checkout
from tests.integration.test_triage import enqueue, reply, root_with_box, run


def test_closed_tickets_and_tombstones(tmp_path, monkeypatch):
    root, box = root_with_box(tmp_path)
    for stem, state in [("live", "confirmed"), ("rej", "rejected"), ("jrej", "confirmed"), ("sat", "confirmed"), ("done", "confirmed")]:
        commit_ticket(root, stem, f"---\nstate: {state}\n---\n\n## Goal / Why\n{stem} goal\n")
    checkout = pause_checkout(root)
    for stem, state in [("jrej", "rejected"), ("sat", "already_satisfied"), ("done", "merged")]:
        checkout.journal.append(EventType.STATE_TRANSITION, {"to": state}, ticket=stem)
    assert asyncio.run(list_open_tickets(checkout)) == "live: live goal"
    ids = [enqueue(box, f"concern {stem}") for stem in ("rej", "live", "done", "sat", "jrej")]
    llm = FakeLLM([reply("tombstone", link=stem) for stem in ("rej", "live", "done", "sat", "jrej")])
    assert run(root, monkeypatch, llm) == 0
    for id, stem, kind in zip(ids, ("rej", "live", "done", "sat", "jrej"), ("declined", "tombstone", "tombstone", "tombstone", "declined")):
        assert box.get(id).resolution.kind == kind
        record, body = parse_record((root / record_path(f"{kind}-{id}")).read_text())
        assert record.kind == kind
        if kind == "declined":
            assert f"unresolvable link: {stem}" in body
