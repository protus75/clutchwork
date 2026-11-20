"""Reproduce an operator keep failing to release a premise park."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Reproduce an operator keep failing to release a premise park.
# relates: [clutch/drain.py, clutch/journal.py]
# owner: engine
# verified: d7719818
# hash: a8bda5fbb03b1d3d9369d2f5efe0c9005002fb725ad31f8591cdb091f48fef2b

import json

from clutch.drain import parked_blob
from clutch.journal import Event, EventType


def event(kind, body):
    return Event(1, kind, "2026-01-01T00:00:00+00:00", "work", None, body)


def main() -> None:
    events = [
        event(EventType.STATE_TRANSITION, {"to": "running", "ticket_sha": "B"}),
        event(EventType.STATE_TRANSITION, {"to": "premise_failed", "stage": "implement"}),
        event(EventType.SIGNAL, {"signal": "reject_verdict", "verdict": "keep", "actor": "operator"}),
    ]
    passed = parked_blob(events, "work") is None
    print(json.dumps({"regression_result": "pass" if passed else "defect"}))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
