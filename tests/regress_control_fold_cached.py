# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Standalone regression script that exits 1 and reports a defect if ControlInbox.consume re-folds an unchanged journal through control.decisions instead of using its cached projection.
# relates: [clutch/control.py, clutch/journal.py]
# owner: engine
# verified: e23307f6
# hash: bd2931f54552b82986daf2a2231857c5efb20a98be663c6a592c28d0e403f723
import json
import sys
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


def main():
    try:
        journal = MemoryJournal()
        for _ in range(5000):
            journal.append(EventType.SIGNAL, {"signal": "heartbeat"})
        path = Path("pause-request.json")
        request = {"request_id": path.stem, "lifecycle_id": "live", "verb": "pause", "hold_id": None}
        inbox = control.ControlInbox(journal=journal, lifecycle_id="live", holds=set, apply=lambda _: None, files=lambda: [path], read=lambda _: json.dumps(request).encode(), known=lambda _: False)
        inbox.consume()
        if inbox.recover().pause_id != path.stem:
            raise ValueError("pause decision missing")
        original = control.decisions
        count = 0

        def counted(events):
            def counted_events():
                nonlocal count
                for event in events:
                    count += 1
                    yield event

            return original(counted_events())

        control.decisions = counted
        inbox.consume()
    except Exception as exc:
        print(f"regression error: {exc}", file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    print(json.dumps({"regression_result": "defect" if count else "pass"}))
    return 1 if count else 0


if __name__ == "__main__":
    sys.exit(main())
