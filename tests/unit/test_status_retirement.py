"""Settled work leaves the status projection while actionable work remains."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Settled work leaves the status projection while actionable work remains.
# relates: [clutch/journal.py, clutch/status.py]
# owner: engine
# verified: 9a610809
# hash: ffd9c750bf78e831da006a3aee4f8fcf55a70316d8996a9b6c1b1b6c84ae0133

from types import SimpleNamespace as NS

from clutch.journal import EventType
from clutch.status import project, render


def event(kind, ticket, body, key=None):
    return NS(type=kind, ticket=ticket, body=body, key=key, ts="2026-01-01T00:00:00+00:00")


def transition(stem, state):
    return event(EventType.STATE_TRANSITION, stem, {"to": state})


def test_intake_drops_settled_and_rejected_stems():
    events = [event(EventType.SIGNAL, s, {"signal": "ticket_intake", "source": "human", "state": "confirmed", "commit": s}) for s in ("gone", "done", "same", "live")]
    events += [transition("gone", "rejected"), transition("done", "merged"), transition("same", "already_satisfied")]
    assert [row[0] for row in project(events).intake] == ["live"]


def test_blocked_keeps_only_states_needing_a_reader():
    states = ("gate_failed", "premise_failed", "infra_error", "incomplete", "abandoned", "rejected", "already_satisfied", "merged", "running")
    events = [transition(state, state) for state in states]
    assert project(events).blocked == tuple(sorted((state, state) for state in states[:5]))


def test_verdict_refusals_drop_settled_and_rejected_stems():
    events = [event(EventType.EFFECT_COMPLETION, s, {"result": {"refusal": s}}, key=f"ticket-plane/{s}/1") for s in ("done", "held")]
    events += [transition("done", "merged"), transition("held", "gate_failed")]
    assert project(events).verdict_refusals == (("held", "held"),)


def test_reopens_drop_resolved_messages():
    messages = [
        NS(id="open", resolution=None, status="pending", reopen=True, summary="open", message_class="suggestion"),
        NS(id="closed", resolution=NS(kind="ticket", link="ticket"), status="resolved", reopen=False, summary="closed", message_class="suggestion"),
    ]
    box = NS(messages=lambda: messages, confirmed_tombstones=lambda policy: [])
    events = [event(EventType.SIGNAL, None, {"kind": "tombstone_auto_reopened", "box_id": id, "reports": 3}) for id in ("open", "closed")]
    assert [body["box_id"] for body in project(events, box=box).reopens] == ["open"]


def test_merged_renders_as_a_count():
    output = render(project([transition("alpha", "merged"), transition("beta", "merged")]))
    block = output.split("merged:\n", 1)[1].split("\n\n", 1)[0]
    assert "merged:\n2\n" in output
    assert "alpha" not in block and "beta" not in block
