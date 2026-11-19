from clutch.journal import EventType
from clutch.runner import mark_running


def test_mark_running_writes_one_transition():
    events = []

    class Journal:
        def append(self, kind, body, *, ticket=None, key=None):
            events.append((kind, body, ticket, key))

    mark_running(Journal(), "a", "sha1")
    assert events == [(EventType.STATE_TRANSITION, {"to": "running", "ticket_sha": "sha1"}, "a", None)]
