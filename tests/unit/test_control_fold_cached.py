# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that ControlInbox caches its control-decision projection, skipping journal iteration when nothing changed and invalidating it when a kill request is appended.
# relates: [clutch/control.py, clutch/journal.py]
# owner: engine
# verified: e23307f6
# hash: 190f847eaf32b384c65ea71d0c9e461268f613c93a61e7322fb7701ea1ef3f4f
import json
from pathlib import Path

import clutch.control as control
from clutch.journal import Event, EventType


class MemoryJournal:
    def __init__(self):
        self.events = []

    def read(self):
        return list(self.events)

    def append(self, type, body, *, ticket=None, key=None):
        event = Event(1, type, "timestamp", ticket, key, body)
        self.events.append(event)
        return event


def test_unchanged_journal_is_not_iterated(monkeypatch):
    journal = MemoryJournal()
    for _ in range(5000):
        journal.append(EventType.SIGNAL, {"signal": "heartbeat"})
    path = Path("pause-request.json")
    request = {"request_id": path.stem, "lifecycle_id": "live", "verb": "pause", "hold_id": None}
    inbox = control.ControlInbox(journal=journal, lifecycle_id="live", holds=set, apply=lambda _: None, files=lambda: [path], read=lambda _: json.dumps(request).encode(), known=lambda _: False)
    inbox.consume()

    original = control.decisions
    count = 0

    def counted(events):
        def counted_events():
            nonlocal count
            for event in events:
                count += 1
                yield event

        return original(counted_events())

    monkeypatch.setattr(control, "decisions", counted)
    inbox.consume()
    assert count == 0
    assert inbox.recover().pause_id == "pause-request"


def test_appended_kill_invalidates_cached_projection():
    journal = MemoryJournal()
    paths = []
    path = Path("kill-request.json")
    request = {"request_id": path.stem, "lifecycle_id": "live", "verb": "kill", "hold_id": None}
    inbox = control.ControlInbox(journal=journal, lifecycle_id="live", holds=set, apply=lambda _: None, files=lambda: paths, read=lambda _: json.dumps(request).encode(), known=lambda _: False)
    inbox.recover()
    paths.append(path)
    inbox.consume()
    assert inbox.recover().kill_requested
