# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify that the roadmap driver skips the release gate while roadmap.ahead or more confirmed tickets are unsettled and runs it once fewer remain.
# relates: [clutch/roadmap.py, clutch/status.py, tests/fakes.py]
# owner: engine
# verified: a8fa2c67
# hash: 2dafef7974bcb5268f9557e0e2a18b7a86b1c60744d969018e19d63af447fbb4
from types import SimpleNamespace

import pytest

from clutch import roadmap
from clutch.journal import EventType
from tests.fakes import FakeJournal

TICKET = "---\nstate: {state}\nsource: human\npriority: P1\nkind: chore\n---\n"


def write(root, stem, state="confirmed"):
    (root / "tickets" / stem).mkdir(parents=True)
    (root / "tickets" / stem / "ticket.md").write_text(TICKET.format(state=state))


@pytest.mark.asyncio
@pytest.mark.parametrize("queued, gated", [(3, False), (2, True)])
async def test_gate_waits_while_queue_is_full(tmp_path, monkeypatch, queued, gated):
    journal = FakeJournal()
    for n in range(queued):
        write(tmp_path, f"open-{n}")
    write(tmp_path, "done")
    journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="done")
    write(tmp_path, "retired")
    journal.append(EventType.STATE_TRANSITION, {"to": "rejected"}, ticket="retired")
    write(tmp_path, "unconfirmed", state="draft")
    calls = []

    async def ship(checkout):
        calls.append(checkout)
        return ["gate ok"]

    monkeypatch.setattr(roadmap, "ship", ship)
    checkout = SimpleNamespace(repo=tmp_path, journal=journal, config=SimpleNamespace(roadmap=SimpleNamespace(ahead=3)))
    lines = await roadmap.ship_when_queue_low(checkout)
    # Merged, rejected and draft tickets never hold the gate back; only confirmed, unsettled ones do.
    assert (bool(calls), lines) == ((True, ["gate ok"]) if gated else (False, [f"gate: waits until fewer than 3 confirmed tickets are unsettled ({queued} now)"]))
