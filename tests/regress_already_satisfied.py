"""Carried reproducer for settled terminals with historical Reject routing."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried reproducer for settled terminals with historical Reject routing.
# relates: [clutch/journal.py, clutch/status.py]
# owner: engine
# verified: d7719818
# hash: ea2ddf4d03d7a8c373672f02f8dcb9aea324a39a6b7e3a3903b29ebd441fd529

import json
import sys
import traceback
from pathlib import Path


def main() -> int:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from clutch.journal import Event, EventType
        from clutch.status import reject_queue

        stem = "harden-serve-activation-3"
        events = [
            Event(v=1, type=EventType.STATE_TRANSITION, ts="2026-01-01T00:00:00+00:00", ticket=stem, key=None, body=body)
            for body in (
                {"to": "running", "ticket_sha": "a42b1dab2ed0cdefe392cfaa8c100a37ebdbed27"},
                {"to": "already_satisfied", "stage": "check", "reason": "already_satisfied", "dispatch": "reject_queue", "routed": "reject_queue"},
            )
        ]
        defect = stem in reject_queue(events)
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    print(json.dumps({"regression_result": "defect" if defect else "pass"}))
    return 1 if defect else 0


if __name__ == "__main__":
    sys.exit(main())
