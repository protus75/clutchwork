"""Detect verdict decisions left visible after an applied verdict."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clutch.journal import EventType
from clutch.status import project


def main():
    decision = SimpleNamespace(
        type=EventType.SIGNAL,
        ticket=None,
        key=None,
        ts="2026-01-01T00:00:00+00:00",
        body={"kind": "control_decision", "request_id": "request", "verb": "confirm", "stem": "draft", "decision": "stale", "reason": "changed"},
    )
    verdict = SimpleNamespace(type=EventType.SIGNAL, ticket="draft", key=None, ts="2026-01-01T00:00:00+00:00", body={"signal": "draft_confirmed"})
    passed = project([decision, verdict]).verdict_decisions == () and project([verdict, decision]).verdict_decisions == (("request", "confirm", "draft", "stale", "changed"),)
    print(json.dumps({"regression_result": "pass" if passed else "defect"}))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
