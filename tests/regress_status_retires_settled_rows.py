"""Detect settled journal rows remaining in status."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clutch.journal import EventType
from clutch.status import project, render


def main():
    def event(kind, stem, body, key=None):
        return NS(type=kind, ticket=stem, body=body, key=key, ts="2026-01-01T00:00:00+00:00")

    events = [
        event(EventType.SIGNAL, "done", {"signal": "ticket_intake", "source": "human", "state": "confirmed", "commit": "abc"}),
        event(EventType.SIGNAL, "live", {"signal": "ticket_intake", "source": "human", "state": "confirmed", "commit": "def"}),
        event(EventType.EFFECT_COMPLETION, "done", {"result": {"refusal": "old"}}, "ticket-plane/done/1"),
        event(EventType.EFFECT_COMPLETION, "held", {"result": {"refusal": "new"}}, "ticket-plane/held/1"),
        event(EventType.STATE_TRANSITION, "done", {"to": "merged"}),
        event(EventType.STATE_TRANSITION, "rejected", {"to": "rejected"}),
        event(EventType.STATE_TRANSITION, "held", {"to": "gate_failed"}),
        event(EventType.SIGNAL, None, {"kind": "tombstone_auto_reopened", "box_id": "open", "reports": 3}),
        event(EventType.SIGNAL, None, {"kind": "tombstone_auto_reopened", "box_id": "closed", "reports": 3}),
    ]
    messages = [
        NS(id="open", resolution=None, status="pending", reopen=True, summary="open", message_class="suggestion"),
        NS(id="closed", resolution=NS(kind="ticket", link="ticket"), status="resolved", reopen=False, summary="closed", message_class="suggestion"),
    ]
    status = project(events, box=NS(messages=lambda: messages, confirmed_tombstones=lambda policy: []))
    passed = (
        [r[0] for r in status.intake] == ["live"]
        and status.blocked == (("held", "gate_failed"),)
        and status.verdict_refusals == (("held", "new"),)
        and [r["box_id"] for r in status.reopens] == ["open"]
        and "merged:\n1\n" in render(status)
    )
    print(json.dumps({"regression_result": "pass" if passed else "defect"}))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
