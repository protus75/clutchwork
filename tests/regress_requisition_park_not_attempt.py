"""Reproduce requisition parks incorrectly exhausting the attempts cap."""

import json

from clutch.caps import failed_attempts, spent
from clutch.config import Caps
from clutch.journal import Event, EventType


def main() -> None:
    events = [Event(1, EventType.STATE_TRANSITION, "2026-01-01T00:00:00+00:00", "red", None, body) for _ in range(5) for body in ({"to": "running"}, {"to": "premise_failed", "stage": "requisition"})]
    passed = failed_attempts(events, "red") == 0 and spent(Caps(), events, "red") is None
    print(json.dumps({"regression_result": "pass" if passed else "defect"}))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
