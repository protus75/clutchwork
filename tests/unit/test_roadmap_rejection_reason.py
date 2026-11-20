# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test roadmap rejection reason
# relates: [clutch/journal.py, clutch/roadmap.py]
# owner: engine
# verified: 9a610809
# hash: 091e3a8cb2220ffac7a0babc6f09ddd497b43702272206f8a6ad807380814961
from clutch.journal import Event, EventType
from clutch.roadmap import rejection_reason


def event(kind, body, stem="work"):
    return Event(1, kind, "time", stem, None, body)


def test_reason_and_latest_diagnosis_lessons():
    events = [
        event(EventType.SIGNAL, {"signal": "diagnosis", "lessons": ["old lesson"]}),
        event(EventType.STATE_TRANSITION, {"to": "premise_failed", "reason": "bad premise", "routed": "reject_queue"}),
        event(EventType.SIGNAL, {"signal": "diagnosis", "lessons": ["fix the path", "check the fence"]}),
    ]
    assert rejection_reason(events, "work") == "bad premise fix the path check the fence"


def test_latest_routed_reason_ignores_unrouted_transition():
    events = [
        event(EventType.STATE_TRANSITION, {"to": "premise_failed", "reason": "earlier", "routed": "reject_queue"}),
        event(EventType.STATE_TRANSITION, {"to": "gate_failed", "reason": "later", "routed": "reject_queue"}),
        event(EventType.STATE_TRANSITION, {"to": "rejected", "reason": "unrouted"}),
    ]
    assert rejection_reason(events, "work") == "later"


def test_other_stems_and_verdict_are_ignored():
    events = [
        event(EventType.STATE_TRANSITION, {"to": "premise_failed", "reason": "other reason", "routed": "reject_queue"}, "other"),
        event(EventType.SIGNAL, {"signal": "diagnosis", "lessons": ["other lesson"]}, "other"),
        event(EventType.SIGNAL, {"signal": "reject_verdict", "reason": "verdict reason"}),
    ]
    assert rejection_reason(events, "work") == "rejected"
