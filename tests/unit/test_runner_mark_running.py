# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test runner mark running
# relates: [clutch/journal.py, clutch/runner.py]
# owner: engine
# verified: 9a610809
# hash: db6ebd15897542997ea89e46cc155d098104256aeb9cb518a54a0c7ccf1205d7
from clutch.journal import EventType
from clutch.runner import mark_running


def test_mark_running_writes_one_transition():
    events = []

    class Journal:
        def append(self, kind, body, *, ticket=None, key=None):
            events.append((kind, body, ticket, key))

    mark_running(Journal(), "a", "sha1")
    assert events == [(EventType.STATE_TRANSITION, {"to": "running", "ticket_sha": "sha1"}, "a", None)]
