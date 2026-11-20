"""Reproduce an overruled premise being incorrectly parked."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Reproduce an overruled premise being incorrectly parked.
# relates: [clutch/drain.py, clutch/journal.py]
# owner: engine
# verified: d7719818
# hash: 84b58639bb7ab111a35508da0c68216edc9fe3aaf50dcef34ad52c9e132b66bf

import json
import sys

from clutch.drain import parked_blob
from clutch.journal import Event, EventType


def main() -> None:
    history = [
        Event(1, EventType.STATE_TRANSITION, "time", "work", None, {"to": "running", "ticket_sha": "ran-sha"}),
        Event(1, EventType.STATE_TRANSITION, "time", "work", None, {"to": "premise_failed", "stage": "implement", "dispatch": "escalate", "rung": {"tier": "high", "effort": "medium"}}),
    ]
    passed = parked_blob(history, "work") is None
    print(json.dumps({"regression_result": "pass" if passed else "defect"}))
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
