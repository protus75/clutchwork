# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test roadmap operator reject reason
# relates: [clutch/journal.py, clutch/roadmap.py]
# owner: engine
# verified: 9a610809
# hash: 38151035d30a810b5f05463ccb9d98025262b0dfdbfab44233658392b92b8585
from clutch.journal import Event, EventType
from clutch.roadmap import rejection_reason


def test_operator_reason_and_context():
    def event(kind, body):
        return Event(1, kind, "time", "work", None, body)

    kill = event(EventType.SIGNAL, {"signal": "reject_verdict", "verdict": "kill", "actor": "operator", "reason": "fence too wide"})
    terminal = event(EventType.STATE_TRANSITION, {"routed": "reject_queue", "reason": "bad premise"})
    diagnosis = event(EventType.SIGNAL, {"signal": "diagnosis", "lessons": ["fix fence"]})
    assert rejection_reason([kill], "work") == "fence too wide"
    assert rejection_reason([terminal, diagnosis, kill], "work") == "fence too wide bad premise fix fence"
    kill.body.pop("reason")
    assert rejection_reason([kill], "work") == "rejected"
