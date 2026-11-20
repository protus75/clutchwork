"""Reproduce requisition parks incorrectly exhausting the attempts cap."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Reproduce requisition parks incorrectly exhausting the attempts cap.
# relates: [clutch/caps.py, clutch/config.py, clutch/journal.py]
# owner: engine
# verified: d7719818
# hash: 3d8f71459bb888c6e2f4cea5f934f5ae37237c2bb64868892681b2878437c733

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
