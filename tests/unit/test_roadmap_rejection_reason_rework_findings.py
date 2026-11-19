from clutch.journal import Event, EventType
from clutch.roadmap import rejection_reason


def test_latest_routed_findings_precede_lessons():
    events = [
        Event(1, EventType.STATE_TRANSITION, "time", "work", None, {"reason": "old", "routed": "reject_queue", "rework_findings": ["old finding"]}),
        Event(2, EventType.STATE_TRANSITION, "time", "work", None, {"reason": "x", "routed": "reject_queue", "rework_findings": ["fence gap; add path", "missing seam; add seam"]}),
        Event(3, EventType.SIGNAL, "time", "work", None, {"signal": "diagnosis", "lessons": ["lesson"]}),
    ]
    # Wrong: omit findings, pick the older terminal, or put findings after lessons.
    assert rejection_reason(events, "work") == "x fence gap; add path missing seam; add seam lesson"
