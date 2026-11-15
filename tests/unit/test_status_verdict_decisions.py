"""Non-accepted control decisions are projected in journal order."""

from types import SimpleNamespace

from clutch.journal import EventType
from clutch.status import project, render


def event(request, verb, decision, reason, **extra):
    return SimpleNamespace(
        type=EventType.SIGNAL,
        ticket=None,
        key=None,
        ts="2026-01-01T00:00:00+00:00",
        body={"kind": "control_decision", "request_id": request, "verb": verb, "decision": decision, "reason": reason, **extra},
    )


def test_nonaccepted_decisions_and_render():
    status = project(
        [
            event("z-request", "confirm", "stale", "hold changed", stem="draft"),
            event("a-request", None, "rejected", "invalid request"),
        ]
    )
    assert status.verdict_decisions == (("z-request", "confirm", "draft", "stale", "hold changed"), ("a-request", "", "", "rejected", "invalid request"))
    block = render(status).split("Verdict decisions:\n", 1)[1].split("\n\n", 1)[0]
    assert block.splitlines() == ["- z-request: confirm draft: stale -- hold changed", "- a-request:  : rejected -- invalid request"]
    assert "None" not in block


def test_accepted_decision_is_not_shown():
    status = project([event("accepted-request", "reject", "accepted", "applied", stem="draft")])
    assert status.verdict_decisions == ()
    assert "Verdict decisions:" not in render(status)


def signal(stem, name, **extra):
    return SimpleNamespace(type=EventType.SIGNAL, ticket=stem, key=None, ts="2026-01-01T00:00:00+00:00", body={"signal": name, **extra})


def test_later_verdicts_retire_decisions():
    for verb, name, extra in (
        ("confirm", "draft_confirmed", {}),
        ("reject", "reject_verdict", {"verdict": "kill"}),
        ("confirm", "reject_verdict", {"verdict": "keep", "actor": "machine"}),
    ):
        status = project([event("request", verb, "stale", "changed", stem="draft"), signal("draft", name, **extra)])
        assert status.verdict_decisions == ()
        assert "Verdict decisions:" not in render(status)


def test_only_later_matching_verdict_retires():
    decision = event("request", "confirm", "stale", "changed", stem="draft")
    expected = (("request", "confirm", "draft", "stale", "changed"),)
    transition = SimpleNamespace(type=EventType.STATE_TRANSITION, ticket="draft", key=None, ts="2026-01-01T00:00:00+00:00", body={"to": "merged"})
    for events in ([decision], [decision, transition], [signal("draft", "draft_confirmed"), decision], [decision, signal("other", "draft_confirmed")]):
        assert project(events).verdict_decisions == expected


def test_stemless_rejection_survives_signals_and_renders_empty_fields():
    status = project([event("invalid", None, "rejected", "bad shape"), signal("draft", "draft_confirmed"), signal("draft", "reject_verdict", verdict="kill")])
    assert status.verdict_decisions == (("invalid", "", "", "rejected", "bad shape"),)
    assert "- invalid:  : rejected -- bad shape" in render(status)
